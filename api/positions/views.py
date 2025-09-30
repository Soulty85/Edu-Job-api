from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from recruitment_process.models import Application

from .models import Department, Position
from .serializers import DepartmentSerializer, PositionSerializer, PositionCreateSerializer, BulkStageUpdateSerializer

from recruitment_process.serializers import ApplicationListSerializer, RecruitmentStageSerializer
from recruitment_process.models import Comment


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        today = timezone.now().date()
        
        queryset = Department.objects.annotate(
            open_positions_count = Count(
                'positions',
                filter=Q(
                    ~Q(positions__status__in=["pourvue", "annulee"]) &
                    Q(positions__application_deadline__gte=today)
                ),
                distinct=True
            ),
            ongoing_applications_count=Count(
                'positions__applications',
                filter=Q(
                    positions__applications__is_active=True,
                    positions__application_deadline__gte=today
                ),
                distinct=True
            )
        ).order_by('name')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Statistiques globales RH"""
        total_positions = Position.objects.count()
        open_positions = Position.objects.filter(status='ouverte').count()
        total_applications = Application.objects.count()
        active_applications = Application.objects.filter(is_active=True).count()
        rejected_applications = Application.objects.filter(is_active=False).count()
        
        return Response({
            "total_positions": total_positions,
            "open_positions": open_positions,
            "total_applications": total_applications,
            "active_applications": active_applications,
            "rejected_applications": rejected_applications
        })


class PositionViewSet(viewsets.ModelViewSet):
    serializer_class = PositionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = Position.objects.select_related('department', 'created_by').annotate(
            applications_count=Count('applications')
        )
        
        # Filtres
        status = self.request.query_params.get('status')
        department = self.request.query_params.get('department')
        contract_type = self.request.query_params.get('contract_type')
        
        if status:
            queryset = queryset.filter(status=status)
        if department:
            queryset = queryset.filter(department_id=department)
        if contract_type:
            queryset = queryset.filter(contract_type=contract_type)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PositionCreateSerializer
        return PositionSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Statistiques pour une position spécifique"""
        position = self.get_object()
        
        stats = {
            'total_applications': position.applications.count(),
            'open_status': position.is_open(),
            'days_until_deadline': (position.application_deadline - timezone.now().date()).days if position.application_deadline else None
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['get'])
    def applications(self, request, pk=None):
        """Lister les candidatures d'une position (paginated)"""
        position = self.get_object()
        applications = position.applications.select_related(
            'candidate__user', 
            'position__current_stage'
        ).prefetch_related('comments').order_by('-applied_at')

        
        page = self.paginate_queryset(applications)
        serializer = ApplicationListSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def open_positions(self, request):
        """Liste des positions ouvertes"""
        open_positions = Position.objects.filter(
            status='ouverte',
            application_deadline__gte=timezone.now().date()
        ).select_related('department')
        
        serializer = self.get_serializer(open_positions, many=True)
        return Response(serializer.data)
        
    @action(detail=True, methods=['post'])
    def next_stage(self, request, pk=None):
        """Passer toutes les candidatures actives de cette position au stage suivant"""
        position = self.get_object()
        serializer = BulkStageUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                current_stage = position.current_stage
                if not current_stage:
                    return Response(
                        {'error': 'Cette position n\'a pas de stage courant.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                next_stage = current_stage.next_stage()
                if not next_stage:
                    return Response(
                        {'error': 'Aucun stage suivant disponible.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Récupérer les candidatures actives de cette position
                active_applications = position.applications.filter(is_active=True)
                
                approved_count = 0
                rejected_count = 0
                
                for application in active_applications:
                    if application.is_approved_current_stage:
                        # Candidature approuvée - elle passe au stage suivant
                        application.is_approved_current_stage = False  # Réinitialiser pour le nouveau stage
                        application.save()
                        approved_count += 1
                        
                        # Pour un passage au stage suivant
                        if serializer.validated_data.get('global_comment'):
                            Comment.objects.create(
                                application=application,
                                author=request.user,
                                content=f"[Passage au stage suivant] {serializer.validated_data['global_comment']}"
                            )
                    else:
                        # Candidature non approuvée - rejet automatique
                        application.is_active = False
                        application.rejection_reason = "Non approuvée lors du passage au stage suivant"
                        application.rejection_stage = current_stage
                        application.save()
                        rejected_count += 1
                        
                        Comment.objects.create(
                            application=application,
                            author=request.user,
                            content="Candidature automatiquement rejetée lors du passage au stage suivant"
                        )
                
                
                # Mettre à jour le stage de la position
                position.current_stage = next_stage
                position.save()
                
                return Response({
                    'message': f'{approved_count} candidature(s) passée(s) au stage suivant, {rejected_count} rejetée(s).',
                    'next_stage': RecruitmentStageSerializer(next_stage).data,
                    'approved_count': approved_count,
                    'rejected_count': rejected_count
                })
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def stage_statistics(self, request, pk=None):
        """Statistiques des candidatures par stage pour cette position"""
        position = self.get_object()
        current_stage = position.current_stage
        
        if not current_stage:
            return Response({'error': 'Cette position n\'a pas de stage courant.'})
        
        applications = position.applications.all()
        
        stats = {
            'position': position.title,
            'current_stage': RecruitmentStageSerializer(current_stage).data,
            'total_active': applications.filter(is_active=True).count(),
            'approved_current_stage': applications.filter(is_active=True, is_approved_current_stage=True).count(),
            'pending_approval': applications.filter(is_active=True, is_approved_current_stage=False).count(),
            'total_rejected': applications.filter(is_active=False).count(),
            'can_proceed_to_next': applications.filter(is_active=True, is_approved_current_stage=True).count() > 0
        }
        
        return Response(stats)
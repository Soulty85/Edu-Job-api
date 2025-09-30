from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction

from .models import Application, RecruitmentStage, Comment
from positions.models import Position
from .serializers import (
    ApplicationDetailSerializer,
    ApplicationCreateSerializer,
    RecruitmentStageSerializer,
    CommentSerializer,
)
from .permissions import IsNotCandidate


class RecruitmentStageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RecruitmentStage.objects.filter(is_active=True).order_by('order')
    serializer_class = RecruitmentStageSerializer
    permission_classes = [permissions.IsAuthenticated, IsNotCandidate]


class CommentViewSet(viewsets.ModelViewSet):
    """CRUD pour les commentaires d'application"""
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsNotCandidate]
    
    def get_queryset(self):
        application_id = self.request.query_params.get("application")
        qs = Comment.objects.select_related("application", "author")
        if application_id:
            qs = qs.filter(application_id=application_id)
        return qs.order_by("-created_at")
    
    def perform_create(self, serializer):
        application_id = self.kwargs.get("application_pk")  # vient du nested router
        serializer.save(
            author=self.request.user,
            application_id=application_id
        )


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        position_id = self.request.query_params.get('position')
        status_filter = self.request.query_params.get('status')
        
        queryset = Application.objects.select_related(
            'candidate__user', 'position', 'position__current_stage'
        )
        
        if position_id:
            queryset = queryset.filter(position_id=position_id)
        
        # filtrage par statut
        if status_filter == 'approved':
            queryset = queryset.filter(is_active=True, is_approved_current_stage=True)
        elif status_filter == 'rejected':
            queryset = queryset.filter(is_active=False)
        elif status_filter == 'pending':
            queryset = queryset.filter(is_active=True, is_approved_current_stage=False)
        else:
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    @action(detail=False, methods=["post"], url_path="apply")
    def apply(self, request):
        candidate = request.user.candidate_profile  # profil candidat lié au user
        serializer = ApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        position = serializer.validated_data["position"]
        
        # Vérifier si le candidat a déjà postulé à cette offre
        if Application.objects.filter(candidate=candidate, position=position).exists():
            return Response(
                {"detail": "Vous avez déjà postulé à cette offre."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer l'application
        application = serializer.save(candidate=candidate)
        
        return Response(
            ApplicationDetailSerializer(application).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approuver une candidature pour le stage courant"""
        application = self.get_object()
        
        if not application.is_active:
            return Response({'error': 'Impossible d\'approuver une candidature rejetée.'},
                            status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                application.is_approved_current_stage = True
                application.save()
                
                # ajouter un commentaire d'approbation
                Comment.objects.create(
                    application=application,
                    author=request.user,
                    content="Candidature approuvée pour cette étape"
                )
                
                return Response({
                    'message': 'Candidature approuvée avec succès.',
                    'application': ApplicationDetailSerializer(application).data
                })
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rejeter une candidature (la désactiver)"""
        application = self.get_object()
        rejection_reason = request.data.get('rejection_reason', '')
        
        if not application.is_active:
            return Response({'error': 'Cette candidature est déjà rejetée.'},
                            status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                application.is_active = False
                application.is_approved_current_stage = False
                application.rejection_reason = rejection_reason
                application.rejection_stage = application.current_stage
                application.save()
                
                Comment.objects.create(
                    application=application,
                    author=request.user,
                    content=f"Candidature rejetée: {rejection_reason}"
                )
                
                return Response({
                    'message': 'Candidature rejetée avec succès.',
                    'application': ApplicationDetailSerializer(application).data
                })
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        """Réactiver une candidature rejetée"""
        application = self.get_object()
        
        if application.is_active:
            return Response({'error': 'Cette candidature est déjà active.'},
                            status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                application.is_active = True
                application.is_approved_current_stage = False 
                application.rejection_reason = ''
                application.rejection_stage = None
                application.save()
                
                Comment.objects.create(
                    application=application,
                    author=request.user,
                    content="Candidature réactivée"
                )
                
                return Response({
                    'message': 'Candidature réactivée avec succès.',
                    'application': ApplicationDetailSerializer(application).data
                })
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

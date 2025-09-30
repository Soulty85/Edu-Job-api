# candidates/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Candidate, Document, DocumentType
from .serializers import (
    CandidateSerializer, CandidateCreateSerializer,
    DocumentSerializer, DocumentTypeSerializer,
)


class CandidateViewSet(viewsets.ModelViewSet):
    serializer_class = CandidateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # les utilisateurs ne voient que leur propre profil candidat
        if not self.request.user.is_staff and self.request.user.group != 'RH':
            return Candidate.objects.filter(user=self.request.user)
        return Candidate.objects.all().select_related('user')
    
    def get_serializer_class(self):
        if self.action in ['create']:
            return CandidateCreateSerializer
        return CandidateSerializer
    
    def get_object(self):
        # pour les non-staff et non-RH, retourner toujours leur propre profil
        if not self.request.user.is_staff and self.request.user.group != 'RH':
            return get_object_or_404(Candidate, user=self.request.user)
        return super().get_object()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Récupérer le profil du candidat connecté"""
        candidate, created = Candidate.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(candidate)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def update_profile(self, request, pk=None):
        """Mettre à jour le profil candidat"""
        candidate = self.get_object()
        serializer = self.get_serializer(candidate, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # les utilisateurs ne voient que leurs propres documents
        candidate = get_object_or_404(Candidate, user=self.request.user)
        return Document.objects.filter(candidate=candidate).select_related('document_type')
    
    def perform_create(self, serializer):
        candidate = get_object_or_404(Candidate, user=self.request.user)
        serializer.save(candidate=candidate)


class DocumentTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DocumentType.objects.all().order_by('name')
    serializer_class = DocumentTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]




# recruitment_process/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CandidateViewSet, DocumentViewSet, DocumentTypeViewSet


router = DefaultRouter()

router.register(r'candidates', CandidateViewSet, basename='candidate')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'document-types', DocumentTypeViewSet, basename='document-type')

urlpatterns = [
    path('', include(router.urls))
]
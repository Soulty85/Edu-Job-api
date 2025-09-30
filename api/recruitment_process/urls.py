# recruitment_process/urls.py
from django.urls import path, include
from rest_framework_nested import routers
from .views import ApplicationViewSet, RecruitmentStageViewSet, CommentViewSet


router = routers.DefaultRouter()
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'recruitment-stages', RecruitmentStageViewSet, basename='recruitment-stage')

applications_router = routers.NestedDefaultRouter(router, r'applications', lookup='application')
applications_router.register(r'comments', CommentViewSet, basename='application-comments')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(applications_router.urls)),
]


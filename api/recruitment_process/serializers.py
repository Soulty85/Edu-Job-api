
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Application, Comment, RecruitmentStage


class RecruitmentStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecruitmentStage
        fields = '__all__'


class RejectApplicationSerializer(serializers.Serializer):
    rejection_reason = serializers.CharField(required=True)


class ApplicationCandidateSerializer(serializers.ModelSerializer):
    """Serializer light pour les infos candidat dans une application"""
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    phone = serializers.CharField(read_only=True)
    
    class Meta:
        model = get_user_model().candidate_profile.related.related_model  # Accès au modèle Candidate
        fields = ['id', 'full_name', 'email', 'phone', 'nationality', 'birthdate', 'specialties']


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer utilisé par un candidat pour postuler à une offre"""
    
    class Meta:
        model = Application
        fields = ["id", "position", "applied_at"]
        read_only_fields = ["id", "applied_at"]


class ApplicationListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='candidate.user.get_full_name', read_only=True)
    email = serializers.EmailField(source='candidate.user.email', read_only=True)
    phone = serializers.CharField(source='candidate.phone', read_only=True)
    nationality = serializers.CharField(source='candidate.nationality', read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)
    current_stage_name = serializers.CharField(source='position.current_stage.name', read_only=True)
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Application
        fields = [
            'id',
            'full_name',
            'email',
            'phone',
            'nationality',
            'applied_at',
            'position_title',
            'current_stage_name',
            'status',
        ]
    
    def get_status(self, obj):
        if not obj.is_active:
            return 'rejected'
        elif obj.is_approved_current_stage:
            return 'approved'
        return 'pending'


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)
    author_email = serializers.EmailField(source="author.email", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "content", "author_name", "author_email", "created_at"]
        read_only_fields = ["author_name", "author_email", "created_at"]


class ApplicationDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="candidate.user.get_full_name")
    email = serializers.EmailField(source="candidate.user.email")
    phone = serializers.CharField(source="candidate.phone")
    nationality = serializers.CharField(source="candidate.nationality")
    birthdate = serializers.DateField(source="candidate.birthdate", format="%Y-%m-%d")
    specialties = serializers.CharField(source="candidate.specialties")
    applied_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    position_title = serializers.CharField(source="position.title")
    current_stage_name = serializers.CharField(source="current_stage.name", default="-")
    comments = CommentSerializer(many=True, read_only=True)
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Application
        fields = [
            "id",
            "full_name",
            "email",
            "phone",
            "nationality",
            "position_title",
            "birthdate",
            "specialties",
            "current_stage_name",
            "applied_at",
            "status",
            "comments",
        ]
    
    def get_status(self, obj):
        if not obj.is_active:
            return 'rejected'
        elif obj.is_approved_current_stage:
            return 'approved'
        return 'pending'
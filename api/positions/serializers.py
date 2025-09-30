# positions/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Department, Position


User = get_user_model()

class DepartmentSerializer(serializers.ModelSerializer):
    head_name = serializers.CharField(source='head.get_full_name', read_only=True)
    open_positions_count = serializers.IntegerField(read_only=True)
    ongoing_applications_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'description', 'head', 'head_name',
            'open_positions_count', 'ongoing_applications_count'
        ]
        read_only_fields = ['open_positions_count', 'ongoing_applications_count']


class PositionSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    is_open = serializers.BooleanField(read_only=True)
    applications_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Position
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by']


class PositionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ['title', 'department', 'subjects', 'level', 'workload', 
                'contract_type', 'start_date', 'application_deadline', 
                'description', 'requirements']
    
    def validate(self, data):
        if data['start_date'] < timezone.now().date():
            raise serializers.ValidationError("La date de début doit être future.")
        if data['application_deadline'] < timezone.now().date():
            raise serializers.ValidationError("La date limite est dépassée.")
        if data['application_deadline'] > data['start_date']:
            raise serializers.ValidationError("La date limite doit précéder la date de début.")
        return data


class BulkStageUpdateSerializer(serializers.Serializer):
    """Serializer pour le passage au stage suivant de toutes les candidatures actives"""
    global_comment = serializers.CharField(
        required=False, 
        allow_blank=True, 
        help_text="Commentaire global appliqué aux candidatures approuvées"
    )
# positions/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Candidate, Document, DocumentType
from authentication.serializers import UserSerializer


User = get_user_model()


class CandidateSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    age = serializers.SerializerMethodField(read_only=True)  # Champ calculé
    
    class Meta:
        model = Candidate
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_age(self, obj):
        from datetime import date
        if obj.birthdate:
            today = date.today()
            return today.year - obj.birthdate.year - ((today.month, today.day) < (obj.birthdate.month, obj.birthdate.day))
        return None


class CandidateCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, required=False)
    group = serializers.ChoiceField(choices=User.ROLE_CHOICES, default='Candidat', write_only=True)
    
    class Meta:
        model = Candidate
        fields = ['email', 'first_name', 'last_name', 'password', 'group', 
                'phone', 'address', 'nationality', 'birthdate', 'experience', 'specialties']
    
    def create(self, validated_data):
        from django.contrib.auth.hashers import make_password
        
        # Extraire les données utilisateur
        user_data = {
            'email': validated_data.pop('email'),
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'password': make_password(validated_data.pop('password', 'defaultpassword')),
            'group': validated_data.pop('group', 'Candidat')
        }
        
        # Créer l'utilisateur
        user = User.objects.create(**user_data)
        
        # Créer le profil candidat
        validated_data['user'] = user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Mettre à jour les données utilisateur si présentes
        user_data = {}
        if 'email' in validated_data:
            user_data['email'] = validated_data.pop('email')
        if 'first_name' in validated_data:
            user_data['first_name'] = validated_data.pop('first_name')
        if 'last_name' in validated_data:
            user_data['last_name'] = validated_data.pop('last_name')
        
        if user_data:
            User.objects.filter(id=instance.user.id).update(**user_data)
        
        return super().update(instance, validated_data)


class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = '__all__'


class DocumentSerializer(serializers.ModelSerializer):
    document_type_name = serializers.CharField(source='document_type.name', read_only=True)
    filename = serializers.CharField(read_only=True)
    
    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['uploaded_at']


class BulkStageUpdateSerializer(serializers.Serializer):
    stage_id = serializers.IntegerField()
    global_comment = serializers.CharField(required=False, allow_blank=True)





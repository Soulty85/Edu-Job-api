from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import AccessToken

from .models import User
from candidates.models import Candidate


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=40, min_length=8, write_only=True)
    password_confirm = serializers.CharField(max_length=40, min_length=8, write_only=True)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'password_confirm']
    
    def validate(self, attrs):
        password = attrs.get('password', '')
        password_confirm = attrs.get('password_confirm', '')
        
        if password != password_confirm:
            raise serializers.ValidationError('Les mots de passe ne correspondent pas')
        
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
        )
        
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class CandidateRegisterSerializer(serializers.ModelSerializer):
    user = UserRegisterSerializer()
    
    class Meta:
        model = Candidate
        fields = ['user', 'phone', 'address', 'birth_date', 'nationality']
        
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = UserRegisterSerializer().create(user_data)
        
        return Candidate.objects.create(user=user, **validated_data)


class UserLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    class Meta:
        model = User
        fields = ['email', 'password']
    
    def validate(self, attrs):
        user = authenticate(username=attrs["email"], password=attrs["password"])
        
        if not user or not user.is_active:
            raise serializers.ValidationError("Email ou mot de passe invalide")
        
        
        attrs["user"] = user
        
        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        access = AccessToken.for_user(user)
        access['full_name'] = user.get_full_name()
        access['email'] = user.email
        access['group'] = user.role
        
        token['access'] = str(access) 
        
        return token

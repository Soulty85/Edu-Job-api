from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import CandidateRegisterSerializer, UserLoginSerializer, CustomTokenObtainPairSerializer
from .models import User


class UserRegisterView(GenericAPIView):
    serializer_class = CandidateRegisterSerializer
    
    def post(self, request):
        user_data = request.data
        serializer = self.serializer_class(data=user_data)
        
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        user = serializer.data
        
        return Response({
            'data': user,
            'detail': 'Inscription reussi avec succes'
        }, status=status.HTTP_201_CREATED)


class UserLoginView(GenericAPIView):
    serializer_class = UserLoginSerializer
    
    def post(self, request):
        user_data = request.data
        serializer = self.serializer_class(data=user_data)
        
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        refresh = RefreshToken().for_user(user)
        refresh['group'] = user.group 
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
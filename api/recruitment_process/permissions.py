# core/permissions.py
from rest_framework import permissions

class IsNotCandidate(permissions.BasePermission):
    """
    Permission qui permet seulement aux utilisateurs qui ne sont pas des candidats.
    Les candidats ne peuvent pas commenter les candidatures.
    """
    def has_permission(self, request, view):
        # Vérifier si l'utilisateur est authentifié
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Vérifier si l'utilisateur a un profil candidat
        from candidates.models import Candidate
        return not Candidate.objects.filter(user=request.user).exists()

class IsHR(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='RH').exists()

class IsDepartmentHead(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='ChefDeDepartement').exists()

class IsDirector(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Direction').exists()

class IsRH(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.group == 'RH'

class IsStaffOrRH(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_staff or request.user.group == 'RH')

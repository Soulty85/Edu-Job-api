from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = (
        ('RH', 'RH'),
        ('Direction','Direction'),
        ('Chef de Département', 'Déartement'),
        ('Candidat', 'Candidat')
    )
    username = None
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, null=False, blank=False)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []



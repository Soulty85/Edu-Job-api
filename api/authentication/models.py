from django.db import models
from django.contrib.auth.models import AbstractUser

from.manager import CustomUserManager

# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = (
        ('RH', 'RH'),
        ('Direction','Direction'),
        ('ChefDeDepartement', 'ChefDeDepartement'),
        ('Candidat', 'Candidat')
    )
    username = None
    email = models.EmailField("email address", unique=True)
    group = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Candidat',null=False, blank=False)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    
    objects = CustomUserManager()
    def __str__(self):
        return self.email



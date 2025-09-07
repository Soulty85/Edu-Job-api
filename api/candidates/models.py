from django.db import models
from django.utils import timezone

from authentication.models import User


# Create your models here.
class Candidate(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True, null=False)
    address = models.TextField(blank=True)
    birth_date = models.DateField(blank=False, null=False)
    nationality = models.CharField(max_length=30, blank=False,null=False)
    # cv_url = models.CharField(max_length=255, blank=False, null=False)
    # diploma_url = models.CharField(max_length=255, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"


class Department(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name


class Position(models.Model):
    CONTRACT_TYPES = (
        ('vacataire', 'Vacataire'),
        ('permanent', 'Permanent'),
    )
    
    STATUS_CHOICES = (
        ('ouverte', 'Ouverte'),
        ('en_cours', 'En cours de sélection'),
        ('pourvue', 'Pourvue'),
        ('annulee', 'Annulée'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    subjects = models.CharField(max_length=300)
    level = models.CharField(max_length=100)
    hourly_volume=models.IntegerField()
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ouverte')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.department}"
    
    def is_open(self):
        return self.status == 'ouverte' and self.application_deadline >= timezone.now().date()
from django.db import models
from django.utils import timezone

from recruitment_process.models import RecruitmentStage
from authentication.models import User


class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    head = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='departments_headed')
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Position(models.Model):
    CONTRACT_TYPES = (
        ('vacataire', 'Vacataire'),
        ('permanent', 'Permanent'),
        ('CDD', 'CDD'),
    )
    
    STATUS_CHOICES = (
        ('ouverte', 'Ouverte'),
        ('en_cours', 'En cours de sélection'),
        ('pourvue', 'Pourvue'),
        ('annulee', 'Annulée'),
    )
    
    title = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions')
    subjects = models.CharField(max_length=300)
    level = models.CharField(max_length=100)
    workload = models.IntegerField(help_text="Volume horaire hebdomadaire")
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPES)
    start_date = models.DateField()
    application_deadline = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ouverte')
    description = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    current_stage = models.ForeignKey("recruitment_process.RecruitmentStage", on_delete=models.SET_NULL, null=True, blank=True, related_name='positions_at_stage')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_positions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # a la creation, definir le premier stage comme stage courant
        if not self.pk and not self.current_stage:
            first_stage = RecruitmentStage.objects.filter(is_active=True).order_by('order').first()
            if first_stage:
                self.current_stage = first_stage
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} - {self.department}"
    
    def is_open(self):
        return self.status == 'ouverte' and self.application_deadline >= timezone.now().date()
    
    def applications_count(self):
        return self.applications.count()
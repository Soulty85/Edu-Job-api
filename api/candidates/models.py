from django.db import models
from django.utils import timezone

from authentication.models import User

import os


def candidate_document_path(instance, filename):
    return f"candidates/{instance.candidate.id}/{filename}"


class Candidate(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='candidate_profile')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    birthdate = models.DateField(null=True, blank=True)
    experience = models.TextField(blank=True, help_text="Expérience professionnelle")
    specialties = models.TextField(blank=True, help_text="Spécialités et compétences")
    
    class Meta:
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()}"
    
    def full_name(self):
        return self.user.get_full_name()
    
    def email(self):
        return self.user.email


class DocumentType(models.Model):
    name = models.CharField(max_length=100)
    is_required = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name


class Document(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='documents')
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to=candidate_document_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.candidate} - {self.document_type}"
    
    def filename(self):
        return os.path.basename(self.file.name)
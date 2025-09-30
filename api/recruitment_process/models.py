from django.db import models
from django.conf import settings

from authentication.models import User


class RecruitmentStage(models.Model):
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.name
    
    def next_stage(self):
        try:
            return RecruitmentStage.objects.filter(
                order__gt=self.order, 
                is_active=True
            ).order_by('order').first()
        except RecruitmentStage.DoesNotExist:
            return None


class Application(models.Model):
    candidate = models.ForeignKey('candidates.Candidate', on_delete=models.CASCADE, related_name='applications')
    position = models.ForeignKey("positions.Position", on_delete=models.CASCADE, related_name='applications')
    is_active = models.BooleanField(default=True)
    is_approved_current_stage = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True)
    rejection_stage = models.ForeignKey(RecruitmentStage, on_delete=models.SET_NULL, null=True, blank=True, related_name='rejected_applications')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['candidate', 'position']
    
    def __str__(self):
        return f"{self.candidate} - {self.position}"
    
    @property
    def current_stage(self):
        """Retourne le stage courant de la position"""
        return self.position.current_stage
    
    def get_status_display(self):
        if not self.is_active:
            return 'Rejetée'
        elif self.is_approved_current_stage:
            return 'Approuvée pour ce stage'
        else:
            return 'En attente'


class Comment(models.Model):
    application = models.ForeignKey(
        "Application",
        related_name="comments",
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="application_comments",
        on_delete=models.SET_NULL,
        null=True
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Commentaire par {self.author} sur {self.application}"

from django.contrib.auth.models import BaseUserManager, UserManager
from django.core.exceptions import ValidationError
from django.core.validators import validate_email


class CustomUserManager(BaseUserManager):
    def email_validator(self, email):
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Entrez une addresse email address")
    
    def create_user(self, email, first_name, last_name, password, **extra_fields):
        if email:
            email=self.normalize_email(email)
            self.email_validator(email)
        else:
            raise ValidationError("Une addresse email est necessaire")
        
        if not first_name:
            raise ValidationError("Un prenom est necessaire")
        
        if not last_name:
            raise ValidationError("Un nom est necessaire")
        
        user=self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        return user
    
    def create_superuser(self, first_name, last_name, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)
        
        if extra_fields.get("is_staff") is not True:
            raise ValidationError("is staff doit etre True pour les utilisateurs")
        
        if extra_fields.get("is_superuser") is not True:
            raise ValidationError("is superuser doit etre True pour les utilisateurs")
        
        user = self.create_user(email, first_name, last_name, password, **extra_fields)
        user.save(using=self._db)
        
        return user
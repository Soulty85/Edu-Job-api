# generate_test_data_v3.py
import os
import django
import random
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from django.contrib.auth.models import Group
from candidates.models import Candidate, DocumentType
from positions.models import Department, Position
from recruitment_process.models import RecruitmentStage, Application, Comment

User = get_user_model()


def create_groups():
    groups = ['RH', 'ChefDeDepartement', 'Direction', 'Candidat']
    for group_name in groups:
        Group.objects.get_or_create(name=group_name)
    print("Groupes créés")


def create_users():
    """Crée des utilisateurs de test"""
    users_data = [
        # RH
        {'email': 'rh1@ecole.com', 'first_name': 'Marie', 'last_name': 'Dupont', 'group': 'RH'},
        {'email': 'rh2@ecole.com', 'first_name': 'Pierre', 'last_name': 'Martin', 'group': 'RH'},

        # Chefs de Département
        {'email': 'chef.math@ecole.com', 'first_name': 'Sophie', 'last_name': 'Garcia', 'group': 'ChefDeDepartement'},
        {'email': 'chef.info@ecole.com', 'first_name': 'Thomas', 'last_name': 'Bernard', 'group': 'ChefDeDepartement'},
        {'email': 'chef.phys@ecole.com', 'first_name': 'Nadia', 'last_name': 'Lambert', 'group': 'ChefDeDepartement'},
        {'email': 'chef.chim@ecole.com', 'first_name': 'Olivier', 'last_name': 'Roux', 'group': 'ChefDeDepartement'},

        # Direction
        {'email': 'directeur@ecole.com', 'first_name': 'Jean', 'last_name': 'Leroy', 'group': 'Direction'},

        # Candidats
        *[
            {'email': f'candidat{i}@mail.com', 'first_name': f'Cand{i}', 'last_name': 'Test', 'group': 'Candidat'}
            for i in range(1, 11)  # 10 candidats
        ]
    ]

    for user_data in users_data:
        user, created = User.objects.get_or_create(
            email=user_data['email'],
            defaults={
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'group': user_data['group']
            }
        )
        if created:
            user.set_password("testpass123")
            user.save()

            if user_data['group'] == 'Candidat':
                from candidates.models import Candidate
                Candidate.objects.create(
                    user=user,
                    phone=f"06{random.randint(10000000, 99999999)}",
                    address=f"{random.randint(1, 100)} rue de l'École, Paris",
                    nationality=random.choice(['Française', 'Espagnole', 'Italienne', 'Allemande']),
                    birthdate=timezone.now() - timedelta(days=random.randint(365*20, 365*40)),
                    experience="Expérience variée",
                    specialties="Spécialités diverses"
                )
    print("Utilisateurs créés")


def create_departments():
    data = [
        {'name': 'Mathématiques', 'description': 'Département de mathématiques'},
        {'name': 'Informatique', 'description': 'Département d’informatique'},
        {'name': 'Physique', 'description': 'Département de physique'},
        {'name': 'Chimie', 'description': 'Département de chimie'},
    ]
    chefs = list(User.objects.filter(group='ChefDeDepartement'))

    for i, d in enumerate(data):
        Department.objects.get_or_create(
            name=d['name'],
            defaults={'description': d['description'], 'head': chefs[i] if i < len(chefs) else None}
        )
    print("Départements créés")


def create_recruitment_stages():
    stages = [
        ('Réception candidature', 1),
        ('Pré-sélection RH', 2),
        ('Entretien pédagogique', 3),
        ('Validation Direction', 4),
        ('Proposition de contrat', 5),
        ('Signature & archivage', 6),
    ]
    for name, order in stages:
        RecruitmentStage.objects.get_or_create(
            name=name,
            defaults={'order': order, 'is_active': True}
        )
    print("Stages créés")


def create_positions():
    departments = list(Department.objects.all())
    rh_users = list(User.objects.filter(group='RH'))
    stages = list(RecruitmentStage.objects.filter(is_active=True).order_by('order'))

    if not departments or not rh_users or not stages:
        print("❌ Impossible de créer les positions (données manquantes)")
        return

    titles = [
        "Professeur de Mathématiques",
        "Enseignant en Informatique",
        "Professeur de Physique",
        "Professeur de Chimie",
        "Assistant en Informatique",
        "Maître de Conférences Mathématiques",
        "Chargé de TP Physique",
        "Vacataire Informatique",
        "Enseignant-Chercheur Chimie",
        "Professeur Associé Informatique"
    ]

    for i, title in enumerate(titles):
        department = departments[i % len(departments)]
        created_by = rh_users[i % len(rh_users)]
        current_stage = random.choice(stages[:3])  # On limite aux 3 premiers pour test

        Position.objects.get_or_create(
            title=title,
            defaults={
                'department': department,
                'subjects': "Matières variées",
                'level': random.choice(['Licence', 'Master']),
                'workload': random.choice([12, 16, 18]),
                'contract_type': random.choice(['permanent', 'vacataire']),
                'start_date': timezone.now() + timedelta(days=30 + i * 3),
                'application_deadline': timezone.now() + timedelta(days=15 + i * 2),
                'status': 'ouverte',
                'current_stage': current_stage,
                'description': f"Description du poste de {title}",
                'requirements': "Diplôme requis, expérience en enseignement",
                'created_by': created_by
            }
        )
    print("Positions créées")


def create_applications():
    candidates = list(Candidate.objects.all())
    positions = list(Position.objects.all())

    if not candidates or not positions:
        print("❌ Pas de candidats ou positions")
        return

    for position in positions:
        # 2 à 4 candidatures par offre
        num_apps = random.randint(2, 4)
        chosen_candidates = random.sample(candidates, num_apps)
        for cand in chosen_candidates:
            Application.objects.get_or_create(
                candidate=cand,
                position=position,
                defaults={
                    'is_active': True,
                    'is_approved_current_stage': random.choice([True, False])
                }
            )
    print("Candidatures créées")


def main():
    print("=== Génération des données V3 ===")
    create_groups()
    create_users()
    create_departments()
    create_recruitment_stages()
    create_positions()
    create_applications()
    print("=== Données générées avec succès ===")
    print("✅ Comptes de test: rh1@ecole.com / testpass123, etc.")


if __name__ == "__main__":
    main()

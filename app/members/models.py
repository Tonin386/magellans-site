from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import secrets
import string

ROLE_CHOICES = [
    ('P', "Président.e"),
    ('C', "Communication"),
    ('G', "Gestionnaire magasin"),
    ('T', "Trésorier.ère"),
    ('S', "Secrétaire"),
    ('M', "Membre"),
    ('E', "Externe"),
    ('O', 'Organisation') #Association, partenaire, entreprise...
]

GENDER_CHOICES = [
    ('M', 'Homme'),
    ('F', 'Femme'),
    ('O', 'Autre'),
]

class MemberManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The email field must be set')
        email = self.normalize_email(email)
        token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(128))
        user = self.model(email=email, api_token=token, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class Member(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name="Courriel")
    first_name = models.CharField(max_length=30, blank=True, verbose_name="Prénom")
    last_name = models.CharField(max_length=30, blank=True, verbose_name="Nom")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    is_staff = models.BooleanField(default=False, verbose_name="CA")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    donation = models.FloatField(default=0, verbose_name="Montant donation")
    phone = models.CharField(max_length=15, blank=True, verbose_name="N° téléphone")
    account = models.FloatField(default=0, verbose_name="Statut compte")
    role = models.CharField(max_length=1, choices=ROLE_CHOICES, default='E', verbose_name="Role")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, verbose_name="Sexe")
    api_token = models.CharField(max_length=128, null=True, blank=True, editable=False)

    objects = MemberManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = "Membre"
        verbose_name_plural = "Membres"

    def __str__(self):
        return "%s %s (%s)" % (self.first_name, self.last_name, self.email)
    
    def phone_formatted(self):
        return ' '.join(self.phone[i:i+2] for i in range(0, len(self.phone), 2))
    
    def account_formatted(self):
        if self.account == 0:
            return "±0.00€"
        return "+%.2f€" % self.account if self.account > 0 else "-%.2f€" % abs(self.account)
    
    def donation_formatted(self):
        if self.donation == 0:
            return "±0.00€"
        return "+%.2f€" % self.donation if self.donation > 0 else "-%.2f€" % abs(self.donation)
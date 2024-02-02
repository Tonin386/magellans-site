from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

ROLE_CHOICES = [
    ('P', "Président.e"),
    ('C', "Communication"),
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
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The username field must be set')
        username = self.normalize_username(username)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, password, **extra_fields)

class Member(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name="Courriel")
    username  = models.CharField(unique=True, verbose_name="Nom d'utilisateur")
    first_name = models.CharField(max_length=30, blank=True, verbose_name="Prénom")
    last_name = models.CharField(max_length=30, blank=True, verbose_name="Nom")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    is_staff = models.BooleanField(default=False, verbose_name="CA")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    donation = models.FloatField(default=0, verbose_name="Montant donation")
    phone = models.CharField(max_length=15, blank=True, verbose_name="N° téléphone")
    account = models.FloatField(default=0, verbose_name="Statut compte")
    role = models.CharField(max_length=1, choices=ROLE_CHOICES, default='M', verbose_name="Role")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, verbose_name="Sexe")

    objects = MemberManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = "Membre"
        verbose_name_plural = "Membres"

    def __str__(self):
        return "%s %s (%s)" % (self.first_name, self.last_name, self.username)
    
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
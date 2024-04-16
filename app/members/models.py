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
    ('M', "Membre Magellans & site"),
    ('Mx', "Membre Magellans & pas site"),
    ('E', "Inscrit site"),
    ('O', 'Organisation'), #Association, partenaire, entreprise...
    ('X', 'Externe site')
]

GENDER_CHOICES = [
    ('M', 'Homme'),
    ('F', 'Femme'),
    ('B', 'Non-binaire'),
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
        profile = Person.objects.create(email=email, first_name="Indéfini", last_name="Indéfini", gender="O", phone="Indéfini", site_profile=user)
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
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    is_staff = models.BooleanField(default=False, verbose_name="CA")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    donation = models.FloatField(default=0, verbose_name="Montant donation")
    account = models.FloatField(default=0, verbose_name="Statut compte")
    api_token = models.CharField(max_length=128, null=True, blank=True, editable=False)

    objects = MemberManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = "Membre"
        verbose_name_plural = "Membres"

    def save(self, *args, **kwargs):
        created = False
        if not hasattr(self, "site_person"):
            site_person = Person.objects.create(first_name="Inconnu", last_name="Inconnu", email="Inconnu", gender="O", role="E")
            self.site_person = site_person
            created = True

        self.is_staff = self.site_person.role in ['P', 'C', 'G', 'T', 'S']
            
        super().save(*args, **kwargs)
        if created:
            site_person.site_profile = self
            site_person.save()

    def __str__(self):
        return "%s %s (%s)" % (self.site_person.first_name, self.site_person.last_name, self.email)
    
    def phone_formatted(self):
        return ' '.join(self.site_person.phone[i:i+2] for i in range(0, len(self.site_person.phone), 2))
    
    def account_formatted(self):
        if self.account == 0:
            return "±0.00€"
        return "+%.2f€" % self.account if self.account > 0 else "-%.2f€" % abs(self.account)
    
    def donation_formatted(self):
        if self.donation == 0:
            return "±0.00€"
        return "+%.2f€" % self.donation if self.donation > 0 else "-%.2f€" % abs(self.donation)
    
    def first_name(self):
        return self.site_person.first_name
    
    def last_name(self):
        return self.site_person.last_name
    
    def gender(self):
        return self.site_person.get_gender_display()
    
    def phone(self):
        return self.site_person.phone
    
    def role(self):
        return self.site_person.get_role_display()
    
class UnregisteredMember(models.Model):
    class Meta:
        verbose_name = "Externe site"
        verbose_name_plural = "Externes site"

    def __str__(self):
        return "%s %s (%s)" % (self.ext_person.first_name, self.ext_person.last_name, self.ext_person.email)
    
    def phone_formatted(self):
        return ' '.join(self.ext_person.phone[i:i+2] for i in range(0, len(self.ext_person.phone), 2))

    def first_name(self):
        return self.ext_person.first_name
    
    def last_name(self):
        return self.ext_person.last_name
    
    def gender(self):
        return self.ext_person.get_gender_display()
    
    def phone(self):
        return self.ext_person.phone
    
    def email(self):
        return self.ext_person.email
    
    def role(self):
        return self.ext_person.get_role_display()

class Person(models.Model):
    email = models.EmailField(verbose_name="Courriel", null=True, blank=True)
    first_name = models.CharField(max_length=30, null=True, blank=True, verbose_name="Prénom")
    last_name = models.CharField(max_length=30, null=True, blank=True, verbose_name="Nom")
    phone = models.CharField(max_length=15, blank=True, verbose_name="N° téléphone")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True, verbose_name="Sexe")
    site_profile = models.OneToOneField(Member, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Profil site lié", related_name="site_person")
    ext_profile = models.OneToOneField(UnregisteredMember, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Profil externe lié", related_name="ext_person")
    role = models.CharField(max_length=2, choices=ROLE_CHOICES, default='X', verbose_name="Role")
    class Meta:
        verbose_name = "Personne"
        
    def __str__(self):
        return "%s %s (%s)" % (self.first_name, self.last_name, self.email)

    def phone_formatted(self):
        return ' '.join(self.phone[i:i+2] for i in range(0, len(self.phone), 2))
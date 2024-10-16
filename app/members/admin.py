from .models import *
from django.contrib import admin
from django.contrib.auth import get_user_model

class MemberAdmin(admin.ModelAdmin):
    def phone_formatted(self, obj):
        return ' '.join(obj.site_person.phone[i:i+2] for i in range(0, len(obj.site_person.phone), 2))
    
    def account_formatted(self, obj):
        if obj.account == 0:
            return "0.00€"
        return "+%.2f€" % obj.account if obj.account > 0 else "-%.2f€" % abs(obj.account)
    
    def donation_formatted(self, obj):
        if obj.donation == 0:
            return "0.00€"
        return "+%.2f€" % obj.donation if obj.donation > 0 else "-%.2f€" % abs(obj.donation)
    
    def first_name(self, obj):
        return obj.site_person.first_name
    
    def last_name(self, obj):
        return obj.site_person.last_name
    
    def gender(self, obj):
        return obj.site_person.gender

    def role(self, obj):
        return obj.site_person.role
    
    phone_formatted.short_description = "N° téléphone"
    account_formatted.short_description = "Statut compte"
    donation_formatted.short_description = "Montant donation"
    first_name.short_description = "Prénom"
    last_name.short_description = "Nom"
    gender.short_description = "Sexe"
    role.short_description = "Rôle"
    
    list_display = ('email', 'date_joined', 'last_name', 'first_name', 'is_staff', 'role', 'is_active', 'phone_formatted', 'account_formatted', 'donation_formatted', 'gender')
    list_filter = ('site_person__role', 'is_active', 'is_staff', 'site_person__gender')
    search_fields =  ('date_joined', 'email', 'site_person__last_name', 'site_person__first_name', 'is_staff', 'site_person__role', 'is_active', 'site_person__phone', 'site_person__gender')
    ordering = ('-date_joined', 'email', 'site_person__last_name', 'site_person__first_name', 'is_staff')

class PersonAdmin(admin.ModelAdmin):
    list_display = ('email', 'last_name', 'first_name', 'gender', 'phone', 'role')
    search_fields = ('email', 'last_name', 'first_name', 'gender', 'phone', 'role')
    ordering = ('email', 'last_name', 'first_name', 'gender', 'role')

class UnregisteredMemberAdmin(admin.ModelAdmin):
    def phone_formatted(self, obj):
        return ' '.join(obj.ext_person.phone[i:i+2] for i in range(0, len(obj.ext_person.phone), 2))
    
    def first_name(self, obj):
        return obj.ext_person.first_name
    
    def last_name(self, obj):
        return obj.ext_person.last_name
    
    def gender(self, obj):
        return obj.ext_person.gender
    
    def email (self, obj):
        return obj.ext_person.email
    
    list_display = ('email', 'last_name', 'first_name', 'gender', 'phone_formatted')
    search_fields = ('ext_person__email', 'ext_person__last_name', 'ext_person__first_name', 'ext_person__gender', 'ext_person__phone')
    ordering = ('ext_person__email', 'ext_person__last_name', 'ext_person__first_name', 'ext_person__gender')


admin.site.register(Member, MemberAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(UnregisteredMember, UnregisteredMemberAdmin)
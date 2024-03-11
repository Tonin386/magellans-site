from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Member

class MemberAdmin(admin.ModelAdmin):
    def phone_formatted(self, obj):
        return ' '.join(obj.phone[i:i+2] for i in range(0, len(obj.phone), 2))
    
    def account_formatted(self, obj):
        if obj.account == 0:
            return "0.00€"
        return "+%.2f€" % obj.account if obj.account > 0 else "-%.2f€" % abs(obj.account)
    
    def donation_formatted(self, obj):
        if obj.donation == 0:
            return "0.00€"
        return "+%.2f€" % obj.donation if obj.donation > 0 else "-%.2f€" % abs(obj.donation)
    
    phone_formatted.short_description = "N° téléphone"
    account_formatted.short_description = "Statut compte"
    donation_formatted.short_description = "Montant donation"
    
    list_display = ('date_joined', 'email', 'last_name', 'first_name', 'is_staff', 'role', 'is_active', 'phone_formatted', 'account_formatted', 'donation_formatted', 'gender')
    list_filter = ('role', 'is_active', 'is_staff', 'gender')
    search_fields =  ('date_joined', 'email', 'last_name', 'first_name', 'is_staff', 'role', 'is_active', 'phone_formatted', 'account_formatted', 'donation_formatted', 'gender')
    ordering = ('-date_joined', 'email', 'last_name', 'first_name', 'is_staff')

admin.site.register(Member, MemberAdmin)
from django import forms
from .models import *

class ProjectFundingRequestForm(forms.ModelForm):
    class Meta:
        model = ProjectFundingRequest
        fields = ['name', 'role', 'directors', 'genre', 'duration', 'production', 'previsional_shoot_start_date', 'previsional_shoot_end_date', 'explanation', 'funding_value', 'script', 'intention_note', 'previsional_budget_plan','contact_list']
        
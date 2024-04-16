from django.contrib import admin
from .models import *

class ProjectFundingRequestAdmin(admin.ModelAdmin):
    list_display = ('deposit_date', 'name', 'asker', 'role', 'directors', 'genre', 'duration', 'production', 'previsional_shoot_start_date', 'previsional_shoot_end_date', 'explanation', 'funding_value')
    search_fields = ('asker__site_person__first_name', 'asker__site_person__last_name', 'asker__site_person__email', 'role', 'explanation', 'genre')
    ordering = ('deposit_date', )
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'genre', 'short_desc', 'shoot_date', 'release_date')
    list_filter = ('genre', )
    search_fields = ('name', 'genre', 'short_desc', 'desc', )
    ordering = ('shoot_date', 'name', 'release_date', 'name')

admin.site.register(ProjectFundingRequest, ProjectFundingRequestAdmin)
admin.site.register(Project, ProjectAdmin)

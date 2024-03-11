from django.contrib import admin
from .models import *

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'genre', 'duration', 'short_desc', 'shoot_date', 'released_date')
    list_filter = ('genre', )
    search_fields = ('name', 'genre', 'duration', 'short_desc', 'shoot_date', 'released_date')
    ordering = ('shoot_date', 'name', 'released_date', 'name')

admin.site.register(Project, ProjectAdmin)

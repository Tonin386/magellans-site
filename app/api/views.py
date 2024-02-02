from django.http import JsonResponse
from dashboard.models import *
from warehouse.models import *
from members.models import *
from bank.models import *

def api_bank(request):
    return JsonResponse({})

def api_dashboard(request):
    return JsonResponse({})

def api_members(request):
    return JsonResponse({})

def api_warehouse(request):
    return JsonResponse({})

from django.shortcuts import render

def warehouse(request):
    return render(request, "warehouse.html", locals())
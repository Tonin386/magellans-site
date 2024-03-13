from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.views.generic.edit import UpdateView
from django.db.models.base import Model as Model
from django.utils.safestring import mark_safe
from django.db.models.query import QuerySet
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.shortcuts import render
from django.conf import settings
from .models import *
from .forms import *

def warehouse(request):
    tags = Tag.objects.all().order_by('name')
    items = Item.objects.all().order_by('name')
    completeProfile = request.user.first_name != "" and request.user.last_name != "" and request.user.phone != "" if type(request.user) == Member else True
    return render(request, "warehouse.html", locals())

def order(request):
    pks = request.GET.get("pks", "undefined")
    values = request.GET.get("values", "undefined")
    
    items = []
    
    if not pks == "undefined":
        pks = [int(pk) for pk in pks.replace(" ", "").split(",")]
        items = Item.objects.filter(pk__in=pks)
        
    if not values == "undefined":
        values = [int(value) for value in values.replace(" ", "").split(",")]
        
    items_values = list(zip(items, values))
    
    return render(request, "order.html", locals())

@require_POST
def placeOrder(request):
    form = PlaceOrderForm(request.POST)
    
    success = False
    
    if 'lastOrder' in request.COOKIES:
        lastOrderTime = datetime.strptime(request.COOKIES['lastOrder'], "%Y-%m-%d %H:%M:%S")
        timePassed = datetime.now() - lastOrderTime
        if not timePassed.seconds > 3600:
            tooManyOrders = True
            return render(request, "place_order.html", locals())
    
    if form.is_valid():
        try:
            startDate = form.cleaned_data['start_date'].strftime("%d/%m/%Y")
            endDate = form.cleaned_data['end_date'].strftime("%d/%m/%Y")
            message = mark_safe(request.POST.get('message'))
            orderText = request.POST.get('order_text').replace("\\n", "\n")
            
            subject = "Demande de réservation de matériel"
            user = request.user
            email_message = render_to_string('email_order.html', locals())
            send_mail(subject, email_message, settings.DEFAULT_FROM_EMAIL, ["contact@magellans.fr", user.email])
            success = True
            
        except Exception as e:
            print(str(e))
            
    response = render(request, "place_order.html", locals())
    if success:
        response.set_cookie('lastOrder', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
    return response

class EditItemDetailView(UpdateView):
    model = Item
    form_class = EditItemForm
    template_name = "edit_item_detail.html"
    success_url = reverse_lazy('warehouse')
    
    def get_object(self, queryset=None):
        return Item.objects.get(pk=self.kwargs['pk'])
    
class EditTagDetailView(UpdateView):
    model = Tag
    form_class = EditTagForm
    template_name = "edit_tag_detail.html"
    success_url = reverse_lazy('warehouse')
    
    def get_object(self, queryset=None):
        return Tag.objects.get(pk=self.kwargs['pk'])
    
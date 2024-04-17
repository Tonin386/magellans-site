from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.views.generic.edit import UpdateView
from django.db.models.base import Model as Model
from django.utils.safestring import mark_safe
from django.db.models.query import QuerySet
from django.views.generic import DetailView
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.shortcuts import render
from django.conf import settings
from .models import *
from .forms import *

def warehouse(request):
    title = "Magasin"
    og_description = "Magasin et liste du matériel proposé par l'association Magellans. "
    tags = Tag.objects.all().order_by('name')
    items = Item.objects.all().order_by('name')
    completeProfile = request.user.first_name != "" and request.user.last_name != "" and request.user.phone != "" if type(request.user) == Member else True
    return render(request, "warehouse.html", locals())

def order(request):
    title = "Réservation"
    og_description = "Effectuer une commande ou une réservation auprès du magasin de l'association Magellans."
    pks = request.GET.get("pks", "undefined")
    values = request.GET.get("values", "undefined")
    
    items = []
    
    if not pks == "undefined":
        pks = [int(pk) for pk in pks.replace(" ", "").split(",")]
        items = Item.objects.filter(pk__in=pks)
        
    if not values == "undefined":
        values = [int(value) for value in values.replace(" ", "").split(",")]
        
    items_values = list(zip(items, values))
    values = ",".join([str(x) for x in values])
    pks = ",".join([str (x) for x in pks])
    
    return render(request, "order.html", locals())

@require_POST
def placeOrder(request):
    title = "Validation réservation"
    og_description = "Validation d'une commande ou réservation auprès du magasin de l'association Magellans."
    form = PlaceOrderForm(request.POST)
    
    success = False
    
    if 'lastOrder' in request.COOKIES and not settings.DEBUG:
        lastOrderTime = datetime.strptime(request.COOKIES['lastOrder'], "%Y-%m-%d %H:%M:%S")
        timePassed = datetime.now() - lastOrderTime
        if not timePassed.seconds > 3600:
            tooManyOrders = True
            return render(request, "place_order.html", locals())
    
    if form.is_valid():
        try:
            startDate = request.POST.get('start_date')
            endDate = request.POST.get('end_date')
            message = mark_safe(request.POST.get('message'))
            pks = request.POST.get("pks", "undefined")
            quantities = request.POST.get("quantities", "undefined")
            pu_first_name = request.POST.get("pickup_first_name", request.user.first_name())
            pu_last_name = request.POST.get("pickup_last_name", request.user.last_name())
            pu_phone = request.POST.get("pickup_phone", request.user.phone())

            if pu_first_name == "":
                pu_first_name = request.user.first_name()
                
            if pu_last_name == "":
                pu_last_name = request.user.last_name()

            if pu_phone == "":
                pu_phone = request.user.phone()

            pu_phone = pu_phone.replace(" ", "").replace(".", "")

            if pks in ["undefined", ""] or quantities in ["undefined", ""]:
                return render(request, "place_order.html", locals())
            
            pks = pks.split(",")
            
            items = Item.objects.filter(pk__in=pks)
            items_values = list(zip(items, quantities))

            quantity_str = ""
            for item, quantity in items_values:
                quantity_str += str(quantity) + ","

            new_order = Order.objects.create(
                user=request.user,
                date_start=startDate, 
                date_end=endDate, 
                message=message,
                quantities=quantities,
                pickup_first_name=pu_first_name,
                pickup_last_name=pu_last_name,
                pickup_phone=pu_phone,
            )

            new_order.items.set(items)
            new_order.save()

            subject = "Demande de réservation de matériel"
            user = request.user
            email_message = render_to_string('email_order.html', locals())
            recipients = ["contact@magellans.fr", user.email]

            for warehouse_handler in Member.objects.filter(site_person__role="G"):
                recipients.append(warehouse_handler.email)

            send_mail(subject, email_message, settings.DEFAULT_FROM_EMAIL, recipients)
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = f"Magasin - Objet {self.object.name}"
        context['og-description'] = f"Page de gestion de l'objet {self.object.name}."

        return context
    
class EditTagDetailView(UpdateView):
    model = Tag
    form_class = EditTagForm
    template_name = "edit_tag_detail.html"
    success_url = reverse_lazy('warehouse')
    
    def get_object(self, queryset=None):
        return Tag.objects.get(pk=self.kwargs['pk'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = f"Magasin - Tag {self.object.name}"
        context['og-description'] = f"Page de gestion du tag {self.object.name}."

        return context
    
class OrderDetailView(DetailView):
    model = Order
    template_name = "order_detail.html"

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)

        obj = self.object
        quantities = obj.quantities.split(",")
        item_set = zip(quantities, obj.items.all())

        context['item_set'] = item_set
        context['title'] = f"Récapitulatif commande #{obj.pk}"
        context['og_description'] = f"Commande #{obj.pk} effectuée aurpès du magasin de l'association Magellans."

        return context
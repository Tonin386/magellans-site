from django.db.models.fields.files import ImageFieldFile
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.views.generic.edit import UpdateView
from django.db.models.base import Model as Model
from django.template.defaulttags import register
from django.core.files.base import ContentFile
from django.utils.safestring import mark_safe
from django.db.models.query import QuerySet
from django.views.generic import DetailView
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.forms import BaseModelForm
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.shortcuts import render
from api.utils import resize_image
from django.conf import settings
from .models import *
from .forms import *

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

def warehouse(request):
    title = "Magasin"
    og_description = "Magasin et liste du matériel proposé par l'association Magellans."
    tags = Tag.objects.all().order_by('name')
    items = Item.objects.all().order_by('name')
    completeProfile = request.user.first_name != "" and request.user.last_name != "" and request.user.phone != "" if type(request.user) == Member else True

    if request.user.is_authenticated:
        saved_order_pk = request.GET.get("order", "undefined")
        saved_order = None
        if not saved_order_pk == "undefined":
            try:
                saved_order = Order.objects.get(pk=saved_order_pk, user=request.user, status=0)
            except:
                saved_order_pk = "undefined"

        if saved_order_pk == "undefined":
            query = Order.objects.filter(user=request.user, status=0)
            if query.count() >= 1:
                saved_order = query[0]
            else:
                saved_order = Order.objects.create(user=request.user)
            
            saved_order_pk = saved_order.pk
            quantities = saved_order.load_quantities()
            keys = list(quantities.keys())
            for key in keys:
                quantities[int(key)] = quantities[key]
                del quantities[key]

        total_items = sum([int(quantities[x]) for x in quantities])

    return render(request, "warehouse.html", locals())

def order(request, pk):
    title = "Réservation"
    og_description = "Effectuer une commande ou une réservation auprès du magasin de l'association Magellans."
    order_pk = pk
    order = Order.objects.get(pk=order_pk)
    quantities = order.load_quantities()
    pks = list(quantities.keys())
    values = list(quantities.values())
    
    items = [Item.objects.get(pk=pk) for pk in pks] #Important to keep mapping intact
        
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
            order_pk = request.POST.get("order_pk", "undefined")
            startDate = request.POST.get('start_date')
            endDate = request.POST.get('end_date')
            project_name = request.POST.get('project_name')
            message = mark_safe(request.POST.get('message'))
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

            order = Order.objects.get(pk=order_pk)
            order.date_start = startDate
            order.date_end = endDate
            order.project_name = project_name
            order.message = message

            order.pickup_first_name = pu_first_name
            order.pickup_last_name = pu_last_name
            order.pickup_phone = pu_phone

            order.status = 1

            order.save()

            subject = "Demande de réservation de matériel"
            user = request.user
            formatted_startDate = datetime.strptime(startDate, "%Y-%m-%dT%H:%M")
            formatted_endDate = datetime.strptime(endDate, "%Y-%m-%dT%H:%M")
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
    
    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        image_file =  form.cleaned_data['image']
        if type(image_file) == ImageFieldFile:
            return super().form_valid(form)
        content = image_file.read()
        image = ContentFile(content, name=image_file.name)
        image = resize_image(image)
        if image:
            new_item = self.object
            path = f"{new_item.pk}.png"
            new_item.image.save(path, image)

        return super().form_valid(form)
    
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
        quantities = obj.load_quantities()
        items = [Item.objects.get(pk=pk) for pk in list(quantities.keys())]
        item_set = zip(quantities.values(), items)

        context['item_set'] = item_set
        context['title'] = f"Récapitulatif commande #{obj.pk}"
        context['og_description'] = f"Commande #{obj.pk} effectuée aurpès du magasin de l'association Magellans."

        return context
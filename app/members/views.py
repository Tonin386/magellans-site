from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from members.decorators import staff_required, login_required
from dashboard.forms import ProjectFundingRequestForm
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.safestring import mark_safe
from django.views.generic import DetailView
from dashboard.models import ResourceFile
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import render
from warehouse.models import Order
from django.conf import settings
from .forms import RegisterForm
from .models import Member
from bank.forms import *
from .forms import *
import secrets
import string

@login_required("Mon profil", "Accéder à son profil personnel sur le site de l'association Magellans.")
def my_profile(request):
    title = request.title
    og_description = request.og_description
    form = EditProfileForm(request.user.site_person)
    orders = Order.objects.filter(user=request.user).order_by('-date_created')
    invoices = Invoice.objects.filter(author=request.user).order_by('-date_created')
    if request.method == "POST":
        form = EditProfileForm(request.user.site_person, request.POST)
        if form.is_valid():
            request.user.site_person.first_name = form.cleaned_data['first_name']
            request.user.site_person.last_name = form.cleaned_data['last_name']
            request.user.site_person.phone = form.cleaned_data['phone'].replace(" ", "")
            request.user.site_person.gender = form.cleaned_data['gender']
            request.user.site_person.save()
            
    return render(request, 'my_profile.html', {'object': request.user, 'form': form, 'orders': orders, 'invoices': invoices, 'title': title, 'og_description': og_description})

@login_required("Créer une note de frais", "Page de création d'une note de frais pour les membres du site de l'association Magellans.")
def create_invoice(request):
    title = request.title
    og_description = request.og_description
    invoice_form = CreateInvoiceForm()
    if request.method == "POST":
        invoice_form = CreateInvoiceForm(request.POST)
        if invoice_form.is_valid():
            new_invoice = invoice_form.save()
            new_invoice.author = request.user
            new_invoice.save()
            linked_expenses = request.POST.get("expenses_ids")
            ids = linked_expenses[1:-1].split(",")

            for id in ids:
                expense = Expense.objects.get(pk=id)
                expense.linked_invoice = new_invoice
                expense.save()
            
            new_invoice.save()
            new_invoice.send_by_email()
            messages.success(request, 'La note de frais a bien été créée et envoyée au trésorier.')

    return render(request, "create_invoice.html", locals())

@login_required("Demande d'aide financière", "Formulaire de demande d'aide financière pour faire financer son projet par l'association Magellans.")
def create_funding_request(request):
    form = ProjectFundingRequestForm()
    title = request.title
    og_description = request.og_description
    if request.method == "POST":
        form = ProjectFundingRequestForm(request.POST, request.FILES)
        if form.is_valid():
            new_funding_request = form.save()

            new_funding_request.asker = request.user
            new_funding_request.save()

            new_funding_request.send_by_email()
            return render(request, "create_funding_request_success.html", {'title': title, 'og_description': og_description})

    return render(request, "create_funding_request.html", locals())

@login_required("Ressources pour les membres", "Ressources mises à disposition des membres de Magellans.")
def resources(request):
    title = request.title
    og_description = request.og_description
    resources = ResourceFile.objects.all()
    return render(request, "resources.html", locals())

def register(request):
    title = "Inscription"
    og_description = "Inscription au site de l'association Magellans."
    form = RegisterForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            new_user = form.save()
            new_user.is_active = False

            first_name=form.cleaned_data.get('first_name')
            last_name=form.cleaned_data.get('last_name')
            email=form.cleaned_data.get('email')
            gender=form.cleaned_data.get('gender', "O")
            phone=form.cleaned_data.get('phone', "")

            new_user.site_person.first_name = first_name
            new_user.site_person.last_name = last_name
            new_user.site_person.email = email
            new_user.site_person.gender = gender
            new_user.site_person.phone = phone.replace(" ", "")

            new_user.site_person.save()
            
            token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(128))
            new_user.api_token = token
            
            new_user.save()
            
            token = default_token_generator.make_token(new_user)
            uidb64 = urlsafe_base64_encode(force_bytes(new_user.pk))
            activation_url = "https://magellans.fr/membres/activate/{}/{}".format(uidb64, token)
            
            subject = "Activation de votre compte magellans.fr"
            message = mark_safe(render_to_string('registration/activation_email.html', {'user': new_user, 'activation_url': activation_url}))
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [new_user.email])

            messages.success(request, 'Vous avez reçu un email pour activer votre compte.')
        else:
            messages.error(request, form.errors)
            
    return render(request, "registration/register.html", locals())

def join_magellans(request):
    title = "Devenir membre"
    og_description = "Devenir un membre de l'association Magellans."

    return render(request, "registration/join_magellans.html", locals())

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Member.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Member.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):

        if user.is_active:
            return redirect("activation_already")

        # Activate user account
        user.is_active = True
        user.save()
    
        subject = "Nouvelle inscription"
        message = mark_safe(f"Un nouvel utilisateur vient d'activer son compte sur le site internet !\nPrénom : {user.first_name()}\nNom : {user.last_name()}\nEmail : {user.email}\nDate d'inscription : {user.date_joined.strftime('%A %d %B %Y %H:%M')}")
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL])

        # Redirect to success page or login page
        return redirect('activation_done')
    
    return redirect('activation_failed')

def activation_done(request):
    title = "Activation de compte réussie"
    og_description = "Activation réussie d'un compte utilisateur sur le site de l'association Magellans."
    return render(request, 'registration/activation_done.html', locals())

def activation_failed(request):
    title = "Activation de compte échouée"
    og_description = "Activation échouée d'un compte utilisateur sur le site de l'association Magellans."
    return render(request, 'registration/activation_failed.html', locals())

def activation_already(request):
    title = "Activation de compte déjà effectuée"
    og_description = "Activation d'un compte utilisateur déjà effectuée sur le site de l'association Magellans."
    return render(request, 'registration/activation_already.html', locals())

@method_decorator(staff_required("Profil utilisateur", "Page du profil utilisateur d'un membre du site de l'association Magellans."), name="dispatch")
class MemberDetailView(DetailView):
    model = Member
    template_name="member_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = "Profil utilisateur"
        context['og_description'] = "Page du profil utilisateur d'un membre du site de l'association Magellans."

        return context

@method_decorator(staff_required("Profil externe ou interne", "Page du profil d'une personne externe ou interne à l'association Magellans."), name="dispatch")
class PersonDetailView(DetailView):
    model = Person
    template_name = "person_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        members = Member.objects.all()
        context['members'] = members

        context['title'] = "Profil externe ou interne"
        context['og_description'] = "Page du profil d'une personne externe ou interne à l'association Magellans."

        if self.request.POST:
            context['form'] = EditPersonForm(self.request.POST, instance=self.object)
        else:
            context['form'] = EditPersonForm(instance=self.object)

        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = EditPersonForm(request.POST, instance=self.object)
        if form.is_valid():
            form.save()
            return redirect('person-detail', pk=self.object.pk)
        else:
            return self.render_to_response(self.get_context_data(form=form))
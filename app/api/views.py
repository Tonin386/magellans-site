from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.utils.encoding import force_bytes
from django.utils.safestring import mark_safe
from django.core.mail import send_mail
from django.http import JsonResponse
from warehouse.models import Order
from dashboard.models import *
from warehouse.models import *
from datetime import datetime
from members.models import *
from bank.models import *
from .utils import *
import base64
import json

def verify_token_permissions(request):
    token = json.loads(request.body.decode("utf-8")).get("token", "undefined")
    permissions = {
        'bank': [],
        'dashboard': [],
        'members': [],
        'warehouse': [],
        'fullpower': []
    }
    
    user = None
    try:
        user = Member.objects.get(api_token=token)
    except Member.DoesNotExist:
        print("No user uses this token")
        pass
    
    if token == "undefined" or user == None:
        permissions['warehouse'] += ['read']
        return permissions
    else:
        permissions['bank'] += ['write-expense']
        
    if user.is_staff:
        permissions['fullpower'] += ['read']
        permissions['dashboard'] += ['read', 'write']
        permissions['members'] += ['read', 'write']
        
        if user.site_person.role == "G":
            permissions['warehouse'] += ['write']
            
        if user.site_person.role == "P":
            permissions['bank'] += ['read']
            
        if user.site_person.role == "T":
            permissions['bank'] += ['read', 'write']
        
    if user.is_superuser:
        permissions['fullpower'] = ['read', 'write']
        
    return permissions, user

def api_bank(request):
    permissions, user = verify_token_permissions(request)
    app_id = 1

    body_post = json.loads(request.body.decode("utf-8"))

    action = body_post.get("action", "undefined")

    if action == "add-expense":
        if not 'write-expense' in permissions['bank'] + permissions['fullpower']:
            createNotification("Ajout dépense", "add-expense", app_id, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})
        
        name = body_post.get("name", "undefined")
        date = body_post.get("date", "undefined")
        amount = float(body_post.get("amount", "0"))
        comm = body_post.get("comm", "undefined")
        proof = body_post.get("proof", "undefined")

        expense = Expense(
            title=name,
            date=date,
            comm=comm,
            amount=amount,
            author=user
        )

        expense.save()

        if not proof in ['undefined', '']:
            try:
                image_data = proof.split(",")
                extension = image_data[0].replace("data:image/", "").replace(";base64", "")
                proof = ContentFile(base64.b64decode(image_data[1]))
                path = f"expense{expense.pk}.{extension}"
                expense.proof.save(path, proof)
            except Exception as e:
                expense.delete()
                createNotification("Ajout dépense", "add-expense", app_id, 3, f"Erreur lors de l'import de l'image. Veuillez réessayer.<hr>{str(e)}", user, str(e))
                return JsonResponse({"status": "error", "error": str(e), "message": "There was a problem when decoding image"})
        
        expense.save()
        createNotification("Ajout dépense", "add-expense", app_id, 0, "La dépense a bien été créée.", user)
        return JsonResponse({"status": "success", "message": "Expense successfully created.", "id": expense.pk})
    
    if action == "edit-invoice_status":
        if not 'write' in permissions['bank'] + permissions['fullpower']:
            createNotification("Edition note de frais", "edit-invoice_status", app_id, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})
        
        pk = body_post.get("pk", "undefined")
        value = body_post.get("value", "undefined")
        
        if not pk == "undefined":
            try:    
                invoice = Invoice.objects.get(pk=int(pk))
                invoice.status = value

                invoice.save()

                createNotification("Edition note de frais", "edit-invoice_status", app_id, 0, "La note de frais a bien été modifiée.", user)
                return JsonResponse({"status": "success", "message": "Invoice updated successfully"})
            except Exception as e:
                createNotification("Edition note de frais", "edit-invoice_status", app_id, 3, f"Une erreur est survenue.<hr>Erreur : {str(e)}", user, str(e))
                return JsonResponse({"status": "error", "message": f"An error occured\n{str(e)}"})

    if action == "email-invoice_status":
        if not 'write' in permissions['bank'] + permissions['fullpower']:
            createNotification("Email note de frais", "email-invoice_status", app_id, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})
        
        pk = body_post.get("pk", "undefined")
        
        if not pk == "undefined":
            try:    
                invoice = Invoice.objects.get(pk=int(pk))

                subject = "Modification du statut de votre note de frais"
                message = render_to_string('email_invoice_status_changed.html', {'invoice': invoice})
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [invoice.author.email])

                createNotification("Email note de frais", "email-invoice_status", app_id, 0, "L'email a bien été envoyé.", user)

                return JsonResponse({"status": "success", "message": "Invoice updated successfully"})
            except Exception as e:
                createNotification("Email note de frais", "email-invoice_status", app_id, 3, f"Une erreur est survenue.<hr>Erreur : {str(e)}", user, str(e))
                return JsonResponse({"status": "error", "message": f"An error occured<\n{str(e)}"})

                    
    return JsonResponse({"status": "error", "message": "Uncaught error."})

def api_dashboard(request):
    permissions, user = verify_token_permissions(request)
    app_id = 2

    body_post = json.loads(request.body.decode("utf-8"))

    action = body_post.get("action", "undefined")

    if action == "add-project":
        if not 'write' in permissions['dashboard'] + permissions['fullpower']:
            createNotification("Ajout projet", "add-project", app_id, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})
        
        name = body_post.get("name", "undefined")
        genre = body_post.get("genre", "undefined")
        desc = body_post.get("desc", "undefined")
        short_desc = body_post.get("short_desc", "undefined")
        poster = body_post.get("poster", "undefined")
        shoot_date = body_post.get("shoot_date", "undefined")
        release_date = body_post.get("release_date", "undefined")
        director = body_post.get("director", "0")
        money_handler = body_post.get("money_handler", "0")
        public = body_post.get("public", "undefined")
        
        fields = {}

        if name == "undefined":
            createNotification("Ajout projet", "add-project", app_id, 3, "Vous devez au moins préciser un nom pour le projet.", user)
            return JsonResponse({"status": "error", "message": "Missing name."})
        else:
            fields['name'] = name
        

        if not director in ['0', '']:
            fields['director'] = Person.objects.get(pk=int(director))

        if not money_handler in ['0', '']:
            fields['money_handler'] = Person.objects.get(pk=int(money_handler))

        if not genre in ['undefined', '']:
            fields['genre'] = genre

        if not desc in ['undefined', '']:
            fields['desc'] = desc

        if not short_desc in ['undefined', '']:
            fields['short_desc'] = short_desc

        if not shoot_date in ['undefined', '']:
            fields['shoot_date'] = shoot_date

        if not release_date in ['undefined', '']:
            fields['release_date'] = release_date

        fields['public'] = public

        project = Project(
            **fields
        )

        project.save()

        if not poster in ['undefined', '']:
            try:
                image_data = poster.split(",")
                extension = image_data[0].replace("data:image/", "").replace(";base64", "")
                poster = ContentFile(base64.b64decode(image_data[1]))
                poster = resize_image(poster, 1000)
                if poster:
                    path = f"{project.slug}.{extension}"
                    project.poster.save(path, poster)
            except Exception as e:
                project.delete()
                createNotification("Ajout projet", "add-project", app_id, 3, f"Erreur lors de l'import de l'image. Veuillez réessayer.<hr>{str(e)}", user, str(e))
                return JsonResponse({"status": "error", "error": str(e), "message": "There was a problem when decoding image"})
        
        project.save()
        createNotification("Ajout projet", "add-project", app_id, 0, "Le projet a bien été créé.", user)
        return JsonResponse({"status": "success", "message": "Project successfully created."})

    if action == "edit-project":
        if not 'write' in permissions['dashboard'] + permissions['fullpower']:
            createNotification("Ajout projet", "add-project", app_id, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})
        
        slug = body_post.get("slug", "undefined")
        name = body_post.get("name", "undefined")
        genre = body_post.get("genre", "undefined")
        desc = body_post.get("desc", "undefined")
        short_desc = body_post.get("short_desc", "undefined")
        poster = body_post.get("poster", "undefined")
        shoot_date = body_post.get("shoot_date", "undefined")
        release_date = body_post.get("release_date", "undefined")
        director = body_post.get("director", "0")
        money_handler = body_post.get("money_handler", "0")
        public = body_post.get("public", "undefined")

        
        fields = {}

        if not director in ['undefined', '']:
            fields['director'] = Person.objects.get(pk=int(director))

        if not money_handler in ['undefined', '']:
            fields['money_handler'] = Person.objects.get(pk=int(money_handler))

        if not name in ['undefined', '']:
            fields['name'] = name

        if not genre in ['undefined', '']:
            fields['genre'] = genre

        if not desc in ['undefined', '']:
            fields['desc'] = desc

        if not short_desc in ['undefined', '']:
            fields['short_desc'] = short_desc

        if not shoot_date in ['undefined', '']:
            fields['shoot_date'] = shoot_date

        if not release_date in ['undefined', '']:
            fields['release_date'] = release_date

        fields['public'] = public

        project = Project.objects.get(slug=slug)

        for key in fields:
            setattr(project, key, fields[key])

        project.save()

        if not poster in ['undefined', '']:
            try:
                image_data = poster.split(",")
                extension = image_data[0].replace("data:image/", "").replace(";base64", "")
                poster = ContentFile(base64.b64decode(image_data[1]))
                poster = resize_image(poster, 1000)
                if poster:
                    path = f"{project.slug}.{extension}"
                    project.poster.save(path, poster)
            except Exception as e:
                createNotification("Edition projet", "edit-project", app_id, 2, f"Erreur lors de l'import de l'image. Veuillez réessayer. Le reste du projet a bien été modifié. Actualisation en cours...<hr>{str(e)}", user, str(e))
                return JsonResponse({"status": "error", "error": str(e), "message": "There was a problem when decoding image"})
        
        project.save()
        createNotification("Edition projet", "edit-project", app_id, 0, "Le projet a bien été modifié. Actualisation en cours...", user)
        return JsonResponse({"status": "success", "message": "Project successfully edited."})

    return JsonResponse({"status": "error", "message": "Uncaught error."})

def api_members(request):
    permissions, user = verify_token_permissions(request)
    app_id = 4
    
    body_post = json.loads(request.body.decode("utf-8"))
            
    action = body_post.get("action", "undefined")

    if action == "add-ext_user":
        if not 'write' in permissions['members'] + permissions['fullpower']:
            createNotification("Ajout utilisateur externe", "add-ext_user", app_id, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})
        
        first_name = body_post.get("first_name", "Non-renseigné")
        last_name = body_post.get("last_name", "Non-renseigné")
        email = body_post.get("email", "")
        phone = body_post.get("phone", "")
        gender = body_post.get("gender", "O")
        role = body_post.get("role", "X")

        if "Non-renseigné" in [first_name, last_name]:
            createNotification("Ajout utilisateur externe", "add-ext_user", app_id, 3, "Le nouvel utilisateur externe n'a pas été ajouté : veuillez renseigner au moins un nom et prénom.", user)
            return JsonResponse({"status": "error", "message": "Missing last or first name"})

        data = dict(
            first_name=first_name,
            last_name=last_name,
            email=email,
            gender=gender,
            phone=phone,
            role=role
        )

        try:
            person = Person.objects.create(
                **data
            )

            data['pk'] = person.pk

            ext_user = UnregisteredMember.objects.create()
            person.ext_profile = ext_user
            person.save()
            createNotification("Ajout utilisateur externe", "add-ext_user", app_id, 0, "Le nouvel utilisateur externe a bien été ajouté.", user)
            return JsonResponse({"status": "success", "message": "The external user was successfully added", 'data': json.dumps(data)})
        except Exception as e:
            person.delete()
            createNotification("Ajout utilisateur externe", "add-ext_user", app_id, 3, f"Une erreur est survenue. Veuillez réessayer<hr>Erreur : {str(e)}", user, str(e))
            return JsonResponse({"status": "error", "message": str(e)})

    if action == "del-ext_user":
        if not 'write' in permissions['members'] + permissions['fullpower']:
            createNotification("Suppression utilisateur externe", "del-ext_user", app_id, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})

        pk = body_post.get('pk')

        try:
            ext_user = UnregisteredMember.objects.get(pk=pk)
            ext_user.delete()
            createNotification("Suppression utilisateur externe", "del-ext_user", app_id, 0, "L'utilisateur a été supprimé.", user)
            return JsonResponse({"status": "success", "message": "External user deleted.", "id_row": f"#extUser{pk}"})
        except Exception as e:
            createNotification("Suppression utilisateur externe ", "del-ext-user", app_id, 3, f"Impossible de supprimer l'utilisateur. Veuillez réessayer.<hr>Erreur : {str(e)}", user, str(e))
            return JsonResponse({"status": "error", "message": str(e)})
    
    if action == "edit-user_role":
        if not 'write' in permissions['members'] + permissions['fullpower']:
            createNotification("Modification utilisateur", "edit-user_role", app_id, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})
        
        pk = body_post.get("pk", "undefined")
        role = body_post.get("role", "undefined")

        try:
            person = Person.objects.get(pk=pk)
            person.role = role
            person.save()
            if person.site_profile:
                person.site_profile.save()

            createNotification("Modification utilisateur", "edit-user_role", app_id, 0, "Le rôle de l'utilisateur a été modifié.", user)
            return JsonResponse({"status": "success", "message": "User role modified."})
        except Exception as e:
            createNotification("Modification utilisateur", "edit-user_role", app_id, 3, f"Une erreur est survenue. Veuillez réessayer<hr>Erreur : {str(e)}", user, str(e))
            return JsonResponse({"status": "error", "message": str(e)})
        
    if action == "redirect-ext_person":
        if not 'write' in permissions['members'] + permissions['fullpower']:
            createNotification("Redirection profil externe", "redirect-ext_person", app_id, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})
                
        pk_person = int(body_post.get("pk_person", "0"))
        pk_member = int(body_post.get("pk_member", "0"))

        if 0 in [pk_person, pk_member]:
            createNotification("Redirection profil externe", "redirect-ext_person", app_id, 3, f"Impossible d'établir la redirection, un des profils est nul.", user)
            return JsonResponse({"status": "error", "message": "Bad PK."})

        try:
            redirected_person = Person.objects.get(pk=pk_person)
            new_member = Member.objects.get(pk=pk_member)
            toDel_person = new_member.site_person

            if redirected_person.site_profile is not None:
                createNotification("Redirection profil externe", "redirect-ext_person", app_id, 3, "Cette personne est déjà associée avec un profil de membre. Vous ne pouvez pas modifier le lien.", user)
                return JsonResponse({"status": "error", "message": "Bad link edit."})

            redirected_person.first_name = toDel_person.first_name
            redirected_person.last_name = toDel_person.last_name
            redirected_person.email = toDel_person.email
            redirected_person.phone = toDel_person.phone
            redirected_person.gender = toDel_person.gender

            for operation in Operation.objects.filter(third_party=toDel_person):
                operation.third_party = redirected_person
                operation.save()

            for project in Project.objects.filter(director=toDel_person):
                project.director = redirected_person
                project.save()
            
            for project in Project.objects.filter(money_handler=toDel_person):
                project.money_handler = redirected_person
                project.save()

            old_person = redirected_person.ext_profile
            old_person.ext_person = None
            old_person.save()
            old_person.delete()

            redirected_person.site_profile = new_member
            toDel_person.delete()
            redirected_person.save()
            
            createNotification("Redirection profil externe", "redirect-ext_person", app_id, 0, "La redirection vers un nouveau profil est réussie. Veuillez rafraîchir la page pour voir les modifications.", user)
            return JsonResponse({"status": "success", "message": "Person redirect success."})
        except Exception as e:
            createNotification("Redirection profil externe", "redirect-ext_person", app_id, 3, f"Une erreur est survenue. Veuillez réessayer.<hr>Erreur : {str(e)}", user, str(e))
            return JsonResponse({"status": "error", "message": str(e)})
        
    if action == "reset-members":
        if not 'write' in permissions['dashboard'] + permissions['fullpower']:
            createNotification("Réinitialisation membres", "reset-members", app_id, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})
        
        site_members = Person.objects.filter(role="M")
        other_members = Person.objects.filter(role="Mx")

        Member.objects.all().update(donation=0)

        site_members.update(role="E")
        other_members.update(role="X")

        createNotification("Reinitialisation membres", "reset-members", app_id, 0, "Les membres ont bien été réinitialisés. Rafraichissez la page pour voir les modifications", user)
        return JsonResponse({"status": "success", "message": "Project successfully edited."})
    
    return JsonResponse({"status": "error", "message": "Uncaught error."})

def api_warehouse(request):
    permissions, user = verify_token_permissions(request)
    app_id = 6
    
    body_post = json.loads(request.body.decode("utf-8"))
            
    action = body_post.get("action", "undefined")
    
    if action == "add-item":
        if not 'write' in permissions['warehouse'] + permissions['fullpower']:
            createNotification("Ajout objet", "add-item", app_id, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})
        
        name = body_post.get("name", "undefined")
        tags = body_post.get("tags", "undefined")
        image = body_post.get("image", "undefined")
        max_stock = int(body_post.get("max_stock", "0"))
        state = int(body_post.get("state", "0"))
        availability = int(body_post.get("availability", "0"))
        
        new_item = Item()
    
        if not name == "undefined":
            new_item.name = name
            
        new_item.max_stock = max_stock
        new_item.state = state
        new_item.availability = availability
        new_item.now_available = max_stock
        
        new_item.save()

        if not tags == "undefined":
            for tag in tags:
                related_tag = Tag.objects.get(pk=int(tag))
                new_item.tags.add(related_tag)
        
        if not image == "undefined":
            try:
                image_data = image.split(",")
                extension = image_data[0].replace("data:image/", "").replace(";base64", "")
                image = ContentFile(base64.b64decode(image_data[1]))
                image = resize_image(image)
                if image:
                    path = f"{new_item.pk}.{extension}"
                    new_item.image.save(path, image)
            except Exception as e:
                new_item.delete()
                createNotification("Ajout objet", "add-item", app_id, 3, f"Erreur lors de l'import de l'image. Veuillez réessayer.<hr>{str(e)}", user, str(e))
                return JsonResponse({"status": "error", "error": str(e), "message": "There was a problem when decoding image"})
        
        new_item.save()
        createNotification("Ajout objet", "add-item", app_id, 0, "L'objet a bien été ajouté au magasin.", user)
        return JsonResponse({"status": "success", "message": "The item was successfully added"})
        
    if action == "add-tag":
        if not 'write' in permissions['warehouse'] + permissions['fullpower']:
            createNotification("Ajout tag", "add-tag", app_id, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})

        name = body_post.get("name", "undefined")
        color = body_post.get("color", "undefined")
        
        new_tag = Tag.objects.create(name=name, color=color)
        
        createNotification("Ajout tag", "add-tag", app_id, 0, "Le tag a bien été ajouté.", user)
        return JsonResponse({"status": "success", "message": "The tag was successfully added", "created_pk": new_tag.pk})
        
    if action == "del-item":
        if not 'write' in permissions['warehouse'] + permissions['fullpower']:
            createNotification("Suppression objet", "del-item", app_id, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})
        
        pk = int(body_post.get('pk', '-1'))
        
        try: 
            item = Item.objects.get(pk=pk)
            item.delete()
        except Exception as e:
            createNotification("Suppression objet", "del-item", app_id, 3, f"Une erreur est survenue. Veuillez réessayer<hr>Erreur : {str(e)}", user, str(e))
            return JsonResponse({"status": "error", "message": str(e)})

        createNotification("Suppression objet", "del-item", app_id, 0, f"L'objet a bien été supprimé.", user)
        return JsonResponse({"status": "success", "message": "Item was successfully deleted"})
    
    if action == "del-tag":
        if not 'write' in permissions['warehouse'] + permissions['fullpower']:
            createNotification("Suppression tag", "del-tag", app_id, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})
        
        pks = body_post.get("pks", "undefined")
        
        if not pks == "undefined":
            deleted = 0
            errors = []
            for pk in pks:
                try: 
                    tag = Tag.objects.get(pk=pk)
                    tag.delete()
                    deleted += 1
                except Exception as e:
                    errors.append(str(e))
                
            if deleted == len(pks):
                createNotification("Suppression tag", "del-tag", app_id, 0, "Les tags ont bien été supprimés.", user)
                return JsonResponse({"status": "success", "message": "Tags deleted successfully"})

            createNotification("Suppression tag", "del-tag", app_id, 2, f"{deleted}/{len(pks)} tags ont été supprimés. Veuillez réessayer avec les tags qui n'ont pas été supprimés.", user, errors)
            return JsonResponse({"status": "warning", "message": "Some tags haven't been deleted"})
        
    if action == "edit-item":
        if not 'write' in permissions['warehouse'] + permissions['fullpower']:
            createNotification("Edition objet", "edit-item", app_id, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})
        
        pk = int(body_post.get("pk", "-1"))
        
        if pk == -1:
            createNotification("Edition objet", "edit-item", app_id, 3, "Requête invalide.", user)
            return JsonResponse({"status": "error", "message": "The PK was set to -1, bad request."})
        
        item = None
        try:
            item = Item.objects.get(pk=pk)
        except Item.DoesNotExist:
            createNotification("Edition objet", "edit-item", app_id, 3, "L'objet demandé n'existe pas.", user, f"Item with pk {pk} not found.")
            return JsonResponse({"status": "error", "message": f"Item with pk {pk} not found."})

        name = body_post.get("name", "undefined")
        tags = body_post.get("tags", "undefined")
        image = body_post.get("image", "undefined")
        max_stock = int(body_post.get("max_stock", "-1"))
        state = int(body_post.get("state", "-1"))
        buy_price = float(body_post.get("buy_price", "-1"))
        owner = body_post.get("owner", "undefined")
        availability = int(body_post.get("availability", "-1"))
        now_available = int(body_post.get("now_available", "-1"))
        
        update_dict = {}
        
        if not name == "undefined":
            update_dict['name'] = name
        
        if not tags == "undefined":
            pass
        
        if not image == "undefined":
            try:
                image_data = image.split(",")
                extension = image_data[0].replace("data:image/", "").replace(";base64", "")
                image = ContentFile(base64.b64decode(image_data[1]))
                image = resize_image(image)
                if image:
                    path = f"{new_item.pk}.{extension}"
                    item.image.save(path, image)
            except Exception as e:
                createNotification("Edition objet", "edit-item", app_id, 3, f"Erreur lors de l'import de l'image. Veuillez réessayer.<hr>{str(e)}", user, str(e))
                return JsonResponse({"status": "error", "error": str(e), "message": "There was a problem when decoding image"})
        
        if not max_stock == -1:
            update_dict['max_stock'] = max_stock
            
        if not state == -1:
            update_dict['state'] = state
            
        if not buy_price == -1:
            update_dict['buy_price'] = buy_price
            
        if not owner == "undefined":
            update_dict['owner'] = owner
            
        if not availability == -1:
            update_dict['availability'] = availability
            
        if not now_available == -1:
            update_dict['now_available'] = now_available
            
        try:
            for key in update_dict:
                setattr(item, key, update_dict[key])
            item.save()
            createNotification("Edition objet", "edit-item", app_id, 0, "L'objet a été modifié.", user, json.dumps(update_dict))
            return JsonResponse({"status": "success", "message": "Item was edited with sucess"})
        except Exception as e:
            createNotification("Edition objet", "edit-item", app_id, 3, f"Une erreur est survenue.<hr>Erreur : {str(e)}", user, str(e))
            return JsonResponse({"status": "error", "message": f"An error occured<hr>{str(e)}"})
    
    if action == "edit-order_status":
        if not 'write' in permissions['warehouse'] + permissions['fullpower']:
            createNotification("Edition commande", "edit-order_status", app_id, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})
        
        pk = body_post.get("pk", "undefined")
        value = body_post.get("value", "undefined")
        
        if not pk == "undefined":
            try:    
                order = Order.objects.get(pk=int(pk))
                order.status = int(value)

                if order.status in [2, 3]:
                    order.date_validated = datetime.now()

                order.save()

                createNotification("Edition commande", "edit-order_status", app_id, 0, "La commande a bien été modifiée", user)
                return JsonResponse({"status": "success", "message": "Order updated successfully"})
            except Exception as e:
                createNotification("Edition commande", "edit-order_status", app_id, 3, f"Une erreur est survenue.<hr>Erreur : {str(e)}", user, str(e))
                return JsonResponse({"status": "error", "message": f"An error occured<hr>{str(e)}"})
        
    if action == "email-order_status":
        if not 'write' in permissions['warehouse'] + permissions['fullpower']:
            createNotification("Email commande", "email-order_status", app_id, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})
        
        pk = body_post.get("pk", "undefined")
        custom_message = body_post.get("message", "")
        
        if not pk == "undefined":
            try:
                order = Order.objects.get(pk=int(pk))
                if custom_message != "":
                    order.answer_message = "Réponse reçue le %s <br><br>" % datetime.now().strftime("%d/%m/%Y à %H:%M") + custom_message.replace("\n", "<br>") + '<hr>' + order.answer_message
                    order.save()

                subject = "Modification du statut de votre commande"
                email_message = render_to_string('email_order_status_changed.html', {'order': order, 'custom_message': custom_message})
                send_mail(subject, email_message, settings.DEFAULT_FROM_EMAIL, [order.user.email])

                createNotification("Email commande", "email-order_status", app_id, 0, "L'email a bien été envoyé.", user)
                return JsonResponse({"status": "success", "message": "Invoice updated successfully"})
            except Exception as e:
                createNotification("Email commande", "email-order_status", app_id, 3, f"Une erreur est survenue.<hr>Erreur : {str(e)}", user, str(e))
                return JsonResponse({"status": "error", "message": f"An error occured<hr>{str(e)}"})
                    
    createNotification("Erreur inconnue", "unknown error", app_id, 3, "Une erreur inconnue est survenue.", user)
    return JsonResponse({"status": "error", "message": "Uncaught error."})

@csrf_exempt
def webhook_helloasso(request):
    print("HelloAsso request received")
    if not request.method == "POST":
        print("BAD HELLOASSO REQUEST RECEIVED")
        return
    
    try:
        data = json.loads(request.body)
        if 'eventType' in data and data['eventType'] == 'Order':

            data = data['data']
            print("New member joined Magellans!")
            firstName = data['items'][0]['user']['firstName']
            lastName = data['items'][0]['user']['lastName']
            email = ""
            phone = ""

            payment = data["amount"]["total"] / 100

            for field in data['items'][0]['customFields']:
                if field['type'] == "TextInput":
                    email = field['answer']
                elif field['type'] == "Phone":
                    phone = field['answer']

            try:
                member = Member.objects.get(email=email)
                member.role = 'M'
                member.save()            
                return JsonResponse({'status': 'success', 'message': "Existing member updated."}, status=200)

            except ObjectDoesNotExist:
                pass


            token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(128))
            new_member = Member.objects.create(
                email=email,
                is_active=False,
                donation=payment,
                api_token=token
            )

            new_member.site_person.email=email
            new_member.site_person.first_name=firstName
            new_member.site_person.last_name=lastName
            new_member.site_person.phone=phone
            new_member.site_person.role="M"

            new_member.site_person.save()

            new_member.save()

            token = default_token_generator.make_token(new_member)
            uidb64 = urlsafe_base64_encode(force_bytes(new_member.pk))
            activation_url = "https://magellans.fr/membres/activate/{}/{}".format(uidb64, token)
            
            subject = "Activation de votre compte magellans.fr"
            message = mark_safe(render_to_string('registration/activation_email.html', {'user': new_member, 'activation_url': activation_url}))
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [new_member.email])

            return JsonResponse({'status': 'success', 'message': "A new member has joined Magellans."}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
from django.core.files.base import ContentFile
from django.http import JsonResponse
from dashboard.models import *
from warehouse.models import *
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
        permissions['warehouse'] = ['read']
        return permissions
        
    if user.is_staff:
        permissions['fullpower'] = ['read']
        permissions['dashboard'] = ['read', 'write']
        permissions['members'] = ['read']
        
        if user.role == "G":
            permissions['warehouse'] = ['read', 'write']
            
        if user.role == "P":
            permissions['bank'] = ['read']
            permissions['members'] = ['read', 'write']
            
        if user.role == "T":
            permissions['bank'] = ['read', 'write']
        
    if user.is_superuser:
        permissions['fullpower'] = ['read', 'write']
        
    return permissions, user

def api_bank(request):
    permissions, user = verify_token_permissions(request)
    
    return JsonResponse({})

def api_dashboard(request):
    permissions, user = verify_token_permissions(request)
    
    return JsonResponse({})

def api_members(request):
    permissions, user = verify_token_permissions(request)
    
    return JsonResponse({})

def api_warehouse(request):
    permissions, user = verify_token_permissions(request)
    
    body_post = json.loads(request.body.decode("utf-8"))
            
    action = body_post.get("action", "undefined")
    
    if action == "add-item":
        if not 'write' in permissions['warehouse'] + permissions['fullpower']:
            createNotification("Ajout objet", "add-item", 6, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
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
                path = f"{new_item.pk}.{extension}"
                new_item.image.save(path, image)
                new_item.image = "/img/items/" + path
            except Exception as e:
                new_item.delete()
                createNotification("Ajout objet", "add-item", 6, 3, f"Erreur lors de l'import de l'image. Veuillez réessayer.\n{str(e)}", user, str(e))
                return JsonResponse({"status": "error", "error": str(e), "message": "There was a problem when decoding image"})
        
        new_item.save()
        createNotification("Ajout objet", "add-item", 6, 0, "L'objet a bien été ajouté au magasin.")
        return JsonResponse({"status": "success", "message": "The item was successfully added"})
        
    if action == "add-tag":
        if not 'write' in permissions['warehouse'] + permissions['fullpower']:
            createNotification("Ajout tag", "add-tag", 6, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})

        name = body_post.get("name", "undefined")
        color = body_post.get("color", "undefined")
        
        new_tag = Tag.objects.create(name=name, color=color)
        
        createNotification("Ajout tag", "add-tag", 6, 0, "Le tag a bien été ajouté.", user)
        return JsonResponse({"status": "success", "message": "The tag was successfully added", "created_pk": new_tag.pk})
        
    if action == "del-item":
        if not 'write' in permissions['warehouse'] + permissions['fullpower']:
            createNotification("Suppression tag", "del-tag", 6, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})
        
        pk = int(body_post.get('pk', '-1'))
        
        try: 
            item = Item.objects.get(pk=pk)
            item.delete()
        except Exception as e:
            createNotification("Suppression objet", "del-item", 6, 3, f"Une erreur est survenue. Veuillez réessayer\nErreur : {str(e)}", user, str(e))
            return JsonResponse({"status": "error", "message": str(e)})

        createNotification("Suppression objet", "del-item", 6, 0, f"L'objet a bien été supprimé.", user)
        return JsonResponse({"status": "success", "message": "Item was successfully deleted"})
    
    if action == "del-tag":
        if not 'write' in permissions['warehouse'] + permissions['fullpower']:
            createNotification("Suppression tag", "del-tag", 6, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
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
                createNotification("Suppression tag", "del-tag", 6, 0, "Les tags ont bien été supprimés.", user)
                return JsonResponse({"status": "success", "message": "Tasg deleted successfully"})

            createNotification("Suppression tag", "del-tag", 6, 2, f"{deleted}/{len(pks)} tags ont été supprimés. Veuillez réessayer avec les tags qui n'ont pas été supprimés.", user, errors)
            return JsonResponse({"status": "warning", "message": "Some tags haven't been deleted"})
        
    if action == "edit-item":
        if not 'write' in permissions['warehouse'] + permissions['fullpower']:
            createNotification("Edition objet", "edit-item", 6, 3, "Vous n'avez pas les permissions suffisantes pour effectuer cette action.", user)
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})
        
        pk = int(body_post.get("pk", "-1"))
        
        if pk == -1:
            createNotification("Edition objet", "edit-item", 6, 3, "Requête invalide.", user).show()
            return JsonResponse({"status": "error", "message": "The PK was set to -1, bad request."})
        
        item = None
        try:
            item = Item.objects.get(pk=pk)
        except Item.DoesNotExist:
            createNotification("Edition objet", "edit-item", 6, 3, "L'objet demandé n'existe pas.", user, f"Item with pk {pk} not found.").show()
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
            pass
        
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
            createNotification("Edition objet", "edit-item", 6, 0, "L'objet a été modifié.", user, json.dumps(update_dict)).show()
            return JsonResponse({"status": "success", "message": "Item was edited with sucess"})
        except Exception as e:
            createNotification("Edition objet", "edit-item", 6, 3, f"Une erreur est survenue.\nErreur : {str(e)}", user, str(e)).show()
            return JsonResponse({"status": "error", "message": f"An error occured\n{str(e)}"})
            
                    
    createNotification("Erreur inconnue", "unknown error", 6, 3, "Une erreur inconnue est survenue.", user)
    return JsonResponse({"status": "error", "message": "Uncaught error."})

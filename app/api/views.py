from django.core.files.base import ContentFile
from django.http import JsonResponse
from dashboard.models import *
from warehouse.models import *
from members.models import *
from bank.models import *
import base64
import json

def verify_token_permissions(request):
    token = json.loads(request.body.decode("utf-8")).get("token", "undefined")
    print(token)
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
        print(token)
        print("BIG ERROR")
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
        
    return permissions

def api_bank(request):
    permissions = verify_token_permissions(request)
    
    return JsonResponse({})

def api_dashboard(request):
    permissions = verify_token_permissions(request)
    
    return JsonResponse({})

def api_members(request):
    permissions = verify_token_permissions(request)
    
    return JsonResponse({})

def api_warehouse(request):
    permissions = verify_token_permissions(request)
    
    body_post = json.loads(request.body.decode("utf-8"))
            
    action = body_post.get("action", "undefined")
    
    if action == "add-item":
        if not 'write' in permissions['warehouse'] + permissions['fullpower']:
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
                return JsonResponse({"status": "error", "error": str(e), "message": "There was a problem when decoding image"})
        
        new_item.save()
                
        return JsonResponse({"status": "success", "message": "The item was successfully added"})
        
    if action == "add-tag":
        if not 'write' in permissions['warehouse'] + permissions['fullpower']:
            return JsonResponse({"status": "error", "message": "Insufficient permissions"})

        name = body_post.get("name", "undefined")
        color = body_post.get("color", "undefined")
        
        new_tag = Tag.objects.create(name=name, color=color)
        
        return JsonResponse({"status": "success", "message": "The tag was successfully added", "created_pk": new_tag.pk})
        
        
    return JsonResponse({"status": "error", "message": "Uncaught error."})

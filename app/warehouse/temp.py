from django.core.files.base import ContentFile
from .models import *
import base64
import json

def import_data_from_json():
    with open("warehouse_save.json", 'r') as json_file:
        import_data = json.load(json_file)
        
        
    for item in import_data:
        new_item = Item()
        new_item.name = item['name']
        new_item.max_stock = item['max_stock']
        new_item.availability = 1
        new_item.now_available = item['max_stock']
        new_item.state = 4
        
        new_item.save()
        
        for tag_name in item['tags']:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            new_item.tags.add(tag)
            
        if not item['image'] == "nan":
            image = ContentFile(base64.b64decode(item['image']))
            path = f"{new_item.pk}.jpg"
            new_item.image.save(path, image)
            new_item.image = "/img/items/" + path
            
        new_item.save()
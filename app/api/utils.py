from django.core.files.base import ContentFile
from .models import Notification
from io import BytesIO
from PIL import Image
import PIL
import os

def createNotification(title, subtitle, application, status, message, user, extra_field=None):
    notification = Notification.objects.create(
        title=title,
        subtitle=subtitle,
        application=application,
        status=status,
        message=message,
        user=user,
        extra_field=extra_field
    )
    
    notification.show()
    
    return notification

#Local function that should be called ONLY IF NEEDED in Django shell
def resize_image(content_file: ContentFile, max_width=200) -> ContentFile:
    binary_image = BytesIO(content_file.read())
    try:
        with Image.open(binary_image) as img:
            width, height = img.size
            aspect_ratio = width / height

            new_width = min(width, max_width)
            new_height = int(new_width / aspect_ratio)

            img_resized = img.resize((new_width, new_height))

            output_buffer = BytesIO()
            img_resized.save(output_buffer, format="PNG", interlace="PNG")

            return ContentFile(output_buffer.getvalue())
    except PIL.UnidentifiedImageError as e: 
        print(f"Image couldn't be converted because it is probably null: {e}")
        return None

def resize_images_in_dir(input_dir: str, max_width=200) -> None:
    for filename in os.listdir(input_dir):
        if filename.endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp")):
            input_path = os.path.join(input_dir, filename)

            with open(input_path, "rb") as image_file:
                print(f"Resizing {input_path}...")
                image_content = image_file.read()
                resized_image = resize_image(ContentFile(image_content), max_width)

                if resized_image:
                    with open(input_path, "wb") as output_file:
                        output_file.write(resized_image.read())
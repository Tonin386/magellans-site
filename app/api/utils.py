from .models import Notification

def createNotification(title, subtitle, application, status, message, user=None, extra_field=None):
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
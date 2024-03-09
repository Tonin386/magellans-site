
from django import template
from members.forms import LogoutForm

register = template.Library()

@register.inclusion_tag('registration/logout.html')
def logout_form():
    form = LogoutForm()
    return  {'form': form}
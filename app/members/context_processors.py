from .models import Member

def get_treasurer(request):
    try: 
        treasurer = Member.objects.filter(role='T')[0]
        return {"treasurer": treasurer.site_person}
    except Exception as e:
        print(e)
        return {"treasurer": None}
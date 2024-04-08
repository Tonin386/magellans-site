from .models import Person

def get_treasurer(request):
    try: 
        treasurer = Person.objects.filter(role='T')[0]
        return {"treasurer": treasurer}
    except Exception as e:
        print(e)
        return {"treasurer": None}
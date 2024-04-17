from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
import os

class FileView(View):
    def get(self, request, filename):
        dir = "templates/static"

        if filename in os.listdir(dir):
            with open(os.path.join(dir, filename), 'r') as file:
                file_content = file.read()
            return HttpResponse(file_content, content_type="text/plain")
        else:
            title = "Fichier introuvable"
            return render(request, "404.html", locals())
            
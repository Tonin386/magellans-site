from django.db import models
from django.urls import reverse
from django.utils.text import slugify

# Create your models here.

class Site(models.Model):
    name = models.CharField(max_length=100)
    desc = models.TextField()
    
    def __str__(self):
        return "Site " + self.name
    
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('category-detail', kwargs={'slug': self.slug})
    
    def __str__(self):
        return "Catégorie " + self.name
    
class Section(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING)
    content = models.TextField(blank=True)
    
    def __str__(self):
        return "Section " + self.name
    

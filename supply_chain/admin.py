from django.contrib import admin
from .models import Supplier, Product

# Registered models here.
admin.site.register(Supplier)
admin.site.register(Product)
from django.db import models


class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    address = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    sku = models.CharField(max_length=50, unique=True)  # stock keeping unit
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
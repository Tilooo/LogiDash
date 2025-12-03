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
    category = models.CharField(max_length=100, default='Unknown')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Order(models.Model):
    order_id = models.IntegerField(unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    customer_city = models.CharField(max_length=100)
    customer_country = models.CharField(max_length=100)
    order_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ], default='pending')

    def __str__(self):
        return f"Order {self.order_id}"
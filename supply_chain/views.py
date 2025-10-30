# supply_chain/views.py

from django.shortcuts import render
from .models import Product, Supplier


def dashboard_view(request):
    # to get some data from the database
    product_count = Product.objects.count()
    supplier_count = Supplier.objects.count()

    # to create a context dictionary to pass data to the template
    context = {
        'product_count': product_count,
        'supplier_count': supplier_count,
    }

    # to render the request, specifying the template and passing the context
    return render(request, 'supply_chain/dashboard.html', context)
# supply_chain/views.py

from django.shortcuts import render, redirect
from .models import Product, Supplier
import plotly.express as px
import pandas as pd
from django.db.models import Q
from django.core.management import call_command
from django.core.files.storage import FileSystemStorage
import os
from django.conf import settings

def dashboard_view(request):
    product_count = Product.objects.count()
    supplier_count = Supplier.objects.count()

    products = Product.objects.all().values('category')

    # to convert the database query result into a pandas DataFrame
    df = pd.DataFrame(list(products))

    if not df.empty:
        category_counts = df['category'].value_counts().reset_index()
        category_counts.columns = ['category', 'count']
        
        # the pie chart using Plotly Express
        fig = px.pie(
            category_counts,
            names='category',
            values='count',
            title='Products by Category',
            hole=0.4, # donut chart
        )

        # customized the chart's appearance
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",  # transparent background
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#eaeaea"), # white ish text for dark theme
            legend_title_text='Categories',
            title_x=0.5 # center the title
        )
        fig.update_traces(textinfo='percent+label', textposition='inside')

        # convert the Plotly figure to an HTML div string
        pie_chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        unique_categories = len(category_counts)
    else:
        pie_chart_html = "<p class='text-center text-muted'>No data available</p>"
        unique_categories = 0

    # the context to pass to the template
    context = {
        'product_count': product_count,
        'supplier_count': supplier_count,
        'category_count': unique_categories,
        'pie_chart': pie_chart_html, # chart's HTML to the context
    }

    return render(request, 'supply_chain/dashboard.html', context)

def product_list_view(request):
    search_query = request.GET.get('q', '')

    products = Product.objects.all()

    # if a search query exists, filter the products
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    context = {
        'products': products,
        'search_query': search_query,
    }

    return render(request, 'supply_chain/product_list.html', context)


def upload_data_view(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        uploaded_file = request.FILES['csv_file']

        fs = FileSystemStorage()
        temp_file_name = 'DataCoSupplyChainDataset.csv'
        if fs.exists(temp_file_name):
            fs.delete(temp_file_name)

        fs.save(temp_file_name, uploaded_file)

        try:
            call_command('import_data')
        except Exception as e:
            print(f"Error during import: {e}")

        return redirect('product-list')

    return render(request, 'supply_chain/upload_data.html')
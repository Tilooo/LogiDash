# supply_chain/views.py

from django.shortcuts import render, redirect
from .models import Product, Supplier, Order
import plotly.express as px
import pandas as pd
from django.db.models import Q
from django.core.management import call_command
from django.core.files.storage import FileSystemStorage
import os
from django.conf import settings
from prophet import Prophet
import plotly.graph_objs as go
import folium
from django.contrib import messages

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
            messages.success(request, "Upload Complete! Your data has been successfully processed.")
        except Exception as e:
            messages.error(request, f"Error during import: {str(e)}")
            print(f"Error during import: {e}")

        return redirect('product-list')

    return render(request, 'supply_chain/upload_data.html')


def forecast_view(request):
    orders = Order.objects.all().values('order_date')
    df = pd.DataFrame(list(orders))

    if not df.empty:
        df['order_date'] = pd.to_datetime(df['order_date']).dt.tz_localize(None)
        
        # group by date and count orders
        daily_orders = df.groupby('order_date').size().reset_index(name='y')
        daily_orders.columns = ['ds', 'y']

        # fit Prophet model
        m = Prophet()
        m.fit(daily_orders)

        future = m.make_future_dataframe(periods=30)
        forecast = m.predict(future)


        result_df = forecast[['ds', 'yhat']].copy()
        result_df['ds'] = result_df['ds'].dt.strftime('%Y-%m-%d')

        daily_orders['ds'] = daily_orders['ds'].dt.strftime('%Y-%m-%d')

        dates = result_df['ds'].tolist()
        predictions = result_df['yhat'].tolist()

        actual_dates = daily_orders['ds'].tolist()
        actual_values = daily_orders['y'].tolist()

        
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=actual_dates, y=actual_values, mode='markers', name='Actual Orders', marker=dict(color='#00d4ff')))
        
        # Forecast
        fig.add_trace(go.Scatter(x=dates, y=predictions, mode='lines', name='Forecast', line=dict(color='#d946ef')))
        
        fig.update_layout(
            title='Order Demand Forecast (Next 30 Days)',
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#eaeaea"),
            xaxis_title='Date',
            yaxis_title='Number of Orders',
            hovermode="x unified"
        )
        
        chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        
    else:
        chart_html = "<p class='text-center text-muted'>No data available for forecasting</p>"

    context = {
        'chart_html': chart_html
    }
    
    return render(request, 'supply_chain/forecast.html', context)



def map_view(request):
    suppliers = Supplier.objects.all()

    m = folium.Map(location=[37.0902, -95.7129], zoom_start=4)
    
    # Mock coordinates for demonstration purposes
    mock_coordinates = {
        0: [40.7128, -74.0060], # New York
        1: [34.0522, -118.2437], # Los Angeles
        2: [41.8781, -87.6298], # Chicago
        3: [29.7604, -95.3698], # Houston
        4: [33.4484, -112.0740], # Phoenix
    }

    for i, supplier in enumerate(suppliers):
        coords = mock_coordinates.get(i % len(mock_coordinates))
        
        folium.Marker(
            coords,
            popup=f"<b>{supplier.name}</b><br>{supplier.address}",
            tooltip=supplier.name,
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)

    # HTML representation of the map
    map_html = m._repr_html_()

    context = {
        'map_html': map_html
    }

    return render(request, 'supply_chain/map.html', context)


def supplier_analytics_view(request):  # Supplier Performance Analytics with scorecards and charts
    suppliers = Supplier.objects.all()
    
    if not suppliers.exists():
        context = {
            'no_data': True,
            'top_chart_html': "<p class='text-center text-muted'>No supplier data available</p>",
            'bottom_chart_html': "<p class='text-center text-muted'>No supplier data available</p>",
            'supplier_scores': []
        }
        return render(request, 'supply_chain/supplier_analytics.html', context)
    
    # Calculate performance metrics for each supplier
    supplier_data = []
    
    for supplier in suppliers:
        orders = Order.objects.filter(product__supplier=supplier)
        order_count = orders.count()
        
        # Calculate reliability score (0-100), based on order volume and consistency
        if order_count > 0:
            orders_with_dates = orders.values('order_date')
            if orders_with_dates:
                df_orders = pd.DataFrame(list(orders_with_dates))
                df_orders['order_date'] = pd.to_datetime(df_orders['order_date']).dt.tz_localize(None)
                
                date_range = (df_orders['order_date'].max() - df_orders['order_date'].min()).days
                active_days = max(date_range, 1)
                
                # Calculate average orders per day
                avg_orders_per_day = order_count / active_days
                
                # Reliability score: combination of volume and consistency
                # Higher order count and consistent delivery = higher score
                volume_score = min(order_count / 10, 50)  # Max 50 points for volume
                consistency_score = min(avg_orders_per_day * 100, 50)  # Max 50 points for consistency
                reliability_score = min(volume_score + consistency_score, 100)
            else:
                reliability_score = 0
        else:
            reliability_score = 0
            avg_orders_per_day = 0
        
        supplier_data.append({
            'name': supplier.name,
            'order_count': order_count,
            'reliability_score': round(reliability_score, 1),
            'avg_orders_per_day': round(avg_orders_per_day, 2)
        })
    
    # By order count
    supplier_data.sort(key=lambda x: x['order_count'], reverse=True)
    
    # Top 5 and bottom 5
    top_5 = supplier_data[:5]
    bottom_5 = supplier_data[-5:] if len(supplier_data) > 5 else []
    
    # Bar chart for top 5 suppliers
    if top_5:
        df_top = pd.DataFrame(top_5)
        fig_top = px.bar(
            df_top,
            x='name',
            y='order_count',
            title='Top 5 Suppliers by Order Volume',
            labels={'name': 'Supplier', 'order_count': 'Total Orders'},
            color='reliability_score',
            color_continuous_scale=['#ef4444', '#eab308', '#22c55e'],  # Red to Yellow to Green
            text='order_count'
        )
        
        fig_top.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#eaeaea"),
            title_x=0.5,
            xaxis_title='Supplier',
            yaxis_title='Total Orders',
            coloraxis_colorbar=dict(title="Reliability<br>Score")
        )
        fig_top.update_traces(textposition='outside')
        
        top_chart_html = fig_top.to_html(full_html=False, include_plotlyjs='cdn')
    else:
        top_chart_html = "<p class='text-center text-muted'>No data available</p>"
    
    # Bar chart for bottom 5 suppliers
    if bottom_5:
        df_bottom = pd.DataFrame(bottom_5)
        fig_bottom = px.bar(
            df_bottom,
            x='name',
            y='order_count',
            title='Bottom 5 Suppliers by Order Volume',
            labels={'name': 'Supplier', 'order_count': 'Total Orders'},
            color='reliability_score',
            color_continuous_scale=['#ef4444', '#eab308', '#22c55e'],  # Red to Yellow to Green
            text='order_count'
        )
        
        fig_bottom.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#eaeaea"),
            title_x=0.5,
            xaxis_title='Supplier',
            yaxis_title='Total Orders',
            coloraxis_colorbar=dict(title="Reliability<br>Score")
        )
        fig_bottom.update_traces(textposition='outside')
        
        bottom_chart_html = fig_bottom.to_html(full_html=False, include_plotlyjs='cdn')
    else:
        bottom_chart_html = "<p class='text-center text-muted'>Not enough suppliers for comparison</p>"
    
    context = {
        'no_data': False,
        'top_chart_html': top_chart_html,
        'bottom_chart_html': bottom_chart_html,
        'supplier_scores': supplier_data,
        'total_suppliers': len(supplier_data)
    }
    
    return render(request, 'supply_chain/supplier_analytics.html', context)
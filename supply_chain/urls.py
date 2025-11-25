from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('products/', views.product_list_view, name='product-list'),
    path('upload/', views.upload_data_view, name='upload-data'),
]
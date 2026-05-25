from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.catalog, name='catalog'),
    path('search-suggest/', views.search_suggest, name='search_suggest'),
    path('brand/<slug:slug>/', views.by_brand, name='by_brand'),
    path('<slug:slug>/', views.product_detail, name='product'),
]

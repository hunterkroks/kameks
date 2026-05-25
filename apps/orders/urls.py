from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.order_create, name='checkout'),
    path('success/<int:pk>/', views.order_success, name='success'),
    path('<int:pk>/', views.order_detail, name='detail'),
]

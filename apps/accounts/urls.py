from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Личный кабинет
    path('profile/', views.profile_overview, name='profile'),
    path('profile/orders/', views.profile_orders, name='profile_orders'),
    path('profile/orders/<str:order_number>/', views.profile_order_detail, name='profile_order_detail'),
    path('profile/notifications/', views.profile_notifications, name='profile_notifications'),
    path('profile/notifications/mark-read/<int:pk>/', views.notification_mark_read, name='notification_mark_read'),
    path('profile/notifications/mark-all-read/', views.notification_mark_all_read, name='notification_mark_all_read'),
    path('profile/addresses/', views.profile_addresses, name='profile_addresses'),
    path('profile/addresses/add/', views.address_add, name='address_add'),
    path('profile/addresses/<int:pk>/edit/', views.address_edit, name='address_edit'),
    path('profile/addresses/<int:pk>/delete/', views.address_delete, name='address_delete'),
    path('profile/addresses/<int:pk>/default/', views.address_set_default, name='address_set_default'),
    path('profile/company/', views.profile_company, name='profile_company'),
    path('profile/settings/', views.profile_settings, name='profile_settings'),
    path('profile/reorder/<str:order_number>/', views.reorder, name='reorder'),
]

from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='detail'),
    path('add/<int:product_id>/', views.cart_add, name='add'),
    path('remove/<int:product_id>/', views.cart_remove, name='remove'),

    # Отложенные товары
    path('save-later/<int:product_id>/', views.move_to_saved, name='save_later'),
    path('restore/<int:saved_id>/', views.restore_from_saved, name='restore'),

    # Промокоды
    path('apply-promo/', views.apply_promo, name='apply_promo'),
    path('remove-promo/', views.remove_promo, name='remove_promo'),

    # Доставка
    path('set-delivery/', views.set_delivery, name='set_delivery'),

    # Спецификация
    path('download-spec/', views.download_spec, name='download_spec'),
    path('email-spec/', views.email_spec, name='email_spec'),

    # B2B
    path('request-invoice/', views.request_invoice, name='request_invoice'),
]

from django.urls import path
from apps.integration import views

app_name = 'integration'

urlpatterns = [
    path('import/', views.import_view, name='import'),
    path('import/confirm/', views.import_confirm_view, name='import_confirm'),
    path('import/result/<int:pk>/', views.import_result_view, name='import_result'),
    path('import/rollback-last/', views.rollback_last_view, name='rollback_last'),
    path('export/catalog/', views.export_catalog_view, name='export_catalog'),
]

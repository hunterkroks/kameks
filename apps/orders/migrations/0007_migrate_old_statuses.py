from django.db import migrations


def forwards(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    # Старые статусы → новые
    Order.objects.filter(status='new').update(status='pending')
    Order.objects.filter(status__in=['processing', 'in_progress']).update(status='confirmed')


def backwards(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    Order.objects.filter(status='pending').update(status='new')


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_order_tracking_number_alter_order_status'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]

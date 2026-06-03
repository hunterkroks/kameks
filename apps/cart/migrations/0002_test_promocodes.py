from django.db import migrations


def create_promos(apps, schema_editor):
    PromoCode = apps.get_model('cart', 'PromoCode')
    PromoCode.objects.get_or_create(
        code='WELCOME5',
        defaults={'discount_percent': 5, 'min_order_amount': 0, 'is_active': True},
    )
    PromoCode.objects.get_or_create(
        code='KAMEKS10',
        defaults={'discount_percent': 10, 'min_order_amount': 30000, 'is_active': True},
    )


def remove_promos(apps, schema_editor):
    PromoCode = apps.get_model('cart', 'PromoCode')
    PromoCode.objects.filter(code__in=['WELCOME5', 'KAMEKS10']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_promos, remove_promos),
    ]

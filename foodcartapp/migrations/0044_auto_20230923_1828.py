# Generated by Django 3.2.15 on 2023-09-23 15:28

from django.db import migrations, models
import django.db.models.deletion


def calculate_price(apps, schema_editor):
    ProductSet = apps.get_model('foodcartapp', 'ProductSet')

    product_sets = ProductSet.objects.all()

    for product_set in product_sets:
        if product_set.price in (0, None):
            product_set.price = product_set.product.price
            product_set.save()


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0043_auto_20230910_1512'),
    ]

    operations = [
        migrations.AddField(
            model_name='productset',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=8),
        ),
        migrations.AlterField(
            model_name='productset',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sets', to='foodcartapp.order'),
        ),
        migrations.RunPython(calculate_price)
    ]

# Generated by Django 3.2.15 on 2023-10-14 18:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0050_auto_20231014_1700'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='comment',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Комментарий'),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('Card', 'Картой на сайте'), ('Cash', 'Наличными')], db_index=True, max_length=200, verbose_name='Способ оплаты'),
        ),
    ]

# Generated by Django 3.2.15 on 2023-09-10 12:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0042_productset'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='first_name',
            new_name='firstname',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='last_name',
            new_name='lastname',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='phone_number',
            new_name='phonenumber',
        ),
    ]

# Generated by Django 3.2.21 on 2023-09-17 02:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_ingridient'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Ingridient',
            new_name='Ingredient',
        ),
    ]
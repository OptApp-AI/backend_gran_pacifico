# Generated by Django 4.1.7 on 2023-04-05 03:48

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_alter_producto_cantidad'),
    ]

    operations = [
        migrations.CreateModel(
            name='Direccion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('CALLE', models.CharField(max_length=200)),
                ('NUMERO', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('COLONIA', models.CharField(max_length=200)),
                ('CIUDAD', models.CharField(max_length=200)),
                ('MUNICIPIO', models.CharField(max_length=200)),
                ('CP', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
            ],
        ),
    ]
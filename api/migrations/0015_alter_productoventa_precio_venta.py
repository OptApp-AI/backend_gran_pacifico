# Generated by Django 4.1.7 on 2025-03-25 18:08

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_empleado_ciudad_registro'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productoventa',
            name='PRECIO_VENTA',
            field=models.FloatField(validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]

# Generated by Django 4.1.7 on 2025-01-31 14:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_alter_venta_fecha'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='empleado',
            name='CIUDAD_REGISTRO',
        ),
    ]

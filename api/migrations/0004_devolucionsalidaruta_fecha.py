# Generated by Django 4.1.7 on 2024-01-23 02:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_rename_catidad_devolucion_devolucionsalidaruta_cantidad_devolucion_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='devolucionsalidaruta',
            name='FECHA',
            field=models.DateTimeField(auto_now=True),
        ),
    ]

# Generated by Django 4.1.7 on 2023-09-19 20:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0049_remove_salidaruta_ruta_ruta_repartidor_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cliente',
            name='RUTAS',
            field=models.ManyToManyField(blank=True, null=True, to='api.ruta'),
        ),
    ]

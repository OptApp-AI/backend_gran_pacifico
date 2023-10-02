# Generated by Django 4.1.7 on 2023-09-29 23:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salidaruta',
            name='RUTA',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='salida_rutas', to='api.rutadia'),
        ),
        migrations.AlterField(
            model_name='salidaruta',
            name='RUTA_NOMBRE',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]

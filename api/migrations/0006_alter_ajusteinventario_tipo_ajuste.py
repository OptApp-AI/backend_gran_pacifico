# Generated by Django 4.1.7 on 2024-10-01 19:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_venta_ciudad_registro'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ajusteinventario',
            name='TIPO_AJUSTE',
            field=models.CharField(choices=[('FALTANTE', 'FALTANTE'), ('SOBRANTE', 'SOBRANTE'), ('PRODUCCION', 'PRODUCCION')], max_length=10),
        ),
    ]
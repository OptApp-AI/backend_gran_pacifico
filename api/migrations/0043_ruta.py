# Generated by Django 4.1.7 on 2023-09-19 01:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0042_alter_productoventa_nombre_producto'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ruta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('NOMBRE', models.CharField(max_length=100)),
                ('DIA', models.CharField(choices=[('LUNES', 'LUNES'), ('MARTES', 'MARTES'), ('MIERCOLES', 'MIERCOLES'), ('JUEVES', 'JUEVES'), ('VIERNES', 'VIERNES'), ('SABADO', 'SABADO'), ('DOMINGO', 'DOMINGO')], max_length=100)),
                ('REPARTIDOR', models.CharField(max_length=100)),
            ],
        ),
    ]

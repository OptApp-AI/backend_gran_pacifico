# Generated by Django 4.1.7 on 2024-10-01 22:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_alter_ajusteinventario_tipo_ajuste'),
    ]

    operations = [
        migrations.AddField(
            model_name='ruta',
            name='CIUDAD_REGISTRO',
            field=models.CharField(choices=[('LAZARO', 'LAZARO'), ('URUAPAN', 'URUAPAN')], db_index=True, default='URUAPAN', max_length=15),
        ),
    ]

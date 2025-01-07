# Generated by Django 5.1.3 on 2024-12-11 13:51

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0006_assistance_inside_alter_assistance_end_date_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='assistance',
            name='inside',
        ),
        migrations.AddField(
            model_name='assistance',
            name='finish',
            field=models.BooleanField(default=False, verbose_name='Terminada'),
        ),
        migrations.AlterField(
            model_name='assistance',
            name='end_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 12, 11, 13, 51, 37, 196050), null=True, verbose_name='Fin'),
        ),
        migrations.AlterField(
            model_name='assistance',
            name='ini_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 12, 11, 13, 51, 37, 196020), null=True, verbose_name='Inicio'),
        ),
    ]
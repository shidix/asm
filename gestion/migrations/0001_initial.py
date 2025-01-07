# Generated by Django 5.1.3 on 2024-11-22 12:39

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=200, verbose_name='Razón Social')),
                ('phone', models.CharField(default='0000000000', max_length=12, null=True, verbose_name='Teléfono de contacto')),
                ('email', models.EmailField(default='', max_length=254, null=True, verbose_name='Email de contacto')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='employee', to=settings.AUTH_USER_MODEL, verbose_name='Usuario')),
            ],
            options={
                'verbose_name': 'Empleado',
                'verbose_name_plural': 'Empleados',
            },
        ),
    ]

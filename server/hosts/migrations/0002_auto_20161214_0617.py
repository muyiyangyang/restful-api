# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-14 06:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hosts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='host',
            name='ipmi_ip',
            field=models.GenericIPAddressField(blank=True, null=True, protocol=b'ipv4', unique=True),
        ),
    ]

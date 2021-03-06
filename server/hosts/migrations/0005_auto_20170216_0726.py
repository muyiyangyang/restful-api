# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-16 07:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hosts', '0004_auto_20161215_0224'),
    ]

    operations = [
        migrations.CreateModel(
            name='MonCpu',
            fields=[
                ('rec_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=32)),
                ('mon_type', models.CharField(blank=True, max_length=32)),
                ('time', models.BigIntegerField()),
                ('user_average', models.FloatField()),
                ('system_average', models.FloatField()),
                ('idle_average', models.FloatField()),
                ('iowait_average', models.FloatField()),
            ],
            options={
                'ordering': ('time',),
            },
        ),
        migrations.CreateModel(
            name='MonDiskIO',
            fields=[
                ('rec_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=32)),
                ('mon_type', models.CharField(blank=True, max_length=32)),
                ('time', models.BigIntegerField()),
                ('await_write', models.FloatField()),
                ('await_read', models.FloatField()),
                ('await_average', models.FloatField()),
                ('iops_write', models.FloatField()),
                ('iops_read', models.FloatField()),
                ('bandwidth_write', models.FloatField()),
                ('bandwidth_read', models.FloatField()),
                ('size_average', models.FloatField()),
            ],
            options={
                'ordering': ('time',),
            },
        ),
        migrations.CreateModel(
            name='MonDiskSpace',
            fields=[
                ('rec_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=32)),
                ('mon_type', models.CharField(blank=True, max_length=32)),
                ('time', models.BigIntegerField()),
                ('used_percent', models.FloatField()),
                ('free', models.IntegerField()),
                ('used', models.IntegerField()),
                ('total', models.IntegerField()),
            ],
            options={
                'ordering': ('time',),
            },
        ),
        migrations.CreateModel(
            name='MonMem',
            fields=[
                ('rec_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=32)),
                ('mon_type', models.CharField(blank=True, max_length=32)),
                ('time', models.BigIntegerField()),
                ('used', models.BigIntegerField()),
                ('free', models.BigIntegerField()),
                ('available', models.BigIntegerField()),
                ('total', models.BigIntegerField()),
                ('percent', models.FloatField()),
            ],
            options={
                'ordering': ('time',),
            },
        ),
        migrations.CreateModel(
            name='MonNetWork',
            fields=[
                ('rec_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=32)),
                ('mon_type', models.CharField(blank=True, max_length=32)),
                ('time', models.BigIntegerField()),
                ('bytes_in', models.IntegerField()),
                ('bytes_out', models.IntegerField()),
                ('error_in', models.IntegerField()),
                ('error_out', models.IntegerField()),
                ('bandwidth_in', models.IntegerField()),
                ('bandwidth_out', models.IntegerField()),
                ('drop_in', models.IntegerField()),
                ('drop_out', models.IntegerField()),
                ('package_in', models.IntegerField()),
                ('package_out', models.IntegerField()),
            ],
            options={
                'ordering': ('time',),
            },
        ),
        migrations.AddField(
            model_name='cpu',
            name='temperature',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='disk',
            name='enclosure_id',
            field=models.IntegerField(default=False),
        ),
        migrations.AddField(
            model_name='disk',
            name='fmt_uuid',
            field=models.CharField(blank=True, max_length=36),
        ),
        migrations.AddField(
            model_name='disk',
            name='formated',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='disk',
            name='health_state',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='disk',
            name='media_type',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='disk',
            name='mounted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='disk',
            name='protocol',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='disk',
            name='size',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='disk',
            name='slot_num',
            field=models.IntegerField(default=False),
        ),
        migrations.AddField(
            model_name='disk',
            name='vendor_info',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='disk',
            name='wwn',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='nic',
            name='ip_type',
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name='nic',
            name='mac',
            field=models.CharField(blank=True, default=b'ff:ff:ff:ff:ff:ff', max_length=32),
        ),
        migrations.AddField(
            model_name='nic',
            name='speed',
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name='nic',
            name='vendor',
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AlterField(
            model_name='cpu',
            name='cpu_state',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AlterField(
            model_name='disk',
            name='disk_name',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AlterField(
            model_name='disk',
            name='status',
            field=models.CharField(blank=True, default=b'st_uninited', max_length=32),
        ),
        migrations.AlterField(
            model_name='host',
            name='device_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='hosts', to='hosts.Device'),
        ),
        migrations.AlterField(
            model_name='nic',
            name='ip',
            field=models.GenericIPAddressField(blank=True, null=True, protocol=b'ipv4'),
        ),
        migrations.AddField(
            model_name='monnetwork',
            name='nic_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='monnetwork', to='hosts.Nic'),
        ),
        migrations.AddField(
            model_name='monmem',
            name='host_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='monmem', to='hosts.Host'),
        ),
        migrations.AddField(
            model_name='mondiskspace',
            name='disk_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mondiskspace', to='hosts.Disk'),
        ),
        migrations.AddField(
            model_name='mondiskio',
            name='disk_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mondiskio', to='hosts.Disk'),
        ),
        migrations.AddField(
            model_name='moncpu',
            name='host_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='moncpu', to='hosts.Host'),
        ),
    ]

# Create your views here.
# -*- coding: utf-8 -*-
import sys  
reload(sys)  
sys.setdefaultencoding('utf8') 

from django.db import models
from django.contrib import admin
from pygments.lexers import get_all_lexers, get_lexer_by_name
from pygments.styles import get_all_styles
from pygments.formatters.html import HtmlFormatter
from pygments import highlight
# Create your models here.

# create device table 
class Device(models.Model):
    device_id = models.AutoField(primary_key=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    device_name = models.CharField(max_length=32,unique=True,) #modified by lzc at 2016.12.27 , del uniq.
    DEVICE_CHOICES = (
                ('1', 'StandardHost'),
                ('2', 'TwoHosts'),
                ('3', 'ThreeHosts'),
                ('4', 'FourHosts'),
                )
    style = models.CharField(max_length=20,choices=DEVICE_CHOICES,default='1',blank=True)
    choice = models.BooleanField(default=False)
    status = models.CharField(max_length=32,blank=True)
    #owner = models.ForeignKey('auth.User', related_name='hosts', on_delete=models.CASCADE)
    highlighted = models.TextField(null=True,blank=True)
    class Meta:
        ordering = ('device_id',)

admin.site.register(Device)


# create host table
class Host(models.Model):
    device_id = models.ForeignKey(Device, related_name='hosts', on_delete=models.CASCADE)
    host_id = models.AutoField(primary_key=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    host_name = models.CharField(max_length=32,unique=True,blank=True)
    #nic_name = models.CharField(max_length=32,blank=False)
    ip = models.GenericIPAddressField(protocol="ipv4",unique=True,blank=False)
    netmask = models.GenericIPAddressField(protocol="ipv4",null=True,blank=True)
    gateway = models.GenericIPAddressField(protocol="ipv4",null=True,blank=True)
    dns = models.GenericIPAddressField(protocol="ipv4",null=True,blank=True)
    HOST_CHOICES = (
                ('VM', 'VirtualMachine'),
                ('PC', 'PhysicalMachine'),
                )
    style = models.CharField(max_length=20,choices=HOST_CHOICES,default='PC',blank=True)
    worker = models.BooleanField(default=False)  #is node or no
    choice = models.BooleanField(default=False)
    status = models.CharField(max_length=32,blank=True)
    ipmi_ip = models.GenericIPAddressField(protocol="ipv4",unique=True,null=True,blank=True)
    ipmi_username = models.CharField(max_length=32,null=True,blank=True)
    ipmi_password = models.CharField(max_length=32,null=True,blank=True)
    #owner = models.ForeignKey('auth.User', related_name='hosts', on_delete=models.CASCADE)
    highlighted = models.TextField(null=True,blank=True)
    class Meta:
        ordering = ('host_id',)

admin.site.register(Host)


# create disk table
class Disk(models.Model):
    host_id = models.ForeignKey(Host, related_name='disks', on_delete=models.CASCADE)
    disk_id = models.AutoField(primary_key=True)
    disk_name = models.CharField(max_length=32, blank=True)
    updated = models.DateTimeField(auto_now=True)
    DISK_CHOICES = (
                ('HDD','HardDiskDrive'),
                ('SSD','SolidStateDrives'),
                )
    style = models.CharField(max_length=20,choices=DISK_CHOICES,default='HDD',blank=True)
    disk_state = models.BooleanField(default=False)
    status = models.CharField(max_length=32,default='st_uninited', blank=True)
    filesystem =  models.CharField(max_length=32,default='XFS',blank=True)
    mountpoint = models.CharField(max_length=32,blank=True)
    choice = models.BooleanField(default=False)
    iops = models.CharField(max_length=32,blank=True)
    io = models.CharField(max_length=32,blank=True)
    delay = models.CharField(max_length=32,blank=True)
    total = models.CharField(max_length=32,blank=True)
    used = models.CharField(max_length=32,blank=True)
    free = models.CharField(max_length=32,blank=True)
    highlighted = models.TextField(null=True,blank=True)

    formated = models.BooleanField(default=False) #if a disk is formated, then it must be set True.
    fmt_uuid = models.CharField(max_length=36,blank=True) #After formating, a disk gets a unique uuid. the uuid can be used in mounting later. 
    mounted = models.BooleanField(default=False) #if a formated disk is mounted, set True. Otherwise False.
    
    
    '''
    added by lizhicheng at 2016.12.22 for collect hardware info.
    '''
    enclosure_id = models.IntegerField(default=False)
    slot_num = models.IntegerField(default=False)
    size = models.CharField(max_length=32,blank=True)
    health_state = models.CharField(max_length=32,blank=True)
    wwn = models.CharField(max_length=32,blank=True)
    media_type = models.CharField(max_length=32,blank=True)
    protocol = models.CharField(max_length=32,blank=True)
    vendor_info = models.CharField(max_length=32,blank=True)
    
    class Meta:
        ordering = ['disk_id']
    #def __unicode__(self):
    #   return "hostid:%d | hdname:%s | type:%s | hdstate:%s | status:%s" % (self.hdid, self.hdname, self.type, self.hdstate, self.status)
admin.site.register(Disk)


# create cpu memory
class Memory(models.Model):
    host_id = models.ForeignKey(Host, related_name='memorys', on_delete=models.CASCADE)
    memory_id = models.AutoField(primary_key=True)
    memory_name = models.CharField(max_length=32,default='memory',blank=False)
    updated = models.DateTimeField(auto_now=True)
    memory_state = models.BooleanField(default=False)
    status = models.CharField(max_length=32,blank=True)
    choice = models.BooleanField(default=False)
    total = models.CharField(max_length=32,blank=True)
    used = models.CharField(max_length=32,blank=True)#info like this belongs to monitor, should not be here. same as cpu\disk .
    free = models.CharField(max_length=32,blank=True)
    highlighted = models.TextField(null=True,blank=True)

    class Meta:
        ordering = ['memory_id']

admin.site.register(Memory)


# create cpu table
class Cpu(models.Model):
    #host_id = models.OneToOneField(Host, related_name='cpus', on_delete=models.CASCADE) #one host to one cpu
    host_id = models.ForeignKey(Host, related_name='cpus', on_delete=models.CASCADE) 
    cpu_id = models.AutoField(primary_key=True)
    cpu_name = models.CharField(max_length=32,default='cpu',blank=False)
    updated = models.DateTimeField(auto_now=True)
    cpu_state = models.CharField(max_length=32,blank=True) #modified by lzc . bool --> char
    choice = models.BooleanField(default=False)
    total = models.CharField(max_length=32,blank=True)
    used = models.CharField(max_length=32,blank=True)
    free = models.CharField(max_length=32,blank=True)
    highlighted = models.TextField(null=True,blank=True)
    
    #added by lzc 
    temperature = models.CharField(max_length=32,blank=True)
    
    class Meta:
        ordering = ['cpu_id']

admin.site.register(Cpu)


# create nic table
class Nic(models.Model):
    host_id = models.ForeignKey(Host, related_name='nics', on_delete=models.CASCADE)
    nic_id = models.AutoField(primary_key=True)
    nic_name = models.CharField(max_length=32,default='eth0',blank=False)
    updated = models.DateTimeField(auto_now=True)
    NIC_CHOICES = (
                ('1','1GbE'),
                ('10','10GbE'),
                )
    style = models.CharField(max_length=20,choices=NIC_CHOICES,default='1',blank=True)
    nic_state = models.BooleanField(default=False)
    ip = models.GenericIPAddressField(protocol="ipv4",null=True,blank=True)
    netmask = models.GenericIPAddressField(protocol="ipv4",null=True,blank=True)
    gateway = models.GenericIPAddressField(protocol="ipv4",null=True,blank=True)
    dns = models.GenericIPAddressField(protocol="ipv4",null=True,blank=True)
    choice = models.BooleanField(default=False)
    highlighted = models.TextField(null=True,blank=True)

    #added by lzc
    mac = models.CharField(max_length=32,default='ff:ff:ff:ff:ff:ff',blank=True)
    vendor = models.CharField(max_length=128,blank=True)  #Intel Corporation Ethernet Controller 10-Gigabit X540-AT2
    ip_type = models.CharField(max_length=16,blank=True) #'management' 'public' 'private' 'iscsi-Initiator'
    speed = models.CharField(max_length=16,blank=True) # Speed: 1000Mb/s

    class Meta:
        ordering = ['nic_id']

admin.site.register(Nic)

# create help table 
class Help(models.Model):
    help_id = models.AutoField(primary_key=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    help_name = models.CharField(max_length=32,unique=True,blank=False)
    description = models.TextField(null=True,blank=True)
    #owner = models.ForeignKey('auth.User', related_name='hosts', on_delete=models.CASCADE)
    highlighted = models.TextField(null=True,blank=True)
    class Meta:
        ordering = ('help_id',)

admin.site.register(Help)

# create log table 
class Log(models.Model):
    log_id = models.AutoField(primary_key=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    log_name = models.CharField(max_length=32,blank=True)
    #owner = models.ForeignKey('auth.User', related_name='hosts', on_delete=models.CASCADE)
    log_level = models.CharField(max_length=32,blank=True)
    description = models.TextField(null=True,blank=True)
    highlighted = models.TextField(null=True,blank=True)
    class Meta:
        ordering = ('log_id',)

admin.site.register(Log)

class MonDiskIO(models.Model):
    #record id
    rec_id = models.AutoField(primary_key=True)
    disk_id = models.ForeignKey(Disk, related_name='mondiskio', on_delete=models.CASCADE)
    #'sda ...'
    name = models.CharField(max_length=32,blank=True)
    # 'disk.io'
    mon_type = models.CharField(max_length=32,blank=True)
    time = models.BigIntegerField()
    
    await_write = models.FloatField()
    await_read = models.FloatField()
    await_average = models.FloatField()
    iops_write = models.FloatField()
    iops_read = models.FloatField()
    bandwidth_write = models.FloatField()
    bandwidth_read = models.FloatField()
    size_average = models.FloatField()
    class Meta:
        ordering = ('time',)

admin.site.register(MonDiskIO)

class MonNetWork(models.Model):
    rec_id = models.AutoField(primary_key=True)
    nic_id = models.ForeignKey(Nic, related_name='monnetwork', on_delete=models.CASCADE)
    name = models.CharField(max_length=32,blank=True)
    mon_type = models.CharField(max_length=32,blank=True)
    time = models.BigIntegerField()
    
    bytes_in = models.IntegerField()
    bytes_out = models.IntegerField()
    error_in = models.IntegerField()
    error_out = models.IntegerField()
    bandwidth_in = models.IntegerField()
    bandwidth_out = models.IntegerField()
    drop_in = models.IntegerField()
    drop_out = models.IntegerField()
    package_in = models.IntegerField()
    package_out = models.IntegerField()
    class Meta:
        ordering = ('time',)

admin.site.register(MonNetWork)

class MonMem(models.Model):
    rec_id = models.AutoField(primary_key=True)
    host_id = models.ForeignKey(Host, related_name='monmem', on_delete=models.CASCADE)
    #'memory' 'swap' ...
    name = models.CharField(max_length=32,blank=True)
    mon_type = models.CharField(max_length=32,blank=True)
    time = models.BigIntegerField()
    
    used = models.BigIntegerField()
    free = models.BigIntegerField()
    available = models.BigIntegerField()
    total = models.BigIntegerField()
    #eg: 10.2
    percent = models.FloatField()
    class Meta:
        ordering = ('time',)

admin.site.register(MonMem)

class MonDiskSpace(models.Model):
    #record id
    rec_id = models.AutoField(primary_key=True)
    disk_id = models.ForeignKey(Disk, related_name='mondiskspace', on_delete=models.CASCADE)
    #'/dev/sda1' '/dev/mapper/VolGroup-lv_root' ...
    name = models.CharField(max_length=32,blank=True)
    mon_type = models.CharField(max_length=32,blank=True)
    time = models.BigIntegerField()
    
    used_percent = models.FloatField()
    free = models.IntegerField()
    used = models.IntegerField()
    total = models.IntegerField()
    class Meta:
        ordering = ('time',)

admin.site.register(MonDiskSpace)

class MonCpu(models.Model):
    rec_id = models.AutoField(primary_key=True)
    host_id = models.ForeignKey(Host, related_name='moncpu', on_delete=models.CASCADE)
    #"all-cpus"
    name = models.CharField(max_length=32,blank=True)
    #"cpu.usage"
    mon_type = models.CharField(max_length=32,blank=True)
    time = models.BigIntegerField()
    
    user_average = models.FloatField()
    system_average = models.FloatField()
    idle_average = models.FloatField()
    iowait_average = models.FloatField()
    class Meta:
        ordering = ('time',)
    
admin.site.register(MonCpu)

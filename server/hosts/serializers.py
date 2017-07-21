from rest_framework import serializers
from hosts.models import *

class HelpSerializer(serializers.ModelSerializer):
    class Meta:
        model = Help
        fields = ('help_id','help_name', 'description')

class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = ('log_id','log_name','log_level','description')

class DiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disk
        fields = ('host_id',
                  'disk_id',
                  'disk_name', 
                  'style',
                  'disk_state',
                  'choice',
                  'status',
                  'iops',
                  'io',
                  'delay',
                  'total',
                  'used',
                  'free', 
                  'enclosure_id', #added by lzc for disk hardware info.
                  'slot_num', 
                  'size', 
                  'health_state', 
                  'wwn', 
                  'media_type', 
                  'protocol', 
                  'vendor_info'
                  )

class MemorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Memory
        fields = ('host_id','memory_id','memory_name','memory_state','total','used','free')

class CpuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cpu
        fields = ('host_id',
                  'cpu_id',
                  'cpu_name',
                  'cpu_state',
                  'total',
                  'used',
                  'free',
                  'temperature') #added by lzc

class NicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nic
        fields = ('host_id',
                  'nic_id',
                  'nic_name', 
                  'nic_state',
                  'ip',
                  'netmask',
                  'gateway',
                  'dns', 
                  'mac', 
                  'vendor', 
                  'ip_type', 
                  'speed')

class HostSerializer(serializers.ModelSerializer):
    #disks = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='disk-detail')
    #disks = serializers.StringRelatedField(many=True)
    disks = DiskSerializer(many=True, read_only=True)
    cpus = CpuSerializer(many=True, read_only=True)
    memorys = MemorySerializer(many=True, read_only=True)
    nics = NicSerializer(many=True, read_only=True)
    class Meta:
        model = Host
        fields = ('device_id',
                  'host_id', 
                  'host_name', 
                  'ip', 
                  'style',
                  'disks',
                  'cpus',
                  'memorys',
                  'nics',
                  'worker',
                  'choice',
                  'ipmi_ip',
                  'ipmi_username',
                  'ipmi_password',
                  'status')

class HostSelfSerializer(serializers.ModelSerializer):
    class Meta:
        model = Host
        fields = ('device_id',
                  'host_id', 
                  'host_name', 
                  'ip', 
                  'style',
                  'disks',
                  'cpus',
                  'memorys',
                  'nics',
                  'worker',
                  'choice',
                  'ipmi_ip',
                  'ipmi_username',
                  'ipmi_password',
                  'status')


class DeviceSerializer(serializers.ModelSerializer):
    hosts = HostSerializer(many=True, read_only=True)
    class Meta:
        model = Device
        fields = ('device_id','device_name', 'style','choice','status','hosts')

'''
taocloudMonitor: [disk io] [network] [memory] [disk] [cpu]
'''
class MonDiskIOSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonDiskIO
        fields = ('rec_id',
                  'disk_id',
                  'name',
                  'mon_type',
                  'time',
                  'await_write',
                  'await_read',
                  'await_average',
                  'iops_write',
                  'iops_read', 
                  'bandwidth_write', 
                  'bandwidth_read', 
                  'size_average')

class MonNetWorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonNetWork
        fields = ('rec_id',
                  'nic_id',
                  'name',
                  'mon_type',
                  'time',
                  'bytes_in',
                  'bytes_out',
                  'error_in',
                  'error_out',
                  'bandwidth_in', 
                  'bandwidth_out', 
                  'drop_in', 
                  'drop_out',
                  'package_in',
                  'package_out')

class MonMemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonMem
        fields = ('rec_id',
                  'host_id',
                  'name',
                  'mon_type',
                  'time',
                  'used',
                  'free',
                  'available',
                  'total',
                  'percent')

class MonDiskSpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonDiskSpace
        fields = ('rec_id',
                  'disk_id',
                  'name',
                  'mon_type',
                  'time',
                  'used_percent',
                  'free',
                  'used',
                  'total')

class MonCpuSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonCpu
        fields = ('rec_id',
                  'host_id',
                  'name',
                  'mon_type',
                  'time',
                  'user_average',
                  'system_average',
                  'idle_average',
                  'iowait_average')

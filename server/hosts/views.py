from django.shortcuts import render
# Create your views here.
from django.http import HttpResponse

from rest_framework import status, renderers, generics, permissions, renderers, viewsets
from rest_framework.decorators import api_view, detail_route
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.decorators import detail_route, list_route
from django.contrib.auth.models import User
from hosts.models import Host
from hosts.serializers import *
from django.http import Http404
from rest_framework.views import APIView

#for celery
from hosts.tasks import tao_host_alive
from hosts.tasks import tao_exc_cmd_instant
from hosts.tasks import tao_collect_hardware_info
from hosts.tasks import taocloud_mon_save_allinfo

from hosts.tasks import tao_collect_disk_logic_info
from hosts.tasks import tao_collect_nic_info_from_host

from hosts.tasks import taocloud_mon_diskio_process
from hosts.tasks import taocloud_mon_cpu_process
from hosts.tasks import taocloud_mon_mem_process

from hosts.tasks import taocloud_job_accept

import json
import time

#for log
import logging
logger = logging.getLogger("django.request")

@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'devices': reverse('device-list', request=request, format=format),
        'collector': reverse('all-info-collection', request=request, format=format),
        'hosts': reverse('host-list', request=request, format=format),
        'disks': reverse('disk-list', request=request, format=format),
        'disks/collector': reverse('disk-info-collect', request=request, format=format),
        'cpus': reverse('cpu-list', request=request, format=format),
        'memorys': reverse('memory-list', request=request, format=format),
        'nics': reverse('nic-list', request=request, format=format),
        'helps': reverse('help-list', request=request, format=format),
        'logs': reverse('log-list', request=request, format=format),
        'monitor': reverse('monitor', request=request, format=format),
    })


class DeviceList(APIView):
    """
    Retrieve, update or delete a device instance.
    """
    def get(self, request, format=None):
        devices = Device.objects.all()
        serializer = DeviceSerializer(devices, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = DeviceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        #logger = logging.getLogger("django.request")
        logger.debug("post device is fail,")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeviceDetail(APIView):
    """
    Retrieve, update or delete a device instance.
    """
    def get_object(self, pk):
        try:
            return Device.objects.get(pk=pk)
        except Device.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        device = self.get_object(pk)
        serializer = DeviceSerializer(device)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        device = self.get_object(pk)
        serializer = DeviceSerializer(device, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        device = self.get_object(pk)
        device.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)





class HostHardInfo(APIView):
    """
    List all hosts, or create a new host.
    """
    def get_object(self, pk):
        try:
            return Host.objects.get(pk=pk)
        except Host.DoesNotExist:
            raise Http404
            
    def get(self, request, pk, format=None):
        '''
        {}
        '''
        ret = '{'
        host = self.get_object(pk)
        host.host_name
        ret = ret + '"Host Name": ' + '"' + host.host_name + '",'
        ret = ret + '"IP": ' + '"' + host.ip + '", '
        ret = ret + '"Power Status": ' + '"On", '
        ret = ret + '"cpu1": "ok", "cpu2": "ok"'
        ret = ret + '}'

        response = json.loads(ret)

        print response
        print ret

        dic = {'Host Name': 'xdfs-01', 'IP': '192.168.1.200', 'Power Status': 'On', 'cpu1': 'ok', 'cpu2': 'ok'}

        li = [['Host Name','xdfs-01'], ['IP','192.168.1.200'], ['Power Status','On'], ['cpu1','ok'], ['cpu2','ok']]

        return Response(li)


class HostList(APIView):
    """
    List all hosts, or create a new host.
    """
    def get_host_obj(self, ip):
        try:
            return Host.objects.get(ip=ip)
        except Host.DoesNotExist:
            raise Http404
            
    def get(self, request, format=None):
        hosts = Host.objects.all()
        serializer = HostSerializer(hosts, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        '''
        1 or n hosts
        '''
        serializer = HostSerializer(data=request.data)
        if serializer.is_valid():
            data=request.data
            hostip=data["ip"]
            
            ret = tao_host_alive(hostip)
            if (ret == False):
                print "add host fail!"
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            print "add host success!"
            
            serializer.save()
            
            #collect disk hardware info backend.
            host = self.get_host_obj(hostip)
            hostid = host.host_id
            
            tao_collect_hardware_info(hostid, hostip)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class HostDetail(APIView):
    """
    Retrieve, update or delete a host instance.
    """
    def get_object(self, pk):
        try:
            return Host.objects.get(pk=pk)
        except Host.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        host = self.get_object(pk)
        serializer = HostSerializer(host)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        host = self.get_object(pk)
        serializer = HostSerializer(host, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        host = self.get_object(pk)
        host.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DiskList(APIView):
    """
    Retrieve, update or delete a disk instance.
    """
    
            
    def get(self, request, format=None):
        '''
        get disk info list.
        '''
        disks = Disk.objects.all()
        serializer = DiskSerializer(disks, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):        
        serializer = DiskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DiskInfoCollector(APIView):
    """
    Retrieve, collect a disk info.
    """
    def get_host_object(self, pk):
        '''
        get host info(eg: ip address) by host_id.
        '''
        try:
            return Host.objects.get(pk=pk)
        except Host.DoesNotExist:
            raise Http404

    def post(self, request, format=None):
        '''
        IN:     (host_id array) eg: 
        {
            "hosts": [
                {
                    "host_id": 3
                },
                {
                    "host_id": 5
                }
            ]
        }
        
        OUT:    OK or ERROR
        DESC:   collect the host's disk (hardware) info by host id posted by user. 
        '''
        host_list = request.data['hosts']
        for host in host_list:
            #get ip
            host_id = host['host_id']
            host_info = self.get_host_object(host_id)
            host_ip = host_info.ip
            print host_ip

            #colletc disk hardware info.
            ret = tao_exc_cmd_instant('bash get_drive_info.sh', host_ip)
            hardware_info = ret[108:]
            print hardware_info
            disk_num = hardware_info.count('\n') + 1
            disk_info = {'host_id':host_id, 'enclosure_id':'', 'slot_num':'', 'size':'', 'health_state':'', 'wwn':'', 'media_type':'', 'protocol':'', 'vendor_info':''}
            for i in range(disk_num):
                x = 128*i
                disk_info['enclosure_id'] = hardware_info[(0+x):(11+x)]
                disk_info['slot_num'] = hardware_info[(12+x):(19+x)]
                disk_info['size'] = hardware_info[(23+x):(38+x)]
                disk_info['health_state'] = hardware_info[(40+x):(51+x)]
                disk_info['wwn'] = hardware_info[(53+x):(70+x)]
                disk_info['media_type'] = hardware_info[(73+x):(80+x)]
                disk_info['protocol'] = hardware_info[(85+x):(95+x)]
                disk_info['vendor_info'] = hardware_info[(96+x):(126+x)]
                print disk_info
                serializer = DiskSerializer(data=disk_info)
                if serializer.is_valid():
                    serializer.save()
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
           
        return Response(status=status.HTTP_200_OK)


class DiskDetail(APIView):
    """
    Retrieve, update or delete a disk instance.
    """
    def get_object(self, pk):
        try:
            return Disk.objects.get(pk=pk)
        except Disk.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        disk = self.get_object(pk)
        serializer = DiskSerializer(disk)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        disk = self.get_object(pk)
        serializer = DiskSerializer(disk, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        disk = self.get_object(pk)
        disk.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CpuList(APIView):
    """
    Retrieve, update or delete a cpu instance.
    """
    def get(self, request, format=None):
        cpus = Cpu.objects.all()
        serializer = CpuSerializer(cpus, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = CpuSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CpuDetail(APIView):
    """
    Retrieve, update or delete a cpu instance.
    """
    def get_object(self, pk):
        try:
            return Cpu.objects.get(pk=pk)
        except Cpu.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        cpu = self.get_object(pk)
        serializer = CpuSerializer(cpu)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        cpu = self.get_object(pk)
        serializer = CpuSerializer(cpu, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        cpu = self.get_object(pk)
        cpu.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class MemoryList(APIView):
    """
    Retrieve, update or delete a memory instance.
    """
    def get(self, request, format=None):
        memorys = Memory.objects.all()
        serializer = MemorySerializer(memorys, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = MemorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MemoryDetail(APIView):
    """
    Retrieve, update or delete a memory instance.
    """
    def get_object(self, pk):
        try:
            return Memory.objects.get(pk=pk)
        except Memory.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        memory = self.get_object(pk)
        serializer = MemorySerializer(memory)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        memory = self.get_object(pk)
        serializer = MemorySerializer(memory, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        memory = self.get_object(pk)
        memory.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)




class NicList(APIView):
    """
    Retrieve, update or delete a nic instance.
    """
    def get(self, request, format=None):
        nics = Nic.objects.all()
        serializer = NicSerializer(nics, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        print request.data
        hostid = request.data['host_id']
        hostip = request.data['ip']
        tao_collect_nic_info_from_host(hostid, hostip)
        return Response(status=status.HTTP_200_OK)
        '''
        serializer = NicSerializer(data=request)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        '''


class NicDetail(APIView):
    """
    Retrieve, update or delete a nic instance.
    """
    def get_object(self, pk):
        try:
            return Nic.objects.get(pk=pk)
        except Nic.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        nic = self.get_object(pk)
        serializer = NicSerializer(nic)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        nic = self.get_object(pk)
        serializer = NicSerializer(nic, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        nic = self.get_object(pk)
        nic.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class HelpList(APIView):
    """
    Retrieve, update or delete a help instance.
    """
    def get(self, request, format=None):
        helps = Help.objects.all()
        serializer = HelpSerializer(helps, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = HelpSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class HelpDetail(APIView):
    """
    Retrieve, update or delete a help instance.
    """
    def get_object(self, pk):
        try:
            return Help.objects.get(pk=pk)
        except Help.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        help = self.get_object(pk)
        serializer = HelpSerializer(help)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        help = self.get_object(pk)
        serializer = HelpSerializer(Help, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        help = self.get_object(pk)
        help.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogList(APIView):
    """
    Retrieve, update or delete a log instance.
    """
    def get(self, request, format=None):
        logs = Log.objects.all()
        serializer = LogSerializer(logs, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = LogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogDetail(APIView):
    """
    Retrieve, update or delete a log instance.
    """
    def get_object(self, pk):
        try:
            return Log.objects.get(pk=pk)
        except Log.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        log = self.get_object(pk)
        serializer = LogSerializer(log)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        log = self.get_object(pk)
        serializer = LogSerializer(log, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        log = self.get_object(pk)
        log.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InfoCollector(APIView):
    """
    Retrieve, collect a disk info.
    """
    def post(self, request, format=None):
        #get all host info from database.
        hosts = Host.objects.all()
        for host in hosts:
            #get host id & ip.
            host_id = host.host_id
            host_ip = host.ip
            print host_ip

            #colletc disk hardware info.
            ret = tao_exc_cmd_instant('bash get_drive_info.sh', host_ip)
            hardware_info = ret[108:]
            print hardware_info
            disk_num = hardware_info.count('\n') + 1
            disk_info = {'host_id':host_id, 'enclosure_id':'', 'slot_num':'', 'size':'', 'health_state':'', 'wwn':'', 'media_type':'', 'protocol':'', 'vendor_info':''}
            disk = DiskList()
            for i in range(disk_num):
                x = 128*i
                disk_info['enclosure_id'] = hardware_info[(0+x):(11+x)]
                disk_info['slot_num'] = hardware_info[(12+x):(19+x)]
                disk_info['size'] = hardware_info[(23+x):(38+x)]
                disk_info['health_state'] = hardware_info[(40+x):(51+x)]
                disk_info['wwn'] = hardware_info[(53+x):(70+x)]
                disk_info['media_type'] = hardware_info[(73+x):(80+x)]
                disk_info['protocol'] = hardware_info[(85+x):(95+x)]
                disk_info['vendor_info'] = hardware_info[(96+x):(126+x)]
                print disk_info
                serializer = DiskSerializer(data=disk_info)
                if serializer.is_valid():
                    serializer.save()
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
           
        return Response(status=status.HTTP_200_OK)


'''
taocloudMonitor's views
'''
class MonitorView(APIView):
    def get_host_obj(self, ip):
        try:
            return Host.objects.get(ip=ip)
        except Host.DoesNotExist:
            raise Http404
    
    def post(self, request, format=None):
        taocloud_mon_save_allinfo(request.data)
        return Response(status=status.HTTP_201_CREATED)
        

class MonDiskIOView(APIView):
    '''
    time: decide the range of data. M
    get_type: decide the record number selected from queried data. N
    '''
    def get(self, request, mon_type, time_len, get_type, disk_str, format=None):
        '''
        [[[eg: /api/monitor/iops/10/i/1-1,2,_2-1,2,_/]]] --> discarded!!!
        eg: 
        /api/monitor/iops/10/i/h-1-3-4-  -->  host id : 1,3,4
        /api/monitor/iops/10/i/d-1-1-2-3-5-6-2-4-  --> (host1,disk 1)-(host2,disk3)...
        /api/monitor/iops/10/i/all     -->all hosts's disk info .
        time: seconds.(eg. 10min = 600s, 30min = 1800s ...)
        '''
        print request.data
        print time_len
        print get_type
        print disk_str

        #Agent record monitor data every 5 seconds.
        #time_piece = 5
        
        # 120 = 10*60/5
        data_range_dic = {'10': 120, '30': 360}
        record_number_dic = {'i': 60, 'a': 1}

        current_time = int((time.time()) * 1000)
        #current_time = 1482283228199

        data_range = data_range_dic[time_len]

        rec_num = record_number_dic[get_type]

        ret = taocloud_mon_diskio_process(mon_type, data_range, rec_num, disk_str, current_time)
        
        
        #rec_list = taocloud_mon_diskio_get_records(1, 1, 120, 60, 1482283228199)

        #ret_data = taocloud_mon_diskio_packagdata(rec_list, 'iops')
        
        return Response(ret)

class MonCpuView(APIView):
    '''
    host's cpu monitor data is much like the mem monitor data.
    1\get a record list (like [...]) queried from database (hosts_moncpu or hosts_monmem).
      if there are many hosts, you need query many times , and get a list like [[...], [...]]
    2\calculate the lists you got. then return the final data.
    '''
    def get(self, request, mon_type, time_len, get_type, host_str, format=None):
        data_range_dic = {'10': 120, '30': 360}
        record_number_dic = {'i': 60, 'a': 1}

        current_time = int((time.time()) * 1000)
        #current_time = 1482291588597

        data_range = data_range_dic[time_len]

        rec_num = record_number_dic[get_type]
        
        ret = taocloud_mon_cpu_process(data_range, rec_num, host_str, current_time)
        return Response(ret)
        
class MonMemView(APIView):
    def get(self, request, mon_type, time_len, get_type, host_str, format=None):
        data_range_dic = {'10': 120, '30': 360}
        record_number_dic = {'i': 60, 'a': 1}

        current_time = int((time.time()) * 1000)
        #current_time = 1482291588597
        
        data_range = data_range_dic[time_len]

        rec_num = record_number_dic[get_type]
        
        ret = taocloud_mon_mem_process(data_range, rec_num, host_str, current_time)
        
        return Response(ret)

class JobView(APIView):
    '''
    IN: {
         "job_name": "",
         "job_args": {}
        }

    OUT: job id
    '''
    def post(self, request, format=None):
        '''
        for key in request.data:
            data = key
            break
        '''

        data = request.data
        
        job_name = data['job_name']
        job_args = data['job_args']
        
        ret = taocloud_job_accept(job_name, job_args)

        return Response(status=status.HTTP_200_OK)
        

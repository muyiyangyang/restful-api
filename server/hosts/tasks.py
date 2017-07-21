# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
import pika
import uuid
import time
import re
import logging

from hosts.serializers import DiskSerializer
from hosts.serializers import HostSerializer
from hosts.serializers import CpuSerializer
from hosts.serializers import NicSerializer

from hosts.serializers import MonDiskIOSerializer
from hosts.serializers import MonMemSerializer
from hosts.serializers import MonCpuSerializer

from hosts.models import Host
from hosts.models import Disk
from hosts.models import Nic

from hosts.models import MonDiskIO
from hosts.models import MonCpu
from hosts.models import MonMem

#++++++++++++++++++++++++++++++++
#            log ^_^
#++++++++++++++++++++++++++++++++
serlog = logging.getLogger('server')
serlog.setLevel(logging.DEBUG)
serlog_handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(name)s:%(levelname)s: %(message)s')
serlog_handler.setFormatter(formatter)
serlog.addHandler(serlog_handler)

_____NEW_RPC_____ = 0
class RPCClient(object):
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                host='localhost'))

        self.channel = self.connection.channel()

        #exchange
        self.channel.exchange_declare(exchange='direct_ip', type='direct')

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue
        
        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, cmd, ip):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='direct_ip',
                                   routing_key=ip,
                                   properties=pika.BasicProperties(
                                         reply_to = self.callback_queue,
                                         correlation_id = self.corr_id,
                                         ),
                                   body=cmd)
        print "published rpc  message"
        
        wait_time_out = 150 # 60*1000 ms / 200 ms = 300
        count = 0
        while self.response is None and count <= wait_time_out:
            self.connection.process_data_events()
            time.sleep(0.2)
            count = count + 1
        
        return (self.response)

@shared_task(bind=True)
def ctask_rpc(self, arg, ip):
    
    cmd_rpc = RPCClient()

    print(" [x] Requesting cmd")
    response = cmd_rpc.call(arg, ip)
    #print(" [.] Got %r" % response)

    return (response)

_____DEFINE_SYN_ASYN_RPC_API_____ = 0
#Synchronous RPC interface
def ser_rpc_sync(arg, ip):
    print "ser_rpc_sync: now excute task."
    ret = ctask_rpc(arg, ip)
    return ret

#Asynchronous RPC interface
def ser_rpc_asyn(arg, ip):
    print "ser_rpc_asyn: now excute task."
    task_handle = ctask_rpc.delay(arg, ip)
    
    print task_handle
    return task_handle

def ser_host_alive(ip):
    ret = ser_rpc_sync('DETACT_HOST', ip)

    if (ret == 'HOST_ALIVE'):
        return True
    else:
        return False

def ser_exc_cmd_timeconsuming(cmdline, ip):
    '''
    excute cmd which is time-consuming on remote node, 
    you can't get result soon but a result handle instead.
    '''
    ret_handle = ser_rpc_asyn(cmdline, ip)
    return ret_handle

def ser_exc_cmd_instant(cmdline, ip):
    '''
    excute cmd on remote node and you can get result soon.
    '''
    ret = ser_rpc_sync(cmdline, ip)
    return ret

_____DEFINE_NORMAL_TOOL_API_____ = 0

#collect disk's logic info by smartctl tool.
#the reason to do this is you don't know disk's logic name is '/dev/sda' or '/dev/sdb'...
#you can solve this problem by disk's guid/wwn, the unique number, just like a primary key in data base.

def ser_get_logic_disk_list(lsblk):
    '''
    IN:
    [root@hostname home]# lsblk
    NAME   MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
    sda      8:0    0 558.9G  0 disk 
    sdb      8:16   0 558.9G  0 disk 
    sdc      8:32   1  14.3G  0 disk 
    --sdc1   8:33   1     2G  0 part [SWAP]
    --sdc2   8:34   1  12.3G  0 part /

    OUT: ['sda', 'sdb', 'sdc']
    '''
    ret = []
    tmp = lsblk
    while 1:
        pos = tmp.find('\n')
        if (pos == -1):
            break

        tmp = tmp[pos + 1:]

        if (len(tmp) < 3):
            break

        name = tmp[0:3]
        if (name[0:2] == 'sd'):
            ret.append(name)

    return ret
        

def ser_collect_disk_logic_info(hostid, hostip):
    '''
    you need run this step after the host's reboot.
    '''
    lsblk_info = ser_exc_cmd_instant('lsblk', hostip)

    name_list = ser_get_logic_disk_list(lsblk_info)
    if (len(name_list) == 0):
        return (0)
    serlog.debug("ser_collect_disk_logic_info:" + str(name_list))

    for name in name_list:
        device_name = '/dev/' + name
        cmd = "smartctl -a " + device_name + " | grep 'Logical Unit id'"
        
        ret = ser_exc_cmd_instant(cmd, hostip)
        if (len(ret) == 0):
            continue

        #ret :  'Logical Unit id:      0x5000cca070863e0c'
        guid = ret[24:40] #'5000cca070863e0c'

        serlog.debug("ser_collect_disk_logic_info:" + "guid = " + guid)

        disks = Disk.objects.filter(host_id=hostid, wwn=guid)
        if (len(disks) != 1):
            serlog.debug("ser_collect_disk_logic_info:" + "host_id="+str(hostid)+"name="+name)
            continue
        
        disk = disks[0]

        disk.disk_name = name
        print name
        print "start saving name info."
        disk.save()

    return (0)

@shared_task(bind=True)
def ser_collect_disk_hardware_info(self, hostid, hostip):
    #colletc disk hardware info.
    ret = ser_exc_cmd_instant('bash get_drive_info.sh', hostip)
    hardware_info = ret[108:]
    print hardware_info
    disk_num = hardware_info.count('\n') + 1
    disk_info = {'host_id':hostid, 'enclosure_id':'', 'slot_num':'', 'size':'', 'health_state':'', 'wwn':'', 'media_type':'', 'protocol':'', 'vendor_info':''}
    for i in range(disk_num):
        x = 128*i
        disk_info['enclosure_id'] = hardware_info[(0+x):(11+x)]
        disk_info['slot_num']     = hardware_info[(12+x):(19+x)]
        disk_info['size']         = hardware_info[(23+x):(38+x)]
        disk_info['health_state'] = hardware_info[(40+x):(51+x)]
        disk_info['wwn']          = hardware_info[(53+x):(70+x)]
        disk_info['media_type']   = hardware_info[(73+x):(80+x)]
        disk_info['protocol']     = hardware_info[(85+x):(95+x)]
        disk_info['vendor_info']  = hardware_info[(96+x):(126+x)]
        print disk_info

        #if disk existed, just update. else insert.
        query_list = Disk.objects.filter(wwn=disk_info['wwn'])
        if (len(query_list) == 1):
            disk_exist = query_list[0]
            serializer = DiskSerializer(disk_exist, data=disk_info)
        else:
            serializer = DiskSerializer(data=disk_info)
        
        if serializer.is_valid():
            serializer.save()
        else:
            print "disk hardware serializer is unvalid."
            print serializer

    return (0)
    
@shared_task(bind=True)
def server_collect_disk_info(self, hostid, hostip):
    ser_collect_disk_hardware_info(hostid, hostip)
    ser_collect_disk_logic_info(hostid, hostip)
    return (0)


def ser_save_nic_info(hostid, hostip, nic):
    line = nic.count('\n')
    if (line < 6):
        print "get nic info failed."
        return (-1)

    nicinfo = {'host_id':hostid, 'ip':'', 'netmask':'', 'gateway':'', 'mac':''}

def ser_save_gen_info(hostid, geninfo):
    '''
    save general info, like power status.
    '''
    pos = geninfo.find('Power Status')
    if (pos == -1):
        print "get Power Status failed."
        return (0)

    if (geninfo[pos + 15] == '\n'):
        print "Power Status is unknow."
        return (0)
    
    gen_info = {'host_id':hostid, 'status':'NA'}
    
    powerline = geninfo[pos:]
    pos_start = powerline.index('=') + 1
    pos_end = powerline.index('\n')

    power_status = powerline[pos_start:pos_end]
    
    print power_status
    
    gen_info['status'] = power_status
    
    serializer = HostSerializer(data=gen_info)
    if serializer.is_valid():
        serializer.save()
    else:
        print "gen_info serializer is unvalid."
        print serializer

def ser_save_cpu_info(hostid, cpuinfo):
    '''
    [Cpu]
    Cpu Number = 6
    Cpu1 = ok|32degreesC|
    Cpu2 = ok|35degreesC|
    Cpu3 = ok|0.69Volts|
    Cpu4 = ok|0.80Volts|
    Cpu5 = ok|0.94Volts|
    Cpu6 = ok|0.94Volts|
    
    
    '''
    #get "Cpu Number = 6 ... ..."
    s = cpuinfo[cpuinfo.find('Cpu Number'):]
    
    cpu_num = int(s[s.index('=')+1:s.index('\n')])

    if (cpu_num == 0):
        print "cpu number is 0."
        return (0)

    cpu_info = {'host_id': hostid,
               'cpu_name': 'cpu',
               'cpu_state': '',
               'temperature': ''
               }

    #start from "Cpu1 = ok|32degreesC| ... ..."
    line = s[s.index('\n') + 1:]
    for i in range(cpu_num):
        #get one row.
        row = line[0:line.index('\n')]
        #Cpu1 = ...
        name = row[0:row.index('=')]
        # = ok| ...
        state = row[row.index('=') + 1:row.index('|')]

        cpu_info['cpu_name'] = name
        cpu_info['cpu_state'] = state

        serializer = CpuSerializer(data=cpu_info)
        if serializer.is_valid():
            serializer.save()
        else:
            print "cpuinfo serializer is unvalid."
            print serializer

        line = line[line.index('\n') + 1:]

    
@shared_task(bind=True)
def ser_collect_ipmi_info(self, hostid, hostip):
    '''
    [General] [Network] [Board] [Cpu] [Memory] [Fan] [VBAT] [User]
    1 save host info( power status...)
    2 save cpu info 
    '''
    r = ser_exc_cmd_instant('cat ipmiresult.txt', hostip)
    
    #network
    pgen   = r.find('[General]')
    pnet   = r.find('[Network]')
    pboard = r.find('[Board]')
    pcpu   = r.find('[Cpu]')
    pmem   = r.find('[Memory]')
    pfan   = r.find('[Fan]')
    
    general = r[pgen:pnet - 2]
    ser_save_gen_info(hostid, general)
    
    cpu = r[pcpu:pmem - 2]
    ser_save_cpu_info(hostid, cpu)
    
    return (0)
    

g_netmask = {8:  "255.0.0.0", 
             16: "255.255.0.0", 
             24: "255.255.255.0"}

@shared_task(bind=True)
def ser_collect_nic_info_from_host(self, hostid, hostip):
    '''
    [root@wangchao ~]# ip a 
    1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN 
        link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
        inet 127.0.0.1/8 scope host lo
        inet6 ::1/128 scope host 
           valid_lft forever preferred_lft forever
    2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP qlen 1000
        link/ether 0c:c4:7a:c6:5e:18 brd ff:ff:ff:ff:ff:ff
        inet 192.168.1.119/24 brd 192.168.1.255 scope global eth0
        inet6 fe80::ec4:7aff:fec6:5e18/64 scope link 
           valid_lft forever preferred_lft forever
    3: eth1: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN qlen 1000
        link/ether 0c:c4:7a:c6:5e:19 brd ff:ff:ff:ff:ff:ff
    '''
    #get 'ip addr'
    r = ""
    r = ser_exc_cmd_instant('ip addr', hostip)
    serlog.debug("get ip a :"+r)
    
    #get nic info and save to database by loop
    #nic_num = r.count('link/ether')
    '''
    1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN 
    2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP qlen 1000
    3: eth1: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN qlen 1000
    '''
    nic_list = re.findall(r'\d.*: <.*\n', r)
    nic_list_len = len(nic_list)

    for i in range(nic_list_len):
        if (nic_list[i].find('lo:') != -1):
            #is loopback.
            continue
        
        if ( i == (nic_list_len - 1) ):
            #the last one
            pos_start = r.find(nic_list[i])
            nic_str = r[pos_start:]
        else:
            pos_start = r.find(nic_list[i])
            pos_end = r.find(nic_list[i + 1])
            nic_str = r[pos_start:pos_end]

        nic = {}
        
        nic['host_id'] = hostid

        #nic name : eth0 eth1...
        nm_start = nic_list[i].find(' ') + 1
        nm_end = nic_list[i].find('<') - 2
        nic['nic_name'] = nic_list[i][nm_start:nm_end]

        #mac addr
        pos_mac = nic_str.find('link/ether')
        if (pos_mac != -1):
            nic['mac'] = nic_str[pos_mac + 11:pos_mac + 28]
            #query nic by mac ,if exist, get primary key,mean update, else, insert.
            query_list = Nic.objects.filter(mac=nic['mac'])
            if (len(query_list) == 1):
                nic_exist = query_list[0]
                nic['nic_id'] = nic_exist.nic_id

        #netmask
        pos_ip = nic_str.find('inet ')
        if (pos_ip != -1):
            '''
            inet 192.168.1.119/24 brd 192.168.1.255 scope global eth0
            inet6 fe80::ec4:7aff:fec6:5e18/64 scope link 
                valid_lft forever preferred_lft forever
            '''
            tmp = nic_str[pos_ip:]
            pos_mask = tmp.find('/')
            #inet 192.168.1.119/
            ip = tmp[5:pos_mask]
            nic['ip'] = ip
            serlog.debug("find ip: "+ip)
            
            prefix = int(tmp[pos_mask + 1: pos_mask + 3])
            nic['netmask'] = g_netmask[prefix]

        serlog.debug(nic)
        if (nic.has_key('mac')):
            query_list = Nic.objects.filter(mac=nic['mac'])
            if (len(query_list) == 1):
                nic_exist = query_list[0]
                serializer = NicSerializer(nic_exist, data=nic)
            else:
                serializer = NicSerializer(data=nic)
        else:
            serializer = NicSerializer(data=nic)
                
        if serializer.is_valid():
            serializer.save()
    
    return (0)

def ser_collect_hardware_info(hostid, hostip):
    #co disk
    ret = server_collect_disk_info.delay(hostid, hostip)
    #co ipmi
    ret = ser_collect_ipmi_info.delay(hostid, hostip)

    ret = ser_collect_nic_info_from_host.delay(hostid, hostip)
    
    return (0)




_____DEFINE_MONITOR_____ = 0
#monitor
def server_mon_save_cpu(reclist, hostid):
    info_cpu = {'host_id':0,
                'name':"",
                'mon_type':"",
                'time':0,
                'user_average':0,
                'system_average':0,
                'idle_average':0,
                'iowait_average':0}

    for cpu in reclist:
        info_cpu['host_id'] = hostid
        info_cpu['name'] = cpu['id']
        info_cpu['mon_type'] = cpu['type']
        info_cpu['time'] = cpu['time']
        info_cpu['user_average'] = 0 #cpu['cpu.time.percent.user.average']
        info_cpu['system_average'] = 0 #cpu['cpu.time.percent.system.average']
        #Currently, only need idle percent.
        info_cpu['idle_average'] = cpu['cpu.time.percent.idle.average']
        info_cpu['iowait_average'] = 0 #cpu['cpu.time.iowait.average']
        serializer = MonCpuSerializer(data=info_cpu)
        if serializer.is_valid():
            serializer.save()
        else:
            print serializer.errors
            print "server_mon_save_cpu: serializer is not valid."

def server_mon_save_diskspace(reclist, hostid):
    pass

def server_mon_save_mem(reclist, hostid):
    info_mem = {'host_id':0,
                'name':"",
                'mon_type':"",
                'time':0,
                'used':0,
                'free':0,
                'available':0,
                'total':0,
                'percent':0}
    
    for mem in reclist:
        if (mem['id'] == 'swap'):
            continue
        
        info_mem['host_id'] = hostid
        info_mem['name'] = mem['id']
        info_mem['mon_type'] = mem['type']
        info_mem['time'] = mem['time']
        info_mem['used'] = mem['memory.used']
        info_mem['free'] = mem['memory.free']
        info_mem['available'] = mem['memory.available']
        info_mem['total'] = mem['memory.total']
        info_mem['percent'] = mem['memory.percent']
        serializer = MonMemSerializer(data=info_mem)
        if serializer.is_valid():
            serializer.save()
        else:
            print serializer.errors
            print "server_mon_save_mem: serializer is not valid."

def server_mon_save_network(reclist, hostid):
    pass

def server_mon_save_diskio(reclist, hostid):
    info_diskio = {'disk_id':0,
                   'name':"",
                   'mon_type':"",
                   'time':0,
                   'await_write':0,
                   'await_read':0,
                   'await_average':0,
                   'iops_write':0,
                   'iops_read':0, 
                   'bandwidth_write':0, 
                   'bandwidth_read':0, 
                   'size_average':0}

    for diskio in reclist:
        #get disk_id by 'host_id' and 'disk name'(sda ... )
        serlog.debug("server_mon_save_diskio:"+"host_id="+str(hostid)+" disk_name="+diskio['id'])
        disk = Disk.objects.filter(host_id=hostid, disk_name=diskio['id'])
        if (len(disk) != 1):
            print "server_mon_save_diskio: query disk info failed."
            continue
        
        #print disk[0]
        
        diskid = disk[0].disk_id

        #only sda sdb sdc ... is valid.
        '''
        if (len(re.findall(r'sd[a-z]', diskio['id']))):
            continue
        '''
        
        info_diskio['disk_id'] = diskid
        info_diskio['name'] = diskio['id']
        info_diskio['mon_type'] = diskio['type']
        info_diskio['time'] = diskio['time']
        info_diskio['await_write'] = diskio['disk.io.await.write']
        info_diskio['await_read'] = diskio['disk.io.await.read']
        info_diskio['await_average'] = diskio['disk.io.await.average']
        info_diskio['iops_write'] = diskio['disk.io.iops.write']
        info_diskio['iops_read'] = diskio['disk.io.iops.read']
        info_diskio['bandwidth_write'] = diskio['disk.io.bandwidth.write']
        info_diskio['bandwidth_read'] = diskio['disk.io.bandwidth.read']
        info_diskio['size_average'] = diskio['disk.io.size.average']
        
        serializer = MonDiskIOSerializer(data=info_diskio)
        if serializer.is_valid():
            serializer.save()
        else:
            print serializer.errors
            print "server_mon_save_diskio: serializer is not valid."
        

@shared_task(bind=True)
def server_mon_process_data(self, data):
    try:
        ip = data['host_ip']
        print "server_mon_process_data: get ip"
        print ip
        host = Host.objects.get(ip=ip)
        hostid = host.host_id
    except Host.DoesNotExist:
        print "server_mon_process_data: get host id by ip failed."

    #print data
    data_cpu = data['cpu.usage']
    data_mem = data['memory.usage']
    data_disk_io = data['disk.io']

    #not need currently.
    #data_network = request.data['network.size']
    #data_disk_space = request.data['disk.size']
    
    server_mon_save_cpu(data_cpu, hostid)
    server_mon_save_mem(data_mem, hostid)
    server_mon_save_diskio(data_disk_io, hostid)

    #not need currently.
    #server_mon_save_diskspace(reclist, diskid)
    #server_mon_save_network(reclist, nicid)
    return (0)

def server_mon_save_allinfo(data):
    server_mon_process_data.delay(data)
    return (0)

_____DEFINE_MON_DISKIO_____ = 0
def server_mon_get_diskio_disks(words):
    '''
    1-1,2,_   ==  [host_id]-[disk_id],[disk_id],_
    '''
    dic = {'host_id':'', 'disk_list':[]}
    pos_hostid = words.find('-')
    if (pos_hostid == -1):
        print "server_mon_get_diskio_disks: get pos_hostid failed."
        return ({})
    
    hostid = words[0:pos_hostid]
    dic['host_id'] = int(hostid)

    #-1,2,_
    tmp = words[pos_hostid:]
    #[1,2]
    disklist = re.findall(r"\d", tmp)
    dic['disk_list'] = disklist
    
    return dic

def server_mon_get_diskio_orderlist(diskstr):
    '''
    diskstr : 1-1,2,_2-1,2,_

    return : [{'host_id': 1, 'disk_list': ['1', '2']}, {'host_id': 2, 'disk_list': ['1', '2']}]
    '''
    order_list = []
    
    tmp = diskstr
    while 1:
        pos_end = tmp.find('_')
        if (pos_end == -1):
            break
        
        #get : ' 1-1,2,_ '
        word = tmp[0:pos_end + 1]
        
        #dic :  {'host_id':'', 'disk_list':[]}
        dic = server_mon_get_diskio_disks(word)
        order_list.append(dic)

        tmp = tmp[pos_end + 1:]
    
    return order_list

def server_mon_get_diskio_orderlist_ex(diskstr):
    '''
    diskstr : 1-2-2-3-1-4-2-5-3-6-
    This string means : (host id 1, disk id 2) - (host id 2, disk id 3) - ...
    
    return : [{'host_id': 1, 'disk_list': ['1', '2']}, {'host_id': 2, 'disk_list': ['2', '3']}]
    '''
    #var_array : [1,2,2,3,1,4,2,5,3,6]
    var_array = re.findall(r"\d+", diskstr)
    
    array_len = len(var_array)
    if (array_len % 2 != 0):
        print "server_mon_get_diskio_orderlist_ex: diskstr is error."

    tmp = {}
    for i in range(0, array_len, 2):
        host_id = var_array[i]
        disk_id = var_array[i + 1]
        if (tmp.has_key(host_id)):
            tmp[host_id].append(disk_id)
        else:
            tmp[host_id] = []
            tmp[host_id].append(disk_id)

    ret = []
    for key in tmp:
        ret.append({'host_id':key, 'disk_list': tmp[key]})

    return ret

def server_mon_get_diskio_orderlist_all():
    # <QuerySet [{u'host_id': 13L}, {u'host_id': 15L}, {u'host_id': 16L}]>
    hostid_set = Host.objects.all().values("host_id")
    ret = []
    for h in hostid_set:
        disk_list = []
        hostid = int(h['host_id'])
        diskid_set = Disk.objects.filter(host_id=hostid)
        for d in diskid_set:
            disk_list.append(d.disk_id)

        ret.append({"host_id": hostid, "disk_list": disk_list})

    return ret

def server_mon_get_diskio_orderlist_by_host(diskstr):
    host_list = re.findall(r"\d+", diskstr)
    ret = []
    for h in host_list:
        disk_list = []
        diskid_set = Disk.objects.filter(host_id=h)
        for d in diskid_set:
            disk_list.append(d.disk_id)

        ret.append({"host_id": h, "disk_list": disk_list})

    return ret

def server_mon_diskio_get_records(hostid, diskid, datarange, number, curtime):
    '''
    curtime: eg. 1483669284874
    return a record list. len = number. if data is not enough, use zero value.
    '''
    if (number > 1):
        #data range
        #every 15s agent post monitor data.
        time_min = curtime - (datarange*5*1000) - 15*1000

        #select * from hosts_mondiskio where time >=time_min and host_id=hostid, disk_id=diskid
        #disk_records = MonDiskIO.objects.filter(host_id=hostid, disk_id=diskid, time__gte=time_min)
        disk_records = MonDiskIO.objects.filter(disk_id=diskid, time__gte=time_min)

        rec_len = len(disk_records)

        step = datarange / number

        #ordered by time
        ret_list = []
        i = 0
        while i <= datarange and i < rec_len:
            ret_list.append(disk_records[i])
            i = i + step
        
        return ret_list
    elif ((number == 1)):
        time_min = curtime - 15*1000
        
        disk_records = MonDiskIO.objects.filter(disk_id=diskid, time__gte=time_min)
        
        rec_len = len(disk_records)
        if (rec_len == 0):
            print "server_mon_diskio_get_records: get records failed when number is 1."
            return ([])

        ret_list = []
        ret_list.append(disk_records[rec_len - 1])

        return ret_list

    else:
        return ([])

def server_mon_diskio_scan_orderlist(orderlist, datarange, num, curtime):
    '''
    order_list --> [{'host_id': 1, 'disk_list': [1, 2]}, {'host_id': 2, 'disk_list': [1, 3]}]
    '''
    if (len(orderlist) == 0):
        print "server_mon_diskio_scan_reclist: size of orderlist is 0"
        return ([])
    
    diskrecslist = []
    for host in orderlist:
        hostid = host['host_id']
        disklist = host['disk_list']
        if (len(disklist) == 0):
            #you can handle all disks in 1 host here.
            continue
        
        for disk in disklist:
            diskrecs = server_mon_diskio_get_records(hostid, disk, datarange, num, curtime)
            #diskrecs is a list.
            if (len(diskrecs) == 0):
                continue
            diskrecslist.append(diskrecs)
            #diskrecslist loos like [[...], [...]]

    return diskrecslist

def server_mon_diskio_calculate_mondata(mondatalist, data_type):
    '''
    calculate data from diffrent disks. or maybe there's only 1 disk's data.
    
    data_type: 'iops' 'bandwidth' 'await'
    '''

    print "server_mon_diskio_calculate_mondata"
    print mondatalist
    
    if (len(mondatalist) == 0):
        print "server_mon_diskio_calculate_mondata: mondatalist len is 0."
        return (0)

    minlistlen = len(mondatalist[0][data_type+'_read'])
    for mondata in mondatalist:
        listlen = len(mondata[data_type+'_read'])
        if (minlistlen > listlen):
            minlistlen = listlen
    
    r_list = []
    w_list = []

    for i in range(minlistlen):
        #diffrent disk's monitor data time stamp maybe diffrent, we choose the first one's time stamp.
        r_list.append({"time":mondatalist[0][data_type+'_read'][0]['time'], "value":0})
        w_list.append({"time":mondatalist[0][data_type+'_write'][0]['time'], "value":0})
    
    if (data_type == 'iops'):
        for mondata in mondatalist:
            for i in range(minlistlen):
                r_list[i]['value'] = r_list[i]['value'] + mondata['iops_read'][i]['value']
                r_list[i]['time'] = mondata['iops_read'][i]['time']
                w_list[i]['value'] = w_list[i]['value'] + mondata['iops_write'][i]['value']
                w_list[i]['time'] = mondata['iops_write'][i]['time']

        ret = {"iops_read":[], "iops_write": []}
        ret["iops_read"] = r_list
        ret["iops_write"] = w_list

        return ret
        
    elif (data_type == 'bandwidth'): 
        for mondata in mondatalist:
            for i in range(minlistlen):
                r_list[i]['value'] = r_list[i]['value'] + mondata['bandwidth_read'][i]['value']
                r_list[i]['time'] = mondata['bandwidth_read'][i]['time']
                w_list[i]['value'] = w_list[i]['value'] + mondata['bandwidth_write'][i]['value']
                w_list[i]['time'] = mondata['bandwidth_write'][i]['time']

        ret = {"bandwidth_read":[], "bandwidth_write": []}
        ret["bandwidth_read"] = r_list
        ret["bandwidth_write"] = w_list

        return ret
        
    elif (data_type == 'await'):
        for mondata in mondatalist:
            for i in range(minlistlen):
                v_read = mondata['await_read'][i]['value']
                v_write = mondata['await_write'][i]['value']
                
                r_list[i]['value'] = (r_list[i]['value'] if r_list[i]['value'] > v_read else v_read)
                r_list[i]['time'] = mondata['await_read'][i]['time']
                
                w_list[i]['value'] = (w_list[i]['value'] if w_list[i]['value'] > v_write else v_write)
                w_list[i]['time'] = mondata['await_write'][i]['time']

        ret = {"await_read":[], "await_write": []}
        ret["await_read"] = r_list
        ret["await_write"] = w_list

        return ret

    return (0)
    
def server_mon_diskio_packagdata(rec_list, data_type):
    '''
    discription : pick monitor data by type.
    
    rec_list: data list queried from table hosts_mondiskio. 
    data_type: 'iops' 'bandwidth' 'await'
    '''
    r_list = []
    w_list = []
    for rec in rec_list:
        if data_type == 'iops':
            r_list.append({"time":rec.time, "value":rec.iops_read})
            w_list.append({"time":rec.time, "value":rec.iops_write})
        elif data_type == 'bandwidth':
            r_list.append({"time":rec.time, "value":rec.bandwidth_read})
            w_list.append({"time":rec.time, "value":rec.bandwidth_write})
        elif data_type == 'await':
            r_list.append({"time":rec.time, "value":rec.await_read})
            w_list.append({"time":rec.time, "value":rec.await_write})

    if (data_type == "iops"):
        ret_iops = {"iops_read":[], "iops_write": []}
        ret_iops["iops_read"] = r_list
        ret_iops["iops_write"] = w_list
        return ret_iops

    elif (data_type == "bandwidth"):
        ret_band = {"bandwidth_read":[], "bandwidth_write": []}
        ret_band["bandwidth_read"] = r_list
        ret_band["bandwidth_write"] = w_list
        return ret_band
        
    elif ((data_type == "await")):
        ret_await = {"await_read":[], "await_write": []}
        ret_await["await_read"] = r_list
        ret_await["await_write"] = w_list
        return ret_await

    return (0)

def server_mon_diskio_collectpkgs(diskrecslist, montype):
    datas = []
    for diskrecs in diskrecslist:
        data = server_mon_diskio_packagdata(diskrecs, montype)
        datas.append(data)

    return datas

def server_mon_diskio_process(montype, datarange, recnum, diskstr, curtime):
    
    # order_list --> [{'host_id': 1, 'disk_list': [1, 2]}, {'host_id': 2, 'disk_list': [1, 3]}]
    #order_list = server_mon_get_diskio_orderlist(diskstr)
    if (diskstr == 'all'):
        #/all/
        order_list = server_mon_get_diskio_orderlist_all()
    elif (diskstr[0] == 'h'):
        #/h-1-3-2-6   host id
        order_list = server_mon_get_diskio_orderlist_by_host(diskstr)
    else:
        #d-1-2-2-5-4-2-    hostid-diskid
        order_list = server_mon_get_diskio_orderlist_ex(diskstr)
        
    print order_list

    diskrecslist = server_mon_diskio_scan_orderlist(order_list, datarange, recnum, curtime)

    mondatalist = server_mon_diskio_collectpkgs(diskrecslist, montype)
    
    ret_data = server_mon_diskio_calculate_mondata(mondatalist, montype)

    return ret_data

_____DEFINE_MON_CPU_____ = 0

def server_mon_get_hostid_by_string(hoststr):
    hostid_list = re.findall(r"\d+", hoststr)
    return hostid_list

def server_mon_get_list_minsize(lists):
    '''
    ARG: [[...], [...], ...]
    '''
    if (len(lists) == 0):
        minsize = 0
        return minsize
        
    minsize = len(lists[0])
    for lst in lists:
        length = len(lst)
        if minsize > length:
            minsize = length

    return minsize

def server_mon_get_mintime(datarange, recnum, curtime):
    if (recnum == 1):
        time_min = curtime - 15*1000
    else:
        time_min = curtime - (datarange*5*1000) - 15*1000

    return time_min

def server_mon_cpu_process(datarange, recnum, hoststr, curtime):
    #get host id
    if (hoststr == 'all'):
        # <QuerySet [{u'host_id': 13L}, {u'host_id': 15L}, {u'host_id': 16L}]>
        hostid_set = Host.objects.all().values("host_id")
        hostid_list = server_mon_get_hostid_by_string(str(hostid_set))
    else:
        hostid_list = server_mon_get_hostid_by_string(hoststr)

    cpurecslist = []

    for hostid in hostid_list:
        #data range
        #every 15s agent post monitor data.
        time_min = server_mon_get_mintime(datarange, recnum, curtime)
        
        cpurecs = MonCpu.objects.filter(host_id=hostid, time__gte=time_min)
        if (len(cpurecs) == 0):
            continue

        v_percent_list = []
        if (recnum == 1):
            rec_len = len(cpurecs)
            if (rec_len == 0):
                print "server_mon_cpu_process: rec_len is 0."
                continue
            v_allused = 100.00 - cpurecs[rec_len - 1].idle_average
            v_allused = round(v_allused, 2)
            v_time = cpurecs[rec_len - 1].time
            v_percent_list.append({"time":v_time, "value":v_allused})
        else:
            for rec in cpurecs:
                v_idle = rec.idle_average
                v_time = rec.time
                v_allused = 100.00 - v_idle
                v_allused = round(v_allused, 2)
                v_percent_list.append({"time":v_time, "value":v_allused})
        
        cpurecslist.append(v_percent_list)

    #cpurecslist --> [[...], [...], ...]
    lstminsize = server_mon_get_list_minsize(cpurecslist)

    retlist = []

    for i in range(lstminsize):
        retlist.append({"time":cpurecslist[0][i]['time'], "value":0})

    for recs in cpurecslist:
        for i in range(lstminsize):
            retlist[i]["value"] = (retlist[i]["value"] + recs[i]["value"]) / 2

    ret = {"cpu":retlist}
    return ret

def server_mon_mem_process(datarange, recnum, hoststr, curtime):
    #get host id
    if (hoststr == 'all'):
        # <QuerySet [{u'host_id': 13L}, {u'host_id': 15L}, {u'host_id': 16L}]>
        hostid_set = Host.objects.all().values("host_id")
        hostid_list = server_mon_get_hostid_by_string(str(hostid_set))
    else:
        hostid_list = server_mon_get_hostid_by_string(hoststr)

    recslist = []

    for hostid in hostid_list:
        #data range
        #every 15s agent post monitor data.
        time_min = server_mon_get_mintime(datarange, recnum, curtime)
        
        memrecs = MonMem.objects.filter(host_id=hostid, time__gte=time_min)
        if (len(memrecs) == 0):
            continue

        v_percent_list = []
        if (recnum == 1):
            rec_len = len(memrecs)
            if (rec_len == 0):
                print "server_mon_mem_process: rec_len is 0."
                continue
            v_percent = memrecs[rec_len - 1].percent
            v_time = memrecs[rec_len - 1].time
            v_percent_list.append({"time":v_time, "value":v_percent})
        else:
            for rec in memrecs:
                v_percent_list.append({"time":rec.time, "value":rec.percent})
        
        recslist.append(v_percent_list)

    #mem recslist --> [[...], [...], ...]
    lstminsize = server_mon_get_list_minsize(recslist)

    retlist = []

    for i in range(lstminsize):
        retlist.append({"time":recslist[0][i]['time'], "value":0})

    for recs in recslist:
        for i in range(lstminsize):
            retlist[i]["value"] = (retlist[i]["value"] + recs[i]["value"]) / 2

    ret = {"mem":retlist}
    return ret

_____DEFINE_JOB_____ = 0

g_disk_state_change = {
    'st_mounted': {
        'ACTION_UMOUNT': 'st_unmounted'
    },
    'st_uninited': {
        'ACTION_INIT': 'st_mounted'
    },
    'st_unmounted': {
        'ACTION_MOUNT': 'st_mounted',
        'ACTION_INIT': 'st_mounted'
    }
}

def tc_get_uuid_by_blkid(blkid):
    '''
    [root@hostname ~]# blkid /dev/sda
    /dev/sda: UUID="4ea81b96-92ef-44d0-9bbd-9f67dc58db11" TYPE="xfs" 
    '''
    pos = blkid.find('UUID')
    if (pos == -1):
        print "tc_get_uuid_by_blkid: find UUID error."
        return ""

    uuid = blkid[pos + 6:pos + 42]

    return uuid

def server_job_init_disk(args):
    '''
    IN: eg  {"disk_id": 1}
    '''
    diskid = args['disk_id']
    disk = Disk.objects.get(pk=diskid)
    host = disk.host_id
    diskname = disk.disk_name
    hostip = host.ip

    if (disk.mounted == True):
        print "server_job_init_disk: you must umount the disk first."
        return (0)
        

    #formate disk
    disk_fullname = '/dev/' + diskname  #  /dev/sda
    fmtcmd = 'mkfs.xfs -f ' + disk_fullname #  mkfs.xfs -f /dev/sda
    ret = ser_exc_cmd_instant(fmtcmd, hostip)

    disk.formated = True

    #get uuid
    blkidcmd = 'blkid ' + disk_fullname  #  blkid /dev/sda
    ret = ser_exc_cmd_instant(blkidcmd, hostip)

    print "print blkid ret."
    print ret

    uuid = tc_get_uuid_by_blkid(ret)
    if (uuid == ""):
        print "server_job_init_disk: get uuid error."
        return (0)
    disk.fmt_uuid = uuid

    #mount
    mnt_point = '/data/' + uuid
    ret = ser_exc_cmd_instant('mkdir -p ' + mnt_point, hostip)
    mnt = 'mount UUID="' + uuid + '" ' + mnt_point
    ret = ser_exc_cmd_instant(mnt, hostip)
    
    #write /etc/fstab
    #UUID=4ea81b96-92ef-44d0-9bbd-9f67dc58db11  /mnt/disk01    xfs defaults    0 0
    fstab = 'echo "UUID=' +uuid+' '+mnt_point+' '+'xfs defaults 0 0" >> /etc/fstab'
    ret = ser_exc_cmd_instant(fstab, hostip)

    disk.mounted = True

    disk.status = g_disk_state_change[disk.status]['ACTION_INIT']

    disk.save()

    return (0)


def server_job_formate(args):
    pass

def server_job_mount(args):
    '''
    IN: eg  {"disk_id": 1}
    '''
    diskid = args['disk_id']
    disk = Disk.objects.get(pk=diskid)
    host = disk.host_id
    diskname = disk.disk_name
    hostip = host.ip

    disk_fullname = '/dev/' + diskname  #  /dev/sda
    #get uuid
    blkidcmd = 'blkid ' + disk_fullname  #  blkid /dev/sda
    ret = ser_exc_cmd_instant(blkidcmd, hostip)

    uuid = tc_get_uuid_by_blkid(ret)
    if (uuid == ""):
        print "server_job_mount: get uuid error."
        return (0)

    #mount
    mnt_point = '/data/' + uuid
    ret = ser_exc_cmd_instant('mkdir -p ' + mnt_point, hostip)
    mnt = 'mount UUID="' + uuid + '" ' + mnt_point
    ret = ser_exc_cmd_instant(mnt, hostip)
    
    #write /etc/fstab
    #UUID=4ea81b96-92ef-44d0-9bbd-9f67dc58db11  /mnt/disk01    xfs defaults    0 0
    fstab = 'echo "UUID=' +uuid+' '+mnt_point+' '+'xfs defaults 0 0" >> /etc/fstab'
    ret = ser_exc_cmd_instant(fstab, hostip)

    disk.mounted = True

    disk.status = g_disk_state_change[disk.status]['ACTION_MOUNT']

    disk.save()
    return (0)

def server_job_umount(args):
    '''
    IN: eg  {"disk_id": 1}
    '''
    diskid = args['disk_id']
    disk = Disk.objects.get(pk=diskid)
    host = disk.host_id
    diskname = disk.disk_name
    hostip = host.ip

    #umount
    disk_fullname = '/dev/' + diskname  #  /dev/sda
    blkidcmd = 'blkid ' + disk_fullname #blkid /dev/sda
    ret = ser_exc_cmd_instant(blkidcmd, hostip)
    
    uuid = tc_get_uuid_by_blkid(ret)
    if (uuid == ""):
        print "server_job_init_disk: get uuid error."
        return (0)

    umnt = 'umount /data/'+uuid
    ret = ser_exc_cmd_instant(umnt, hostip)

    #del line contains UUID=uuid
    clear_fstab = "sed -i '/"+uuid+"/d' /etc/fstab"
    ret = ser_exc_cmd_instant(clear_fstab, hostip)

    disk.mounted = False
    disk.status = g_disk_state_change[disk.status]['ACTION_UMOUNT']
    disk.save()
    
    return (0)

g_job_dic = {
            "JOB_INIT_A_DISK"    : server_job_init_disk, 
            "JOB_FORMATE_A_DISK" : server_job_formate, 
            "JOB_MOUNT_A_DISK"   : server_job_mount, 
            "JOB_UMOUNT_A_DISK"  : server_job_umount
            }

def server_job_accept(job_name, job_args):
    return g_job_dic[job_name](job_args)

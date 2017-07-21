from django.shortcuts import render
# Create your views here.
from django.http import HttpResponse

from rest_framework import status, renderers, generics, permissions, renderers, viewsets
from rest_framework.decorators import api_view, detail_route
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django.contrib.auth.models import User
from hosts.models import Host
from hosts.serializers import *

from rest_framework import generics, permissions, renderers, viewsets
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, detail_route
from rest_framework.response import Response
from rest_framework.reverse import reverse

#for celery
from hosts.tasks import CT_HOST_is_ok

@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'hosts': reverse('host-list', request=request, format=format),
        'disks': reverse('disk-list', request=request, format=format),
        #'users': reverse('user-list', request=request, format=format),
        #'groups': reverse('group-list', request=request, format=format),
    })


@api_view(['GET','POST'])
def Host_list(request, format=None):
    if request.method=="GET":
   	hosts = Host.objects.all()
       	serializer = HostSerializer(hosts,many=True)

       	return Response(serializer.data)

    elif request.method == 'POST':
        data=request.data
	hostip=data["ip"]
	print hostip
        #--test--
        #is_host_ok = CT_HOST_is_ok('ip')
        #if (is_host_ok == True):
        #    print "add host ok!"
        #else:
        #    print "add host fail!"
        #--test--

        #serializer = HostSerializer(data=request.data)
        #if serializer.is_valid():
        #    is_host_ok = CT_HOST_is_ok('ip')
        #    if (is_host_ok == True):
        #        serializer.save()
        #        return Response(serializer.data, status=status.HTTP_201_CREATED)
        #        print "add host ok!"
        #    else:
        #        print "add host fail!"
        #        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        #else:
        #    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        #--test--
        serializer = HostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def Host_detial(request, pk, format=None):
    try:
        host = Host.objects.get(pk=pk)
    except Host.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = HostSerializer(host)
        return Response(serializer.data)

    elif request.method == "PUT":
        serializer = HostSerializer(host,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        host.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET','POST'])
def Disk_list(request, format=None):
    if request.method=="GET":
        disks = Disk.objects.all()
        serializer = DiskSerializer(disks,many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = DiskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def Disk_detial(request, pk, format=None):
    try:
        disk = Disk.objects.get(pk=pk)
    except Disk.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = DiskSerializer(disk)
        return Response(serializer.data)

    elif request.method == "PUT":
        serializer = DiskSerializer(disk,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        disk.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class HostViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = Host.objects.all()
    serializer_class = HostSerializer

class DiskViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = Disk.objects.all()
    serializer_class = DiskSerializer


class MemoryViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = Memory.objects.all()
    serializer_class = MemorySerializer

    #@detail_route(renderer_classes=[renderers.StaticHTMLRenderer])
    #def highlight(self, request, *args, **kwargs):
    #    memory = self.get_object()
    #    return Response(memory.highlighted)


class CpuViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = Cpu.objects.all()
    serializer_class = CpuSerializer


class NicViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = Nic.objects.all()
    serializer_class = NicSerializer

class DeviceViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

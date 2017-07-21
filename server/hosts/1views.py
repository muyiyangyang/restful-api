from django.shortcuts import render
# Create your views here.
# Create your views here.
from django.http import HttpResponse

from rest_framework import status
from rest_framework import renderers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import generics
from django.contrib.auth.models import User
from hosts.models import Host
from hosts.serializers import *


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'hosts': reverse('host-list', request=request, format=format),
        'hds': reverse('hd-list', request=request, format=format),
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
            #print request.body
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
def Hd_list(request, format=None):
        if request.method=="GET":
            hds = Hd.objects.all()
            serializer = HdSerializer(hds,many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            serializer = HdSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        #else:
        #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def Hd_detial(request, pk, format=None):
        try:
            hd = Hd.objects.get(pk=pk)
        except Hd.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if request.method == "GET":
            serializer = HdSerializer(hd)
            return Response(serializer.data)

        elif request.method == "PUT":
            serializer = HdSerializer(hd,data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

        elif request.method == "DELETE":
            hd.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

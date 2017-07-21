from django.conf.urls import url, include
from hosts import views

urlpatterns = [
    url(r'^devices/$', views.DeviceList.as_view(), name='device-list'),
    url(r'^devices/(?P<pk>[0-9]+)/$', views.DeviceDetail.as_view(), name='device-detial'),
    url(r'^collector/$', views.InfoCollector.as_view(), name='all-info-collection'),
    url(r'^hosts/$', views.HostList.as_view(), name='host-list'),
    url(r'^hosts/hardinfo/(?P<pk>[0-9]+)/$', views.HostHardInfo.as_view(), name='host-hard-info'),#added by lzc
    url(r'^hosts/(?P<pk>[0-9]+)/$', views.HostDetail.as_view(), name='host-detial'),
    url(r'^disks/$', views.DiskList.as_view(), name='disk-list'),
    url(r'^disks/collector$', views.DiskInfoCollector.as_view(), name='disk-info-collect'),#added by lzc
    url(r'^disks/(?P<pk>[0-9]+)/$', views.DiskDetail.as_view(), name='disk-detial'),
    url(r'^cpus/$', views.CpuList.as_view(), name='cpu-list'),
    url(r'^cpus/(?P<pk>[0-9]+)/$', views.CpuDetail.as_view(), name='cpu-detial'),
    url(r'^memorys/$', views.MemoryList.as_view(), name='memory-list'),
    url(r'^memorys/(?P<pk>[0-9]+)/$', views.MemoryDetail.as_view(), name='memory-detial'),
    url(r'^nics/$', views.NicList.as_view(), name='nic-list'),
    url(r'^nics/(?P<pk>[0-9]+)/$', views.NicDetail.as_view(), name='nic-detial'),
    url(r'^helps/$', views.HelpList.as_view(), name='help-list'),
    url(r'^helps/(?P<pk>[0-9]+)/$', views.HelpDetail.as_view(), name='help-detial'),
    url(r'^logs/$', views.LogList.as_view(), name='log-list'),
    url(r'^logs/(?P<pk>[0-9]+)/$', views.LogDetail.as_view(), name='log-detial'),

    #taocloudMonitor
    url(r'^monitor/$', views.MonitorView.as_view(), name='monitor'),
    url(r'^monitor/(iops)/(\d+)/(i|a)/(.*)/$', views.MonDiskIOView.as_view(), name='monitor-diskio-iops'),
    url(r'^monitor/(bandwidth)/(\d+)/(i|a)/(.*)/$', views.MonDiskIOView.as_view(), name='monitor-diskio-bandwidth'),
    url(r'^monitor/(await)/(\d+)/(i|a)/(.*)/$', views.MonDiskIOView.as_view(), name='monitor-diskio-bandwidth'),
    url(r'^monitor/(cpu)/(\d+)/(i|a)/(.*)/$', views.MonCpuView.as_view(), name='monitor-cpu'),
    url(r'^monitor/(mem)/(\d+)/(i|a)/(.*)/$', views.MonMemView.as_view(), name='monitor-mem'),
    url(r'^job/$', views.JobView.as_view(), name='job'),
]


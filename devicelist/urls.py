from django.conf.urls import url, include
from django.urls import include, path
from . import views, wbs, maps, tests, szo,fire


urlpatterns = [
	path('', views.devicelist, name='devicelist'),
	path('get_devicelist/', views.get_devicelist, name='get_devicelist'),
	path('fias_data_update/', views.fias_data_update, name='fias_data_update'),
	path('device_update/', views.device_update, name='device_update'),
	path('device_add/', views.device_add, name='device_add'),
	path('argus_sync/', views.argus_sync, name='argus_sync'),
	# path('tests/', tests.devicelist, name='devicelist'),
	# path('tests/get_devicelist/', tests.get_devicelist, name='get_devicelist'),
	path('wbs/', wbs.wbsdevicelist, name='wbs'),
	path('fire/', fire.firelist, name='fire'),
	path('fire/set_fire_data/', fire.set_fire_data, name='fire_set'),
	path('fire/firejornal/', fire.firejornal, name='firejornal'),
	path('wbs/set_wbs_data/', wbs.set_wbs_data, name='wbs_set'),
	path('maps/', maps.mainmap, name='maps'),
	path('maps/get_data', maps.get_data_for_map, name='get_data_for_map'),
	path('maps/get_service_data', maps.get_service_for_map, name='get_service_for_map'),
	path('topology/', views.topology, name='topology'),
	path('szo/', szo.start, name='szo'),
]

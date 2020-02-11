from django.conf.urls import url, include
from django.urls import include, path
from . import views, massconfig, generator, patterns_checking


urlpatterns = [
	path('', views.activator, name='activator'),
	path('generator/', generator.start_page, name='generator'),
	path('deactivator/', views.deactivator, name='deactivator'),
	path('other/', views.device_move, name='device_move'),
	path('history/', views.history, name='history'),
	path('massconfig/', massconfig.massconfig, name='massconfig'),
	path('massconfig/mass_config_send/', massconfig.configsend, name='massconfigsend'),
	path('admin/', views.admin, name='admin'),
	path('get_history/', views.get_history, name='get_history'),
	path('get_uplink_info/', views.get_uplink_info, name='get_uplink_info'),
	path('get_model/', views.get_model, name='get_model'),
	path('get_acds_id/', views.get_acds_id, name='get_acds_id'),
	path('get_acds_id_deactivator/', views.get_acds_id_deactivator, name='get_acds_id_deactivator'),
	path('get_device_move/', views.get_device_move, name='get_device_move'),
	path('admin/free_ip_refresh/', views.free_ip_refresh, name='free_ip_refresh'),
	path('admin/get_ticket_info/', views.get_ticket_info, name='get_ticket_info'),
	path('admin/get_acsw_node_id_update/', views.get_acsw_node_id_update, name='get_acsw_node_id_update'),
	path('admin/get_acds_id_remove/', views.get_acds_id_remove, name='get_acds_id_remove'),
	path('admin/get_acds_argus_status/', views.get_acds_argus_status, name='get_acds_argus_status'),
	path('admin/device_configure/', views.device_configure, name='device_configure'),
	path('generator/get_template/', generator.get_template, name='get_template'),
	path('generator/get_data_device/', generator.get_data_device, name='get_data_device'),
	path('patterns_checking/', patterns_checking.start, name='patterns_checking'),
	path('patterns_checking/get_patterns/', patterns_checking.get_patterns, name='get_patterns'),
	path('patterns_checking/add_pattern/', patterns_checking.add_pattern, name='add_pattern'),
	path('patterns_checking/get_networks/', patterns_checking.get_networks, name='get_networks'),
	path('patterns_checking/get_vlans/', patterns_checking.get_vlans, name='get_vlans'),
	path('patterns_checking/add_patterns_vlans/', patterns_checking.add_patterns_vlans, name='add_patterns_vlans'),
	path('patterns_checking/delete_pattern/', patterns_checking.delete_pattern, name='delete_pattern'),
]
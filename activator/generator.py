from django.shortcuts import render
from django.conf import settings
from django.shortcuts import redirect
from django.core.mail import send_mail
from django.core.mail import mail_admins
from django.http import JsonResponse

import jinja2
import sys, os, re, time
import json
import multimodule
import free_ip
import ipaddress
import configuration


def start_page(request):
	# check_aut_generator(request)
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]


	models = ['Cisco_ME-3600','Cisco_ME-3400','Zyxel_MES-3528',
		'Zyxel_1212/1248', 'Zyxel_1008', 
		'Alcatel_7330/7302',
		'ZTE_C300',
		'Eltex_MES1124', 'Eltex_MES2308', 'Eltex_MES2124', 'Eltex_MES3124', 'Eltex_MES2324', 'Eltex_MES3324', 'Eltex_MES2408', 'Eltex_MES2428', 'Eltex_MA-4000', 'Eltex_LTP-8X', 'Eltex_LTP-4X',
		'Dlink_DES-3200-10', 'Dlink_DES-3200-18', 'Dlink_DES-3200-28', 'Dlink_DES-3200-52', 
		'EdgeCore_ES3528',
		'Raisecom_ISCOM2608','Raisecom_ISCOM2624',
		'SNR-S2960','S2985G-24T', 'S2985G-8T',
		'Huawei_5800'
	]

	values = {'models': {}.fromkeys(models, '')}
	return render(request, 'activator/generator.html', values)


def get_template(request):
	# check_aut_generator(request)
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]


	
	main_path_template = 'scripts/jn_templates'
	data = ['model', 'ip', 'mask', 'gateway', 'hostname', 'uplink_hostname', 'uplink_port', 'MGM', 'HSI', 'IPTV', 'IMS', 'TR069']
	
	values = {}.fromkeys(data, '')


	if request.method == 'GET':
		for column in data:
			values[column] = request.GET[f"{column}"]
			match = re.search(r'^\s*(.*?)\s*$', request.GET[f'{column}']) # обрезаем пробелы в начале и конце строки
			if (match):
				values[column] = match.group(1)

	if values['ip']:
		t = multimodule.FastModulAut()
		t.sql_connect('connect')
		t.count_website(t, page='generator', username=request.user.username)
		user = request.user.username
		values['user'] = user
		values['error'] = ''


		ip = values['ip']
		model = values['model']
		port_uplink = 'None'
		port_downlink = 'None'
		data_settings = {}
		iptacacs = 'none'
		model_templite = 'None'
		ims_server = 'None'
		ims_domain = 'None'

		ftp_server = '10.224.62.2'

		if re.search(r'^10\.228\.', ip):
			if re.search(r'^45-', values['hostname']):
				ftp_server = '10.228.65.253'
			else:
				ftp_server = '10.228.63.237'
			
		if re.search(r'^10\.225\.', ip):
			ftp_server = '10.225.80.253'



		if not values['mask']:
			values['mask'] = 0
				
		netaddress = ipaddress.IPv4Network(f"{ip}/{values['mask']}", strict=False)
		netmask = str(netaddress.netmask)

		if re.search(r'^10.228.', ip):
			logging_host = '10.228.60.12'

		if re.search(r'MES2124|MES1124|MES3124|MES3324|MES2324|MES2208|MES2308|MES3508', model):
			model_templite = '21xx'
			if re.search(r'2124', model):
				port_downlink = 'Gi0/1-24'
				port_uplink = 'Gi0/28'

			elif re.search(r'1124', model):
				port_downlink = 'Fa0/1-24'
				port_uplink = 'Gi0/4'

			elif re.search(r'3124|3324|2324', model):
				model_templite = '31xx'
				port_downlink = 'Gi0/1-23'
				port_uplink = 'Te0/4'
				if re.search(r'3324|2324', model):
					model_templite = 'x3xx'

			elif re.search(r'2208|2308|3508', model):
				port_downlink = 'Gi0/1-8'
				port_uplink = 'Gi0/12'
				if re.search(r'2308|3508', model):
					model_templite = 'x3xx'

			path_file = f"{main_path_template}/template_commands_eltex_mes_all.jn2"
			path_file_mng = f"{main_path_template}/template_commands_eltex_mes_all_mng.jn2"

		elif re.search(r'MES2428|MES2408', model):
			model_templite = '24xx'
			if re.search(r'MES2428', model):
				port_downlink = 'Gi 0/1-24'
				port_uplink = 'Gi 0/28'

			elif re.search(r'MES2408', model):
				port_downlink = 'Gi 0/1-8'
				port_uplink = 'Gi 0/10'

			values['mask'] = netmask

			path_file = f"{main_path_template}/template_commands_eltex_mes_24xx.jn2"
			path_file_mng = f"{main_path_template}/template_commands_eltex_mes_24xx_mng.jn2"

		elif re.search(r'DES-3200', model):
			model_templite = 'dlink'
			if re.search(r'3200-10', model):
				port_downlink = '1-9'
				port_uplink = '10'
			elif re.search(r'3200-18', model):
				port_downlink = '1-16'
				port_uplink = '18'
			elif re.search(r'3200-28', model):
				port_downlink = '1-26'
				port_uplink = '28'
			elif re.search(r'3200-52', model):
				port_downlink = '1-50'
				port_uplink = '52'

			path_file = f"{main_path_template}/template_commands_dlink_3200.jn2"
			path_file_mng = f"{main_path_template}/template_commands_dlink_3200_mng.jn2"

		elif re.search(r'ES3528', model):
			port_downlink = '1-26'
			port_uplink = '28'

			path_file = f"{main_path_template}/template_commands_edge_core_3528.jn2"
			path_file_mng = f"{main_path_template}/template_commands_edge_core_3528_mng.jn2"

		elif re.search(r'ME-3600', model):
			values['mask'] = netmask
			port_downlink = '0/1-24'
			port_uplink = 'Te0/2'
			path_file = f"{main_path_template}/template_commands_cisco_ME3600.jn2"
			path_file_mng = f"{main_path_template}/template_commands_cisco_ME3600_mng.jn2"

		elif re.search(r'ME-3400', model):
			values['mask'] = netmask
			port_downlink = '1/0/1-15'
			port_uplink = 'gi1/0/16'			
			path_file = f"{main_path_template}/template_commands_cisco_ME3400.jn2"
			path_file_mng = f"{main_path_template}/template_commands_cisco_ME3400_mng.jn2"


		elif re.search(r'MES-3528', model):
			port_downlink = '1-26'
			port_uplink = '28'

			path_file = f"{main_path_template}/template_commands_zyxel_3528.jn2"
			path_file_mng = f"{main_path_template}/template_commands_zyxel_3528_mng.jn2"

		elif re.search(r'ISCOM2608|ISCOM2624', model):
			port_downlink = '1/1/1-24'
			port_uplink = '1/1/10'

			if re.search(r'ISCOM2608', model):
				port_downlink = '1/1/1-9'
				port_uplink = '1/1/10'

			path_file = f"{main_path_template}/template_commands_iscom_26xx.jn2"
			path_file_mng = f"{main_path_template}/template_commands_iscom_26xx_mng.jn2"

		elif re.search(r'SNR-S2960', model):
			port_downlink = '1/1-26'
			port_uplink = '1/28'
			# if re.search(r'SNR-S2960-24', model):
			# 	port_downlink = '1/1-24'
			# 	port_uplink = '1/28'
			if re.search(r'SNR-S2960-8T', model):
				port_downlink = '1/1-8'
				port_uplink = '1/10'

			values['mask'] = netmask

			path_file = f"{main_path_template}/template_commands_snr_s2960.jn2"
			path_file_mng = f"{main_path_template}/template_commands_snr_s2960_mng.jn2"

		elif re.search(r'S2985G-24T|S2985G-8T', model):
			port_downlink = '1/1-26'
			port_uplink = '1/28'
			if re.search(r'S2985G-8T', model):
				port_downlink = '1/1-8'
				port_uplink = '1/10'

			values['mask'] = netmask

			path_file = f"{main_path_template}/template_commands_snr_s298x.jn2"
			path_file_mng = f"{main_path_template}/template_commands_snr_s298x_mng.jn2"


		elif re.search(r'C300', model):
			# port_downlink = '1/1-24'
			# port_uplink = '1/28'
			# if re.search(r'SNR-S2960-24', model):
			# 	port_downlink = '1/1-24'
			# 	port_uplink = '1/28'

			values['mask'] = netmask
			path_file = f"{main_path_template}/template_commands_zte_C300.jn2"
			path_file_mng = f"{main_path_template}/template_commands_zte_C300_mng.jn2"

		elif re.search(r'1212|1248|1008', model):
			vpi_pppoe = 8
			vpi_ip_tv = 8
			vci_pppoe = 35
			vci_ip_tv = 37
			if re.search(r'^59-', values['hostname']):
				vpi_pppoe = 8
				vpi_ip_tv = 0
				vci_pppoe = 35
				vci_ip_tv = 34
			if re.search(r'^74-', values['hostname']):
				vpi_pppoe = 8
				vpi_ip_tv = 0
				vci_pppoe = 35
				vci_ip_tv = 34
			if re.search(r'^72-', values['hostname']):
				vpi_pppoe = 8
				vpi_ip_tv = 8
				vci_pppoe = 35
				vci_ip_tv = 37
			if re.search(r'^45-', values['hostname']):
				vpi_pppoe = 1
				vpi_ip_tv = 1
				vci_pppoe = 500
				vci_ip_tv = 501

			data_settings['vpi_pppoe'] = vpi_pppoe
			data_settings['vpi_ip_tv'] = vpi_ip_tv
			data_settings['vci_pppoe'] = vci_pppoe
			data_settings['vci_ip_tv'] = vci_ip_tv
			values['netmask'] = netmask

			if re.search(r'1212|1248', model):
				path_file = f"{main_path_template}/template_commands_zyxel_1212_1248.jn2"
				path_file_mng = f"{main_path_template}/template_commands_zyxel_1212_1248_mng.jn2"
			elif re.search(r'1008', model):
				path_file = f"{main_path_template}/template_commands_zyxel_1008.jn2"
				path_file_mng = f"{main_path_template}/template_commands_zyxel_1008_mng.jn2"

		elif re.search(r'7330|7302', model):
			vpi_pppoe = 8
			vpi_ip_tv = 8
			vci_pppoe = 35
			vci_ip_tv = 37
			if re.search(r'^59-', values['hostname']):
				vpi_pppoe = 8
				vpi_ip_tv = 0
				vci_pppoe = 35
				vci_ip_tv = 34
			if re.search(r'^74-', values['hostname']):
				vpi_pppoe = 8
				vpi_ip_tv = 0
				vci_pppoe = 35
				vci_ip_tv = 34
			if re.search(r'^72-', values['hostname']):
				vpi_pppoe = 8
				vpi_ip_tv = 8
				vci_pppoe = 35
				vci_ip_tv = 37
			if re.search(r'^45-', values['hostname']):
				vpi_pppoe = 1
				vpi_ip_tv = 1
				vci_pppoe = 500
				vci_ip_tv = 501

			port_uplink = 1
			data_settings['vpi_pppoe'] = vpi_pppoe
			data_settings['vpi_ip_tv'] = vpi_ip_tv
			data_settings['vci_pppoe'] = vci_pppoe
			data_settings['vci_ip_tv'] = vci_ip_tv

			path_file = f"{main_path_template}/template_commands_alcatel_7302.jn2"
			path_file_mng = f"{main_path_template}/template_commands_alcatel_7302_mng.jn2"

		elif re.search(r'5800', model):
			model_templite = '5800'
			path_file = f"{main_path_template}/template_commands_huawei_5800.jn2"
			path_file_mng = f"{main_path_template}/template_commands_huawei_5800_mng.jn2"
			if re.search(r'^59-', values['hostname']):
				ims_server = '172.16.2.200'
				ims_domain = '342.rt.ru'
			if re.search(r'^86-', values['hostname']):
				ims_server = '172.16.6.200'
				ims_domain = '346.rt.ru'
			if re.search(r'^89-', values['hostname']):
				ims_server = '172.16.7.200'
				ims_domain = '349.rt.ru'
			if re.search(r'^74-', values['hostname']):
				ims_server = '172.16.3.200'
				ims_domain = '351.rt.ru'
			if re.search(r'^66-', values['hostname']):
				ims_server = '172.16.1.200'
				ims_domain = '343.rt.ru'				
			if re.search(r'^72-', values['hostname']):
				ims_server = '172.16.4.200'
				ims_domain = '345.rt.ru'
			if re.search(r'^45-', values['hostname']):
				ims_server = '172.16.5.200'
				ims_domain = '352.rt.ru'

		elif re.search(r'4000', model):
			model_templite = 'MA-4000'
			path_file = f"{main_path_template}/template_commands_ma4000.jn2"
			path_file_mng = f"{main_path_template}/template_commands_ma4000_mng.jn2"

		elif re.search(r'LTP-8', model):
			model_templite = 'LTP'
			path_file = f"{main_path_template}/template_commands_ltp-8x.jn2"
			path_file_mng = f"{main_path_template}/template_commands_ltp-8x_mng.jn2"
		elif re.search(r'LTP-4', model):
			model_templite = 'LTP'
			path_file = f"{main_path_template}/template_commands_ltp-4x.jn2"
			path_file_mng = f"{main_path_template}/template_commands_ltp-4x_mng.jn2"		
		else:
			values['error'] = 'Not find fail for model'
			return JsonResponse(values, safe=False)

		query = f"""SELECT m.DEVICEMODELNAME
								FROM guspk.host h, guspk.host_model m
								WHERE h.MODELID = m.MODELID
								AND h.NETWORKNAME = '{values['uplink_hostname']}';
							"""
		request_sql = t.sql_select(query, 'full')
		t.sql_connect('disconnect')

		if request_sql:
			up_model = request_sql[0][0]
			data_port = {
								'pppoe': {'vlan': values['HSI'], 'name':'PPPoE'},
								'iptv': {'vlan': values['IPTV'], 'name':'IP-TV'},
								'ims': {'vlan': values['IMS'], 'name':'IMS'},
								'tr069': {'vlan': values['TR069'], 'name':'TR069'},
								'model': up_model,
								'mgmvlan': values['MGM'],
								'downlink': values['uplink_port'],
								'hostname_port': f"{values['hostname']}_{port_uplink}",
			}
			with open (f"{main_path_template}/template_commands_port_all_model.jn2") as f:
				device_template_port = f.read()
				template = jinja2.Template(device_template_port)
				commands_device_port = template.render(data_port).splitlines()
				values['setting_uplink'] = commands_device_port

		data_settings['ipaddmgm'] = ip
		data_settings['hostname'] = values['hostname']
		data_settings['default_gateway'] = values['gateway']
		data_settings['port_uplink'] = port_uplink
		data_settings['port_downlink'] = port_downlink
		data_settings['model'] = model
		data_settings['uplink'] = values['uplink_hostname']
		data_settings['uplink_and_port'] = f"{values['uplink_hostname']}_{values['uplink_port']}"

		data_settings['mgmvlan'] = values['MGM']
		data_settings['pppoe'] = {'vlan': values['HSI'], 'name':'PPPoE'}
		data_settings['iptv'] = {'vlan': values['IPTV'], 'name':'IP-TV'}
		data_settings['ims'] = {'vlan': values['IMS'], 'name':'IMS', 'server': ims_server, 'domain': ims_domain}
		data_settings['tr069'] = {'vlan': values['TR069'], 'name':'TR069'}


		data_mgm = {
			'ipaddmgm': ip,
			'mask': values['mask'],
			'gw': values['gateway'],
			'mgmvlan': values['MGM'],
			'port_uplink': port_uplink,
			'hostname': values['hostname'],
			'uplink': values['uplink_hostname']
		}

		with open (path_file) as f:
			device_template = f.read()
			template = jinja2.Template(device_template)
			commands_device = template.render(data_settings).splitlines()
			values['setting_all'] = commands_device

		with open (path_file_mng) as f:
			device_template_mng = f.read()
			template_mng = jinja2.Template(device_template_mng)
			commands_device_mng = template_mng.render(data_mgm).splitlines()
			values['setting_mng'] = commands_device_mng

		data_download_software = {
			'model': model_templite,
			'ftp_server': ftp_server,
		}
		with open (f"{main_path_template}/download_software.jn2") as f:
			device_download_software = f.read()
			template_download_software = jinja2.Template(device_download_software)
			download_software = template_download_software.render(data_download_software).splitlines()
			values['download_software'] = download_software

	return JsonResponse(values, safe=False)


def get_data_device(request):
	# check_aut_generator(request)
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]

	ip = request.GET['ip']
	print(f"ip: {ip}")

	if ip:
		t = multimodule.FastModulAut()
		t.sql_connect('connect')


		query = f"""SELECT h.NETWORKNAME, hm.DEVICEMODELNAME, (SELECT NETWORKNAME FROM guspk.host WHERE DEVICEID = top.parent) AS 'UPLINK', top.parent_port, hn.GW, hn.MASK, hn.VLAN, hv.HSI, hv.IPTV, hv.IMS, hv.TR069, hn.NETWORK
					FROM guspk.host h
					LEFT JOIN guspk.host_model hm ON h.MODELID = hm.MODELID
					LEFT JOIN guspk.topology top ON top.child = h.DEVICEID
					LEFT JOIN guspk.host_acsw_node an ON an.DEVICEID = h.DEVICEID
					LEFT JOIN guspk.host_networks hn ON hn.NETWORK_ID = an.NETWORK_ID
					LEFT JOIN guspk.host_vlan_template hv ON hv.VLAN_TEMPLATE_ID = an.VLAN_TEMPLATE_ID
					WHERE h.IPADDMGM = '{ip}';
				"""

		values = {
			'hostname': '',
			'model': '',
			'uplink': '',
			'port_uplink': '',
			'gw': '',
			'mask': '',
			'mng': '',
			'hsi': '',
			'iptv': '',
			'ims': '',
			'tr069': '',
		}
		request_sql = t.sql_select(query, 'full')


		# print(request_sql)
		for i, request in enumerate(request_sql):
			print(f"{i:5}{request}")
			print(f'start for: {values}')
			values.update({
				'hostname': request_sql[i][0],
				'model': request_sql[i][1],
				'uplink': request_sql[i][2],
				'port_uplink': request_sql[i][3],
				'model_select': 'Cisco_ME-3600',
			})
			if request_sql[i][5] and request_sql[i][11] and ipaddress.ip_address(ip) in ipaddress.ip_network(f"{request_sql[i][11]}/{request_sql[i][5]}"):
				print(f'do: {values}')
				values.update({
					'gw': request_sql[i][4],
					'mask': request_sql[i][5],
					'mng': request_sql[i][6],
					'hsi': request_sql[i][7],
					'iptv': request_sql[i][8],
					'ims': request_sql[i][9],
					'tr069': request_sql[i][10],
				})
				print(f'post: {values}')
			print(f'end for: {values}')

		if re.search(r'ME-3600', values['model']):
			values['model_select'] = 'Cisco_ME-3600'

		elif re.search(r'ME-3400', values['model']):
			values['model_select'] = 'Cisco_ME-3400'

		elif re.search(r'1212|1248', values['model']):
			values['model_select'] = 'Zyxel_1212/1248'

		elif re.search(r'1008', values['model']):
			values['model_select'] = 'Zyxel_1008'

		elif re.search(r'7330|7302', values['model']):
			values['model_select'] = 'Alcatel_7330/7302'

		elif re.search(r'MES1124', values['model']):
			values['model_select'] = 'Eltex_MES1124'

		elif re.search(r'MES2308', values['model']):
			values['model_select'] = 'Eltex_MES2308'

		elif re.search(r'MES2124', values['model']):
			values['model_select'] = 'Eltex_MES2124'

		elif re.search(r'MES3124', values['model']):
			values['model_select'] = 'Eltex_MES3124'

		elif re.search(r'MES2324', values['model']):
			values['model_select'] = 'Eltex_MES2324'

		elif re.search(r'MES3324', values['model']):
			values['model_select'] = 'Eltex_MES3324'

		elif re.search(r'MES2408', values['model']):
			values['model_select'] = 'Eltex_MES2408'

		elif re.search(r'MES2428', values['model']):
			values['model_select'] = 'Eltex_MES2428'

		elif re.search(r'MA-4000', values['model']):
			values['model_select'] = 'Eltex_MA-4000'

		elif re.search(r'LTP-\d', values['model']):
			values['model_select'] = f"Eltex_{values['model']}"

		elif re.search(r'DES-3200-10', values['model']):
			values['model_select'] = 'Dlink_DES-3200-10'

		elif re.search(r'DES-3200-18', values['model']):
			values['model_select'] = 'Dlink_DES-3200-18'

		elif re.search(r'DES-3200-28', values['model']):
			values['model_select'] = 'Dlink_DES-3200-28'

		elif re.search(r'DES-3200-52', values['model']):
			values['model_select'] = 'Dlink_DES-3200-52'

		elif re.search(r'ES3528', values['model']):
			values['model_select'] = 'EdgeCore_ES3528'

		elif re.search(r'MES-3528', values['model']):
			values['model_select'] = 'Zyxel_MES-3528'

		elif re.search(r'ISCOM2608', values['model']):
			values['model_select'] = 'Raisecom_ISCOM2608'

		elif re.search(r'ISCOM2624', values['model']):
			values['model_select'] = 'Raisecom_ISCOM2624'

		elif re.search(r'SNR-S2960', values['model']):
			values['model_select'] = 'SNR_S2960'

		elif re.search(r'C300', values['model']):
			values['model_select'] = 'ZTE_C300'

		elif re.search(r'5800', values['model']):
			values['model_select'] = 'Huawei_5800'

		t.sql_connect('disconnect')

	return JsonResponse(values, safe=False)
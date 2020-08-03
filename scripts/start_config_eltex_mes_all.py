#!/usr/bin/python3
# -*- coding: utf-8 -*-
import datetime
import multimodule as telnet
import sys, os, re, time
import jinja2
import getpass
import argparse
from multiprocessing import Pool
import subprocess
import ipaddress
import start_topology

try:
	from acds import configuration
except:
	import configuration
# from websocket import create_connection


def createParser ():
	parametr = {
		0:{'vlan_f':'--ip',		'vlan_l':'-a',	'vlan_typ':str,	'vlan_sub':'ip',},
		1:{'vlan_f':'--pppoe',	'vlan_l':'-p',	'vlan_typ':int,	'vlan_sub':'vlan_pppoe',},
		2:{'vlan_f':'--tv',		'vlan_l':'-t',	'vlan_typ':int,	'vlan_sub':'vlan_ip_tv',},
		3:{'vlan_f':'--ims',	'vlan_l':'-i',	'vlan_typ':int,	'vlan_sub':'vlan_ims',},
		4:{'vlan_f':'--tr069',	'vlan_l':'-r',	'vlan_typ':int,	'vlan_sub':'vlan_tr069',},
		5:{'vlan_f':'--name',	'vlan_l':'-n',	'vlan_typ':str,	'vlan_sub':'name',},
		6:{'vlan_f':'--uplink',	'vlan_l':'-u',	'vlan_typ':str,	'vlan_sub':'uplink',},
		7:{'vlan_f':'--model',	'vlan_l':'-m',	'vlan_typ':str,	'vlan_sub':'model',},
		8:{'vlan_f':'--onlyup',	'vlan_l':'-l',	'vlan_typ':str,	'vlan_sub':'onlyup',},
	}

	parser = argparse.ArgumentParser(
		prog = 'Setting MES Eltex',
		description = '''Данный скрипт позволяет настроить базовый конфиг MES Eltex.''',
		epilog = '''(c) January 2019. Автор программы, как всегда,
			не несет никакой ответственности ни за что.'''
		)
	# subparsers = parser.add_subparsers (dest='command')

	for n in range(len(parametr)):
		# subparsers.add_parser (parametr[n]['vlan_sub'])
		parser.add_argument (parametr[n]['vlan_l'], parametr[n]['vlan_f'], type=parametr[n]['vlan_typ'], nargs='?')

	return parser


def upgrade(t, model, ip, hostname):

<<<<<<< HEAD
	image_33 = 'mes3300-4013-3R1.ros'
=======
	image_33 = 'mes3300-4014-R5.ros'
>>>>>>> d3f3321f8327dedfea4735d1938bae833af7f7b9
	version_33 = '4.0.14'

	image_21 = 'mes2000-11486.ros'
	version_21 = '1.1.48.6'

	image_31 = 'mes3000-25486.ros'
	version_31 = '2.5.48.6'

	t.new_sendline('configure')
	t.new_sendline('port jumbo-frame')
	t.new_sendline('exit')

	# ftp_dic = {
	# 	'tmn_core': '10.224.62.2',
	# 	'tmn_fttx': '10.228.63.237',
	# 	'kgn_core': '10.225.80.253',
	# 	'kgn_fttx': '10.228.65.253',
	# }

	ip_ftp = '10.224.62.2'

	if re.search(r'^10\.228\.', ip):
		if re.search(r'^45-', hostname):
			ip_ftp = '10.228.65.253'
		else:
			ip_ftp = '10.228.63.237'
		
	if re.search(r'^10\.225\.', ip):
		ip_ftp = '10.225.80.253'



	counter = 0
	download_required = 'yes'
	while download_required != 'no':
		t.new_sendline('show version') # Смотрим активную версию
		data = t.data_split()
		match_active = re.search(r'Active-image.*\n\s+Version: ([\d\.]+)|SW version\s+([\d\.]+)', data, re.M)

		# х300 серия
		if match_active and match_active[1]:	
			activ_version = match_active[1]
			t.ws_send_message(f"current sw version: {activ_version}")

			# Сравниваем активную версию с эталонной
			if activ_version != version_33:
				download_command = (f"boot system tftp://{ip_ftp}/FTP/FTTb/{image_33}") # boot system tftp://10.224.62.2/FTP/FTTb/mes3300-4014-R5.ros
			else:
				t.ws_send_message("software is up to date")
				return 'end_version'


			# Сравниваем не активную версию с эталонной
			match_inactive = re.search(r'Inactive-image.*\n\s+Version: ([\d\.]+)', data, re.M)	# Смотрим не активную версию для x300-й серии
			# Если в неактивном оброзе нет актуального ПО, то потребуется загрузка
			if match_inactive and match_inactive[1] == version_33:
				# В неактивном образе уже загружено актуальное ПО
				download_required = 'no'
				t.ws_send_message("new sw already loaded")

				active_after = re.search(r'Active after reboot', data, re.M)
				# Активируем не активное ПО и перезагружаемся, если ПО уже было активировано, то только перезагрузка
				if not active_after:
					t.ws_send_message("activating new sw")
					t.new_sendline('boot system inactive-image')


		# х100 серия
		elif match_active and match_active[2]:	
			activ_version = match_active[2]
			t.ws_send_message(f"current sw version: {activ_version}")

			# Сравниваем активную версию с эталонной
			if re.search(r'MES31\d\d', model) and activ_version != version_31:
				download_command = (f"copy tftp://{ip_ftp}/FTP/FTTb/{image_31} flash://image")
			elif re.search(r'MES21\d\d', model) and activ_version != version_21:
				download_command = (f"copy tftp://{ip_ftp}/FTP/FTTb/{image_21} flash://image")
			else:
				t.ws_send_message("software is up to date")
				return 'end_version'


			# Сравниваем не активную версию с эталонной
			t.new_sendline('show bootvar') # Смотрим активную версию
			data = t.data_split()
			match_inactive = re.search(r'image-([12])\s+([\d\.]+).+Not active(\*?)', data, re.M)
			# Если в неактивном оброзе нет актуального ПО, то потребуется загрузка
			if match_inactive and (match_inactive[2] == version_21 or match_inactive[2] == version_31):
				# В неактивном образе уже загружено актуальное ПО
				download_required = 'no'
				t.ws_send_message("new sw already loaded")

				# Активируем не активное ПО и перезагружаемся, если ПО уже было активировано, то только перезагрузка
				if not match_inactive[3]:
					t.ws_send_message("activating new sw")
					t.new_sendline(f"boot system image-{match_inactive[1]}")


		# исключение на случай если не удалось определить версию
		else:
			error = "Error id_210 = SW Version not found"
			t.ws_send_message(error)
			t.ws_send_message("""Данное регуулярное выражение не сработало: Active-image.*\\n\\s+Version: ([\\d\\.]+)|SW version\\s+([\\d\\.]+)""")
			t.ws_send_message(f'''Вывод команды "show version": {data}''')
			return error

		# Если ни в одном из образов не было обнаружено актуальное ПО, то сработает это условие
		if download_required == 'yes':
			t.ws_send_message(f'''waiting for the command to load new sw "timeout=30 min": {download_command}''')
			t.new_sendline(download_command, timeout=1800)
			t.ws_send_message("sw loaded")

		counter += 1
		if counter == 3:
			error = "Error id_211 = sw loading error"
			return error


	t.ws_send_message("saving configuration")
	t.new_sendline('write memory', prompt='\[startup-config\]')
	t.new_sendline('y', timeout_expect=1)
	t.ws_send_message("reload")
	t.new_sendline('reload', prompt='[yY]')
	t.new_sendline('y')
	t.new_sendline('y')
	print(f"""\n{datetime.datetime.today().strftime("%H:%M:%S")}\t""", sep='', end='')
	print(f"Ждём перезагрузки коммутатора")
	time.sleep(10)
	for n in range(500):
		time.sleep(5)
		try:
			ping = subprocess.check_output(["ping", ip, "-c 1"], universal_newlines=True)
			# print(f"{n} ping: {ping}")
			if re.search(r"icmp_seq=1", ping, re.M):
				break
		except subprocess.CalledProcessError as err:
			pass
			# print(f'{datetime.datetime.today().strftime("%H:%M:%S")} not responding to ping')
	print(f"""\n{datetime.datetime.today().strftime("%H:%M:%S")}\tКоммутатор перезагружен""")
	t.ws_send_message("switch reloaded")
	return 'upgrade'




def authorization_in_eltex(t, data_mes, vlans_mng_list):					# id	hostname	model	ticket	office	datemodify	status	uplink	mac

	print(f"authorization_in_eltex|{data_mes}")
	error = 'ok'

	ip = data_mes['ipaddmgm']
	model = data_mes['model']
	uplink = data_mes['uplink_and_port']

	if data_mes['login'] != 'default':
		def_login = data_mes['login']
	else:
		def_login = 'tacacs'

	if data_mes['password'] != 'default':
		def_password = data_mes['password']
	else:
		def_password = 'tacacs'

	logins = {
		0 :{
			'login':'admin',
			'password':'admin'},
		1 :{
			'login':'admin',
			'password':'Cdbnx0AA'},
		2 :{
			'login':def_login,
			'password':def_password},
	}

	check_version = 'none'
	check_for = 0
	# print(data_mes)

	# print(data_mes)
	# return

	if uplink == None or not uplink:
		t.ws_send_message(f"this device haven't data for uplink, topology started")
		topology_result = start_topology.loop(ip)
		t.sql_connect('connect')
		add = t.sql_select(f"""SELECT CONCAT((SELECT NETWORKNAME FROM guspk.host WHERE DEVICEID = top.parent), '_', top.parent_port) 
								FROM guspk.host h 
								LEFT JOIN guspk.topology top ON top.child = h.DEVICEID WHERE h.IPADDMGM = '{ip}'""", 'full')
		t.sql_connect('disconnect')
		if topology_result['status'] == 'end_device':
			uplink = add[0][0]
			t.ws_send_message(f"uplink: {uplink}")
		else:
			t.ws_send_message(f"topology error {topology_result['message_error']}")

	if not uplink:
		print(f'authorization_in_eltex|Нет данных по uplink')
		t.ws_send_message("Error in topology, no data for uplink")
		error = f"Error id_201 = Error in topology, {topology_result['message_error']}"
		return error

	while check_version != 'end_version':
		if check_for == 3:
			print(f'authorization_in_eltex|Неудалось загрузить или обновить коммутатор на новое ПО')
			error = "Error id_202 = Failed to load or update the switch to the new software"
			t.ws_send_message(error)
			return error
		check_for += 1
		t.ws_send_message("log in to the device")
		for n in range (len(logins)):
			i = t.aut(ip = ip, model = model, login=logins[n]['login'], password=logins[n]['password'], logs_dir = f"{getattr(configuration, 'LOGS_DIR')}/config_eltex")
			if i == 0:
				break

		if i != 0:
			error = "Error id_203 = Cant log in"
			t.ws_send_message(error)
			return error
		t.ws_send_message("success")

		t.new_sendline('terminal width 0')
		# t.new_sendline('show system') # Определяем модель коммутатора
		# data = t.data_split()
		# match = re.search(r'System Description:\s+\w+(\d+)', data, re.M)
		# if (match):
		# 	model = match.group(1)
		# 	print(model)
		t.ws_send_message("sw check started")
		check_version = upgrade(t, model, ip, data_mes['hostname'])

	if data_mes['onlyup'] == 'up':
		t.disconnect()
		t.ws_send_message("update completed")
		error = "ok"
		return error

	# t.new_sendline('sho ip route | i 0.0.0.0/0') # определяем geteway
	# data = t.data_split()
	# match = re.search(r'via\s+([\d\.]+)', data, re.M)
	# if (match):
	# 	data_mes['default_gateway'] = match.group(1)
	# 	t.ws_send_message (f"data_mes['default_gateway']: {data_mes['default_gateway']}")

	t.new_sendline(f"ping {data_mes['default_gateway']}") # определяем порт аплинка
	t.new_sendline(f"show arp | include {data_mes['default_gateway']}") # определяем порт аплинка
	data = t.data_split()
	match = re.search(r'vlan\s+\d+\s+([\w\/]+)', data, re.M)
	port_uplink = 'none'
	if (match):
		port_uplink = match[1]
		t.ws_send_message(f"port_uplink: {port_uplink}")

	# t.new_sendline(f"show running-config interface vlan{vlan_mng} | i ip") # определяем маску geteway
	# data = t.data_split()
	# match = re.search(r'ip address\s+[\d\.]+\s+([\d\.]+)', data, re.M)
	# if (match):
	# 	mask = match.group(1)
	# 	print(f"mask: {mask}")

	if port_uplink == 'none':
		t.disconnect()
		error = "Error id_201 = No data for uplink"
		t.ws_send_message(error)
		return error

	# t.new_sendline (f"model: {model}")
	check_port_uplink = 'bad'
	if re.search(r'2124', model):
		port_downlink = 'Gi0/1-24'
		if re.search(r'gi1\/0\/2[5-8]', port_uplink, re.I):
			check_port_uplink = 'good'
	elif re.search(r'1124', model):
		port_downlink = 'Fa0/1-24'
		if re.search(r'gi1\/0\/[1-4]', port_uplink, re.I):
			check_port_uplink = 'good'
	elif re.search(r'3124|3324|3348|2324', model):
		if re.search(r'gi1\/0\/24', port_uplink, re.I):
			port_downlink = 'Gi0/1-23'
			check_port_uplink = 'good'
		elif re.search(r'te1\/0\/[1-4]', port_uplink, re.I):
			if re.search(r'3324|3124|2324', model):
				port_downlink = 'Gi0/1-24'
			elif re.search(r'3348', model):
				port_downlink = 'Gi0/1-48'
			else:
				error = "Error id_2010 = error in inspected model 3324|3348"
				t.ws_send_message(error)
				return error

			check_port_uplink = 'good'
		elif re.search(r'gi1\/0\/1$', port_uplink, re.I):
			port_downlink = 'Gi0/2-24'
			check_port_uplink = 'good'
	elif re.search(r'2208|2308|3508', model):
		port_downlink = 'Gi0/1-8'
		if re.search(r'gi1\/0\/(9|1[0-2])', port_uplink, re.I):
			check_port_uplink = 'good'

	if check_port_uplink == 'bad':
		print(f"authorization_in_eltex|Необходимо сменить порт аплинка. Рекомендуется использовать последний порт в коммутаторе.\n{port_uplink} - данный порт не рекомендуется еспользовать, потому что он пересекается с портами которые используются под услуги абонетов или подключения других устройств")
		t.disconnect()
		error = "Error id_204 = Need to change the port of uplink"
		t.ws_send_message(error)
		return error

	if uplink == None:
		print(f"authorization_in_eltex|Для данного {ip} не указан uplink в bd")
		t.disconnect()
		error = "Error id_205 = Not specified uplink"
		t.ws_send_message(error)
		return error

	# data_mes['mask'] = mask	не нашёл для чего раньше использовал, в конфиге этой переменной нету
	data_mes['port_uplink'] = port_uplink
	data_mes['port_downlink'] = port_downlink
	data_mes['uplink_and_port'] = uplink

	print(f"authorization_in_eltex|{data_mes}")

	with open (getattr(configuration, 'JN_PATH')+'template_commands_eltex_mes_all.jn2') as f:
		mes_switches_template = f.read()
		template = jinja2.Template(mes_switches_template)
		commands_mes_switches = template.render(data_mes).splitlines()

	nn = 0
	t.ws_send_message("started device configure")
	for command in commands_mes_switches:
		t.ws_send_message(command)
		t.new_sendline(command, timeout=2, timeout_expect=.200)
		data = t.data_split('list')
		check_command = 'bed'
		check_command_nn = 0
		while check_command == 'bed' and check_command_nn != 4:
			check_command_nn += 1
			if data[0] in command:
				print(f"{nn:4} - {command:90} ║ {data[0]}")
				check_command = 'good'

		for d in data:
			if re.search(r'Unrecognized command|Incomplete command', d):
				print(f"\t\t\tКоманда: {command} не проходит")
		nn += 1

	for vlan in vlans_mng_list:
		t.new_sendline('vlan database', timeout=1)
		t.new_sendline(f"vlan {vlan}", timeout=1)
		t.new_sendline('exit', timeout=1)
		t.new_sendline(f"interface {data_mes['port_uplink']}", timeout=1)
		t.new_sendline(f"switchport trunk allowed vlan add {vlan}", timeout=1)
		t.new_sendline('exit', timeout=1)

		
	# t.new_sendline('banner login ^', timeout=1)
	# t.new_sendline('UNAUTHORIZED ACCESS TO THIS DEVICE IS PROHIBITED', timeout=1)
	# t.new_sendline('You must have explicit, authorized permission to access or configure this device.', timeout=1)
	# t.new_sendline('Unauthorized attempts and actions to access or use this system may result in civil and/or', timeout=1)
	# t.new_sendline('criminal penalties.', timeout=1)
	# t.new_sendline('All activities performed on this device are logged and monitored.', timeout=1)
	# t.new_sendline('^', timeout=1)
	t.new_sendline('exit', timeout=1)
	t.ws_send_message("completed device configure, saving config")
	t.new_sendline('write memory', prompt='\[startup-config\]')
	t.new_sendline('y')

	t.disconnect()
	return error

"""
Для new_sendline опционально можно применить prompt и timeout, по умолчанию эти значения равны # и 10 секунд соответственно
t.new_sendline('sys info', prompt='>', timeout=100)

Для sql_connect опционально можно применить server, login и password, по умолчанию они берутся из личного конфигурационного файла
Обязательный параметр это "connect" и "disconnect"
t.sql_connect('connect', server='10.10.10.10', login='username', password='userpassword')


t.aut(ip = k, model = reply[k]['model'], login='admin', password='admin')
"""

def start_config(data_key, login='default', password='default', login_log='default'):
	t = telnet.FastModulAut() # prompt = '#' - настройка по умолчанию
	t.ws_connect('chat/log_configure/')
	t.ws_send_message(f"=== START {data_key['ip']} ===")

	data_mes = {}
	vlans_mng_list = []
	gw = None

	if 'onlyup' in data_key:
		onlyup = data_key['onlyup']
	else:
		onlyup = None

	if 'ip' in data_key and data_key['ip']:
		t.sql_connect('connect')

		reply = t.sql_select(f"""SELECT h.NETWORKNAME, hm.DEVICEMODELNAME, CONCAT((SELECT NETWORKNAME FROM guspk.host WHERE DEVICEID = top.parent), '_', top.parent_port), 
				hv.HSI, hv.IPTV, hv.IMS, hv.TR069, hn.GW, hn.NETWORK, hn.MASK, hn.VLAN, h.DEVICEID
				FROM guspk.host h
				LEFT JOIN guspk.host_status hs ON h.DEVICESTATUSID = hs.status_id
				LEFT JOIN guspk.host_model hm ON h.MODELID = hm.MODELID
				LEFT JOIN guspk.topology top ON top.child = h.DEVICEID
				LEFT JOIN guspk.host_acsw_node an ON an.DEVICEID = h.DEVICEID
				LEFT JOIN guspk.host_networks hn ON hn.NETWORK_ID = an.NETWORK_ID
				LEFT JOIN guspk.host_vlan_template hv ON hv.VLAN_TEMPLATE_ID = an.VLAN_TEMPLATE_ID
				WHERE h.IPADDMGM = '{data_key['ip']}'
			""", 'full')

		t.sql_connect('disconnect')

		template_check = False
		for i, request in enumerate(reply):
			# t.ws_send_message(f"=== authorization_in_eltex i -{i} r - {request} ===")
			if ipaddress.ip_address(data_key['ip']) in ipaddress.ip_network(f"{request[8]}/{request[9]}"):
				# t.ws_send_message(f"=== {request[8]} ===")
				template_check = True
				data_mes = {
					'ipaddmgm': data_key['ip'],
					'hostname': request[0],
					'model': request[1],
					'uplink_and_port': request[2],
					'login': login,
					'password': password,
					'pppoe': {
						'vlan': request[3], 
						'name':'PPPoE'},
					'iptv': {
						'vlan': request[4], 
						'name':'IP-TV'},
					'ims': {
						'vlan': request[5], 
						'name':'IMS'},
					'tr069': {
						'vlan': request[6], 
						'name':'TR069'},
					'default_gateway': request[7],
					'mgmvlan': request[10],
					'deviceid': request[11],
					'onlyup': onlyup,
				}
			else:
				vlans_mng_list.append(request[10])

	else:
		error = "Error id_200 = Not IP"
		return error

	if template_check == True:
		t.ws_send_message(f"=== authorization_in_eltex {data_mes} ===")
		error = authorization_in_eltex(t, data_mes, vlans_mng_list)
		t.ws_send_message(f"=== END {data_key['ip']} ===")
	else:
		t.ws_send_message(f"=== ERROR Networks in template not include select IP ===")
		error = "Error id_200 = Networks in template not include select IP"
		return error

	t.ws_close()
	t.sql_connect('disconnect')
	return error

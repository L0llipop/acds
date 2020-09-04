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
# from websocket import create_connection
try:
	from acds import configuration
except:
	import configuration

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
		description = '''Данный скрипт позваляет настроить базовый конфиг MES Eltex.''',
		epilog = '''(c) January 2019. Автор программы, как всегда,
			не несет никакой ответственности ни за что.'''
		)
	# subparsers = parser.add_subparsers (dest='command')

	for n in range(len(parametr)):
		# subparsers.add_parser (parametr[n]['vlan_sub'])
		parser.add_argument (parametr[n]['vlan_l'], parametr[n]['vlan_f'], type=parametr[n]['vlan_typ'], nargs='?')

	return parser


def upgrade(t, model, ip, hostname):

	image_24_boot = 'mes2400-1023-R1.boot'
	image_24 = 'mes2400-1023-R1.iss'
	version_24 = '10.2.3'

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
		t.new_sendline('show system information') # Смотрим активную версию
		data = t.data_split()
		match_active = re.search(r'Software Version\s+: ([\d\.]+)', data, re.M)

		#24xx version
		if match_active and match_active[1]:
			activ_version = match_active[1]
			t.ws_send_message(f"current sw version: {activ_version}")

			# Сравниваем активную версию с эталонной
			if activ_version != version_24:
				download_required = 'yes'
				download_command_boot = (f"copy tftp://{ip_ftp}/FTP/FTTb/mes24xx/{image_24_boot} boot")
				download_command = (f"copy tftp://{ip_ftp}/FTP/FTTb/mes24xx/{image_24} image")
			else:
				t.ws_send_message("software is up to date")
				return 'end_version'


			# Ищем новое ПО в неативном
			t.new_sendline('show bootvar')
			data = t.data_split()
			match_inactive = re.findall(r'Version\s+:\s+([\d\.]+)', data)
			t.ws_send_message(f"match_inactive - {match_inactive}")

			if version_24 in match_inactive:
				download_required = 'no'
				t.ws_send_message("new sw already loaded")
				t.ws_send_message("activating new sw")
				t.new_sendline(f"boot system inactive")
				# t.new_sendline(download_command_boot, timeout=60)

		# исключение на случай если не удалось определить версию
		else:
			error = "Error id_210 = SW Version not found"
			t.ws_send_message(error)
			t.ws_send_message("""Данное регулярное выражение не сработало: Software Version\s+: ([\d\.]+)""")
			t.ws_send_message(f'''Вывод команды "show version": {data}''')
			return error

		# Если ни в одном из образов не было обнаружено актуальное ПО, то сработает это условие
		if download_required == 'yes':
			t.ws_send_message(f'''waiting for the command to load new sw "timeout=30 min": {download_command}''')
			t.new_sendline(download_command_boot, timeout=60)
			t.ws_send_message("boot loaded")
			t.new_sendline(download_command, timeout=1800)
			t.ws_send_message("sw loaded")

		counter += 1
		if counter == 3:
			error = "Error id_211 = sw loading error"
			return error


	t.ws_send_message("saving configuration")
	t.new_sendline('copy running-config startup-config', timeout=12)
	t.ws_send_message("reload")
	t.new_sendline('reload', prompt = '(Y/N)')
	t.new_sendline('Y')
	print (f"""\n{datetime.datetime.today().strftime("%H:%M:%S")}\t""", sep='', end='')
	print (f"Ждём перезагрузки коммутатора")
	time.sleep(10)
	for n in range(500):
		time.sleep(5)
		try:
			ping = subprocess.check_output(["ping", ip, "-c 1"], universal_newlines=True)
			# print (f"{n} ping: {ping}")
			if re.search(r"icmp_seq=1", ping, re.M):
				break
		except subprocess.CalledProcessError as err:
			pass
			# print (f'{datetime.datetime.today().strftime("%H:%M:%S")} not responding to ping')
	print (f"""\n{datetime.datetime.today().strftime("%H:%M:%S")}\tКоммутатор перезагружен""")
	t.ws_send_message("switch reloaded")
	return 'upgrade'




def authorization_in_eltex(t, data_mes):					# id	hostname	model	ticket	office	datemodify	status	uplink	mac

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

	print (ip, data_mes['hostname'])
	check_version = 'none'
	check_for = 0
	# print (data_mes)

	# print (data_mes)
	# return

	if uplink == None or not uplink:
		
		t.ws_send_message(f"this device haven't data for uplink, topology started")
		topology_result = start_topology.loop(ip)
		t.sql_connect('connect')
		add = t.sql_select(f"""SELECT CONCAT((SELECT NETWORKNAME FROM guspk.host WHERE DEVICEID = top.parent), '_', top.parent_port) 
							FROM guspk.host h 
							LEFT JOIN guspk.topology top ON top.child = h.DEVICEID 
							WHERE h.IPADDMGM = '{ip}'""", 'full')
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
			print ('Не удалось загрузить или обновить коммутатор на новое ПО')
			error = "Error id_203 = Failed to load or update the switch to the new software"
			t.ws_send_message(error)
			return error
		check_for += 1
		t.ws_send_message("login to the device")
		for n in range (len(logins)):
			i = t.aut(ip = ip, model = model, login=logins[n]['login'], password=logins[n]['password'], logs_dir = f"{getattr(configuration, 'LOGS_DIR')}/config_eltex24")
			if i == 0:
				break

		if i != 0:
			error = "Error id_203 = Can't log in"
			t.ws_send_message(error)
			return error
		t.ws_send_message("success")
		t.ws_send_message("sw check started")
		check_version = upgrade(t, model, ip, data_mes['hostname'])

		# check_version = 'end_version'




	t.new_sendline(f"ping {data_mes['default_gateway']}")
	t.new_sendline(f"show ip arp") # определяем mac gw
	data = t.data_split()

	t.ws_send_message(f"default_gateway - {data_mes['default_gateway']} ")
	t.ws_send_message(f"vlan_mng - {data_mes['vlan_mng']}")
	t.ws_send_message(f"show ip arp - {data}")

	port_uplink = 'none'
	print(data)
	print(rf"{data_mes['default_gateway']}\s+([\w:]+)\s+ARPA\s+vlan{data_mes['vlan_mng']}")
	match = re.search(rf"{data_mes['default_gateway']}\s+([\w:]+)\s+ARPA\s+vlan{data_mes['vlan_mng']}", data, re.M)
	print(f"match: {match}")
	if (match):
		mac = match[1]
		print(f"mac: {mac}")
		t.ws_send_message(f"mac - {mac}")

		t.new_sendline(f"show mac address {mac}") # определяем порт аплинка
		data2 = t.data_split()
		print(f"data2: {data2}")

		t.ws_send_message(f"show mac address - {data2}")

		match2 = re.search(rf"{data_mes['vlan_mng']}\s+{mac}\s+Learnt\s+([a-zA-Z]+)([\d\/]+)", data2, re.M)
		print(f"match2: {match2}")
		if (match2):
			port_uplink = f"{match2[1]} {match2[2]}"
			t.ws_send_message(f"port_uplink - {port_uplink}")

	if port_uplink == 'none':
		t.disconnect()
		error = "Error id_206 = No port uplink"
		t.ws_send_message(error)
		return error

	t.ws_send_message(f"model: {model}")
	check_port_uplink = 'bad'
	if re.search(r'2428', model):
		port_downlink = 'Gi 0/1-24'
		if re.search(r'Gi 0\/2[5-8]', port_uplink, re.I):
			check_port_uplink = 'good'
	elif re.search(r'2408', model):
		port_downlink = 'Gi 0/1-8'
		if re.search(r'Gi 0\/(9|10)', port_uplink, re.I):
			check_port_uplink = 'good'

	if check_port_uplink == 'bad':
		print (f"Необходимо сменить порт аплинка. Рекомендуется использовать последний порт в коммутаторе.\n{port_uplink} - данный порт не рекомендуется еспользовать, потому что он пересекается с портами которые используются под услуги абонетов или подключения других устройств")
		t.disconnect()
		error = "Error id_204 = Need to change the port of uplink"
		t.ws_send_message(error)
		return error


	uplink = uplink.replace(' ', '')

	# data_mes['mask'] = mask	не нашёл для чего раньше использовал, в конфиге этой переменной нету
	data_mes['port_uplink'] = port_uplink
	data_mes['port_downlink'] = port_downlink
	data_mes['uplink_and_port'] = uplink

	with open (getattr(configuration, 'JN_PATH')+'template_commands_eltex_mes_24xx.jn2') as f:
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
				print (f"{nn:4} - {command:90} ║ {data[0]}")
				check_command = 'good'

		for d in data:
			if re.search(r'Unrecognized command|Incomplete command', d):
				print(f"\t\t\tКоманда: {command} не проходит")
		nn += 1
		
	t.ws_send_message("completed device configure, saving config")
	t.new_sendline('copy running-config startup-config')
	t.ws_send_message("save config")

	t.disconnect()
	return error

def start_config(data_key, login='default', password='default', login_log='default'):
	t = telnet.FastModulAut() # prompt = '#' - настройка по умолчанию
	t.ws_connect('chat/log_configure/')
	t.ws_send_message(f"=== START {data_key['ip']} ===")

	reply = {}
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

		for i, request in enumerate(reply):
			if ipaddress.ip_address(data_key['ip']) in ipaddress.ip_network(f"{request[8]}/{request[9]}"):

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
					'vlan_mng': request[10],
					'deviceid': request[11],
					'onlyup': onlyup,
				}
	else:
		error = "Error id_200 = Not IP"
		return error


	error = authorization_in_eltex(t, data_mes)
	t.ws_send_message(f"=== END {data_key['ip']} ===")

	t.ws_close()
	t.sql_connect('disconnect')
	return error
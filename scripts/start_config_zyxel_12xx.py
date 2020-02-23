#!/usr/bin/python3
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
import ftplib
import binascii
import ipaddress
import start_topology
# from ftplib import FTP
# from websocket import create_connection
try:
	from acds import configuration
except:
	import configuration



def upgrade(t, model, ip, logins):

	log_upgrade = subprocess.check_output(['perl', "/var/scripts/fttn/update_zyxel_12xx.pl", ip], universal_newlines=True)
	print(log_upgrade)
	return 'end_version'


def authorization_in_zyxel(t, data_mes):
	error = 'ok'
	ip = data_mes['ipaddmgm']
	model = data_mes['model']
	uplink = data_mes['uplink']

	if data_mes['login'] != 'default':
		def_login = data_mes['login']
	else:
		def_login = 'tacacs'

	if data_mes['password'] != 'default':
		def_password = data_mes['password']
	else:
		def_password = 'tacacs'

	logins = {
		0:{
			'login':'admin',
			'password':'1234'},
		2:{
			'login':'admin',
			'password':'Pikachu12'},
		1:{
			'login':def_login,
			'password':def_password},
	}

	print(f"authorization_in_zyxel|data_mes: {data_mes}")
	check_version = 'none'
	check_for = 0

	if not uplink:
		print(f"authorization_in_zyxel|start topology")
		t.ws_send_message(f"this device haven't data for uplink, topology started")
		topology_result = start_topology.loop(ip)
		t.sql_connect('connect')
		add = t.sql_select(f"""SELECT (SELECT NETWORKNAME FROM guspk.host WHERE DEVICEID = top.parent) 
							FROM guspk.host h 
							LEFT JOIN guspk.topology top ON top.child = h.DEVICEID 
							WHERE h.IPADDMGM = '{ip}'""", 'full')
		t.sql_connect('disconnect')
		print(f"authorization_in_zyxel|add: {add}")
		if add[0][0]:
			uplink = add[0][0]
			data_mes['uplink'] = uplink
			print(f"authorization_in_zyxel|data_mes['uplink']: {data_mes['uplink']}")
			t.ws_send_message(f"uplink: {uplink}")
		else:
			print("authorization_in_zyxel|Не отстроилась топология")
			t.ws_send_message("topology error")

	if not uplink:
		print('authorization_in_zyxel|Нет данных по uplink')
		t.ws_send_message("Error in topology, no data for uplink")
		error = "Error id_201 = Error in topology, no data for uplink"
		return error

	while check_version != 'end_version':
		if check_for == 3:
			print('authorization_in_zyxel|Неудалось загрузить или обновить коммутатор на новое ПО')
			error = "Error id_202 = Failed to load or update the switch to the new software"
			t.ws_send_message(error)
			return error
		check_for += 1
		t.ws_send_message("log in to the device")
		for n in range (len(logins)):
			i = t.aut(ip = ip, model = model, login=logins[n]['login'], password=logins[n]['password'])
			if i == 0:
				break

		if i != 0:
			error = "Error id_203 = Can't log in"
			t.ws_send_message(error)
			return error
		t.ws_send_message("success")

		t.new_sendline('sys info show')
		data = t.data_split()
		print(f"authorization_in_zyxel|data: {data}")

		match = re.search(r"Model: (\S+)", data, re.M)
		model = match[1]
		print(f"authorization_in_zyxel|model: {model}")

		match = re.search(r"ZyNOS version: (.+)", data, re.M)
		version = match[1]
		print(f"authorization_in_zyxel|version: {version}")

		versions = {
			'AAM1212-51': r"V3\.53\(AB[AQ]\.5\)",
			'IES1248-51': r"V3\.53\(AB[AQ]\.11\)",
		}
		# if versions.get(model):
			# print(f"authorization_in_zyxel|version model: {versions[model]}")
		if re.search(r"V3\.53\(AB[AQ]\.5\)|V3\.53\(AB[AQ]\.11\)", version):
			print(f"authorization_in_zyxel|check_version: {check_version}")
			check_version = 'end_version'
		else:
			print(f"authorization_in_zyxel|upgrade")
			check_version = upgrade(t, ip, logins[n]['login'], logins[n]['password'])


	print(check_version)

	with open (getattr(configuration, 'JN_PATH')+'template_commands_zyxel_1212_1248.jn2') as f:
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
		
	# t.new_sendline('banner login ^', timeout=1)


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
	t = telnet.FastModulAut(login=login_log) # prompt = '#' - настройка по умолчанию
	t.ws_connect('chat/log_configure/')
	t.ws_send_message(f"=== START {data_key['ip']} ===")

	error = 'ok'
	onlyup = None
	data_mes = {}

	if 'ip' in data_key and data_key['ip']:
		t.sql_connect('connect')
		reply = t.sql_select(f"""SELECT h.NETWORKNAME, hm.DEVICEMODELNAME, (SELECT NETWORKNAME FROM guspk.host WHERE DEVICEID = top.parent), 
				hv.HSI, hv.IPTV, hv.IMS, hv.TR069, hn.GW, hn.NETWORK, hn.MASK, hn.VLAN
				FROM guspk.host h
				LEFT JOIN guspk.host_status hs ON h.DEVICESTATUSID = hs.status_id
				LEFT JOIN guspk.host_model hm ON h.MODELID = hm.MODELID
				LEFT JOIN guspk.topology top ON top.child = h.DEVICEID
				LEFT JOIN guspk.host_acsw_node an ON an.DEVICEID = h.DEVICEID
				LEFT JOIN guspk.host_networks hn ON hn.NETWORK_ID = an.NETWORK_ID
				LEFT JOIN guspk.host_vlan_template hv ON hv.VLAN_TEMPLATE_ID = an.VLAN_TEMPLATE_ID
				WHERE h.IPADDMGM = '{data_key['ip']}'
			""", 'full')
		# print (reply)
		# vlans = t.sql_select(f"""SELECT vt.HSI, vt.IPTV, vt.IMS, vt.TR069, hn.GW, CONCAT(hn.NETWORK,'/',hn.MASK), hn.VLAN
		# 	FROM guspk.host h, guspk.host_acsw_node an, guspk.host_vlan_template vt, guspk.host_networks hn
		# 	WHERE h.DEVICEID = an.DEVICEID
		# 	AND an.VLAN_TEMPLATE_ID = vt.VLAN_TEMPLATE_ID
		# 	AND an.NETWORK_ID = hn.NETWORK_ID
		# 	AND h.IPADDMGM = '{data_key['ip']}'
		# 	""", 'full')
		t.sql_connect('disconnect')

		vpi_pppoe = 8
		vpi_ip_tv = 8
		vci_pppoe = 35
		vci_ip_tv = 37
		if re.search(r'^59-', reply[0][0]):
			vpi_pppoe = 8
			vpi_ip_tv = 0
			vci_pppoe = 35
			vci_ip_tv = 34
		elif re.search(r'^74-', reply[0][0]):
			vpi_pppoe = 8
			vpi_ip_tv = 0
			vci_pppoe = 35
			vci_ip_tv = 34
		elif re.search(r'^45-', reply[0][0]):
			vpi_pppoe = 1
			vpi_ip_tv = 1
			vci_pppoe = 500
			vci_ip_tv = 501

		for i, request in enumerate(reply):
			if ipaddress.ip_address(data_key['ip']) in ipaddress.ip_network(f"{request[8]}/{request[9]}"):

				data_mes = {
					'ipaddmgm': data_key['ip'],
					'hostname': request[0],
					'model': request[1],
					'uplink': request[2],
					'login': login,
					'password': password,
					'pppoe': {
						'vlan': request[3], 
						'name':'PPPoE'},
					'iptv': {
						'vlan': request[4], 
						'name':'IP-TV'},
					'tr069': {
						'vlan': request[6], 
						'name':'TR069'},
					'default_gateway': request[8],
					'vlan_mng': request[10],
					'vpi_pppoe': vpi_pppoe,
					'vpi_ip_tv': vpi_ip_tv,
					'vci_pppoe': vci_pppoe,
					'vci_ip_tv': vci_ip_tv,
					'onlyup': onlyup,
				}

	print(data_mes)
	if data_mes:
		error = authorization_in_zyxel(t, data_mes)
	else:
		error = "Error id_200 = Error sql select, no data"
	# t.ws_send_message(f"=== END {data_key['ip']} ===")

	t.ws_close()	
	t.sql_connect('disconnect')
	return error


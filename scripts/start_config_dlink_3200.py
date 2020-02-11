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
	}

	parser = argparse.ArgumentParser(
		prog = 'Setting MES Eltex',
		description = '''Данный скрипт позваляет настроить базовый конфиг MES Eltex.''',
		epilog = '''(c) January 2019. Автор программы, как всегда,
			не несет никакой ответственности ни за что.'''
		)
	# subparsers = parser.add_subparsers (dest='command')

	for n in range(8):
		# subparsers.add_parser (parametr[n]['vlan_sub'])
		parser.add_argument (parametr[n]['vlan_l'], parametr[n]['vlan_f'], type=parametr[n]['vlan_typ'], nargs='?')

	return parser


def upgrade(t, model, ip):
	pass	# Здесь нежно переписать процесс обновления под Dlink

	# image_33 = 'mes3300-4011-R310.ros'
	# version_33 = '4.0.11'

	# image_21 = 'mes2000-11485.ros'
	# version_21 = '1.1.48.5'

	# image_31 = 'mes3000-25482.ros'
	# version_31 = '48.2'

	# t.new_sendline('configure')
	# t.new_sendline('port jumbo-frame')
	# t.new_sendline('exit')

	# t.new_sendline('show version') # Смотрим активную версию
	# data = t.data_split()
	# match = re.search(r'Active-image.*\n\s+Version: ([\d\.]+)|SW version\s+([\d\.]+)', data, re.M)
	# if match and match.group(1):
	# 	activ_version = match.group(1)
	# elif match and match.group(2):
	# 	activ_version = match.group(2)
	# print (f"version: {activ_version}")

	# download_required = 'yes'
	# match = re.search(r'Inactive-image.*\n\s+Version: ([\d\.]+)', data, re.M)	# Смотрим не активную версию для x300-й серии
	# if match and match.group(1) == version_33:
	# 	download_required = 'no'

	# t.new_sendline('show bootvar')	# Смотрим не активную версию для x100-й серии
	# data = t.data_split()
	# match = re.search(r"([12]).+{}.+Not active".format(version_21), data, re.M)
	# if (match):
	# 	t.new_sendline(f"boot system image-{match.group(1)}")
	# 	download_required = 'no'

	# # орпеделяем модель, проверяем активную версию с заданным шаблоном.
	# if re.search(r'MES23[\d]{2}|MES33[\d]{2}', model) and activ_version != version_33:
	# 	download_command = (f"boot system tftp://10.228.63.237/FTP/FTTb/{image_33}")
	# elif re.search(r'MES21[\d]{2}|MES11[\d]{2}', model) and activ_version != version_21:
	# 	download_command = (f"copy tftp://10.228.63.237/FTP/FTTb/{image_21} flash://image")
	# elif re.search(r'MES31[\d]{2}', model) and activ_version != version_31:
	# 	download_command = (f"copy tftp://10.228.63.237/FTP/FTTb/{image_31} flash://image")
	# else: 
	# 	print ("Коммутатор на последней версии")
	# 	return 'end_version'


	# if re.search(r'MES21[\d]{2}| MES23[\d]{2}|MES11[\d]{2}|MES31[\d]{2}|MES22[\d]{2}', model):
	# 	t.new_sendline('boot system inactive-image')
	# 	data = t.data_split()
	# 	match = re.search(r'missing mandatory parameter', data, re.M)
	# 	if (match):
	# 		t.new_sendline('show bootvar')
	# 		data = t.data_split()
	# 		match = re.search(r"([12]).+{}.+Not active".format(version_21), data, re.M)
	# 		if (match):
	# 			t.new_sendline(f"boot system image-{match.group(1)}")
			

	# if download_required == 'yes':
	# 	print (f"""\n{datetime.datetime.today().strftime("%H:%M:%S")}\t""", sep='', end='')
	# 	print (f"Скачиваем последнюю версию ПО")
	# 	t.new_sendline(download_command, timeout=300)
	# else:
	# 	print (f"""\n{datetime.datetime.today().strftime("%H:%M:%S")}\t""", sep='', end='')
	# 	print (f"Последняя версия ПО уже загружена")
	# t.new_sendline('write memory', prompt='\[startup-config\]')
	# t.new_sendline('y', timeout_expect=1)
	# t.new_sendline('reload', prompt='[yY]')
	# t.new_sendline('y')
	# print (f"""\n{datetime.datetime.today().strftime("%H:%M:%S")}\t""", sep='', end='')
	# print (f"Ждём перезагрузки коммутатора")
	# time.sleep(10)
	# for n in range(500):
	# 	try:
	# 		ping = subprocess.check_output(["ping", ip, "-c 1"], universal_newlines=True)
	# 		# print (f"{n} ping: {ping}")
	# 		if re.search(r"icmp_seq=1", ping, re.M):
	# 			break
	# 	except subprocess.CalledProcessError as err:
	# 		pass
	# 		# print (f'{datetime.datetime.today().strftime("%H:%M:%S")} not responding to ping')
	# print (f"""\n{datetime.datetime.today().strftime("%H:%M:%S")}\tКоммутатор перезагружен""")
	# return 'upgrade'



def authorization_in_eltex(t, reply, data_config):					# id	hostname	model	ticket	office	datemodify	status	uplink	mac

	ip = data_config['ip']
	model = data_config['model']
	uplink = data_config['port_uplink']

	if data_config['login'] != 'default':
		def_login = data_config['login']
	else:
		def_login = 'tacacs'

	if data_config['password'] != 'default':
		def_password = data_config['password']
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

	print (ip, data_config['hostname'])
	check_version = 'none'
	check_for = 0
	# print (data_config)

	# print (data_config)
	# return
	if uplink == None or not uplink:
		try:
			t.ws_send_message(f"this device haven't data for uplink, topology started")
			uplink = subprocess.check_call(["perl", "/var/scripts/system/find_ip.pl", ip], universal_newlines=True)
			t.sql_connect('connect')
			add = t.sql_select(f"SELECT CONCAT((SELECT NETWORKNAME FROM guspk.host WHERE DEVICEID = top.parent), '_', top.parent_port) FROM guspk.host h LEFT JOIN guspk.topology top ON top.child = h.DEVICEID WHERE h.IPADDMGM = '{ip}'", 'full')
			t.sql_connect('disconnect')
			if add[0][0]:
				uplink = add[0][0]
				t.ws_send_message(f"uplink: {uplink}")
			else:
				print(f"authorization_in_eltex|Не отстроилась топология")
				t.ws_send_message("topology error")

		except subprocess.CalledProcessError as err:
			print(f'authorization_in_eltex|Не удалось запустить скрипт топологии /var/scripts/core/find_ip.pl')
			t.ws_send_message(f"can't run topology script /var/scripts/core/find_ip.pl")
	if not uplink:
		print ('Нет данных по uplink')
		error =  'Error id_101 =  Нет данных по uplink'
		return error

	while check_version != 'end_version':
		if check_for == 3:
			print ('Неудалось загрузить или обновить коммутатор на новое ПО')
			return
		check_for += 1
		for n in range (len(logins)):
			i = t.aut(ip = ip, model = model, login=logins[n]['login'], password=logins[n]['password'])
			if i == 0:
				break

		if i != 0:
			return

		# check_version = upgrade(t, model, ip)
		check_version = 'end_version' # убарть эту строку и разкоментировать выше кода будет описан процес обновления

	t.new_sendline('show config current_config include "iproute default"') # определяем geteway
	data = t.data_split()
	match = re.search(r'\s+([\d\.]+)', data, re.M)
	if (match):
		default_gateway = match.group(1)
		print (f"default_gateway: {default_gateway}")

	t.new_sendline(f"show arpentry ipaddress {default_gateway}") # mac default gateway для определения vlan mng и порта аплинка
	data = t.data_split()
	match = re.search(fr'{default_gateway}\s+([\w-]+)\s+', data, re.M)
	if (match):
		mac_gateway = match.group(1)
		print (f"mac_gateway: {mac_gateway}")

	t.new_sendline(f"show fdb mac_address {mac_gateway}") # определяем порт аплинка и влан управления
	data = t.data_split()
	match = re.search(fr'(\d+)\s+.+?MNG.+?\s+{mac_gateway}\s+(\d+)', data, re.M)
	port_uplink = 'none'
	if (match):
		vlan_mng = int(match.group(1))
		port_uplink = int(match.group(2))
		print (f"vlan_mng: {vlan_mng}")
		print (f"port_uplink: {port_uplink}")

	if port_uplink == 'none':
		t.disconnect()
		error =  "Error id_102 = Не удалось определить порт uplink"
		return error

	print (f"model: {model}")
	check_port_uplink = 'bad'
	if re.search(r'3200-10', model):
		port_downlink = '1-9'
		if port_uplink != 10:
			check_port_uplink = 'good'

	elif re.search(r'3200-18', model):
		port_downlink = '1-16'
		if port_uplink != 18:
			check_port_uplink = 'good'

	elif re.search(r'3200-28', model):
		port_downlink = '1-26'
		if port_uplink != 28:
			check_port_uplink = 'good'

	elif re.search(r'3200-52', model):
		port_downlink = '1-50'
		if port_uplink != 52:
			check_port_uplink = 'good'

	if check_port_uplink == 'bad':
		print (f"Необходимо сменить порт аплинка. Рекомендуется использовать последний порт в коммутаторе.\n{port_uplink} - данный порт не рекомендуется еспользовать, потому что он пересекается с портами которые используются под услуги абонетов или подключения других устройств")
		t.disconnect()
		return

	iptacacs = 'none'
	if re.search(r'^10.228.', ip):
		iptacacs = '10.228.63.10'
	elif re.search(r'^10.224.', ip):
		iptacacs = '10.224.78.250'

	if iptacacs == 'none':
		print (f"Для данного {ip} не указан tacacs server")
		t.disconnect()
		return

	if uplink == None:
		print (f"Для данного {ip} не указан uplink в bd")
		t.disconnect()
		return

	uplink = uplink.replace(' ', '_')

	data_config['mask'] = mask
	data_config['port_uplink'] = port_uplink
	data_config['port_downlink'] = port_downlink
	data_config['vlan_mng'] = vlan_mng
	data_config['model'] = model
	data_config['iptacacs'] = iptacacs
	data_config['default_gateway'] = default_gateway
	data_config['uplink'] = uplink

	with open ('/var/scripts/fttb/template_commands_dlink_3200.jn2') as f:
		mes_switches_template = f.read()
		template = jinja2.Template(mes_switches_template)
		commands_mes_switches = template.render(data_config).splitlines()

	nn = 0
	for command in commands_mes_switches:
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
	# t.new_sendline('UNAUTHORIZED ACCESS TO THIS DEVICE IS PROHIBITED', timeout=1)
	# t.new_sendline('You must have explicit, authorized permission to access or configure this device.', timeout=1)
	# t.new_sendline('Unauthorized attempts and actions to access or use this system may result in civil and/or', timeout=1)
	# t.new_sendline('criminal penalties.', timeout=1)
	# t.new_sendline('All activities performed on this device are logged and monitored.', timeout=1)
	# t.new_sendline('^', timeout=1)
	# t.new_sendline('exit', timeout=1)

	t.new_sendline('save')

	t.disconnect()

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
	reply = {}
	t.ws_connect('chat/log_configure/')
	t.ws_send_message(f"=== START {data_key['ip']} ===")

	if not data_key.get('hostname') or not data_key.get('port_uplink') or not data_key.get('model'):
		t.sql_connect('connect')
		reply = t.sql_select(f"h.IPADDMGM LIKE '{data_key['ip']}'")
		# print (reply)
		vlans = t.sql_select(f"""SELECT vt.HSI, vt.IPTV, vt.IMS, vt.TR069
			FROM guspk.host h, guspk.host_acsw_node an, guspk.host_vlan_template vt
			WHERE h.DEVICEID = an.DEVICEID
			AND an.VLAN_TEMPLATE_ID = vt.VLAN_TEMPLATE_ID
			AND h.IPADDMGM = '{data_key['ip']}'""", 'full')
		t.sql_connect('disconnect')

		if vlans:
			data_key['pppoe'] = vlans[0][0]
			data_key['tv'] = vlans[0][1]
			data_key['ims'] = vlans[0][2]
			data_key['tr069'] = vlans[0][3]


		if not data_key.get('hostname'):
			data_key['hostname'] = reply[data_key['ip']]['hostname']

		if not data_key.get('port_uplink'):
			if reply[data_key['ip']].get('uplink'):
				data_key['port_uplink'] = reply[data_key['ip']]['uplink']
			else:
				data_key['port_uplink'] = ''

		if not data_key.get('model'):
			data_key['model'] = reply[data_key['ip']]['model']

	data_config = {
		'login': login_log,
		'ip': data_key['ip'],
		'hostname': data_key['hostname'],
		'port_uplink': data_key['port_uplink'],
		'model': data_key['model'],
		'login': login,
		'password': password,
		'pppoe': {
			'vlan': data_key['pppoe'], 
			'name':'PPPoE'},
		'iptv': {
			'vlan': data_key['tv'], 
			'name':'IP-TV'},
		'ims': {
			'vlan': data_key['ims'], 
			'name':'IMS'},
		'tr069': {
			'vlan': data_key['tr069'], 
			'name':'TR069'},
	}
	authorization_in_eltex(t, reply, data_config)
	t.ws_close()

if __name__ == "__main__":
	parser = createParser()
	namespace = parser.parse_args()
	
	data_key = {}
	data_key['ip'] = namespace.ip
	data_key['hostname'] = namespace.name
	data_key['port_uplink'] = namespace.uplink
	data_key['model'] = namespace.model
	data_key['pppoe'] = namespace.pppoe
	data_key['tv'] = namespace.tv
	data_key['ims'] = namespace.ims
	data_key['tr069'] = namespace.tr069

	if namespace.ip == None:
		print('Нужно указать IP в формате --ip 192.168.1.1')
		sys.exit(ip)
	print (datetime.datetime.today().strftime("%H:%M:%S"))
	start_config(data_key)
	print ("\n",datetime.datetime.today().strftime("%H:%M:%S"), sep="")

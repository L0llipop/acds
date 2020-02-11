#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, os, re
import getpass
import mysql.connector 
import requests
import ipaddress
from mysql.connector import Error
from configparser import ConfigParser
import multimodule
from multiprocessing import Pool
import argparse
import datetime

# user = getpass.getuser()
# pathini = "/home/"+user+"/.config/config_data.ini"
# config = ConfigParser()
# config.read(pathini)
# p_sql = config.get('login_pass', 'mysql')
# tacacs_password = config.get('login_pass', 'tacacs')

def createParser ():
	# args= {'ip':'10.228.130.6', 'mask':'255.255.255.0', 'pppoe':'413', 'tv':'992', 'ims':'65', 'tr069':'3050', 'login':'yuzhakov-da', 'uplink':'72-TUMEN-AGG035-BBAGG-1'}
	parametr = {
		0:{'key_f':'--ip',		'key_l':'-a',	'key_typ':str,	'key_sub':'ip',},
		1:{'key_f':'--pppoe',	'key_l':'-p',	'key_typ':int,	'key_sub':'vlan_pppoe',},
		2:{'key_f':'--tv',		'key_l':'-t',	'key_typ':int,	'key_sub':'vlan_ip_tv',},
		3:{'key_f':'--ims',		'key_l':'-i',	'key_typ':int,	'key_sub':'vlan_ims',},
		4:{'key_f':'--tr069',	'key_l':'-r',	'key_typ':int,	'key_sub':'vlan_tr069',},
		5:{'key_f':'--network',	'key_l':'-n',	'key_typ':str,	'key_sub':'network',},
	}

	parser = argparse.ArgumentParser(
		prog = 'Add network temlplate',
		description = '''Добавляет шаблон в БД для динамического выделения IP.''',
		epilog = '''(c) January 2019. Автор программы, как всегда,
			не несет никакой ответственности ни за что.'''
		)
	# subparsers = parser.add_subparsers (dest='command')

	for n in range(len(parametr)):
		# subparsers.add_parser (parametr[n]['key_sub'])
		parser.add_argument (parametr[n]['key_l'], parametr[n]['key_f'], type=parametr[n]['key_typ'], nargs='?')

	return parser


def template_check(data_key):
	t = multimodule.FastModulAut()
	t.sql_connect('connect')

	interface = ipaddress.IPv4Interface(f"{data_key['ip']}")
	ip_uplink = str(interface.ip)

	network_mask = ipaddress.IPv4Network(f"{data_key['ip']}", strict=False)
	network = str(network_mask.network_address)

	# ipfree = ipaddress.IPv4Network(f"{data_key['ip']}/{data_key['mask']}", strict=False)
	# print (f"ipfree: {ipfree}")
	# print (f"network: {network}")

	network_id = t.sql_select(f"select NETWORK_ID from guspk.host_networks where NETWORK like '{network}'", 'full')
	if network_id:
		network_id = network_id[0][0]
		# print (f"network_id: {network_id}")
	else:
		# print (f"network_id not founded, {network} {data_key['mask']} {data_key['ip']}")
		return f"network_id not founded, {network} {data_key['mask']} {ip_uplink}"

	data_key_network_id = None
	network_mask = str(network_mask)
	if data_key['network'] and data_key['network'] != None and data_key['network'] != network_mask:
		add_network = ipaddress.IPv4Network(f"{data_key['network']}", strict=False)
		add_network = str(add_network.network_address)
		# print (f"network: {data_key['network']}")
		data_key_network_id = t.sql_select(f"select NETWORK_ID from guspk.host_networks where NETWORK like '{add_network}'", 'full')
		if data_key_network_id:
			data_key_network_id = data_key_network_id[0][0]
			# print (f"data_key_network_id: {data_key_network_id}")
		else:
			# print (f"data_key_network_id not founded, {data_key_network_id}")
			return f"data_key_network_id not founded, {data_key_network_id}"


	vlan_template_id = t.sql_select(f"""select VLAN_TEMPLATE_ID from guspk.host_vlan_template where HSI like {data_key['pppoe']} and IPTV like {data_key['tv']} and IMS like {data_key['ims']} and TR069 like {data_key['tr069']}""", 'full')
	if vlan_template_id:
		vlan_template_id = vlan_template_id[0][0]
		# print (f"vlan_template_id: {vlan_template_id}")
	else:
		# t.sql_update(f"insert into guspk.host_vlan_template (HSI,IPTV,IMS,TR069) values ({data_key['pppoe']}, {data_key['tv']}, {data_key['ims']}, {data_key['tr069']})")
		# print("vlan_template not founded")
		# print(f"\ninsert into guspk.host_vlan_template (HSI,IPTV,IMS,TR069) values ({data_key['pppoe']}, {data_key['tv']}, {data_key['ims']}, {data_key['tr069']})")
		t.sql_update(f"insert into guspk.host_vlan_template (HSI,IPTV,IMS,TR069) values ({data_key['pppoe']}, {data_key['tv']}, {data_key['ims']}, {data_key['tr069']})")
		return "vlan_template not founded"


	deviceid = t.sql_select(f"select DEVICEID from guspk.host where IPADDMGM like '{ip_uplink}'", 'full')
	if deviceid:
		deviceid = deviceid[0][0]
	else:
		# print (f"Не найдено устройство в BD guspk.host: {ip_uplink}")
		return f"Не найдено устройство в BD guspk.host: {ip_uplink}"

	summary = t.sql_select(f"select DEVICEID, NETWORK_ID, VLAN_TEMPLATE_ID from guspk.host_acsw_node where DEVICEID like {deviceid} and NETWORK_ID like {network_id} and VLAN_TEMPLATE_ID like {vlan_template_id}", 'full')

	if summary:
		summary = summary[0][0]
	else:
		# print(f"\ntable acsw_node not founded temlplate deviceid: {deviceid} network: {network_id}")
		# print(f"\ninsert into guspk.host_acsw_node (DEVICEID, NETWORK_ID, VLAN_TEMPLATE_ID) values ('{deviceid}', '{network_id}', '{vlan_template_id}')")
		t.sql_update(f"insert into guspk.host_acsw_node (DEVICEID, NETWORK_ID, VLAN_TEMPLATE_ID) values ('{deviceid}', '{network_id}', '{vlan_template_id}')")

	if data_key_network_id:
		summary = t.sql_select(f"select DEVICEID, NETWORK_ID, VLAN_TEMPLATE_ID from guspk.host_acsw_node where DEVICEID like {deviceid} and NETWORK_ID like {data_key_network_id} and VLAN_TEMPLATE_ID like {vlan_template_id}", 'full')
		if summary:
			summary = summary[0][0]
			print(summary)
		else:
			# print(f"\ntable acsw_node not founded temlplate deviceid: {deviceid} network: {data_key_network_id}")
			# print(f"\ninsert into guspk.host_acsw_node (DEVICEID, NETWORK_ID, VLAN_TEMPLATE_ID) values ('{deviceid}', '{data_key_network_id}', '{vlan_template_id}')")
			sql_update(f"insert into guspk.host_acsw_node (DEVICEID, NETWORK_ID, VLAN_TEMPLATE_ID) values ('{deviceid}', '{data_key_network_id}', '{vlan_template_id}')")

	t.sql_connect('disconnect')
	return 'good'


# def main(data_key):
# 	pass

if __name__ == "__main__":
	parser = createParser()
	namespace = parser.parse_args()

	data_key = {}
	data_key['ip'] = namespace.ip
	data_key['pppoe'] = namespace.pppoe
	data_key['tv'] = namespace.tv
	data_key['ims'] = namespace.ims
	data_key['tr069'] = namespace.tr069
	data_key['network'] = namespace.network
	print (data_key)
	for key in data_key:
		if key == 'ims' or key == 'network':
			continue
		if data_key[key] == None:
			print('-h | --help - для подробной информации')
			print('Нужно указать все значения в формате: --ip 192.168.1.1 --pppoe 400 --tv 992 --tr069 3050')
			print('Не обязательный параметр: --network 192.168.1.0 --ims 65')
			sys.exit()

	print (datetime.datetime.today().strftime("%H:%M:%S"))
	result = template_check(data_key)
	if result != 'good':
		print (result)
	print (f"""\n{datetime.datetime.today().strftime("%H:%M:%S")}""")
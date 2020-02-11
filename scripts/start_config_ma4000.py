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
		6:{'vlan_f':'--model',	'vlan_l':'-m',	'vlan_typ':str,	'vlan_sub':'model',},
	}

	parser = argparse.ArgumentParser(
		prog = 'Setting OLT',
		description = '''Данный скрипт позволяет настроить базовый конфиг GPON Eltex OLT.''',
		epilog = '''(c) January 2019. Автор программы, как всегда,
			не несет никакой ответственности ни за что.'''
		)
	# subparsers = parser.add_subparsers (dest='command')

	for n in range(8):
		# subparsers.add_parser (parametr[n]['vlan_sub'])
		parser.add_argument (parametr[n]['vlan_l'], parametr[n]['vlan_f'], type=parametr[n]['vlan_typ'], nargs='?')

	return parser


def authorization_in_eltex(t, reply, data_olt):	
	ip = data_olt['ip']
	model = data_olt['model']
	error = 'ok'

	if data_olt['login'] != 'default':
		def_login = data_olt['login']
	else:
		def_login = 'tacacs'

	if data_olt['password'] != 'default':
		def_password = data_olt['password']
	else:
		def_password = 'tacacs'

	logins = {
		0 :{
			'login':'admin',
			'password':'password'},
		1 :{
			'login':'admin',
			'password':'admin'},
		2 :{
			'login':def_login,
			'password':def_password},
	}


	check_for = 0
	for n in range (len(logins)):
		check_for += 1
		i = t.aut(ip = ip, model = model, login=logins[n]['login'], password=logins[n]['password'])
		if i == 0:
			break

	if i != 0:
		error = "Error id_203 = Can't connect"
		t.ws_send_message(error)
		return error

	t.new_sendline('show management') # определяем geteway
	data = t.data_split()
	# print (data)
	match = re.search(r'gateway:?\s+([\d\.]+)', data, re.M | re.I)
	if (match):
		data_olt['default_gateway'] = match[1]
		t.ws_send_message(f"default_gateway: {match[1]}")
	else:
		error = "Error id_204 = no default gateway"
		t.ws_send_message(error)
		t.disconnect()
		return error


	if model == 'MA-4000px':
		path = '/var/www/acds/static/jn_templates/template_commands_ma4000.jn2'
	elif model == 'LTP-8X':
		path = '/var/www/acds/static/jn_templates/template_commands_ltp-8x.jn2'
	elif model == 'LTP-4X':
		path = '/var/www/acds/static/jn_templates/template_commands_ltp-4x.jn2'

	try:
		with open (path) as f:
			olt_template = f.read()
			template = jinja2.Template(olt_template)
			commands_olt = template.render(data_olt).splitlines()

	except FileNotFoundError:
		error = "Error id_205 = could not open file"
		t.ws_send_message(error)
		t.disconnect()
		return error


	nn = 0
	for command in commands_olt:
		t.new_sendline(command, timeout=20, timeout_expect=.500)
		data = t.data_split('list')
		t.ws_send_message(f"{nn:4} - {command:80} ║ {data[0]}")

		for d in data:
			if re.search(r'Unrecognized command|Incomplete command', d):
				print(f"\t\t\tКоманда: {command} не проходит")
		nn += 1
	# t.new_sendline('exit')
	# t.new_sendline('commit')
	# t.ws_send_message(f"commit")
	# t.new_sendline('confirm')
	# t.ws_send_message(f"confirm")
	# t.new_sendline('exit')
	t.disconnect()
	return error


def start_config(data_key, login='default', password='default', login_log='default'):
	t = telnet.FastModulAut(prompt = '#', login=login_log)
	reply = {}
	t.ws_connect('chat/log_configure/')
	t.ws_send_message(f"=== START {data_key['ip']} ===")

	reply = {}

	if 'ip' in data_key and data_key['ip']:
		t.sql_connect('connect')
		reply = t.sql_select(f"h.IPADDMGM LIKE '{data_key['ip']}'")
		# print (reply)
		vlans = t.sql_select(f"""SELECT vt.HSI, vt.IPTV, vt.IMS, vt.TR069
			FROM guspk.host h, guspk.host_acsw_node an, guspk.host_vlan_template vt
			WHERE h.DEVICEID = an.DEVICEID
			AND an.VLAN_TEMPLATE_ID = vt.VLAN_TEMPLATE_ID
			AND h.IPADDMGM = '{data_key['ip']}'
			AND vt.HSI != 0
			AND vt.IPTV != 0
			AND vt.IMS != 0
			AND vt.TR069 != 0""", 'full')
		t.sql_connect('disconnect')

		if reply:
			if vlans:
				data_key['pppoe'] = vlans[0][0]
				data_key['tv'] = vlans[0][1]
				data_key['ims'] = vlans[0][2]
				data_key['tr069'] = vlans[0][3]
				t.ws_send_message(f"PPPoE: {vlans[0][0]}\tIP-TV: {vlans[0][1]}\tIMS: {vlans[0][2]}\tTR069: {vlans[0][3]}")
			else:
				error = "Error id_200 = Not VLANS in DB"
				t.ws_send_message(f"Error id_200 = Not VLANS in DB")
				return error

			data_key['hostname'] = reply[data_key['ip']]['hostname']
			data_key['model'] = reply[data_key['ip']]['model']

		else:
			error = "Error id_201 = Not DATA in DB"
			t.ws_send_message(f"Error id_201 = Not DATA in DB")
			return error

	else:
		error = "Error id_202 = Not IP"
		t.ws_send_message(f"Error id_202 = Not IP")
		return error

	data_olt = {
		'ip': data_key['ip'],
		'hostname': data_key['hostname'],
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

	error = authorization_in_eltex(t, reply, data_olt)

	t.ws_send_message(f"=== END {data_key['ip']} ===")
	t.ws_close()
	return error

if __name__ == "__main__":
	parser = createParser()
	namespace = parser.parse_args()
	
	data_key = {}
	data_key['ip'] = namespace.ip
	data_key['hostname'] = namespace.name
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


 # -p 3507 -t 3527 -i 3547 -r 3567
 # |olt_to_proviso| 72-OMUT-EDG561-O1 1/2 (10.228.140.157) OLT
 # set interfaces xe-0/0/18 description "|olt_to_proviso| 72-OMUT-EDG561-O1 1/2 (10.228.140.157) OLT"
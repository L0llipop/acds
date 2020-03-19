#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, os, re
import getpass
# import mysql.connector 
# from mysql.connector import Error
import multimodule
import ipaddress
import multiprocessing
from multiprocessing import Pool
import subprocess
import datetime
from datetime import datetime, timedelta
import template_check


from transliterate import translit, get_available_language_codes
# from websocket import create_connection

def translate_to_en(text):
	text = text.replace(" ", "")
	text = text.replace("ь", "")
	text = text.replace("ъ", "")
	try:
		text_en = translit(f"{text}", reversed=True)
	except:
		return text
	text_en = text_en[0:6]
	text_en = text_en.upper()
	return text_en
	# print(f"Translation: {text_en}")


def get_data(uplink_ip, model, vrf, t):
	user = getpass.getuser()
	hosts = []

	query = f"""SELECT b.NETWORK, b.MASK, c.HSI, c.IPTV, c.IMS, c.TR069, b.VLAN, b.GW, b.NETWORK_ID
					FROM guspk.host_acsw_node a, guspk.host_networks b, guspk.host_vlan_template c, guspk.host d
					WHERE 
					d.DEVICEID = a.DEVICEID AND
					a.NETWORK_ID = b.NETWORK_ID AND
					a.VLAN_TEMPLATE_ID = c.VLAN_TEMPLATE_ID AND
					d.IPADDMGM like '{uplink_ip}' AND
					b.VRF like '{vrf}'"""

	print (f"def get_data | query: {query}")
	summary = t.sql_select(query, 'full')
	print (f"def get_data | summary: {summary}")
	# summary = [['10.228.128.0', 28, 422, 992, 65, 3052]]
	if __name__ == "__main__" and not summary:
		# Если для аплинка не указан шаблон сетей и вланов, то необходимо зайти на устройство и посмотреть его маску, и основные вланы услуг
		data_key_temp = {}
		data_key_temp['network'] = None

		print (f"not found templates for {uplink_ip}")
		print ('Specify mask uplink (format: 24): ', end='')
		data_key_temp['ip'] = f"{uplink_ip}/{input()}"
		print ('Specify the network (format: 10.228.52.0/24): ', end='')
		data_key_temp['network'] = input()
		print ('vlan PPPoE: ', end='')
		data_key_temp['pppoe'] = input()
		print ('vlan IP-TV: ', end='')
		data_key_temp['tv'] = input()
		print ('vlan IMS:   ', end='')
		data_key_temp['ims'] = input()
		print ('vlan TR069: ', end='')
		data_key_temp['tr069'] = input()

		if data_key_temp['ip']:
			template_check.template_check(data_key_temp)

		print ("Send 'y' for next settings: ", end='')
		next_settings = input()
		# Ещё раз запрашиваем необходимые данные
		t.sql_connect('disconnect')
		t.sql_connect('connect')
		summary = t.sql_select(query, 'full')

	if not summary:
		error_free_ip = 'Error id_101: no found vlan template for uplink'
		# t.sql_update(f"insert into guspk.logs (scr_name, DEVICEID, WHO, message) values ('free_ip','Null','{user}', '{error_free_ip}');")
		return error_free_ip, None

	ipfree = ipaddress.IPv4Network(f"{summary[0][0]}/{summary[0][1]}", strict=False)
	list(map(lambda x: hosts.append(str(x)) ,list(ipfree.hosts())))		# Формируем список свободных IP
	hosts.pop(0)
	hosts = hosts[:-1]

	return hosts, summary


def ping(ip):
	devnull = open(os.devnull, 'w')
	response = subprocess.call(["ping", "-c", "3", "-w", '3', ip], stdout=devnull)
	if response != 0:
		return ip

def ping_check(hosts):
	# multiprocessing.set_start_method("spawn") #для корректного дебага в vscode
	pool = Pool(50)
	hosts_unreacheble = list(filter(None, pool.map(ping, hosts)))
	pool.close()
	pool.join()
	return hosts_unreacheble

def get_free_ip(hosts_unreacheble, vrf, search_type, t):
	data_chek = datetime.today() - timedelta(days=200)
	hosts_free = []
	free_ip = None
	out_of_exp = None
	for ip_in_hosts in hosts_unreacheble:
		if vrf == 'CORE' and search_type == 'ACSW':
			if re.search(r"\.((\d|[12]\d|30)|1(0\d|[1234]\d|50)|2(0\d|[1234]\d|5\d))$", ip_in_hosts):
				continue
		elif vrf == 'CORE':
			# Для CORE сетей пропускаем все свободные IP до 31
			if re.search(r"\.((\d|[1234]\d|50)|1(0\d|[1234]\d|50)|2(0\d|[1234]\d|5\d))$", ip_in_hosts):
				continue

		astu_host_check = t.sql_select(f"SELECT DEVICEID, NETWORKNAME, DATEMODIFY, DEVICESTATUSID from guspk.host where IPADDMGM like '{ip_in_hosts}'", 'full')
		if astu_host_check:
			continue

		else:
			hosts_free.append(ip_in_hosts)

	if not free_ip and hosts_free:
		free_ip = hosts_free[0]

	print (f"def get_free_ip | hosts_free: {hosts_free}")

	# print (hosts_free)
	return free_ip


def create_hostname(id_acds, ip_uplink, search_type, vrf, free_ip, t):

	error_free_ip = 'ok'
	final_hostname = None
	numbers_node_end = []			# Список номеров из последней части hostname
	# index1 = '01'
	code_type_node = None

	# numbers_first = []		# Список номеров из середины hostname
	# first_half_number = '01'
	# index = 1

	# Берём данные по адресу устанавлевоемого оборудования для созднания первой половины hostname
	query = f"""SELECT fr.region_code, (
				CASE 
					WHEN af.city_fias_id IS NOT NULL THEN fc.city_en
					WHEN af.settlement_fias_id IS NOT NULL THEN fs.settlement_en
					ELSE NULL
				END) AS total,
				(CASE 
					WHEN af.city_fias_id IS NOT NULL THEN fc.city
					WHEN af.settlement_fias_id IS NOT NULL THEN fs.settlement
					ELSE NULL
				END) AS rus
			FROM guspk.acds_fias af
			LEFT JOIN guspk.fias_region fr ON af.region_fias_id = fr.region_fias_id
			LEFT JOIN guspk.fias_city fc ON af.city_fias_id = fc.city_fias_id
			LEFT JOIN guspk.fias_settlement fs ON af.settlement_fias_id = fs.settlement_fias_id
			WHERE af.id = {id_acds}"""

	other_devices = t.sql_select(query, 'full')
	if other_devices:
		region_code = other_devices[0][0]
		city_en = other_devices[0][1]
		city_ru = other_devices[0][2]
		t.ws_send_message(f"region_code: {region_code}")
		t.ws_send_message(f"city_en: {city_en}")
	else:
		error_free_ip = 'Error id_111: region code and city not found'
		t.ws_send_message(f"{error_free_ip}")
		return final_hostname, error_free_ip, None

	if not city_en:
		city_en = translate_to_en(city_ru)


	temp_ip = None
	t.ws_send_message(f"ip_uplink: {ip_uplink}")
	if re.search(r'^10\.22[2-7]', ip_uplink):
		temp_ip = ip_uplink

	else:
		query = f"""SELECT n.NETWORK
				FROM guspk.host_acsw_node an, guspk.host h, guspk.host_networks n
				WHERE h.DEVICEID = an.DEVICEID
				AND an.NETWORK_ID = n.NETWORK_ID
				AND n.VRF = 'CORE'
				AND h.IPADDMGM = '{ip_uplink}'"""

		other_devices = t.sql_select(query, 'full')
		t.ws_send_message(f"other_devices: {other_devices}")
		if other_devices:
			temp_ip = other_devices[0][0]
		else:
			error_free_ip = f"Error id_115: No template CORE for {ip_uplink}"
			t.ws_send_message(f"{error_free_ip}")
			return final_hostname, error_free_ip


	if temp_ip == None:
		error_free_ip = "Error id_112: Not in core network uplink or not templates in host_acsw_node"
		t.ws_send_message(f"{error_free_ip}")
		return final_hostname, error_free_ip

	match = re.search(r'\.(\d+)\.\d+$', temp_ip)
	if match:
		first_num_core = str(match[1]).zfill(4)
		first_num_fsw = str(match[1]).zfill(2)
		t.ws_send_message(f"first_num: {first_num_core}")
		t.ws_send_message(f"first_num: {first_num_fsw}")
	else:
		error_free_ip = "Error id_113: regex doesn't work"
		t.ws_send_message(f"{error_free_ip}")
		return final_hostname, error_free_ip


	match = re.search(r'(\d+)\.(\d+)$', free_ip)
	if match:
		index1 = str(match[1]).zfill(3)
		index2 = match[2]
		t.ws_send_message(f"index1: {index1}")
		t.ws_send_message(f"index2: {index2}")
	else:
		error_free_ip = "Error id_114: regex doesn't work"
		t.ws_send_message(f"{error_free_ip}")
		return final_hostname, error_free_ip


	if search_type == 'ACSW':
		code_type_node = 'ACC'
	elif search_type == 'ADSL':
		code_type_node = 'ACC'
	else:
		code_type_node = 'ACCF'

	t.ws_send_message(f"code type node: {code_type_node}")


	t.ws_send_message(f"error_free_ip: {error_free_ip}")
	if error_free_ip == 'ok':
		if vrf == 'CORE':
			final_hostname = f"{region_code}-{city_en}-{code_type_node}{first_num_core}-{search_type}-{index2}"
		elif vrf == 'FTTX_MNG' and search_type == 'O':
			final_hostname = f"{region_code}-{city_en}-{code_type_node}{first_num_fsw}{index1}-{search_type}{index2}"
		elif vrf == 'FTTX_MNG' and search_type == 'CNT':
			final_hostname = f"{region_code}-{city_en}-{index1}{index2}-{search_type}"
		else:
			final_hostname = f"{region_code}-{city_en}-{code_type_node}{first_num_fsw}{index1}-{search_type}-{index2}"
		t.ws_send_message(f"final_hostname: {final_hostname}")

	return final_hostname, error_free_ip



def main(data_key, t, error_free_ip):
	user = getpass.getuser()

	olt  = ['LTP-4X', 'LTP-8X', 'MA-4000', 'MA5800-X17']
	fttb = ['MES1124','MES1124M','MES2124','MES2124M','MES2124P','MES2124MB','MES2428','MES2408','MES2408C','MES2408P','MES2408B','MES2428B','MES2324B','MES3108F','MES3116F','MES2208P','MES2308','MES2308P','MES2324','MES2324F','MES2324P','MES3508P','MES3524F','MGS-3712','DES-3200-10','DES-3200-18','DES-3200-28','DES-3200-58','GS-3012', 'ES-2024a', '4024','ES-2108G','MGS-3712F','MES-3528','MGS-3712','MES3500-24','ES-3124','XGS-4728F','DES-2110','DES-3526','DES-3828','DGS-3700-12G','DGS-3200-10G','DES-3200-10','DES-3528','DES-3550','DES-1210-28/ME','DES-3200-28','DES-3200-18','DGS-3120-24SC','DGS-3627G','DES-3028','DES-3026','DES-3010G','DES-2108','DGS-3612G','DGS-1100-06','DGS-1210-10/ME','DGS-1210-12TS/ME','DGS-1210-20/ME','DES-3200-10/C','DGS-1210-28/ME','DES-3200-28/C','DGS-3000-28SC','DES-3226S','DGS-3100-24','DES-3552','DGS-3420-52T','DGS-3100-24TG','DXS-3400-24SC','DGS-3120-24SC/B1','DES-3200-52','DGS-3120-48TC','DES-3200-18/C','DGS-3200-10','DES-3028G','DGS-3420-26SC','DES-1210-52/ME','GS-4012F','ES3528M', 'ES3526XA', 'WS-C2950-12', 'SNR-S2985G-8T', 'SNR-S2965-8T']
	wbs  = ['ePMP 1000', 'WOP-2AC-LR5', 'WOP-12ac-LR']
	vg   = ['SMG2016', 'MG-8FXS', 'MG-16FXS', 'MG-24FXS', 'MG-32FXS', 'MG-36FXS', 'MG-44FXS', 'MG-52FXS', 'MG-60FXS', 'MG-72FXS','TAU-72.IP','TAU-60.IP','TAU-24.IP','TAU-16.IP','TAU-36.IP','TAU-8.IP','TAU-4.IP']
	adsl = ['AAM1212', 'IES-1248-51', 'AAM1008-61', 'DSL IES-5000', '7330 FD', '7302 FD', 'C300', 'C350MB']
	acsw = ['ME-3600X-24TS-M', 'ME-3600X-24FS-M', 'ME-3400G-12CS-D','ME-3400-24TS-A','MES3124','MES3124F','MES3324F', 'MES3348F', 'WS-C3750E-24TD-S','ACX2100','WS-C3560E-24TD-S']
	cnt  = ['КУБ-Микро']

	vrf  = None

	if data_key['model'] in fttb:
		vrf = 'FTTX_MNG'
		search_type = 'FSW'
		structura = 71
	elif data_key['model'] in olt:
		vrf = 'FTTX_MNG'
		search_type = 'O'
		structura = 218
	elif data_key['model'] in wbs:
		vrf = 'FTTX_MNG'
		search_type = 'WBS'
		structura = 71
	elif data_key['model'] in vg:
		vrf = 'FTTX_MNG'
		search_type = 'VG'
		structura = 71
	elif data_key['model'] in adsl:
		vrf = 'CORE'
		search_type = 'DSL'
		structura = 64
	elif data_key['model'] in acsw:
		vrf = 'CORE'
		search_type = 'ACSW'
		structura = 16
	elif data_key['model'] in cnt:
		vrf = 'FTTX_MNG'
		search_type = 'CNT'
		structura = 71
	else:
		error_free_ip = 'Error id_100: The model does not fit the conditions'
		t.ws_send_message(error_free_ip)
		# t.sql_update(f"insert into guspk.logs (scr_name, DEVICEID, WHO, message) values ('free_ip','Null','{user}', '{error_free_ip}');")
		return error_free_ip

	# =========== Выделение IP ===========
	#Блок изменении ключевых параметров на случай когда ранее выделенный ip не совпадает с сетью характерной для этой модели
	if data_key.get('freeip'):
		free_ip = data_key['freeip']
			
		reply = t.sql_select(f"""SELECT h.NETWORKNAME, hm.DEVICEMODELNAME, CONCAT((SELECT NETWORKNAME FROM guspk.host WHERE DEVICEID = top.parent), '_', top.parent_port), 
				hv.HSI, hv.IPTV, hv.IMS, hv.TR069, hn.GW, hn.NETWORK, hn.MASK, hn.VRF, hn.VLAN, h.DEVICEID
				FROM guspk.host h
				LEFT JOIN guspk.host_status hs ON h.DEVICESTATUSID = hs.status_id
				LEFT JOIN guspk.host_model hm ON h.MODELID = hm.MODELID
				LEFT JOIN guspk.topology top ON top.child = h.DEVICEID
				LEFT JOIN guspk.host_acsw_node an ON an.DEVICEID = h.DEVICEID
				LEFT JOIN guspk.host_networks hn ON hn.NETWORK_ID = an.NETWORK_ID
				LEFT JOIN guspk.host_vlan_template hv ON hv.VLAN_TEMPLATE_ID = an.VLAN_TEMPLATE_ID
				WHERE h.IPADDMGM = '{data_key['up']}'
			""", 'full')
		if len(reply) < 2 or len(reply) > 2:
			error_free_ip = 'Error id_110: uplink must have 2 templates (FTTX, CORE)'
			return error_free_ip
		type_changed = False
		for i, request in enumerate(reply):
			if ipaddress.ip_address(free_ip) in ipaddress.ip_network(f"{request[8]}/{request[9]}"):
				type_changed = True
				if request[10] != vrf:
					if vrf == 'CORE' and structura == 16:
						vrf = 'FTTX_MNG'
						search_type = 'FSW'
						structura = 71
					elif vrf == 'FTTX_MNG' and structura == 71:
						vrf = 'CORE'
						search_type = 'ACSW'
						structura = 16
		if type_changed == False:
			error_free_ip = 'Error id_121: The specified ip does not fit into the templates for uplink.'
			return error_free_ip
			
		hosts, summary = get_data(data_key['up'], data_key['model'], vrf, t)
		if 'Error' in hosts:
			return hosts		

	else:
		hosts, summary = get_data(data_key['up'], data_key['model'], vrf, t)
		if 'Error' in hosts:
			return hosts
		t.ws_send_message(f"scanning network {hosts}")
		hosts_unreacheble = ping_check(hosts)
		t.ws_send_message("define free ip")
		free_ip = get_free_ip(hosts_unreacheble, vrf, search_type, t)
		t.ws_send_message(f"selected ip: {free_ip}")
		if not free_ip:
			error_free_ip = 'Error id_103: no free ip in the network'
			t.ws_send_message(error_free_ip)
			# t.sql_update(f"insert into guspk.logs (scr_name, DEVICEID, WHO, message) values ('free_ip','Null','{user}', '{error_free_ip}');")
			return error_free_ip

	# hosts, summary = get_data(data_key['up'], data_key['model'], vrf, t)
	# if 'Error' in hosts:
	# 	return hosts
	# out_of_exp = 'insert'
	# free_ip = '10.225.2.41'
	# print (free_ip)
	# =========== =========== ===========

	# =========== Выделение Hostname ===========
	if free_ip and search_type:
		t.ws_send_message("creating hostname")
		new_hostname, error_free_ip = create_hostname(data_key['id_acds'], data_key['up'], search_type, vrf, free_ip, t)
		if 'Error' in error_free_ip:
			return error_free_ip
		t.ws_send_message(f"selected hostname: {new_hostname}")

	# =========== =========== ===========


	query = f"""SELECT MODELID, VENDORID, TYPE_ID
		FROM guspk.host_model
		WHERE DEVICEMODELNAME LIKE '{data_key['model']}'
		"""
	data_model = t.sql_select(query, 'full')
	model_id = data_model[0][0]
	vendor_id = data_model[0][1]
	type_id = data_model[0][2]


	# print (new_hostname,free_ip,serial_number,office,sd,type_id,vendor_id,model_id)
	if not data_key['sn']:
		serial_number = '-'
	else:
		serial_number = data_key['sn']

	if type_id and vendor_id and model_id:

		#INSERT IN host table
		t.ws_send_message(f"""INSERT INTO guspk.host (IPADDMGM, NETWORKNAME, MODELID, DEVICEDESCR, OFFICE, DEVICESTATUSID, SERIALNUMBER) 
						VALUES ('{free_ip}','{new_hostname}', '{model_id}', '{data_key['id_acds']} {data_key['sd']}', '{data_key['office']}', 2, '{serial_number}')""")
		deviceid = t.sql_update(f"""INSERT INTO guspk.host (IPADDMGM, NETWORKNAME, MODELID, DEVICEDESCR, OFFICE, DEVICESTATUSID, SERIALNUMBER) 
						VALUES ('{free_ip}','{new_hostname}', '{model_id}', '{data_key['id_acds']} {data_key['sd']}', '{data_key['office']}', 2, '{serial_number}')
						""")

		network = summary[0][0]
		mask = summary[0][1]
		HSI = summary[0][2]
		IPTV = summary[0][3]
		IMS = summary[0][4]
		TR069 = summary[0][5]
		MNG = summary[0][6]
		GW = summary[0][7]
		NETWORK_ID = summary[0][8]

		query = f"""SELECT (SELECT DEVICEID FROM guspk.host WHERE IPADDMGM = '{free_ip}'), an.NETWORK_ID, an.VLAN_TEMPLATE_ID
			FROM guspk.host_acsw_node an, guspk.host h
			WHERE an.DEVICEID = h.DEVICEID 
			AND h.IPADDMGM = '{data_key['up']}'"""
		print (f"def main | query: {query}")

		t.sql_connect('disconnect')
		t.sql_connect('connect')

		data_query = t.sql_select(query, 'full')
		t.sql_update(f"INSERT INTO guspk.host_logs (DEVICEID, `user`, `column`, `new`) VALUES({deviceid}, '{user}', 'ALL', 'FREE_IP');")

		if search_type == 'O':
			vlan_template_id = 206
		else:
			vlan_template_id = data_query[0][2]

		for data in data_query:
			print (f"INSERT INTO guspk.host_acsw_node (DEVICEID, NETWORK_ID, VLAN_TEMPLATE_ID) VALUES ({deviceid}, {data[1]}, {vlan_template_id});")
			t.sql_update(f"INSERT INTO guspk.host_acsw_node (DEVICEID, NETWORK_ID, VLAN_TEMPLATE_ID) VALUES ({deviceid}, {data[1]}, {vlan_template_id});")

		query = f"""SELECT an.ACSD_NODE_ID
			FROM guspk.host_acsw_node an, guspk.host h
			WHERE an.DEVICEID = h.DEVICEID 
			AND h.IPADDMGM = '{free_ip}'
			AND an.NETWORK_ID = {NETWORK_ID}"""
		data_query = t.sql_select(query, 'full')
		acsw_node_id = data_query[0][0]
		t.sql_update(f"UPDATE guspk.acds SET acsw_node_id='{acsw_node_id}' WHERE id={data_key['id_acds']};")
	else:
		error_free_ip = 'Error id_104: The model does not fit the conditions'
		t.ws_send_message(error_free_ip)
		# t.sql_update(f"insert into guspk.logs (scr_name, DEVICEID, WHO, message) values ('free_ip','Null','{user}', '{error_free_ip}');")
		return error_free_ip

	if __name__ == "__main__":
		print (f"""\n\nNUMBER SD: {data_key['sd']}\n\nIP: {free_ip}\tHostname: {new_hostname}\tvlan MNG: {MNG}
HSI: {HSI}  IPTV: {IPTV}  IMS: {IMS}  TR069: {TR069}
GW: {GW}  Mask: /{mask}\n""")

	return error_free_ip


def get_free_data(id_acds):
	# ws = create_connection("ws://10.180.7.35/ws/chat/log_free_ip/")
	t = multimodule.FastModulAut()
	t.ws_connect('chat/log_free_ip/')
	t.ws_send_message("=== START ===")
	if not id_acds:
		print(f"id_acds is Null")
		t.ws_send_message("Error id_404: id_acds is Null")
		t.ws_close()
		return 'Error id_404: id_acds is Null'

	t.sql_connect('connect')
	user = getpass.getuser()
	query = f"""SELECT a.uplink, m.DEVICEMODELNAME, a.serial, a.office, a.ticket, a.status, a.oldip, a.reason
FROM guspk.acds a, guspk.host_model m
WHERE m.MODELID = a.modelid
and a.id={id_acds};
"""

	oldip = t.sql_select(f"""SELECT oldip from guspk.acds WHERE id = {id_acds}""", 'full')

	error_free_ip = 'ok'
	data_request = t.sql_select(query, 'full')
	if data_request[0][5] == 'new' or data_request[0][5] == 'error(f)':
		data_key = {}
		data_key['up'] = data_request[0][0]
		data_key['model'] = data_request[0][1]
		data_key['sn'] = data_request[0][2]

		data_key['office'] = data_request[0][3]
		data_key['sd'] = f"{data_request[0][4]} {data_request[0][7]}"
		if oldip[0][0]:
			t.ws_send_message(f"oldip detected {oldip[0][0]}")
			data_key['freeip'] = oldip[0][0]
		data_key['id_acds'] = id_acds
		data_key['oldip'] = data_request[0][6]

		error_free_ip = main(data_key, t, error_free_ip)

		print(error_free_ip)
		# t.ws_send_message(error_free_ip)

		t.ws_send_message("=== END ===")
		# ws.close()
	else:
		error_free_ip = 'Error id_110: Status incorrect'
		t.ws_send_message(f"Error id_110: Status incorrect {data_request}")

	t.sql_connect('disconnect')
	t.ws_close()
	return error_free_ip
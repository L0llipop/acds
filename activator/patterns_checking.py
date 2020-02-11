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


def start(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

	return render(request, 'activator/patterns_checking.html')

def get_data_patterns(t, ip_address):
	query = f"""SELECT an.ACSD_NODE_ID, CONCAT(n.GW, "/", n.MASK), n.VLAN, v.HSI, v.IPTV, v.IMS, v.TR069, n.NETWORK_ID, v.VLAN_TEMPLATE_ID, (SELECT NETWORKNAME FROM guspk.host WHERE DEVICEID = top.parent), h.DEVICEID, h.IPADDMGM, h.NETWORKNAME, m.DEVICEMODELNAME
		FROM guspk.host h
		LEFT JOIN guspk.host_acsw_node an ON an.DEVICEID = h.DEVICEID
		LEFT JOIN guspk.host_model m ON h.MODELID = m.MODELID
		LEFT JOIN guspk.host_networks n ON an.NETWORK_ID = n.NETWORK_ID
		LEFT JOIN guspk.host_vlan_template v ON an.VLAN_TEMPLATE_ID = v.VLAN_TEMPLATE_ID
		LEFT JOIN guspk.topology top ON top.child = h.DEVICEID
		WHERE h.IPADDMGM = '{ip_address}' OR h.NETWORKNAME = '{ip_address}' OR h.DEVICEID = '{ip_address}';
		"""

	arr = ['ACSD_NODE_ID', 'GW', 'MNG', 'HSI', 'IPTV', 'IMS', 'TR069', 'NETWORK_ID', 'VLAN_TEMPLATE_ID', 'UPLINK']
	att = ['DEVICEID', 'IPADDMGM', 'NETWORKNAME', 'DEVICEMODELNAME']

	request_sql = t.sql_select(query, 'full')
	request = {}
	uplink = ''

	for column in request_sql:
		request[column[0]] = {}
		for n in range(1, len(arr)):
			if arr[n] == 'UPLINK':
				uplink = column[n]
			else:
				request[column[0]].update({arr[n]: column[n]})

	if request_sql and request_sql[0]:
		for i, col in enumerate(att, len(arr)):
			request[col] = request_sql[0][i]

	return request, uplink

def get_patterns(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

	group = [ x.name for x in request.user.groups.all()]
	ip_address = None

	if request.method == 'GET':
		ip_address = request.GET["ip_address"]
		match = re.search(r'^\s*(.*?)\s*$', request.GET["ip_address"]) # обрезаем пробелы в начале и конце строки
		if (match):
			ip_address = match.group(1)

	if ip_address:
		t = multimodule.FastModulAut()
		t.sql_connect('connect')

		request_all = {'group': group}
		end = ''
		nn = 1
		while True:
			request_sql, uplink = get_data_patterns(t, ip_address)
			if request_sql:
				request_all[nn] = request_sql
			nn += 1

			if request_sql and uplink:
				if uplink:
					query = f"""SELECT IPADDMGM FROM guspk.host WHERE NETWORKNAME = '{uplink}';"""
					request_sql = t.sql_select(query, 'full')
					if request_sql[0][0]:
						if ip_address != request_sql[0][0]:
							ip_address = request_sql[0][0]
						else:
							break
					else:
						break
				else:
					break
			else:
				break
			
		# count_select('patt_select_patterns', request.user.username, t)
		t.count_website(t, page='patt_select_patterns', username=request.user.username)
		t.sql_connect('disconnect')

	return JsonResponse(request_all, safe=False)

def add_pattern(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group and not 'engineers' in group:
		return render(request, 'activator/access.html')

	def check_pattern(data_pattern, t):
		query = f"""SELECT DEVICEID, NETWORK_ID, VLAN_TEMPLATE_ID
								FROM guspk.host_acsw_node 
								WHERE DEVICEID LIKE {data_pattern['device_id']} 
								AND NETWORK_ID LIKE {data_pattern['network_id']} 
								AND VLAN_TEMPLATE_ID LIKE {data_pattern['vlans_id']};
						"""
		request_sql = t.sql_select(query, 'full')
		return request_sql

	data_pattern = {
		'device_id': '',
		'network_id': '',
		'vlans_id': '',
	}

	if request.method == 'GET':
		for name in data_pattern:
			if request.GET[name]:
				data_pattern[name] = f"{request.GET[name]}"
				match = re.search(r'^\s*(.*?)\s*$', request.GET[name]) # обрезаем пробелы в начале и конце строки
				if (match):
					data_pattern[name] = f"{match.group(1)}"

	if ''.join(data_pattern.values()):
		t = multimodule.FastModulAut()
		t.sql_connect('connect')

		request_sql = check_pattern(data_pattern, t)

		if not request_sql:
			# count_select('patt_insert_pattern', request.user.username, t)
			t.count_website(t, page='patt_insert_pattern', username=request.user.username)
			t.sql_update(f"INSERT INTO guspk.host_acsw_node (DEVICEID, NETWORK_ID, VLAN_TEMPLATE_ID) VALUES ({data_pattern['device_id']}, {data_pattern['network_id']}, {data_pattern['vlans_id']});")
			request_sql = check_pattern(data_pattern, t)
			if request_sql:
				t.sql_update(f"INSERT INTO guspk.logs (scr_name, DEVICEID, WHO, message) VALUES ('patterns_checking', '{request_sql[0][0]}', '{request.user.username}', 'add device_id:{data_pattern['device_id']}, network_id:{data_pattern['network_id']}, vlans_id:{data_pattern['vlans_id']}');")
			request_all = "Ok"
		else:
			request_all = "Can not add"

		t.sql_connect('disconnect')

	return JsonResponse(request_all, safe=False)

def get_networks(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group and not 'engineers' in group:
		return render(request, 'activator/access.html')

	request_all = {}
	data_networks = {
		'netid': '',
		'mng': '',
		'vrf': '',
		'gw_net': '',
		'region': '',
	}
	columns = {
		'netid': 'NETWORK_ID',
		'mng': 'VLAN',
		'vrf': 'VRF',
		'gw_net': 'GW',
		'region': 'REGION',
	}
	if request.method == 'GET':
		for name in data_networks:
			if request.GET[name]:
				data_networks[name] = f"{request.GET[name]}"
				match = re.search(r'^\s*(.*?)\s*$', request.GET[name]) # обрезаем пробелы в начале и конце строки
				if (match):
					data_networks[name] = f"{match.group(1)}"

	if ''.join(data_networks.values()):
		t = multimodule.FastModulAut()
		t.sql_connect('connect')

		where_sql = ''
		first = 'WHERE'
		for vlan in data_networks:
			if data_networks[vlan]:
				where_sql += f"{first} {columns[vlan]} LIKE '{data_networks[vlan]}%' "
				if first == 'WHERE':
					first = 'AND'

		# count_select('patt_select_network', request.user.username, t)
		t.count_website(t, page='patt_select_network', username=request.user.username)
		query = f"""SELECT NETWORK_ID, VLAN, VRF, CONCAT(GW, "/", MASK), REGION, `DESC` FROM guspk.host_networks {where_sql} LIMIT 10;"""
		request_sql = t.sql_select(query, 'full')
		for req in request_sql:
			request_all[req[0]] = {}
			for i, name in enumerate(data_networks):
				request_all[req[0]].update({name: req[i]})
			request_all[req[0]].update({'desc': req[5]})

		t.sql_connect('disconnect')

	return JsonResponse(request_all, safe=False)

def get_vlans(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group and not 'engineers' in group:
		return render(request, 'activator/access.html')

	request_all = {}
	data_vlans = {
		'id': '',
		'hsi': '',
		'iptv': '',
		'ims': '',
		'tr069': '',
	}
	columns = {
		'id': 'VLAN_TEMPLATE_ID',
		'hsi': 'HSI',
		'iptv': 'IPTV',
		'ims': 'IMS',
		'tr069': 'TR069',
	}
	if request.method == 'GET':
		for name in data_vlans:
			if request.GET[name]:
				data_vlans[name] = f"{request.GET[name]}"
				match = re.search(r'^\s*(.*?)\s*$', request.GET[name]) # обрезаем пробелы в начале и конце строки
				if (match):
					data_vlans[name] = f"{match.group(1)}"

	if ''.join(data_vlans.values()):
		t = multimodule.FastModulAut()
		t.sql_connect('connect')

		where_sql = ''
		first = 'WHERE'
		for vlan in data_vlans:
			if data_vlans[vlan]:
				where_sql += f"{first} {columns[vlan]} LIKE '{data_vlans[vlan]}%' "
				if first == 'WHERE':
					first = 'AND'

		# count_select('patt_select_vlan', request.user.username, t)
		t.count_website(t, page='patt_select_vlan', username=request.user.username)
		query = f"""SELECT VLAN_TEMPLATE_ID, HSI, IPTV, IMS, TR069
							FROM guspk.host_vlan_template {where_sql} LIMIT 10;
						"""
		request_sql = t.sql_select(query, 'full')
		for req in request_sql:
			request_all[req[0]] = {}
			for i, name in enumerate(data_vlans):
				request_all[req[0]].update({name: req[i]})

		t.sql_connect('disconnect')

	return JsonResponse(request_all, safe=False)

def add_patterns_vlans(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group and not 'engineers' in group:
		return render(request, 'activator/access.html')

	def check_pattern_vlan(data_pattern, t):
		query = f"""SELECT VLAN_TEMPLATE_ID, HSI, IPTV, IMS, TR069
								FROM guspk.host_vlan_template 
								WHERE HSI LIKE {data_vlans['hsi']} 
								AND IPTV LIKE {data_vlans['iptv']} 
								AND IMS LIKE {data_vlans['ims']} 
								AND TR069 LIKE {data_vlans['tr069']};
						"""
		request_sql = t.sql_select(query, 'full')
		return request_sql

	data_vlans = {
		'hsi': '',
		'iptv': '',
		'ims': '',
		'tr069': '',
	}

	if request.method == 'GET':
		for name in data_vlans:
			if request.GET[name]:
				data_vlans[name] = f"{request.GET[name]}"
				match = re.search(r'^\s*(.*?)\s*$', request.GET[name]) # обрезаем пробелы в начале и конце строки
				if (match):
					data_vlans[name] = f"{match.group(1)}"

	if ''.join(data_vlans.values()):
		t = multimodule.FastModulAut()
		t.sql_connect('connect')
		request_sql = check_pattern_vlan(data_vlans, t)

		if not request_sql:
			# count_select('patt_insert_vlan', request.user.username, t)
			t.count_website(t, page='patt_insert_vlan', username=request.user.username)
			t.sql_update(f"INSERT INTO guspk.host_vlan_template (HSI, IPTV, IMS, TR069) VALUES ({data_vlans['hsi']}, {data_vlans['iptv']}, {data_vlans['ims']}, {data_vlans['tr069']});")
			request_sql = check_pattern_vlan(data_vlans, t)
			if request_sql:
				t.sql_update(f"INSERT INTO guspk.logs (scr_name, DEVICEID, WHO, message) VALUES ('patterns_checking', 'vlan_template:{request_sql[0][0]}', '{request.user.username}', 'add hsi:{data_vlans['hsi']}, iptv:{data_vlans['iptv']}, ims:{data_vlans['ims']}, tr069:{data_vlans['tr069']}');")
			request_all = "Ok"
		else:
			request_all = "Can not add"

		t.sql_connect('disconnect')

	return JsonResponse(request_all, safe=False)


# def count_select(name, user, t):
# 	count_generator = t.sql_select(f"SELECT count FROM guspk.count WHERE name = '{name}' and user = '{user}'", 'full')
# 	if count_generator:
# 		count_generator[0][0] += 1
# 		t.sql_update(f"UPDATE guspk.count SET count={count_generator[0][0]} WHERE name='{name}' and user='{user}';")
# 	else:
# 		t.sql_update(f"INSERT INTO guspk.count (name, `user`, count) VALUES('{name}', '{user}', 1);")


def delete_pattern(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group and not 'engineers' in group:
		return render(request, 'activator/access.html')

	t = multimodule.FastModulAut()
	t.sql_connect('connect')
	t.count_website(t, page='patt_delete_pattern', username=request.user.username)
	request_sql = t.sql_select(f"SELECT * FROM guspk.acds WHERE acsw_node_id={request.GET['id']};", 'full')
	if request_sql:
		t.sql_connect('disconnect')
		return JsonResponse('Error: Need to change template in Admin portal', safe=False)

	t.sql_update(f"DELETE FROM guspk.host_acsw_node WHERE ACSD_NODE_ID={request.GET['id']};")
	t.sql_connect('disconnect')

	return JsonResponse('Ok', safe=False)
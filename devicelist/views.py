from django.shortcuts import render
from django.conf import settings
from django.shortcuts import redirect
from django.core.mail import send_mail
from django.core.mail import mail_admins
from django.http import JsonResponse

import sys, os, re, time
import datetime
import jinja2
import json
import multimodule
import fias_import
import subprocess
import diff_argus_host

from acds import configuration
# import free_ip

def settings_col():
	column = {
		'ip_address'	: {'html_name':'IP',			'column_size_head':'10%',	'column_size':'7%'},
		'hostname'		: {'html_name':'hostname',		'column_size_head':'14%',	'column_size':'14%'},
		'model'			: {'html_name':'model',			'column_size_head':'8%',	'column_size':'7%'},
		'description'	: {'html_name':'Описание',		'column_size_head':'8%',	'column_size':'8%'},
		'addres'		: {'html_name':'Адрес',			'column_size_head':'23%',	'column_size':'24%'},
		'office'		: {'html_name':'Доп инфо',		'column_size_head':'8%',	'column_size':'10%'},
		'date'			: {'html_name':'date',			'column_size_head':'0%',	'column_size':'0%'},
		'status'		: {'html_name':'status',		'column_size_head':'5%',	'column_size':'0%'},
		'uplink'		: {'html_name':'uplink',		'column_size_head':'10%',	'column_size':'17%'},
		'mac'			: {'html_name':'mac',			'column_size_head':'6%',	'column_size':'6%'},
		'serial'		: {'html_name':'serial',		'column_size_head':'0%',	'column_size':'0%'},
		# 'limit'			: {'html_name':'limit',			'column_size_head':'6%',	'column_size':'6%'},
		# 'addres_node'	: {'column_name':'CITY_NAME',	'html_name':'Адрес_узла',	'column_size_head':'12%',	'column_size':'10%'},
		}
	return column

def devicelist(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

	values = {'request_column': settings_col()}
	return render(request, 'devicelist/devicelistPage.html', values)

def get_devicelist(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

	group = [ x.name for x in request.user.groups.all()]
	if 'admins' in group or 'engineers' in group:
		values = {'access': 'yes'}
	else:
		values = {'access': 'no'}

	column = settings_col()
	column_bd = {}.fromkeys(list(column.keys()),'')
	data = list(column.keys())
	# values = {}
	data_req = {}

	if request.method == 'GET':
		limit = request.GET['limit']
		if not limit:
			limit = 1000
		for col in data:
			if col == 'date' or col == 'serial':
				continue
			data_req[col] = request.GET[f'{col}']
			match = re.search(r'^\s*(.*?)\s*$', request.GET[f'{col}']) # обрезаем пробелы в начале и конце строки
			if (match):
				data_req[col] = match.group(1)

	if any(data_req.values()):
		t = multimodule.FastModulAut()
		# t.ws_connect('chat/test/')
		t.sql_connect('connect')
		t.count_website(t, page='devicelist', username=request.user.username)
		
		addres_fias = {
			'region_fias_id': '',
			'area_fias_id': '',
			'city_fias_id': '',
			'settlement_fias_id': '',
			'street_fias_id': '',
			'house_fias_id': '',
		}
		if request.GET['addres']:
			addres_fias = json.loads(request.GET['addres'])

		data_req.update(addres_fias)

		# t.ws_send_message(f"data_req: {data_req}")
		# t.ws_send_message(f"region_fias_id: {addres_fias['region_fias_id']}")



		column_name = []
		data_table_null = {
				'description':'DEVICEDESCR',
				'office':'OFFICE',
				'uplink':'UPLINK',
				'mac':'MAC', 
				'region_fias_id': 'region_fias_id',
				'area_fias_id': 'area_fias_id',
				'city_fias_id': 'city_fias_id',
				'settlement_fias_id': 'settlement_fias_id',
				'street_fias_id': 'street_fias_id',
				'house_fias_id': 'house_fias_id',
		}

		for key in data_table_null:

			table = 'h'
			if 'fias_id' in key:
				table = 'fa'

					# Если необходимо найти поля со значением null
			if data_req[key] == 'null':		
				column_name.append(f"""{table}.{data_table_null[key]} IS NULL""")

					# Если поле было заполнено какими то данными
			elif data_req[key]:
				if key == 'uplink':
					column_name.append(f"""(top.parent = (SELECT deviceid from guspk.host WHERE NETWORKNAME like '%{data_req[key]}%' or IPADDMGM like '%{data_req[key]}%'))""")
				else:
					column_name.append(f"""{table}.{data_table_null[key]} LIKE '%{data_req[key]}%'""")

					# Если поле осталось пустым
			else:
				if key == 'uplink':
					column_name.append(f"""top.parent like '%%'""")
				else:
					column_name.append(f"""{table}.{data_table_null[key]} LIKE '%%' or {table}.{data_table_null[key]} IS NULL""")


		query_astu = f"""SELECT h.DEVICEID, h.IPADDMGM, h.NETWORKNAME, hm.DEVICEMODELNAME, h.DEVICEDESCR, h.OFFICE, h.DATEMODIFY, hs.status_name, CONCAT((SELECT NETWORKNAME FROM guspk.host WHERE DEVICEID = top.parent), ' ', top.parent_port, COALESCE(CONCAT(' ← ', top.child_port), '')), h.MAC, h.SERIALNUMBER, 
					far.area_with_type, fc.city_with_type, fs.settlement_with_type, fst.street_with_type, fh.house, fh.block_type_full, fh.block, fa.geo_lat, fa.geo_lon
			FROM guspk.host h
			LEFT JOIN guspk.host_status hs ON h.DEVICESTATUSID = hs.status_id
			LEFT JOIN guspk.host_model hm ON h.MODELID = hm.MODELID
			LEFT JOIN guspk.host_fias fa ON h.DEVICEID = fa.id
			LEFT JOIN guspk.topology top ON top.child = h.DEVICEID
			LEFT JOIN guspk.fias_region fr ON fa.region_fias_id = fr.region_fias_id
			LEFT JOIN guspk.fias_area far ON fa.area_fias_id = far.area_fias_id
			LEFT JOIN guspk.fias_city fc ON fa.city_fias_id = fc.city_fias_id
			LEFT JOIN guspk.fias_settlement fs ON fa.settlement_fias_id = fs.settlement_fias_id
			LEFT JOIN guspk.fias_street fst ON fa.street_fias_id = fst.street_fias_id
			LEFT JOIN guspk.fias_house fh ON fa.house_fias_id = fh.house_fias_id
			WHERE (h.IPADDMGM LIKE '%{data_req['ip_address']}%' OR h.DEVICEID = '{data_req['ip_address']}')
			AND h.NETWORKNAME LIKE '%{data_req['hostname']}%'
			AND hm.DEVICEMODELNAME LIKE '%{data_req['model']}%'
			AND ({column_name[0]})
			AND ({column_name[1]})
			AND hs.status_name LIKE '%{data_req['status']}%'
			AND ({column_name[2]})
			AND ({column_name[3]})
				AND (({column_name[4]})
				AND ({column_name[5]})
				AND ({column_name[6]})
				AND ({column_name[7]})
				AND ({column_name[8]})
				AND ({column_name[9]}))
			ORDER BY INET_ATON(IPADDMGM)
			LIMIT {limit};
			"""

		# t.ws_send_message(f"query_astu: {query_astu}")
			
		# t.ws_send_message(f"_SELECT_")
		print(query_astu)
		request_sql = t.sql_select(query_astu, 'full')
		# t.ws_send_message(f"_END_SELECT_")
		# t.ws_send_message(f"request_sql: {request_sql}")


		for data_in_sql in request_sql:

			if data_in_sql[7] == 'Выведен из эксплуатации':
				data_in_sql[7] = 'Выведен'
			if data_in_sql[6]:
				date = data_in_sql[6].strftime("%d/%m/%y")
			else:
				date = 'Null'

			# address = None

			address = None
			for n_col in range(11,18):
				if data_in_sql[n_col]:
					if address:
						address = f"{address}; {data_in_sql[n_col]}"
					else:
						address = data_in_sql[n_col]

			# t.ws_send_message(f"address: {address}")
			ticket = data_in_sql[4]
			# if ticket:
			# 	match = re.search(r"(.*?)([1-5])\s?(\d{3})\s?(\d{3})(.*?)", ticket)
			# 	if match:
			# 		sd_tick = f"{match.group(2)}{match.group(3)}{match.group(4)}"
					
			# 		ticket = f"""{match.group(1)}<a href="http://10.180.5.39/sd/claim.php?ser_id={sd_tick}" target="HPSD">{sd_tick}</a>{match.group(5)}"""

			for i, item in enumerate(data_in_sql):
				if not item:
					data_in_sql[i] = 'Null'

			values.update({data_in_sql[1]: {'ip_address': data_in_sql[1],
								'hostname': data_in_sql[2],
								'model': data_in_sql[3],
								'ticket': ticket,
								'addres': address,
								'office': data_in_sql[5],
								'date': date,
								'status': data_in_sql[7],
								'uplink': data_in_sql[8],
								'mac': data_in_sql[9],
								'serial': data_in_sql[10],
								'id': data_in_sql[0],
								'latitude': data_in_sql[18],
								'longitude': data_in_sql[19],
								}})
			
		t.sql_connect('disconnect')
		# t.ws_close()

	return JsonResponse(values, safe=False)

def fias_data_update(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group:
		return render(request, 'devicelist/access.html')

	user = request.user.username
	t = multimodule.FastModulAut()
	values = {}
	if request.GET:
		ip = ''.join(list(request.GET.get('ip', str(False))))
		t.oracle_connect('connect', server = getattr(configuration, 'ARGUS_DB'), login = getattr(configuration, 'ARGUS_LOGIN'), password = getattr(configuration, 'ARGUS_PASS'))
		summ = t.oracle_select(f"""SELECT argus_sys.name3(ip.ip_interface_id,1,27200005), reg.REGION_TREE_NAME, reg.REGION_NAME, str.STREET_NAME, bld.HOUSE, bld.CORPUS, (SELECT REGION_NAME FROM ARGUS_SYS.REGION_L x WHERE x.OBJECT_ID = reg.PARENT_ID) AS region,
		        i.host_name,
		        i.title,
		        e.ENTITY_NAME model
		from ip_.ip_interface ip
		       join argus_sys.network_interface ni on ni.network_interface_id=ip.ip_interface_id
		       join argus_sys.connection_unit cu on ni.node_id=cu.node_id
		       join argus_sys.connection_point cp on cp.cu_id=cu.connection_unit_id
		       JOIN argus_sys.NODE node on ni.NODE_ID=node.NODE_ID
		       JOIN argus_sys.REGION_L reg on reg.OBJECT_ID=node.REGION_ID
		       JOIN argus_sys.BUILDING_L bld ON bld.OBJECT_ID=node.BUILDING_ID
		       JOIN argus_sys.STREET_L str ON bld.STREET_ID=str.OBJECT_ID
		       JOIN ip_.ip_logical_node i on i.ip_logical_node_id=node.node_id
		       join argus_sys.entity e on node.entity_id=e.entity_id
		where argus_sys.name3(ip.ip_interface_id,1,27200005) LIKE '{ip}'
		GROUP BY argus_sys.name3(ip.ip_interface_id,1,27200005), reg.REGION_TREE_NAME, reg.REGION_NAME, str.STREET_NAME, bld.HOUSE, bld.CORPUS, reg.PARENT_ID, i.host_name, i.title, e.ENTITY_NAME""")
		t.oracle_connect('disconnect')
		if summ:
			address = f"{summ[0][6]} {summ[0][2]} {summ[0][3]} {summ[0][4]} {summ[0][5]}"
			# print(address)
			answer = fias_import.fias_data_check(summ[0], source = "db")
			values.update({'answer': answer, 'address': address})
		else:
			values.update({'answer': 'error, not found address in argus'})

	return JsonResponse(values, safe=False)


def device_update(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'engineers' in group and not 'admins' in group:
		return render(request, 'devicelist/access.html')

	user = request.user.username
	t = multimodule.FastModulAut()
	# t.ws_connect('chat/device_update/')
	values = {}
	if request.GET:
		all_data = json.loads(request.GET['all_data'])
		print(f"device_update|all_data: {all_data}")
		t.sql_connect('connect')
		t.count_website(t, page='device_update', username=request.user.username)
		# t.sql_update(f"INSERT INTO guspk.logs (scr_name, DEVICEID, WHO, message) values ('device_update','{all_data['id']}','{user}', '{all_data['ip']}|{all_data['hostname']}|{all_data['model']}|{all_data['description']}|{all_data['addres']}|{all_data['info']}|{all_data['status']}|{all_data['mac']}|{all_data['serial']}');")
		# t.ws_send_message(f"all_data: {all_data}")
		values = {'status': 'ok', 'message': None}

		# keys = ['ip', 'hostname', 'model', 'description', 'addres', 'info', 'status', 'uplink', 'port', 'mac']
		if not all_data.get('id'):
			values['status'] = "Error"
			values['message'] = f"Deviceid not found"
			return JsonResponse(values, safe=False)

		query_astu = f"""SELECT h.IPADDMGM, h.NETWORKNAME, hm.DEVICEMODELNAME, h.DEVICEDESCR, h.OFFICE, hs.status_name, h.MAC, h.SERIALNUMBER, 
					far.area_with_type, fc.city_with_type, fs.settlement_with_type, fst.street_with_type, fh.house, fh.block_type_full, fh.block,
					(SELECT NETWORKNAME FROM guspk.host WHERE DEVICEID = top.parent), top.parent_port, top.child_port
			FROM guspk.host h
			LEFT JOIN guspk.host_status hs ON h.DEVICESTATUSID = hs.status_id
			LEFT JOIN guspk.host_model hm ON h.MODELID = hm.MODELID
			LEFT JOIN guspk.host_fias fa ON h.DEVICEID = fa.id
			LEFT JOIN guspk.fias_region fr ON fa.region_fias_id = fr.region_fias_id
			LEFT JOIN guspk.fias_area far ON fa.area_fias_id = far.area_fias_id
			LEFT JOIN guspk.fias_city fc ON fa.city_fias_id = fc.city_fias_id
			LEFT JOIN guspk.fias_settlement fs ON fa.settlement_fias_id = fs.settlement_fias_id
			LEFT JOIN guspk.fias_street fst ON fa.street_fias_id = fst.street_fias_id
			LEFT JOIN guspk.fias_house fh ON fa.house_fias_id = fh.house_fias_id
			LEFT JOIN guspk.topology top ON top.child = h.DEVICEID
			WHERE h.DEVICEID = {all_data['id']};
			"""

		# request_sql = t.sql_select(f"SELECT h.IPADDMGM FROM guspk.host h WHERE h.DEVICEID = 103579", 'full')
		request_sql = t.sql_select(query_astu, 'full')
		print(f"device_update|request_sql: {request_sql}")
		# t.ws_send_message(f"request_sql: {request_sql}")

		address = None
		for n_col in range(8,15):
			if request_sql[0][n_col]:
				if address:
					address = f"{address}; {request_sql[0][n_col]}"
				else:
					address = request_sql[0][n_col]

		for i, item in enumerate(request_sql[0]):
			if not item:
				request_sql[0][i] = 'Null'

		print(f"device_update|address: {address}")
		
		#dict of all values received from DB
		sql_hesh = {
			'ip': request_sql[0][0],
			'hostname': request_sql[0][1],
			'model': request_sql[0][2],
			'description': request_sql[0][3],
			'info': request_sql[0][4],
			'status': request_sql[0][5],
			'mac': request_sql[0][6],
			'serial': request_sql[0][7],
			'addres': address,
			'uplink': request_sql[0][15],
			'port': request_sql[0][16],
			'port_uplink': request_sql[0][17],
		}

		sql_col = {
			'ip': 'IPADDMGM',
			'hostname': 'NETWORKNAME',
			'model': 'MODELID',
			'description': 'DEVICEDESCR',
			'info': 'OFFICE',
			'status': 'DEVICESTATUSID',
			'mac': 'MAC',
			'serial': 'SERIALNUMBER',
			'addres': 'None',
			'uplink': 'None',
			'port': 'None',
			'port_uplink': 'None',
		}

		#diff between db and web
		for key in sql_hesh:
			if all_data[key] == sql_hesh[key]:
				pass
				# t.ws_send_message(f"{key}: {all_data[key]} == {sql_hesh[key]}")

			else:
				# t.ws_send_message(f"{key}: {all_data[key]} != {sql_hesh[key]}")
				if all_data[key] == 'Null':
					all_data[key] = 'None'

				if key == 'ip':
					ipaddmgm = t.sql_select(f"SELECT IPADDMGM, DEVICEID FROM guspk.host WHERE IPADDMGM = '{all_data['ip']}'", 'full')
					if ipaddmgm:
						values['status'] = "Error"
						values['message'] = f"This IP '{ipaddmgm[0][0]}' занят, ID {ipaddmgm[0][1]}"
						break
					else:
						t.sql_update(f"UPDATE guspk.host SET IPADDMGM = '{all_data['ip']}' WHERE DEVICEID = '{all_data['id']}'")

				if key == 'hostname':
					networkname = t.sql_select(f"SELECT NETWORKNAME, DEVICEID FROM guspk.host WHERE NETWORKNAME = '{all_data['hostname']}'", 'full')
					if networkname == {all_data['hostname']}:
						values['status'] = "Error"
						values['message'] = f"This Hostname '{networkname[0][0]}' занят, ID {networkname[0][1]}"
						break
					else:
						t.sql_update(f"""UPDATE guspk.host SET NETWORKNAME = '{all_data['hostname']}' WHERE DEVICEID = '{all_data['id']}'""")

				if key == 'model':
					t.sql_update(f"""UPDATE guspk.host h
									INNER JOIN guspk.host_model m on m.MODELID = h.MODELID 
									SET h.MODELID = (SELECT MODELID from guspk.host_model where DEVICEMODELNAME = '{all_data['model']}')
									WHERE h.DEVICEID = '{all_data['id']}' """)

				if key == 'description':
					t.sql_update(f"""UPDATE guspk.host SET DEVICEDESCR = "{all_data['description']}" WHERE DEVICEID = '{all_data['id']}'""")

				if key == 'info':
					t.sql_update(f"""UPDATE guspk.host SET OFFICE = "{all_data['info']}" WHERE DEVICEID = '{all_data['id']}'""")

				if key == 'serial':
					t.sql_update(f"""UPDATE guspk.host SET SERIALNUMBER = "{all_data['serial']}" WHERE DEVICEID = '{all_data['id']}'""")

				if key == 'status':
					status_id = t.sql_select(f"SELECT status_id FROM guspk.host_status WHERE status_name LIKE '{all_data['status']}%'", 'full')
					if status_id:
						t.sql_update(f"""UPDATE guspk.host SET DEVICESTATUSID = '{status_id[0][0]}' WHERE DEVICEID = '{all_data['id']}'""")

				if key == 'mac':
					mac = t.sql_select(f"SELECT MAC, DEVICEID FROM guspk.host WHERE MAC = '{all_data['mac']}'", 'full')
					if mac:
						values['status'] = "Error"
						values['message'] = f"Данный Mac '{mac[0][0]}' занят, ID {mac[0][1]}"
						break
					else:
						t.sql_update(f"""UPDATE guspk.host SET MAC = '{all_data['mac']}' WHERE DEVICEID = '{all_data['id']}'""")

				if key == 'addres':
					if all_data['addres'] != 'null':
						t.sql_update(f"DELETE FROM guspk.host_fias WHERE id={all_data['id']};")
						t.sql_connect('disconnect')
						t.sql_connect('connect')
						device_info = {'id': all_data['id'], 'address': all_data['addres'], 'dest': 'host_fias'}
						# t.ws_send_message(f"device_info: {device_info}")
						fias_import.host_fias_insert(device_info)
						# t.ws_send_message(f"INSERT INTO guspk.host_logs (DEVICEID, `user`, `column`, `old`, `new`) VALUES({all_data['id']}, '{user}', 'addres_fias', '{sql_hesh['addres']}', '{all_data['addres']}');")
						t.sql_update(f"INSERT INTO guspk.host_logs (DEVICEID, `user`, `column`, `old`, `new`) VALUES({all_data['id']}, '{user}', 'addres_fiass', '{sql_hesh['addres']}', '{all_data['addres']}');")
					continue

				if key == 'uplink':
					if all_data['uplink'] != 'null':
						device_id = t.sql_select(f"""SELECT DEVICEID FROM guspk.host 
												WHERE DEVICEID = '{all_data['uplink']}' 
												OR IPADDMGM = '{all_data['uplink']}' 
												OR NETWORKNAME = '{all_data['uplink']}'""", 'full')
						if device_id:
							device_id = device_id[0][0]
							child = t.sql_select(f"SELECT child FROM guspk.topology WHERE child = {all_data['id']}", 'full')
							if child:
								t.sql_update(f"UPDATE guspk.topology SET parent={device_id} WHERE child={all_data['id']};")
							else:
								t.sql_update(f"INSERT INTO guspk.topology (child, parent, child_port, parent_port) VALUES({all_data['id']}, {device_id}, NULL, NULL);")

							t.sql_update(f"INSERT INTO guspk.host_logs (DEVICEID, `user`, `column`, `old`, `new`) VALUES({all_data['id']}, '{user}', 'parent', '{sql_hesh[key]}', '{all_data[key]}');")
					if not all_data['uplink']:
						t.sql_update(f"""DELETE from guspk.topology WHERE child = {all_data['id']}""")
					continue

				if key == 'port':
					if all_data['port'] != 'null':
						child = t.sql_select(f"SELECT child FROM guspk.topology WHERE child = {all_data['id']}", 'full')
						if child:
							t.sql_update(f"UPDATE guspk.topology SET parent_port='{all_data['port']}' WHERE child={all_data['id']};")
							t.sql_update(f"""INSERT INTO guspk.host_logs (DEVICEID, `user`, `column`, `old`, `new`) 
											VALUES ({all_data['id']}, '{user}', 'parent_port', '{sql_hesh[key]}', '{all_data[key]}');""")
					continue

				if key == 'port_uplink':
					if all_data['port_uplink'] != 'null':
						child = t.sql_select(f"SELECT child FROM guspk.topology WHERE child = {all_data['id']}", 'full')
						if child:
							t.sql_update(f"UPDATE guspk.topology SET child_port='{all_data['port_uplink']}' WHERE child={all_data['id']};")
							t.sql_update(f"""INSERT INTO guspk.host_logs (DEVICEID, `user`, `column`, `old`, `new`) 
											VALUES ({all_data['id']}, '{user}', 'child_port', '{sql_hesh[key]}', '{all_data[key]}');""")
					continue

				# t.sql_update(f"UPDATE guspk.host SET {sql_col[key]} = '{all_data[key]}' WHERE DEVICEID = {all_data['id']};")
				t.sql_update(f"""INSERT INTO guspk.host_logs (DEVICEID, `user`, `column`, `old`, `new`) 
				VALUES ({all_data['id']}, '{user}', '{sql_col[key]}', '{sql_hesh[key]}', '{all_data[key]}');""")

		t.sql_connect('disconnect')


	# t.ws_close()
	return JsonResponse(values, safe=False)



def device_add(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'engineers' in group and not 'admins' in group:
		return render(request, 'devicelist/access.html')

	user = request.user.username
	t = multimodule.FastModulAut()
	# t.ws_connect('chat/device_update/')
	values = {}
	if request.GET:
		all_data = json.loads(request.GET['all_data'])
		t.sql_connect('connect')
		t.count_website(t, page='device_add', username=request.user.username)
		# t.ws_send_message(f"all_data: {all_data}")
		values = {'status': 'ok', 'message': None}

		ipaddmgm = t.sql_select(f"SELECT IPADDMGM, DEVICEID FROM guspk.host WHERE IPADDMGM = '{all_data['ip']}'", 'full')
		if ipaddmgm:
			values['status'] = "Error"
			values['message'] = f"Данный IP '{ipaddmgm[0][0]}' занят, ID {ipaddmgm[0][1]}"
			return JsonResponse(values, safe=False)

		networkname = t.sql_select(f"SELECT NETWORKNAME, DEVICEID FROM guspk.host WHERE NETWORKNAME = '{all_data['hostname']}'", 'full')
		if networkname:
			values['status'] = "Error"
			values['message'] = f"Данный Hostname '{networkname[0][0]}' занят, ID {networkname[0][1]}"
			return JsonResponse(values, safe=False)

		model_id = t.sql_select(f"SELECT MODELID, VENDORID, TYPE_ID FROM guspk.host_model WHERE DEVICEMODELNAME = '{all_data['model']}'", 'full')
		if model_id:
			all_data['model'] = int(model_id[0][0])
			vendor = int(model_id[0][1])
			classid = int(model_id[0][2])
		else:
			values['status'] = "Error"
			values['message'] = f"Для модели '{all_data['model']}' не найден ID"
			return JsonResponse(values, safe=False)

		status_id = t.sql_select(f"SELECT status_id FROM guspk.host_status WHERE status_name = '{all_data['status']}'", 'full')
		if status_id:
			all_data['status'] = int(status_id[0][0])
		else:
			values['status'] = "Error"
			values['message'] = f"Для статуса '{all_data['model']}' не найден ID"
			return JsonResponse(values, safe=False)


		deviceid = t.sql_update(f"""INSERT INTO guspk.host (IPADDMGM, NETWORKNAME, MODELID, DEVICEDESCR, OFFICE, DEVICESTATUSID, SERIALNUMBER) 
									VALUES ('{all_data['ip']}', '{all_data['hostname']}', '{all_data['model']}', '{all_data['description']}', '{all_data['info']}', {all_data['status']}, '{all_data['serial']}')""")
		if deviceid:
			device_info = {'id': deviceid, 'address': all_data['addres'], 'dest': 'host_fias'}
			fias_import.host_fias_insert(device_info)
		else:
			values['status'] = "Error"
			values['message'] = "ID не найден"

		t.sql_update(f"INSERT INTO guspk.host_logs (DEVICEID, `user`, `column`, `new`) VALUES({deviceid}, '{user}', 'ALL', '{all_data['ip']} added');")
		t.sql_connect('disconnect')

	return JsonResponse(values, safe=False)

def topology(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

	return render(request, 'devicelist/topology.html')

def argus_sync(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

	values = diff_argus_host.guspk_sync()

	return render(request, 'devicelist/diff_argus_host.html', values)
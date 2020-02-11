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
import astu_data
import subprocess
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

					# Есди поле было заполнено какими то данными
			elif data_req[key]:														
				column_name.append(f"""{table}.{data_table_null[key]} LIKE '%{data_req[key]}%'""")

					# Если поле остальсь пустым
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
				AND ({column_name[9]})
			)
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
			if ticket:
				match = re.search(r"(.*?)([1-5])\s?(\d{3})\s?(\d{3})(.*?)", ticket)
				if match:
					sd_tick = f"{match.group(2)}{match.group(3)}{match.group(4)}"
					
					ticket = f"""{match.group(1)}<a href="http://10.180.5.39/sd/claim.php?ser_id={sd_tick}" target="HPSD">{sd_tick}</a>{match.group(5)}"""

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
		t.oracle_connect('connect', server = "10.184.67.7:1521/DESIGNER", login = "T_BORISOV-SV_", password = "ghj&&832$$--+GG")
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
			values['message'] = f"Небыл передан ID"
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

		if sql_hesh['status'] == 'Выведен из эксплуатации':
			sql_hesh['status'] = 'Выведен'


		model = all_data['model']
		astu_data_dic = {'update': {}}
		for key in sql_hesh:
			if all_data[key] == sql_hesh[key]:
				pass
				# t.ws_send_message(f"{key}: {all_data[key]} == {sql_hesh[key]}")

			else:
				# t.ws_send_message(f"{key}: {all_data[key]} != {sql_hesh[key]}")
				if all_data[key] == 'Null':
					all_data[key] = 'None'

				astu_data_dic['update']['ip'] = all_data['ip']
				if key == 'ip':
					ipaddmgm = t.sql_select(f"SELECT IPADDMGM, DEVICEID FROM guspk.host WHERE IPADDMGM = '{all_data['ip']}'", 'full')
					if ipaddmgm:
						values['status'] = "Error"
						values['message'] = f"This IP '{ipaddmgm[0][0]}' занят, ID {ipaddmgm[0][1]}"
						del astu_data_dic['update']['ip']
						break

				if key == 'hostname':
					networkname = t.sql_select(f"SELECT NETWORKNAME, DEVICEID FROM guspk.host WHERE NETWORKNAME = '{all_data['hostname']}'", 'full')
					if networkname == {all_data['hostname']}:
						values['status'] = "Error"
						values['message'] = f"This Hostname '{networkname[0][0]}' занят, ID {networkname[0][1]}"
						break
					astu_data_dic['update']['hostname'] = all_data['hostname']

				if key == 'model':
					model_id = t.sql_select(f"SELECT MODELID, VENDORID, TYPE_ID FROM guspk.host_model WHERE DEVICEMODELNAME = '{all_data['model']}'", 'full')
					if model_id:
						all_data['model'] = int(model_id[0][0])
						astu_data_dic['update']['model'] = model_id[0][0]
						astu_data_dic['update']['vendor'] = model_id[0][1]
						astu_data_dic['update']['classid'] = model_id[0][2]

				if key == 'description':
					astu_data_dic['update']['sd'] = all_data['description']

				if key == 'info':
					astu_data_dic['update']['office'] = all_data['info']

				if key == 'serial':
					astu_data_dic['update']['serial'] = all_data['serial']

				if key == 'status':
					status_id = t.sql_select(f"SELECT status_id FROM guspk.host_status WHERE status_name LIKE '{all_data['status']}%'", 'full')
					if status_id:
						all_data[key] = status_id[0][0]
						astu_data_dic['update']['status'] = int(status_id[0][0])

				if key == 'mac':
					mac = t.sql_select(f"SELECT MAC, DEVICEID FROM guspk.host WHERE MAC = '{all_data['mac']}'", 'full')
					if mac:
						values['status'] = "Error"
						values['message'] = f"Данный Mac '{mac[0][0]}' занят, ID {mac[0][1]}"
						break

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
						device_id = t.sql_select(f"SELECT DEVICEID FROM guspk.host WHERE DEVICEID = '{all_data['uplink']}' OR IPADDMGM = '{all_data['uplink']}' OR NETWORKNAME = '{all_data['uplink']}'", 'full')
						if device_id:
							device_id = device_id[0][0]
							child = t.sql_select(f"SELECT child FROM guspk.topology WHERE child = {all_data['id']}", 'full')
							if child:
								t.sql_update(f"UPDATE guspk.topology SET parent={device_id} WHERE child={all_data['id']};")
							else:
								t.sql_update(f"INSERT INTO guspk.topology (child, parent, child_port, parent_port) VALUES({all_data['id']}, {device_id}, NULL, NULL);")

							t.sql_update(f"INSERT INTO guspk.host_logs (DEVICEID, `user`, `column`, `old`, `new`) VALUES({all_data['id']}, '{user}', 'parent', '{sql_hesh[key]}', '{all_data[key]}');")
					continue

				if key == 'port':
					if all_data['port'] != 'null':
						child = t.sql_select(f"SELECT child FROM guspk.topology WHERE child = {all_data['id']}", 'full')
						if child:
							t.sql_update(f"UPDATE guspk.topology SET parent_port='{all_data['port']}' WHERE child={all_data['id']};")
							t.sql_update(f"INSERT INTO guspk.host_logs (DEVICEID, `user`, `column`, `old`, `new`) VALUES({all_data['id']}, '{user}', 'parent_port', '{sql_hesh[key]}', '{all_data[key]}');")
					continue

				if key == 'port_uplink':
					if all_data['port_uplink'] != 'null':
						child = t.sql_select(f"SELECT child FROM guspk.topology WHERE child = {all_data['id']}", 'full')
						if child:
							t.sql_update(f"UPDATE guspk.topology SET child_port='{all_data['port_uplink']}' WHERE child={all_data['id']};")
							t.sql_update(f"INSERT INTO guspk.host_logs (DEVICEID, `user`, `column`, `old`, `new`) VALUES({all_data['id']}, '{user}', 'child_port', '{sql_hesh[key]}', '{all_data[key]}');")
					continue

				# t.ws_send_message(f"UPDATE guspk.host SET {sql_col[key]}='{all_data[key]}' WHERE DEVICEID={all_data['id']};")
				# t.ws_send_message(f"INSERT INTO guspk.host_logs (DEVICEID, `user`, `column`, `old`, `new`) VALUES({all_data['id']}, '{user}', '{sql_col[key]}', '{sql_hesh[key]}', '{all_data[key]}');")
				t.sql_update(f"UPDATE guspk.host SET {sql_col[key]}='{all_data[key]}' WHERE DEVICEID={all_data['id']};")
				t.sql_update(f"INSERT INTO guspk.host_logs (DEVICEID, `user`, `column`, `old`, `new`) VALUES({all_data['id']}, '{user}', '{sql_col[key]}', '{sql_hesh[key]}', '{all_data[key]}');")
				# t.sql_update(f"INSERT INTO guspk.count (name, `user`, count) VALUES('devicelist', '{user}', 1);")

		# t.ws_send_message(f"values: {values}")
		# t.ws_send_message(f"astu_data_dic: {astu_data_dic['update']}")
		if astu_data_dic['update'].get('ip'):

			olt  = [1771,2752,2774,2812,2829,2880,3075,3098,3100,3101,3189,3229]
			fttb = [1270,1272,1297,1304,1305,1345,1788,2365,2742,2750,2753,2754,2755,2758,2759,2763,2766,2767,2834,2839,2847,2867,2884,2887,2903,2939,2974,3006,3020,3022,3024,3055,3078,3086,3112,3113,3115,3124,3125,3133,3134,3136,3137,3138,3142,3148,3149,3150,3152,3158,3159,3161,3162,3163,3164,3165,3166,3167,3168,3169,3176,3180,3181,3182,3183,3184,3185,3187,3195,3196,3197,3198,3199,3200,3202,3204,3205,3217,3219,3222,3224,3225,3226,3231,3232,3233,3234,3235,3236,3239,3240,3242,3245,3247,3248,3249,3250,3253,3254,3255,3256,3257,3258,3259,3260,3262,3263,3264,3265,3269,3273,3276,3278,3279,3281,3282,3283,3286,3288,3291,3295,3302,3303,3304,3305,3306,3308,3309,3310]
			adsl = [1451,1455,1458,1460,1461,1464,1472,1473,1479,1482,1487,1491,1492,1499,1504,1505,1507,1509,1511,1518,1519,1521,1523,1690,1691,1709,1712,1713,1723,1724,1750,1767,1768,2788,2789,2797,2810,2815,2831,2832,2853,2855,2856,2857,2868,2870,2883,3103,3147,3175,3228,3268,3292,3293]
			acsw = [1101,1102,1104,1105,1111,1113,1120,1121,1123,1125,1149,1166,1181,1182,1202,1204,1249,1255,1257,1274,1278,1279,1280,1282,1284,1286,1288,1290,1291,1296,1300,1307,1322,1335,1337,1344,1346,1348,1353,1359,1366,1367,1377,1393,1395,1397,1402,1414,1415,1430,1445,1537,1554,1571,1599,1602,1605,1609,1614,1657,1701,1707,1721,1778,1779,1791,1815,1816,1817,1819,1820,1821,1834,1843,1848,2364,2366,2376,2377,2378,2379,2380,2382,2383,2727,2734,2735,2738,2743,2764,2769,2770,2779,2780,2784,2785,2786,2830,2844,2848,2882,2891,2894,2904,2905,2926,2946,2949,2953,2970,2971,2973,2997,3005,3017,3019,3021,3023,3027,3036,3037,3041,3046,3047,3052,3087,3088,3089,3102,3109,3110,3111,3120,3123,3134,3145,3153,3155,3156,3160,3190,3191,3192,3194,3208,3209,3211,3212,3213,3216,3218,3220,3221,3237,3243,3244,3246,3252,3272,3274,3290,3301]

			if type(all_data['model']) == int:
				if all_data['model'] in fttb:
					astu_data_dic['update']['structura'] = 71
				elif all_data['model'] in olt:
					astu_data_dic['update']['structura'] = 218
				elif all_data['model'] in adsl:
					astu_data_dic['update']['structura'] = 64
				elif all_data['model'] in acsw:
					astu_data_dic['update']['structura'] = 16
				else:
					values['status'] = "Error"
					values['message'] = f"Для данной модели '{model}' {all_data['model']} не указан ID структуры"
					# t.ws_send_message(f"ERROR")
					# t.sql_update(f"insert into guspk.logs (scr_name, DEVICEID, WHO, message) values ('free_ip','Null','{user}', '{error_free_ip}');")

			if values['status'] == 'ok':
				# t.ws_send_message(f"START: astu_data_dic")
				res = astu_data.main(astu_data_dic)

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

		if all_data['status'] == 'Выведен':
			all_data['status'] = 'Выведен из эксплуатации'
		status_id = t.sql_select(f"SELECT status_id FROM guspk.host_status WHERE status_name = '{all_data['status']}'", 'full')
		if status_id:
			all_data['status'] = int(status_id[0][0])
		else:
			values['status'] = "Error"
			values['message'] = f"Для статуса '{all_data['model']}' не найден ID"
			return JsonResponse(values, safe=False)
		t.sql_connect('disconnect')
		# return JsonResponse(values, safe=False)

		olt  = [1771,2752,2774,2812,2829,2880,3075,3098,3100,3101,3189,3229]
		fttb = [1270,1272,1297,1304,1305,1345,1788,2365,2742,2750,2753,2754,2755,2758,2759,2763,2766,2767,2834,2839,2847,2867,2884,2887,2903,2939,2974,3006,3020,3022,3024,3055,3078,3086,3112,3113,3115,3124,3125,3133,3134,3136,3137,3138,3142,3148,3149,3150,3152,3158,3159,3161,3162,3163,3164,3165,3166,3167,3168,3169,3176,3180,3181,3182,3183,3184,3185,3187,3195,3196,3197,3198,3199,3200,3202,3204,3205,3217,3219,3222,3224,3225,3226,3231,3232,3233,3234,3235,3236,3239,3240,3242,3245,3247,3248,3249,3250,3253,3254,3255,3256,3257,3258,3259,3260,3262,3263,3264,3265,3269,3273,3276,3278,3279,3281,3282,3283,3286,3288,3291,3295,3302,3303,3304,3305,3306,3308,3309,3310]
		adsl = [1451,1455,1458,1460,1461,1464,1472,1473,1479,1482,1487,1491,1492,1499,1504,1505,1507,1509,1511,1518,1519,1521,1523,1690,1691,1709,1712,1713,1723,1724,1750,1767,1768,2788,2789,2797,2810,2815,2831,2832,2853,2855,2856,2857,2868,2870,2883,3103,3147,3175,3228,3268,3292,3293]
		acsw = [1101,1102,1104,1105,1111,1113,1120,1121,1123,1125,1149,1166,1181,1182,1202,1204,1249,1255,1257,1274,1278,1279,1280,1282,1284,1286,1288,1290,1291,1296,1300,1307,1322,1335,1337,1344,1346,1348,1353,1359,1366,1367,1377,1393,1395,1397,1402,1414,1415,1430,1445,1537,1554,1571,1599,1602,1605,1609,1614,1657,1701,1707,1721,1778,1779,1791,1815,1816,1817,1819,1820,1821,1834,1843,1848,2364,2366,2376,2377,2378,2379,2380,2382,2383,2727,2734,2735,2738,2743,2764,2769,2770,2779,2780,2784,2785,2786,2830,2844,2848,2882,2891,2894,2904,2905,2926,2946,2949,2953,2970,2971,2973,2997,3005,3017,3019,3021,3023,3027,3036,3037,3041,3046,3047,3052,3087,3088,3089,3102,3109,3110,3111,3120,3123,3134,3145,3153,3155,3156,3160,3190,3191,3192,3194,3208,3209,3211,3212,3213,3216,3218,3220,3221,3237,3243,3244,3246,3252,3272,3274,3290,3301]

		if all_data['model'] in fttb:
			structura = 71
		elif all_data['model'] in olt:
			structura = 218
		elif all_data['model'] in adsl:
			structura = 64
		elif all_data['model'] in acsw:
			structura = 16
		else:
			values['status'] = "Error"
			values['message'] = f"Для данной модели '{model}' {all_data['model']} не указан ID структуры"
			return JsonResponse(values, safe=False)

		if re.match(r'^45-', all_data['hostname']):
			nodeid = 33294
		elif re.match(r'^59-', all_data['hostname']):
			nodeid = 33513
		elif re.match(r'^89-', all_data['hostname']):
			nodeid = 33510
		elif re.match(r'^86-', all_data['hostname']):
			nodeid = 33511
		elif re.match(r'^74-', all_data['hostname']):
			nodeid = 33512
		else:
			nodeid = 33270

		astu_data_dic = {'insert': {
			'ip': all_data['ip'],
			'hostname': all_data['hostname'],
			'model': all_data['model'],
			'vendor': vendor,
			'classid': classid,
			'sd': all_data['description'],
			'office': all_data['info'],
			'serial': all_data['serial'],
			'status': all_data['status'],
			'structura': structura,
			'uplink': nodeid,
		}}

		# t.sql_update(f"""INSERT INTO guspk.host
		# 	(IPADDMGM, NETWORKNAME, MODELID, DEVICEDESCR, OFFICE, DEVICESTATUSID, MAC, SERIALNUMBER)
		# 	VALUES('{all_data['ip']}', '{all_data['hostname']}', {all_data['model']}, '{all_data['description']}', '{all_data['info']}', {all_data['status']}, '{all_data['mac']}', '{all_data['serial']}');
		# 	""")

		res = astu_data.main(astu_data_dic)
		# values['message'] = f"{res}"
		# return JsonResponse(values, safe=False)
		if res == 'ok':

			subprocess.check_output(["python3", "/var/scripts/system/astu_check.py"], universal_newlines=True)

			t.sql_connect('connect')
			deviceid = t.sql_select(f"SELECT DEVICEID FROM guspk.host WHERE IPADDMGM = '{all_data['ip']}'", 'full')
			if deviceid:
				deviceid = deviceid[0][0]
				device_info = {'id': deviceid, 'address': all_data['addres'], 'dest': 'host_fias'}
				fias_import.host_fias_insert(device_info)
			else:
				values['status'] = "Error"
				values['message'] = "ID не найден"

			# t.sql_update(f"INSERT INTO guspk.logs (scr_name, DEVICEID, WHO, message) values ('device_update','{deviceid}','{user}', '{all_data['ip']}|{all_data['hostname']}|{all_data['model']}|{all_data['description']}|{all_data['addres']}|{all_data['info']}|{all_data['status']}|{all_data['serial']}');")
			t.sql_update(f"INSERT INTO guspk.host_logs (DEVICEID, `user`, `column`, `new`) VALUES({deviceid}, '{user}', 'ALL', '{all_data['ip']}');")
			t.sql_connect('disconnect')
		else:
			values['status'] = "Error"
			values['message'] = res


	return JsonResponse(values, safe=False)
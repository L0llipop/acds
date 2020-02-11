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

	values = {}
	column = settings_col()
	values['request_column'] = column
	return render(request, 'devicelist/devicelistPage.html', values)

def get_devicelist(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

	group = [ x.name for x in request.user.groups.all()]
	if 'admins' in group:
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

	if ''.join(data_req.values()):
		t = multimodule.FastModulAut()
		# t.ws_connect('chat/test/')
		t.sql_connect('connect')
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

		user = request.user.username
		count_generator = t.sql_select(f"SELECT count FROM guspk.count WHERE name = 'devicelist' and user = '{user}'", 'full')
		if count_generator:
			count_generator[0][0] += 1
			t.sql_update(f"UPDATE guspk.count SET count={count_generator[0][0]} WHERE name='devicelist' and user='{user}';")
		else:
			t.sql_update(f"INSERT INTO guspk.count (name, `user`, count) VALUES('devicelist', '{user}', 1);")


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


		query_astu = f"""SELECT h.DEVICEID, h.IPADDMGM, h.NETWORKNAME, hm.DEVICEMODELNAME, h.DEVICEDESCR, h.OFFICE, h.DATEMODIFY, hs.status_name, CONCAT((SELECT NETWORKNAME FROM guspk.host WHERE DEVICEID = top.parent), ' ', top.parent_port), h.MAC, h.SERIALNUMBER, 
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
		request_sql = t.sql_select(query_astu, 'full')
		# t.ws_send_message(f"_END_SELECT_")
		# t.ws_send_message(f"request_sql: {request_sql}")


		for data_in_sql in request_sql:

			if data_in_sql[7] == 'Выведен из эксплуатации':
				data_in_sql[7] = 'Выведен'
			if data_in_sql[6]:
				date = data_in_sql[6].strftime("%d/%m/%y")

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
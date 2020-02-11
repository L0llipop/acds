#!/usr/bin/python3
# -*- coding: utf-8 -*-
import mysql.connector 
import cx_Oracle
import multimodule
import datetime
import subprocess
import re

def form_sql_answer(cursor, column):
	sql_answer = {}
	for (column_list) in cursor:
		column_list = list(column_list)
		sql_answer[str(column_list[0])] = {}
		list(map(lambda x, y: sql_answer[str(column_list[0])].update({x:y}) ,list(column.keys()), column_list))
	return sql_answer

def astu_data_select(query, what_to_do, column=None):
	cursor = m.oracle_select(query)
	if what_to_do == 'all':
		return form_sql_answer(cursor, column)

	if what_to_do == 'who':
		name = None
		for (column_list) in cursor:
			name = list(column_list)[0]
		return name

def host_data_select(query, what_to_do, column=None):
	cursor = m.sql_select(query, 'full')
	if what_to_do == 'all':
		return form_sql_answer(cursor, column)
	return cursor

def who(what_to_do, is_like, astu_id):
	who_template = """SELECT USERNAME
	FROM ASTU.STU_AUDIT
	WHERE AUDIT_EVENT LIKE '{}'
	AND TABLENAME LIKE 'device'
	AND NEW_VALUE {}
	AND ROW_ID LIKE '{}'
	"""
	query = who_template.format(what_to_do, is_like, astu_id)
	# print (query)
	return astu_data_select(query, 'who')

def host_update(what_to_do, value, name_column, table):
	astu_id = value[0]
	message = f"{what_to_do.upper()}: {value[1]}"

	# Добавлено для экранирования спецсимволов
	escape_symbol = r'[\'\"\\]'
	def escape(match):
		return f"\\{match.group(0)}"

	if what_to_do == 'update':
		if type(value[1]) == str:
			value[1] = re.sub(escape_symbol, escape, value[1])

		if value[1] is None or value[1] == 'None' or not value[1]:
			is_like = 'IS NULL'
			new_valum = 'NULL'
		else:
			is_like = f"LIKE '{value[1]}'"
			new_valum = f"'{value[1]}'"

		if table == 'host':
			if name_column != 'DATEMODIFY':
				name = who(what_to_do, is_like, astu_id)

		update_template = """UPDATE guspk.{} SET {} = {} WHERE {} = '{}'"""
		query = update_template.format(table, name_column, new_valum, value[3], astu_id)
		message = f"{what_to_do.upper()} {name_column}: {value[2]} to {value[1]}"

	if what_to_do == 'insert':
		for n in range(len(value)):
			if value[n] is None or value[n] == 'None' or not value[n]:
				value[n] = 'NULL'
			else:
				if type(value[n]) == str:
					value[n] = re.sub(escape_symbol, escape, value[n])
				value[n] = f"'{value[n]}'"

		data_insert = ", ".join(name_column)
		if table == 'host':
			name = who(what_to_do, 'IS NULL', astu_id)
		
		insert_template = f"""INSERT INTO guspk.{table} ({data_insert}) VALUES ({str("{}, "*len(value))[:-2]})"""

		query = insert_template.format(*list(value))

	if what_to_do == 'delete':
		delete_template = """DELETE FROM guspk.{} WHERE {}='{}'"""
		query = delete_template.format(table, name_column, astu_id)
		name = 'system'
	
	if table == 'host':
		insert_log_template = """INSERT INTO guspk.logs (SCR_NAME, DEVICEID, WHO, MESSAGE) VALUES ('astu_check', '{}', '{}', '{}')"""
		if name_column != 'DATEMODIFY':
			query_log = insert_log_template.format(astu_id, name, message)
		

	print (f"{'host_update:':15} {query}")
	try:
		m.sql_update(query)
		if name_column != 'DATEMODIFY' and table == 'host':
			print (f"{'LOG:':15} {query_log}")
			m.sql_update(query_log)
	except mysql.connector.errors.IntegrityError as err:
		print (f"{'Error:':10} {err}")
		insert_log_template = """INSERT INTO guspk.logs (SCR_NAME, DEVICEID, WHO, MESSAGE) VALUES ('astu_check', '{}', '{}', '{}')"""
		query_log = insert_log_template.format(astu_id, name, err)
		m.sql_update(query_log)


def main(sql_answer_astu, sql_answer_host, column, tabel):
	for astu_id, data in sql_answer_astu.items():
		# print (f"ID: {astu_id}\tvendor: {data['vendor']}")
		if astu_id in sql_answer_host:
			for name_column in column:
				if name_column == 'id':
					continue
				if sql_answer_astu[astu_id][name_column] != sql_answer_host[astu_id][name_column]:
					print (f"\"{sql_answer_astu[astu_id][name_column]}\" != \"{sql_answer_host[astu_id][name_column]}\" | {type(sql_answer_astu[astu_id][name_column])} - {type(sql_answer_host[astu_id][name_column])}")
					host_update('update', [astu_id, sql_answer_astu[astu_id][name_column], sql_answer_host[astu_id][name_column], column['id']], column[name_column], tabel)
					print ()

			del sql_answer_host[astu_id]

		else:
			print (f"Добавить новую запись id: {astu_id}")
			host_update('insert', list(data.values()), list(column.values()), tabel)
			print ()

	for host_id in sql_answer_host:
		print (f"Удалить из таблицы host id: {host_id}")
		host_update('delete', [host_id, sql_answer_host[host_id]['id']], column['id'], tabel)
		print ()

m = multimodule.FastModulAut()
def start():
	m.oracle_connect('connect')
	m.sql_connect('connect')

				# Добавить к ключам словаря column дополнительную запись в виде порядкового номера, в не зависимости от размера словаря
				# list(map(lambda x, y: column[x].update({'pn':y}), column.keys(), range(len(column))))

	# Обновление таблицы вендеров
	column_vendor = {
		'id' : 'VENDORID',
		'vendor' : 'VENDORNAME',
	}

	query_astu_vendor = "SELECT VENDORID, VENDORNAME FROM ASTU.DDVENDOR"
	query_host_vendor = "SELECT VENDORID, VENDORNAME FROM guspk.host_vendor"
	sql_answer_astu_vendor = astu_data_select(query_astu_vendor, 'all', column_vendor)
	sql_answer_host_vendor = host_data_select(query_host_vendor, 'all', column_vendor)

	main(sql_answer_astu_vendor, sql_answer_host_vendor, column_vendor, 'host_vendor')
	# """"""


	# Обновление таблицы моделей
	column_model = {
		'id' : 'OBJECTMODELID',
		'model' : 'DEVICEMODELNAME',
		'vendorid' : 'VENDORID',
		'classid' : 'OBJECTCLASSID',
	}


	query_astu_model_template = """SELECT o.{0}, o.{1}, dv.{2}, o.{3}
	FROM ASTU.DDOBJECTMODEL o, ASTU.DDVENDOR dv
	WHERE o.{2} = dv.{2}
	"""
	query_astu_model = query_astu_model_template.format(*list(column_model.values()))
	column_model['id'] = 'MODELID'
	column_model['classid'] = 'TYPE_ID'
	query_host_model = f"""SELECT {', '.join(list(column_model.values()))} FROM guspk.host_model"""

	sql_answer_astu_model = astu_data_select(query_astu_model, 'all', column_model)
	sql_answer_host_model = host_data_select(query_host_model, 'all', column_model)

	main(sql_answer_astu_model, sql_answer_host_model, column_model, 'host_model')
	# """"""

	# Обновление таблицы узлов
	column_node = {
		'id' : 'NODEID',
		'name' : 'NODENAME',
		'city' : 'CITY_NAME',
		'street' : 'STREET_NAME',
		'building' : 'BUILDING',
		'statusid' : 'DEVICESTATUSID',
		'region' : 'KLADRCITYID',
	}

	# SELECT n.NODEID, n.NODENAME, kc.CITY_NAME, ks.STREET_NAME, n.BUILDING, ns.DEVICESTATUSID, CAST(SUBSTR (n.KLADRCITYID, 1, 2) AS int)
	# FROM ASTU.NODE n, ASTU.KLADR_CITY kc, ASTU.KLADR_STREET ks, ASTU.DDNODESTATUS ns
	# WHERE n.KLADRCITYID = kc.CITY_CODE
	# AND n.KLADRSTREETID = ks.STREET_CODE
	# AND n.NODESTATUS = ns.DEVICESTATUSID

	query_astu_node_template = """SELECT n.{0}, n.{1}, kc.{2}, ks.{3}, n.{4}, ns.{5}, CAST(SUBSTR (n.{6}, 1, 2) AS int)
	FROM ASTU.NODE n, ASTU.KLADR_CITY kc, ASTU.KLADR_STREET ks, ASTU.DDNODESTATUS ns
	WHERE n.KLADRCITYID = kc.CITY_CODE
	AND n.KLADRSTREETID = ks.STREET_CODE
	AND n.NODESTATUS = ns.DEVICESTATUSID"""
	query_astu_node = query_astu_node_template.format(*list(column_node.values()))

	column_node['region'] = 'REGION'
	query_host_node = f"""SELECT {', '.join(list(column_node.values()))} FROM guspk.host_node"""

	sql_answer_astu_node = astu_data_select(query_astu_node, 'all', column_node)
	sql_answer_host_node = host_data_select(query_host_node, 'all', column_node)

	main(sql_answer_astu_node, sql_answer_host_node, column_node, 'host_node')
	# """"""


	# Обновление основной таблицы таблицы
		# Формирование зароса в базу ASTU.DEVICE и запрос
	column = {
		'id' : 'DEVICEID',
		'ip' : 'IPADDMGM',
		'hostname' : 'NETWORKNAME',
		'model' : 'OBJECTMODELID',
		'description' : 'DEVICEDESCR',
		'office' : 'OFFICE',
		'date' : 'DATEMODIFY',
		'status' : 'DEVICESTATUSID',
		'nodeid' : 'NODEID',
		'sn' : 'SERIALNUMBER',
	}

	query_astu_template = """SELECT d.{0}, d.{1}, d.{2}, d.{3}, d.{4}, d.{5}, d.{6}, s.{7}, n.{8}, d.{9}
		FROM ASTU.DEVICE d, ASTU.DDDEVICESTATUS s, ASTU.NODE n
		WHERE d.DEVICESTATUS = s.DEVICESTATUSID
		AND d.NODEID = n.NODEID
		AND (d.{2} like '45-%' 
			OR d.{2} like '72-%' 
			OR d.{2} like '59-%' 
			OR d.{2} like '74-%' 
			OR d.{2} like '86-%' 
			OR d.{2} like '89-%'
			OR d.{2} like '66-%'
			OR d.{2} like 'RRL%'
			OR d.{2} like 'ОРС%'
			OR d.{2} like 'ORS%'
			OR d.{2} like '%RGR%'
			OR d.{2} like '%-UCN%')
		AND (d.{1} LIKE '10.%' 
			or d.{1} LIKE '172.%' 
			or d.{1} LIKE '192.%'
			OR d.NETWORKNAME like '%RGR%')
		"""
	query_astu = query_astu_template.format(*list(column.values()))

	sql_answer_astu = astu_data_select(query_astu, 'all', column)
		# """"""

		# Формирование зароса в базу guspk.host и запрос
	column['model'] = 'MODELID'
	query_host = f"""SELECT {', '.join(list(column.values()))} FROM guspk.host"""	#  
	sql_answer_host = host_data_select(query_host, 'all', column)
		# """"""

		# Запуск синхронизации таблиц
	main(sql_answer_astu, sql_answer_host, column, 'host')
		# """"""
	# """"""


	m.sql_connect('disconnect')
	m.oracle_connect('disconnect')
	# subprocess.check_output(["perl", "/var/crtscript/file_formation_from_BD.pl"], universal_newlines=True)



	# для того что бы вытащить список значений ключа name в словаре column
	# column_lists = ', '.join(list(map(lambda x:str(list(column[x].values())), list(column.keys()))))
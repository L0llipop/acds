#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import mysql.connector
from mysql.connector import Error
import re
import cx_Oracle
import multimodule
import json
import requests
import time
from termcolor import colored
from multiprocessing import Pool


def host_fias_insert(device_info, request = True, **fias_data):
	t = multimodule.FastModulAut()
	if request == True:
		fias_data = t.fias_suggest(device_info['address'])
	else:
		# print(fias_data)
		fias_data = fias_data['fias_data']
	# t.ws_connect('chat/fias_import/')
	# t.ws_send_message(f"fias_data - {fias_data}")
	if fias_data != 'error':
		# for d in fias_data:
			# t.ws_send_message(f"fias_data - {d}: {fias_data[d]}")
			# print(f"error in fias_data {device_info['address']}")
			# return f"error in fias_data {device_info['address']}"
	
		region_fias_id = fias_data['region_fias_id']
		region_with_type = fias_data['region_with_type']
		region_type_full = fias_data['region_type_full']
		region = fias_data['region']
		area_fias_id = fias_data['area_fias_id']
		area_with_type = fias_data['area_with_type']
		area_type_full = fias_data['area_type_full']
		area = fias_data['area']
		city_fias_id = fias_data['city_fias_id']
		city_with_type = fias_data['city_with_type']
		city_type_full = fias_data['city_type_full']
		city = fias_data['city']
		settlement_fias_id = fias_data['settlement_fias_id']
		settlement_with_type = fias_data['settlement_with_type']
		settlement_type_full = fias_data['settlement_type_full']
		settlement = fias_data['settlement']
		street_fias_id = fias_data['street_fias_id']
		street_with_type = fias_data['street_with_type']
		street_type_full = fias_data['street_type_full']
		street = fias_data['street']
		house_fias_id = fias_data['house_fias_id']
		house_type_full = fias_data['house_type_full']
		house = fias_data['house']
		block_type_full = fias_data['block_type_full']
		block = fias_data['block']
		geo_lat = fias_data['geo_lat']
		geo_lon = fias_data['geo_lon']
		fias_id = fias_data['fias_id']
		sum_data = {}
		sum_data[device_info['id']] = {
			'region_fias_id': region_fias_id, 
			'region_with_type': region_with_type, 
			'region_type_full': region_type_full, 
			'region': region, 
			'area_fias_id': area_fias_id, 
			'area_with_type': area_with_type, 
			'area_type_full': area_type_full, 
			'area': area, 
			'city_fias_id': city_fias_id, 
			'city_with_type': city_with_type, 
			'city_type_full': city_type_full, 
			'city': city, 
			'settlement_fias_id': settlement_fias_id, 
			'settlement_with_type': settlement_with_type, 
			'settlement_type_full': settlement_type_full, 
			'settlement': settlement, 
			'street_fias_id': street_fias_id, 
			'street_with_type': street_with_type, 
			'street_type_full': street_type_full, 
			'street': street, 
			'house_fias_id': house_fias_id, 
			'house_type_full': house_type_full, 
			'house': house, 
			'block_type_full': block_type_full, 
			'block':block, 
			'geo_lat': geo_lat, 
			'geo_lon': geo_lon,
			'fias_id': fias_id,
		}
		# print (sum_data)
		
		columns = ['region_fias_id', 'area_fias_id', 'city_fias_id', 'settlement_fias_id', 'street_fias_id', 'house_fias_id', 'geo_lat', 'geo_lon', 'fias_id']
		keys = [values for values in columns if sum_data[device_info['id']][values]]
		
		db_columns = ', '.join(keys)
		db_values = '\', \''.join([sum_data[device_info['id']][values] for values in keys])
		
		# t.ws_send_message(f"db_columns: {db_columns}")
		# t.ws_send_message(f"db_values: {db_values}")
		t.sql_connect('connect')
	
		db_region = t.sql_select(f"""SELECT region_fias_id from guspk.fias_region WHERE region_fias_id like '{region_fias_id}'""", 'full')
		if not db_region and region_fias_id:
			# t.ws_send_message(f"""INSERT into guspk.fias_region (region_fias_id, region_with_type, region_type_full, region) VALUES ('{region_fias_id}', '{region_with_type}', '{region_type_full}', '{region}')""")
			t.sql_update(f"""INSERT into guspk.fias_region (region_fias_id, region_with_type, region_type_full, region) VALUES ('{region_fias_id}', '{region_with_type}', '{region_type_full}', '{region}')""")
			# print(f'{region:70}\t-\tadded to\tfias_region')
	
		db_area = t.sql_select(f"""SELECT area_fias_id from guspk.fias_area WHERE area_fias_id like '{area_fias_id}'""", 'full')
		if not db_area and area_fias_id:
			# t.ws_send_message(f"""INSERT into guspk.fias_area (area_fias_id, area_with_type, area_type_full, area) VALUES ('{area_fias_id}', '{area_with_type}', '{area_type_full}', '{area}')""")
			t.sql_update(f"""INSERT into guspk.fias_area (area_fias_id, area_with_type, area_type_full, area) VALUES ('{area_fias_id}', '{area_with_type}', '{area_type_full}', '{area}')""")
			# print(f'{area:70}\t-\tadded to\tfias_area')
	
		db_city = t.sql_select(f"""SELECT city_fias_id from guspk.fias_city WHERE city_fias_id like '{city_fias_id}'""", 'full')
		if not db_city and city_fias_id:
			# t.ws_send_message(f"""INSERT into guspk.fias_city (city_fias_id, city_with_type, city_type_full, city) VALUES ('{city_fias_id}', '{city_with_type}', '{city_type_full}', '{city}')""")
			t.sql_update(f"""INSERT into guspk.fias_city (city_fias_id, city_with_type, city_type_full, city) VALUES ('{city_fias_id}', '{city_with_type}', '{city_type_full}', '{city}')""")
			# print(f'{city:70}\t-\tadded to\tfias_city')
	
		db_settlement = t.sql_select(f"""SELECT settlement_fias_id from guspk.fias_settlement WHERE settlement_fias_id like '{settlement_fias_id}'""", 'full')
		if not db_settlement and settlement_fias_id:
			# t.ws_send_message(f"""INSERT into guspk.fias_settlement (settlement_fias_id, settlement_with_type, settlement_type_full, settlement) VALUES ('{settlement_fias_id}', '{settlement_with_type}', '{settlement_type_full}', '{settlement}')""")
			t.sql_update(f"""INSERT into guspk.fias_settlement (settlement_fias_id, settlement_with_type, settlement_type_full, settlement) VALUES ('{settlement_fias_id}', '{settlement_with_type}', '{settlement_type_full}', '{settlement}')""")
			# print(f'{settlement:70}\t-\tadded to\tfias_settlement')
	
		db_street = t.sql_select(f"""SELECT street_fias_id from guspk.fias_street WHERE street_fias_id like '{street_fias_id}'""", 'full')
		if not db_street and street_fias_id:
			# t.ws_send_message(f"""INSERT into guspk.fias_street (street_fias_id, street_with_type, street_type_full, street) VALUES ('{street_fias_id}', '{street_with_type}', '{street_type_full}', '{street}')""")
			t.sql_update(f"""INSERT into guspk.fias_street (street_fias_id, street_with_type, street_type_full, street) VALUES ('{street_fias_id}', '{street_with_type}', '{street_type_full}', '{street}')""")
			# print(f'{street:70}\t-\tadded to\tfias_street')
	
		db_house = t.sql_select(f"""SELECT house_fias_id from guspk.fias_house WHERE house_fias_id like '{house_fias_id}'""", 'full')
		if not db_house and house_fias_id:
			columns_house = ['house_fias_id', 'house_type_full', 'house', 'block_type_full', 'block']
			keys_house = [values for values in columns_house if sum_data[device_info['id']][values]]
	
			db_columns_house = ', '.join(keys_house)
			db_values_house = '\', \''.join([sum_data[device_info['id']][values] for values in keys_house])
	
			# t.ws_send_message(f"""INSERT into guspk.fias_house ({db_columns_house}) VALUES ('{db_values_house}')""")
			t.sql_update(f"""INSERT into guspk.fias_house ({db_columns_house}) VALUES ('{db_values_house}')""")
			# print(f'{house_fias_id:70}\t-\tadded to\tfias_house')
	
		t.sql_connect('disconnect')
		t.sql_connect('connect')
	
		# print(f"""INSERT into guspk.{device_info['dest']} (id, {db_columns}) VALUES ('{device_info['id']}', '{db_values}')""")
	
		# t.ws_send_message(f"""INSERT into guspk.{device_info['dest']} (id, {db_columns}) VALUES ('{device_info['id']}', '{db_values}')""")
		# print(f"{device_info['id']:10}\t-\tadded to\t{device_info['dest']}")
		t.sql_update(f"""DELETE FROM guspk.{device_info['dest']} WHERE id = {device_info['id']}""")
		t.sql_update(f"""INSERT into guspk.{device_info['dest']} (id, {db_columns}) VALUES ('{device_info['id']}', '{db_values}')""")
	
		# t.ws_send_message("Ok")
	
		# t.ws_close()
		t.sql_connect('disconnect')
	
		return 'ok'
		
	else:
		return fias_data


def fias_data_check(line, source = "csv"):
	if source == "csv":
		line = (list(line.split(';')))

	t = multimodule.FastModulAut()
	# t.ws_connect('chat/log_yuzhakov/')
	t.sql_connect('connect')

	print(line[0], line[1], line[2], line[3], line[4], line[5], line[6])
	device_info_argus = {}
	device_info_db = {}
	ip = line[0]
	address = f"{line[1]} {line[2]} {line[3]} {line[4]}"
	if line[5]:
		address = f"{address} к{line[5]}"
	db_devices = t.sql_select(f"""SELECT h.IPADDMGM, h.NETWORKNAME, m.DEVICEMODELNAME, CONCAT(COALESCE(fc.city, ''), COALESCE(fs.settlement, ''), COALESCE(CONCAT(' ул. ', fstr.street), ''), COALESCE(CONCAT(' д. ', fhouse.house), ''), COALESCE(CONCAT(' к. ', fhouse.block), '')) as address, hf.city_fias_id, hf.settlement_fias_id, hf.street_fias_id, hf.house_fias_id, h.DEVICEID, hf.geo_lat, hf.geo_lon
								FROM guspk.host h
								LEFT JOIN guspk.host_model m ON h.MODELID = m.MODELID
								LEFT JOIN guspk.host_acsw_node an ON h.DEVICEID = an.DEVICEID
								LEFT JOIN guspk.host_vlan_template vt ON an.VLAN_TEMPLATE_ID = vt.VLAN_TEMPLATE_ID 
								LEFT JOIN guspk.host_networks net ON an.NETWORK_ID = net.NETWORK_ID
								LEFT JOIN guspk.host host ON an.DEVICEID = host.DEVICEID
								LEFT JOIN guspk.host_fias hf ON hf.id = h.DEVICEID
								LEFT JOIN guspk.fias_city fc ON hf.city_fias_id = fc.city_fias_id
								LEFT JOIN guspk.fias_settlement fs ON hf.settlement_fias_id = fs.settlement_fias_id
								LEFT JOIN guspk.fias_street fstr ON hf.street_fias_id = fstr.street_fias_id
								LEFT JOIN guspk.fias_house fhouse ON hf.house_fias_id = fhouse.house_fias_id
								WHERE h.IPADDMGM like '{ip}' LIMIT 1""", 'full')
	if (db_devices):
		device_info_argus.update({'address': address})
		print(colored(f'{ip}, {address}', 'cyan'))
		# print(device_info_argus)
		fias_data = t.fias_suggest(device_info_argus['address'] , 1)
		# print(fias_data)
		if fias_data == 'error':
			# print('err')
			fias_data = t.fias_suggest(device_info_argus['address'] , 0)
			# print(fias_data)
		device_info_db.update({'city_fias_id': db_devices[0][4], 'settlement_fias_id': db_devices[0][5], 'street_fias_id': db_devices[0][6], 'house_fias_id': db_devices[0][7], 'geo_lat': db_devices[0][9], 'geo_lon': db_devices[0][10]}) #'ip': db_devices[0][0], 'hostname': db_devices[0][1], 'model': db_devices[0][2], 'address': db_devices[0][3], 
		for param in device_info_db:
			if device_info_db[param] == fias_data[param]:
				print(colored(f'\t+ {ip} {param}: {device_info_db[param]}', 'green'))
			elif not (fias_data[param]): 
				print(colored(f'\t- {ip} {db_devices[0][8]} {param}: {device_info_db[param]} - {fias_data[param]}\tпроверить адрес', 'red'))
				# t.ws_send_message(f'{ip} {db_devices[0][8]} {address} {param}: {device_info_db[param]} - {fias_data[param]}\tпроверить адрес')
				return "error, address not found in fias"
			else:
				print(colored(f'\t- {ip} {param}: {device_info_db[param]} - {fias_data[param]}', 'red'))
				t.sql_update(f"DELETE from guspk.host_fias WHERE id = {db_devices[0][8]}")
				device_info = {'id': db_devices[0][8], 'address': address, 'dest': 'host_fias'}
				host_fias_insert(device_info, False, fias_data = fias_data)
				return "updated"
	
	# t.ws_close()
	t.sql_connect('disconnect')

if __name__ == "__main__":
	print('ok')
	device_info = {'id': acds_id, 'address': address, 'dest': 'acds_fias'}
	host_fias_insert()

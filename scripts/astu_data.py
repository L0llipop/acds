#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, os, re, datetime
import getpass
import argparse
import cx_Oracle
import mysql.connector 
from mysql.connector import Error
import requests
from configparser import ConfigParser
import multimodule
from multiprocessing import Pool
from acds import configuration

def main(args_temp):
	action =  (''.join(list(args_temp.keys())))
	args = {action: {'ip': None, 'hostname': None, 'sd': None, 'uplink': None, 'office': None, 'structura': None, 'classid': None, 'vendor': None, 'model': None, 'serial': None, 'status': None}}
	for k in args_temp[action]:
		if k in args[action].keys():
			args[action].update ({
				k: args_temp[action][k],
			})

	user = getpass.getuser()
	try:
		astu_password = getattr(configuration, 'ASTU_PASS')
	except:
		print (f"add ASTU_PASSWORN in configuration file")
		sys.exit()

	os.environ['LINES'] = "100"
	os.environ['COLUMNS'] = "80"

	date_now =  (datetime.datetime.now().strftime("%d.%m.%Y"))
	nodeinfo = 'none'
	t = multimodule.FastModulAut()

	if args[action]['ip'] != None:
		ip = args[action]['ip']
	else:
		print ('Введите IP --ip')
		sys.exit()

	hostname = args[action]['hostname']
	sd = args[action]['sd']
	uplink = args[action]['uplink']
	office = args[action]['office']
	structura = args[action]['structura']
	classid = args[action]['classid']
	vendor = args[action]['vendor']
	model = args[action]['model']
	serial = args[action]['serial']
	status = args[action]['status']

	options = {}
	options[action] = {}

	t.sql_connect('connect')
	t.sql_update(f"INSERT INTO guspk.logs (scr_name, DEVICEID, who, message) VALUES ('astu_data', '{ip}', '{user}', '{action}') ")
	if model == None and action == 'insert':
		if structura != None and vendor != None:
			query = "SELECT DEVICEMODELNAME, MODELID FROM guspk.host_model WHERE TYPE_ID LIKE '{}' AND VENDORID LIKE '{}'".format(classid, vendor)
			# print (query)
			cursor = t.sql_select(query, 'full')
			print ('Available models list')
			for models in cursor:
				print ("{:25}{:5}".format(models[0], models[1]))
			sys.exit()
		else:
			print('Please select only --str and --vendor. And I show you available models list.')
			sys.exit()

	if action == 'update':
		uplink = None
		device_data = t.sql_select(f"SELECT DEVICEID FROM guspk.host WHERE IPADDMGM like '{ip}' or NETWORKNAME like '{ip}'", 'full')
		deviceid = device_data[0][0]
		if uplink != None:
			query = f"SELECT NODEID, BUILDING, NODENAME FROM guspk.host_node WHERE NODEID LIKE '{uplink}'"
		else:
			query = f"SELECT b.NODEID, b.BUILDING, b.NODENAME FROM guspk.host a, guspk.host_node b WHERE a.IPADDMGM LIKE '{ip}' AND a.NODEID = b.NODEID"
		options[action].update ({
			'id': deviceid,
			'deviceid': deviceid,
		})

	if action == 'insert':
		if uplink != None:
			query = f"SELECT NODEID, BUILDING, NODENAME FROM guspk.host_node WHERE NODEID LIKE '{uplink}'"
		else:
			print ('Input --uplink')
			sys.exit()

	# print (query)
	cursor = t.sql_select(query, 'full') 
	# print (cursor)
	t.sql_connect('disconnect')
	for (nodeid, nodebuilding, nodename) in cursor:
		nodeinfo = (nodeid, nodebuilding, nodename)
	# print (nodeinfo)
	if nodeinfo == 'none':
		print ('Uplink not founded in astu')
		sys.exit()
	options[action].update({
		'user':user, 
		'password':astu_password, 
		'ipmgm':ip, 
		'networkname':hostname, 
		'devicedescr':sd, 
		'nodeid':nodeid, 
		'nodename':nodename, 
		'parentid':nodeid, 
		'parenttype':nodeid, 
		'nodebuilding':nodebuilding, 
		'dateinstall':date_now, 
		'datazip':date_now, 
		'strukturalevelid':structura, 
		'objectclassidid':classid, 
		'objectclassid':classid, 
		'vendorid':vendor, 
		'objectmodelid':model, 
		'serialnumber':serial, 
		'devicestatus':status,
		'office':office,
	})



	if action == 'update':
		save = update(options, action)
		if save == '':
			# save = 'OK'
			print ('OK')
		else:
			print (save)
	if action == 'insert':
		save = insert(options, action)
		# print (save)
		if save == '':
			# save = 'OK'
			print ('OK')
		else:
			print (save)

	return save


def update(options, action):
	logpass = {}
	logpass['user_login'] = options[action]['user']
	logpass['user_pwd'] = options[action]['password']
	
	device_edit = { 
		"tree" : "mdevice",
	}
	device_edit['id'] = options[action]['id']

	check_uniq = {}
	devicefield_save = {}
	if options[action]['networkname'] != None:
		# check_uniq['networkname'] = options[action]['networkname']
		devicefield_save['networkname'] = options[action]['networkname']
	if options[action]['deviceid'] != None:
		check_uniq['deviceid'] = options[action]['deviceid']
		devicefield_save['deviceid'] = options[action]['deviceid']
	if options[action]['ipmgm'] != None:
		check_uniq['ipmgm'] = options[action]['ipmgm']
		devicefield_save['ipmgm'] = options[action]['ipmgm']
	if 	options[action]['devicedescr'] != None:
		check_uniq['devicedescr'] = options[action]['devicedescr']
		devicefield_save['devicedescr'] = options[action]['devicedescr']
	if options[action]['objectclassidid'] != None:
		check_uniq['objectclassidid'] = options[action]['objectclassidid']
		devicefield_save['objectclassidid'] = options[action]['objectclassidid']
	if options[action]['strukturalevelid'] != None:
		check_uniq['strukturalevelid'] = options[action]['strukturalevelid']
		devicefield_save['strukturalevelid'] = options[action]['strukturalevelid']
	if options[action]['vendorid'] != None:
		check_uniq['vendorid'] = options[action]['vendorid']
		devicefield_save['vendorid'] = options[action]['vendorid']
	if options[action]['objectmodelid'] != None:
		check_uniq['objectmodelid'] = options[action]['objectmodelid']
		devicefield_save['objectmodelid'] = options[action]['objectmodelid']
	if options[action]['serialnumber'] != None:
		check_uniq['serialnumber'] = options[action]['serialnumber']
		devicefield_save['serialnumber'] = options[action]['serialnumber']
	if options[action]['devicestatus'] != None:
		check_uniq['devicestatus'] = options[action]['devicestatus']
		devicefield_save['devicestatus'] = options[action]['devicestatus']
	if options[action]['parentid'] != None:
		check_uniq['parentid'] = options[action]['parentid']
		devicefield_save['parentid'] = options[action]['parentid']
		devicefield_save['nodeid'] = options[action]['nodeid']
	if options[action]['parenttype'] != None:
		check_uniq['parenttype'] = options[action]['parenttype']
		devicefield_save['parenttype'] = options[action]['parenttype']
	if options[action]['office'] != None:
		devicefield_save['office'] = options[action]['office']
	check_uniq['user_login_saved'] = options[action]['user']
	
	

	with requests.Session() as s:
		auth = s.post('http://10.184.67.68/', data = logpass) #If auth ok, return '1' # , headers = headers
		cookie_phpid = {'PHPSESSID': requests.utils.dict_from_cookiejar(s.cookies)['PHPSESSID']}
		check_uniq['PHPSESSID'] = cookie_phpid['PHPSESSID']
		device_edit = s.post('http://10.184.67.68/device/edit', data = device_edit)
		devicefield_save = s.post('http://10.184.67.68/device/device_field/save', data = devicefield_save)
		devicefield_get = s.get('http://10.184.67.68/device/device_field/get')
		check_uniq = s.post('http://10.184.67.68/device/check_uniq', data = check_uniq)
		save = s.post('http://10.184.67.68/device/save')

	result = 'ok'
	if save.text:
		result = save.text
	return result

def insert(options, action):
	logpass = {}
	logpass['user_login'] = options[action]['user']
	logpass['user_pwd'] = options[action]['password']

	device_edit = { 
		"parent" : "node",
		"tree" : "mdevice",
	}
	device_edit['parentid'] = options[action]['nodeid']

	devicefield_save_b = { 
		"deviceid" : "",
		"devicetype" : "device",
		"office" : "",
		"numinstall" : "",
		"sysname" : "",
		"ipmgmid" : "",
		"qosid" : "0",
		"forvlan" : "0",
		"foragg" : "0",
		"timeout" : "0",
		"port" : "",
		"mezhregion" : "0",
		"deviceelectricpoint" : "0",
		"avalmodeid" : "1",
		"meid" : "",
	}
	devicefield_save_b['parentid'] = options[action]['parentid']
	devicefield_save_b['parenttype'] = options[action]['parenttype']
	devicefield_save_b['nodeid'] = options[action]['nodeid']
	devicefield_save_b['dateinstall'] = options[action]['dateinstall']
	devicefield_save_b['networkname'] = options[action]['networkname']
	devicefield_save_b['ipmgm'] = options[action]['ipmgm']
	devicefield_save_b['devicedescr'] = options[action]['devicedescr']
	devicefield_save_b['strukturalevelid'] = options[action]['strukturalevelid']

	fizdevice_edit = { 
		"tree" : "mdevice",
	}
	vendor_load = {}
	vendor_load['objectclassid'] = options[action]['objectclassid']
	
	model_load = {}
	model_load['vendor'] = options[action]['vendorid']
	model_load['objectclassid'] = options[action]['objectclassid']
	
	devicefield_save_a = {
		"deviceid" : "",
		"devicetype" : "device",
		"zipregionid" : "",
		"zipnodeid" : "",
		"deviceinvnumber" : "",
		"kategoriyaid" : "4",
		"bssid" : "",
		"macadr" : "",
		"covertype" : "",
		"lastmileid" : "",
	}
	devicefield_save_a['parentid'] = options[action]['parentid']
	devicefield_save_a['parenttype'] = options[action]['parenttype']
	devicefield_save_a['objectclassidid'] = options[action]['objectclassidid']
	devicefield_save_a['datazip'] = options[action]['datazip']
	devicefield_save_a['vendorid'] = options[action]['vendorid']
	devicefield_save_a['objectmodelid'] = options[action]['objectmodelid']
	devicefield_save_a['serialnumber'] = options[action]['serialnumber']
	devicefield_save_a['devicestatus'] = options[action]['devicestatus']
	devicefield_save_a['office'] = options[action]['office']

	check_uniq = {
		"cityname" : "null",
		"streetname" : "null",
		"nodeoffice" : "null",
		"region" : "null",
		"avalmodeid" : "1",	#24*7,
		"forvlan" : "0",
		"foragg" : "0",
		"timeout" : "0",
		"treeinfo" : "null",
		"deviceid" : "false",
		"devicetype" : "device",
		# "office" : "false",
		"numinstall" : "false",
		"sysname" : "false",
		"ipmgmid" : "false",
		"qosid" : "false",
		"port" : "false",
		"mezhregion" : "0",
		"deviceelectricpoint" : "false",
		"meid" : "false",
		"user_login_saved" : "yuzhakov-da",			#login
		"zipregionid" : "false",
		"zipnodeid" : "false",
		"deviceinvnumber" : "false",
		"kategoriyaid" : "4",
		"bssid" : "false",
		"macadr" : "false",
		"covertype" : "false",
		"lastmileid" : "false",
	}
	check_uniq['nodename'] = options[action]['nodename']
	check_uniq['nodebuilding'] = options[action]['nodebuilding']
	check_uniq['nodeid'] = options[action]['nodeid']
	check_uniq['networkname'] = options[action]['networkname']
	check_uniq['dateinstall'] = options[action]['dateinstall']
	check_uniq['parentid'] = options[action]['parentid']
	check_uniq['parenttype'] = options[action]['parenttype']
	check_uniq['ipmgm'] = options[action]['ipmgm']
	check_uniq['devicedescr'] = options[action]['devicedescr']
	check_uniq['strukturalevelid'] = options[action]['strukturalevelid']
	check_uniq['objectclassidid'] = options[action]['objectclassidid']
	check_uniq['datazip'] = options[action]['datazip']
	check_uniq['vendorid'] = options[action]['vendorid']
	check_uniq['objectmodelid'] = options[action]['objectmodelid']
	check_uniq['serialnumber'] = options[action]['serialnumber']
	check_uniq['devicestatus'] = options[action]['devicestatus']
	check_uniq['office'] = options[action]['office']

	with requests.Session() as s:
		auth = s.post('http://10.184.67.68/', data = logpass) #If auth ok, return '1' # , headers = headers
		cookie_phpid = {'PHPSESSID': requests.utils.dict_from_cookiejar(s.cookies)['PHPSESSID']}
		check_uniq['PHPSESSID'] = cookie_phpid['PHPSESSID']
	
		device_edit = s.post('http://10.184.67.68/device/edit', data = device_edit) #, headers = header_devicelist
		devicefield_save_b = s.post('http://10.184.67.68/device/device_field/save', data = devicefield_save_b) #, headers = headersssave
		fizdevice_edit = s.post('http://10.184.67.68/device/fizdevice/edit', data = fizdevice_edit)
		vendor_load = s.post('http://10.184.67.68/vendor/load', data = vendor_load)
		model_load = s.post('http://10.184.67.68/model/load', data = model_load)
		devicefield_save_a = s.post('http://10.184.67.68/device/device_field/save', data = devicefield_save_a)
		devicefield_get = s.get('http://10.184.67.68/device/device_field/get')
	
		check_uniq = s.post('http://10.184.67.68/device/check_uniq', data = check_uniq) #, headers = headers
		save = s.post('http://10.184.67.68/device/save') #, headers = headersssave

	result = 'ok'
	if save.text:
		result = save.text
	return result



def start():
	parser = createParser()
	namespace = parser.parse_args()
	args = {}
	args[namespace.req] = {
		'action' : namespace.req,
		'ip' : namespace.ip,
		'hostname' : namespace.hostname,
		'sd' : namespace.sd,
		'uplink' : namespace.uplink,
		'office' : namespace.office,
		'structura' : namespace.str,
		'classid' : namespace.classid,
		'vendor' : namespace.vendor,
		'model' : namespace.model,
		'serial' : namespace.serial,
		'status' : namespace.status,
	}
	result = main(args)


if __name__ == "__main__":
	start()
from django.shortcuts import render
from django.conf import settings
from django.shortcuts import redirect
from django.core.mail import send_mail
from django.core.mail import mail_admins
from django.http import JsonResponse

#
import jinja2
import sys, os, re, time
import json
import time
import multimodule
import free_ip
import conf_routing
import fias_import
from ipaddress import IPv4Network

import mysql.connector 
from mysql.connector import Error


def activator(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [x.name for x in request.user.groups.all()]
	if not 'admins' in group and not 'testers' in group:
		return render(request, 'activator/access.html')
	# send_mail(f"""Ваша заявка""", f"""Здравствуй""", 'acds@ural.rt.ru', ['yuzhakov-da@ural.rt.ru'])
	
	return render(request, 'activator/activator.html')

def get_acds_id(request): #УБРАТЬ КОСТЫЛИ С ТАИМАУТОМ ОТПРАВКИ ПОЧТЫ
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group and not 'testers' in group:
		return render(request, 'activator/access.html')

	ip = request.META.get('HTTP_X_FORWARDED_FOR')
	user = request.user.username
	email = request.user.email
	acds_id = {}
	mail_error_user = 'error'
	mail_error_admin = 'error'

	if request.GET:
		mip = ''.join(list(request.GET.get('mip', str(False))))
		uplink = ''.join(list(request.GET.get('uplink', str(False))))
		address = ''.join(list(request.GET.get('address', str(False))))
		office = ''.join(list(request.GET.get('office', str(False))))
		model = ''.join(list(request.GET.get('model', str(False))))
		serial = ''.join(list(request.GET.get('serial', str(False))))
		sd = ''.join(list(request.GET.get('sd', str(False))))
		old_ip = ''.join(list(request.GET.get('oldip', str(False))))
		ip = ''.join(list(request.GET.get('ip', str(False))))

		# sd = sd.replace(" ", "")
		t = multimodule.FastModulAut()
		t.sql_connect('connect')
		t.ws_connect('chat/log_free_ip/')

		t.ws_send_message(f"""INSERT INTO guspk.acds (ticket, reason, uplink, modelid, serial, office, status, online, argus, email) 
						VALUES ('{sd}', '{mip}', '{uplink}', (SELECT MODELID FROM guspk.host_model WHERE DEVICEMODELNAME like '{model}'), '{serial}', '{office}', 'new', 0, 0, '{email}')""")
		acds_id = t.sql_update(f"""INSERT INTO guspk.acds (ticket, reason, uplink, modelid, serial, office, status, online, argus, email) 
						VALUES ('{sd}', '{mip}', '{uplink}', (SELECT MODELID FROM guspk.host_model WHERE DEVICEMODELNAME like '{model}'), '{serial}', '{office}', 'new', 0, 0, '{email}')""")
		t.sql_update(f"""INSERT INTO guspk.acds_logs (id, status, user, message) VALUES ('{acds_id}', 'new', '{user}', 'Инициирована заявка на ввод нового оборудования')""")
		# acds_id = acds_id[0][0]
		# t.sql_connect('disconnect')
		# t.sql_connect('connect')

		t.ws_send_message(f"acds_id - {acds_id}")

		device_info = {'id': acds_id, 'address': address, 'dest': 'acds_fias'}
		t.ws_send_message(f"device_info - {device_info}")
		fias_import.host_fias_insert(device_info)
		t.ws_send_message(f"fias_import - ok")

		if old_ip != 'False':
			t.sql_update(f"""UPDATE guspk.acds SET oldip = '{old_ip}' WHERE id like '{device_info['id']}'""")
			t.ws_send_message(f"oldip insert - {old_ip}")
		free_ip_run = free_ip.get_free_data(acds_id)
		t.ws_send_message(f"free_ip_run - {free_ip_run}")

		if free_ip_run == 'ok':
			deviceid = t.sql_select(f"""SELECT an.DEVICEID, h.IPADDMGM
							FROM guspk.host_acsw_node an
							LEFT JOIN guspk.acds a ON a.acsw_node_id = an.ACSD_NODE_ID
							LEFT JOIN guspk.host h ON an.DEVICEID = h.DEVICEID
							WHERE a.id = {acds_id}""", 'full')
			deviceid, ip = deviceid[0]
			device_info2 = {'id': deviceid, 'address': address, 'dest': 'host_fias'}
			# Присвоение адреса устройству через функцию ФИАС
			fias_import.host_fias_insert(device_info2)

			# Отправка почты
			mail_data, email, data_settings, header, footer = mail_generator(acds_id)
			mail_data = '\n'.join(mail_data)

			device_info.update({"acds_data": data_settings})

			mail_sender(f"""Ваша заявка на ввод оборудования {acds_id}""",
						f"""Здравствуй {user}!\n\n Реквизиты по вашей заявке № {acds_id}.\nОжидается установка на сеть.\n{header}\n{mail_data}\n{footer}""",
						f'{email}')
			mail_sender(f"""Заявка {acds_id} [INIT]""", 
						f"""Отработано успешно\nIP\t{data_settings['ipaddmgm']}\nnetname\t{data_settings['networkname']}\nGW\t{data_settings['gw']}\nMASK\t{data_settings['mask']}\nmgmvlan\t{data_settings['mgmvlan']}\nvlans\t{data_settings['vlans']}\noffice\t{data_settings['office']}\nserial\t{data_settings['serial']}\nmodel\t{data_settings['model']}""",
						 admins=True)

			t.sql_update(f"UPDATE guspk.acds SET status = 'init', report = '{free_ip_run}' WHERE id like {acds_id}")
			print(f"UPDATE guspk.acds SET status = 'init', report = '{free_ip_run}' WHERE id like {acds_id}")
			t.sql_update(f"""INSERT INTO guspk.acds_logs (id, ip, status, user, message) VALUES ('{acds_id}', '{ip}', 'init', '{user}', 'Предоставлены реквизиты {data_settings['ipaddmgm']}\t{data_settings['networkname']}\t{data_settings['serial']}\t{data_settings['model']}\t{address}')""")
			t.sql_update(f"UPDATE guspk.acds_logs SET ip = '{ip}' WHERE id like {acds_id}")
		else:
			device_info.update({"error": "Вы получите данные в течении нескольких минут на вашу почту"})
			mail_sender(f"""Ваша заявка на ввод оборудования {acds_id}""",
						f"""Здравствуй {user}!\n\n Ваша заявка № {acds_id} выполняется, чуть позже вы получите все реквизиты""",
						f'{email}')
			mail_sender(f"""Заявка {acds_id} [ERROR]""",
						f"""free_ip_run  {free_ip_run}""",
						admins=True)

			t.sql_update(f"""UPDATE guspk.acds SET status = 'error(f)', report = '{free_ip_run}' WHERE id like '{acds_id}'""")
			t.sql_update(f"""INSERT INTO guspk.acds_logs (id, status, user, message) VALUES ('{acds_id}', 'error(f)', '{user}', '{free_ip_run}')""")

		t.ws_close()
		t.sql_connect('disconnect')

	return JsonResponse(device_info, safe=False)

def deactivator(request): #Здесь блок вывода из эксплуатации
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group and not 'testers' in group:
		return render(request, 'activator/access.html')
	# send_mail(f"""Ваша заявка""", f"""Здравствуй""", 'acds@ural.rt.ru', ['yuzhakov-da@ural.rt.ru'])
	
	return render(request, 'activator/deactivator.html')

def get_acds_id_deactivator(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group and not 'testers' in group:
		return render(request, 'activator/access.html')

	ip = request.META.get('HTTP_X_FORWARDED_FOR')
	user = request.user.username
	email = request.user.email
	acds_id = {}

	if request.GET:
		mip = ''.join(list(request.GET.get('mip', str(False))))
		ip = ''.join(list(request.GET.get('ip', str(False))))
		comment = ''.join(list(request.GET.get('comment', str(False))))
	
		t = multimodule.FastModulAut()
		t.sql_connect('connect')
		# t.ws_connect('chat/log_free_ip/')
		if ip != 'False':
			ip_data = t.sql_select(f"""SELECT  hm.MODELID, CONCAT(COALESCE(fc.city, ''), COALESCE(fs.settlement, ''), COALESCE(CONCAT(' ул. ', fstr.street), ''), COALESCE(CONCAT(' д. ', fhouse.house), ''), COALESCE(CONCAT(' к. ', fhouse.block), '')) as address, (SELECT IPADDMGM from guspk.host WHERE DEVICEID = top.parent), COALESCE(h.SERIALNUMBER, '-'), h.DEVICEID
							FROM guspk.host h
							LEFT JOIN guspk.host_model hm ON hm.MODELID = h.MODELID
							LEFT JOIN guspk.host_fias hf ON hf.id = h.DEVICEID
							LEFT JOIN guspk.host_acsw_node an ON an.DEVICEID = h.DEVICEID
							LEFT JOIN guspk.host_vlan_template vt ON vt.VLAN_TEMPLATE_ID = an.VLAN_TEMPLATE_ID
							LEFT JOIN guspk.fias_city fc ON hf.city_fias_id = fc.city_fias_id
							LEFT JOIN guspk.fias_settlement fs ON hf.settlement_fias_id = fs.settlement_fias_id
							LEFT JOIN guspk.fias_street fstr ON hf.street_fias_id = fstr.street_fias_id
							LEFT JOIN guspk.fias_house fhouse ON hf.house_fias_id = fhouse.house_fias_id
							LEFT JOIN guspk.topology top ON top.child = h.DEVICEID
							WHERE h.IPADDMGM = '{ip}'
							LIMIT 1""", 'full')
			model, address, uplink, serial, deviceid = ip_data[0]

			acswnodeid = t.sql_update(f"""INSERT INTO guspk.host_acsw_node (DEVICEID, NETWORK_ID, VLAN_TEMPLATE_ID) VALUES ('{deviceid}', '860', '206')""")
			acds_id = t.sql_update(f"""INSERT INTO guspk.acds (ticket, reason, uplink, modelid, serial, office, acsw_node_id, status, online, argus, email, report) 
							VALUES ('{comment}', '{mip}', '{uplink}', '{model}', '{serial}', '{address}', '{acswnodeid}', 'del', 0, 2, '{email}', 'removing')""")
			t.sql_update(f"""INSERT INTO guspk.acds_logs (id, ip,  status, user, message) VALUES ('{acds_id}', '{ip}', 'del', '{user}', 'Инициирована заявка на вывод оборудования {model}. {comment}. {mip}')""")
			# t.ws_send_message(f"acds_id - {acds_id}")
			mail_admins(f"""Заявка {acds_id} [DEL]""", f"""Пришла заявка на вывод оборудования {ip}""")
			time.sleep(2)
			send_mail(f"""Заявка на вывод в Аргус № {acds_id}""", f"""Поступила новая заявка № {acds_id}.""", 'acds@ural.rt.ru', ['zaripova-ak@ural.rt.ru'])
			time.sleep(2)
			send_mail(f"""Ваша заявка на вывод оборудования {acds_id}""", f"""Здравствуй {user}!\n\n Ваша заявка № {acds_id} выполняется, вы получите уведомление по завершению работ""", 'acds@ural.rt.ru', [f'{email}'])
			device_info = {'id': acds_id}

		# t.ws_close()
		t.sql_connect('disconnect')

	return JsonResponse(device_info, safe=False)


def device_move(request): #Здесь блок прочих действий с устройствами
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group and not 'testers' in group:
		return render(request, 'activator/access.html')
	# send_mail(f"""Ваша заявка""", f"""Здравствуй""", 'acds@ural.rt.ru', ['yuzhakov-da@ural.rt.ru'])
	
	return render(request, 'activator/device_move.html')

def get_device_move(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group and not 'testers' in group:
		return render(request, 'activator/access.html')

	ip = request.META.get('HTTP_X_FORWARDED_FOR')
	user = request.user.username
	email = request.user.email
	acds_id = {}

	if request.GET:
		# mip = ''.join(list(request.GET.get('mip', str(False))))
		ip = ''.join(list(request.GET.get('ip', str(False))))
		comment = ''.join(list(request.GET.get('comment', str(False))))
	
		t = multimodule.FastModulAut()
		t.sql_connect('connect')
		# t.ws_connect('chat/log_free_ip/')
		if ip != 'False':
			ip_data = t.sql_select(f"""SELECT  hm.MODELID, CONCAT(COALESCE(fc.city, ''), COALESCE(fs.settlement, ''), COALESCE(CONCAT(' ул. ', fstr.street), ''), COALESCE(CONCAT(' д. ', fhouse.house), ''), COALESCE(CONCAT(' к. ', fhouse.block), '')) as address, (SELECT IPADDMGM from guspk.host WHERE DEVICEID = top.parent), COALESCE(h.SERIALNUMBER, '-'), h.DEVICEID
							FROM guspk.host h
							LEFT JOIN guspk.host_model hm ON hm.MODELID = h.MODELID
							LEFT JOIN guspk.host_fias hf ON hf.id = h.DEVICEID
							LEFT JOIN guspk.host_acsw_node an ON an.DEVICEID = h.DEVICEID
							LEFT JOIN guspk.host_vlan_template vt ON vt.VLAN_TEMPLATE_ID = an.VLAN_TEMPLATE_ID
							LEFT JOIN guspk.fias_city fc ON hf.city_fias_id = fc.city_fias_id
							LEFT JOIN guspk.fias_settlement fs ON hf.settlement_fias_id = fs.settlement_fias_id
							LEFT JOIN guspk.fias_street fstr ON hf.street_fias_id = fstr.street_fias_id
							LEFT JOIN guspk.fias_house fhouse ON hf.house_fias_id = fhouse.house_fias_id
							LEFT JOIN guspk.topology top ON top.child = h.DEVICEID
							WHERE h.IPADDMGM = '{ip}'
							LIMIT 1""", 'full')
			model, address, uplink, serial, deviceid = ip_data[0]

			acswnodeid = t.sql_update(f"""INSERT INTO guspk.host_acsw_node (DEVICEID, NETWORK_ID, VLAN_TEMPLATE_ID) VALUES ('{deviceid}', '860', '206')""")
			acds_id = t.sql_update(f"""INSERT INTO guspk.acds (ticket, reason, uplink, modelid, serial, office, acsw_node_id, status, online, argus, email, report) 
							VALUES ('{comment}', 'other', '{uplink}', '{model}', '{serial}', '{address}', '{acswnodeid}', 'other', 0, 0, '{email}', '{comment}')""")
			t.sql_update(f"""INSERT INTO guspk.acds_logs (id, ip, status, user, message) VALUES ('{acds_id}', '{ip}', 'del', '{user}', 'Инициирована заявка внесение изменений. {comment}.')""")
			# t.ws_send_message(f"acds_id - {acds_id}")
			mail_admins(f"""Заявка {acds_id} [OTHER]""", f"""Пришла заявка, читайте комментарий""")
			time.sleep(2)
			# send_mail(f"""Заявка № {acds_id}""", f"""Поступила новая заявка № {acds_id}.""", 'acds@ural.rt.ru', ['zaripova-ak@ural.rt.ru'])
			# time.sleep(2)
			send_mail(f"""Ваша заявка № {acds_id}""", f"""Здравствуй {user}!\n\n Ваша заявка № {acds_id} выполняется, вы получите уведомление по завершению работ""", 'acds@ural.rt.ru', [f'{email}'])
			device_info = {'id': acds_id}

		# t.ws_close()
		t.sql_connect('disconnect')

	return JsonResponse(device_info, safe=False)

def history(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	# if not 'admins' in group and not 'testers' in group:
	# 	return render(request, 'activator/access.html')
	# send_mail(f"""Ваша заявка""", f"""Здравствуй""", 'acds@ural.rt.ru', ['yuzhakov-da@ural.rt.ru'])
	
	return render(request, 'activator/history.html')

def get_history(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]	
	ip = request.META.get('HTTP_X_FORWARDED_FOR')
	user = request.user.username
	email = request.user.email

	if request.GET:
		acds_id = ''.join(list(request.GET.get('id', str(False))))
	
	if(acds_id != 'False'):
		info = {}
		logs = []
		t = multimodule.FastModulAut()
		t.sql_connect('connect')
		# t.ws_connect('chat/log_free_ip/')
		logs_db = t.sql_select(f"""SELECT * FROM guspk.acds_logs WHERE id = '{acds_id}'""", "full")
		if logs_db:
			for n in logs_db:
				logs.append(n)
			info = {'logs': logs, 'report': 'ok'}
		else:
			info = {'report': 'error'}


		# t.ws_close()
		t.sql_connect('disconnect')

	return JsonResponse(info, safe=False)

def get_uplink_info(request):
	summary = []
	t = multimodule.FastModulAut()
	t.sql_connect('connect')

	if request.GET:
		address_get = ''.join(list(request.GET.get('address', str(False))))
		if address_get:
			addresses = {}
			networkname = t.sql_select(f"SELECT IPADDMGM, NETWORKNAME from guspk.host where IPADDMGM like '{address_get}' or NETWORKNAME like '{address_get}'", 'full')
			if networkname:
				summary = {'ip': networkname[0][0], 'hostname': networkname[0][1]}
			else:
				summary = {'error': 'uplink not exist'}

	t.sql_connect('disconnect')
	# summary = json.dumps(summary)
	
	return JsonResponse(summary, safe=False)

def get_model(request):
	summary = []
	t = multimodule.FastModulAut()
	t.sql_connect('connect')

	if request.GET:
		model_get = ''.join(list(request.GET.get('model', str(False))))
		if (model_get != 'False'):
			models = {}
			db = t.sql_select(f"SELECT MODELID, DEVICEMODELNAME from guspk.host_model WHERE DEVICEMODELNAME like '%{model_get}%'", 'full')
			models_list = []
			for (modelid, modelname) in db:
				models.update({modelid:modelname})
				models_list.append(modelname)
				summary = models

		# address_get = ''.join(list(request.GET.get('address', str(False))))
		# if address_get:
		# 	addresses = {}
		# 	networkname = t.sql_select(f"SELECT NETWORKNAME from guspk.host where IPADDMGM like '{address_get}'", 'full')
		# 	if networkname:
		# 		summary = {'hostname': networkname[0][0]}
		# 	else:
		# 		summary = {'error': 'uplink not exist'}

	t.sql_connect('disconnect')
	# summary = json.dumps(summary)
	
	return JsonResponse(summary, safe=False)



def free_ip_refresh(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group and not 'testers' in group:
		return render(request, 'activator/access.html')
	user = request.user.username
	# email = request.user.email
	if request.GET:
		values = {}
		t = multimodule.FastModulAut()
		t.sql_connect('connect')

		acds_id = ''.join(list(request.GET.get('id', str(False))))
		status = ''.join(list(request.GET.get('status', str(False))))
		if status == 'error(f)' or status == 'new':
			t.sql_update(f"""INSERT into guspk.logs (scr_name, DEVICEID, WHO, message) VALUES ('free_ip_refresh', '{acds_id}', '{user}', 'pushed free_ip_refresh')""")
			t.sql_update(f"""INSERT INTO guspk.acds_logs (id, status, user, message) VALUES ('{acds_id}', '{status}', '{user}', 'Повторный запуск процесса выделения реквизитов')""")
			free_ip_run = free_ip.get_free_data(acds_id)
			if 'Error' in free_ip_run:
				values.update({'status': 'error(f)'})
				values.update({'report': free_ip_run})
				values.update({'badge': 'danger'})
				t.sql_update(f"""UPDATE guspk.acds SET status = '{values['status']}', report = '{values['report']}' WHERE id like '{acds_id}'""")
				t.sql_update(f"""INSERT INTO guspk.acds_logs (id, status, user, message) VALUES ('{acds_id}', 'error(f)', '{user}', '{free_ip_run}')""")
			elif free_ip_run == 'ok':
				address = t.sql_select(f"""SELECT  CONCAT(COALESCE(fc.city, ''), COALESCE(fs.settlement, ''), COALESCE(CONCAT(' ул. ', fstr.street), ''), COALESCE(CONCAT(' д. ', fhouse.house), ''), COALESCE(CONCAT(' к. ', fhouse.block), '')) as address
										FROM guspk.acds a
										LEFT JOIN guspk.acds_fias af ON af.id = a.id
										LEFT JOIN guspk.fias_city fc ON af.city_fias_id = fc.city_fias_id
										LEFT JOIN guspk.fias_settlement fs ON af.settlement_fias_id = fs.settlement_fias_id
										LEFT JOIN guspk.fias_street fstr ON af.street_fias_id = fstr.street_fias_id
										LEFT JOIN guspk.fias_house fhouse ON af.house_fias_id = fhouse.house_fias_id
										WHERE a.id = {acds_id}""", 'full')
				##Уберите это когда откажетесь от АСТУ
				deviceid = t.sql_select(f"""SELECT an.DEVICEID, h.IPADDMGM
							FROM guspk.host_acsw_node an
							LEFT JOIN guspk.acds a ON a.acsw_node_id = an.ACSD_NODE_ID
							LEFT JOIN guspk.host h ON an.DEVICEID = h.DEVICEID
							WHERE a.id = {acds_id}""", 'full')
				deviceid, ip = deviceid[0]
				device_info2 = {'id': deviceid, 'address': address, 'dest': 'host_fias'}
				fias_import.host_fias_insert(device_info2)
				##
				mail_data, email, data_settings, header, footer = mail_generator(acds_id)
				mail_data = '\n'.join(mail_data)

				mail_sender(f"""Ваша заявка на ввод оборудования {acds_id}""",
							f"""Здравствуй {user}!\n\n Реквизиты по вашей заявке № {acds_id}.\nОжидается установка на сеть.\n{header}\n{mail_data}\n{footer}""",
							f'{email}')
				mail_sender(f"""Заявка {acds_id} [INIT]""", 
							f"""Отработано успешно\nIP\t{data_settings['ipaddmgm']}\nnetname\t{data_settings['networkname']}\nGW\t{data_settings['gw']}\nMASK\t{data_settings['mask']}\nmgmvlan\t{data_settings['mgmvlan']}\nvlans\t	{data_settings['vlans']}\noffice\t{data_settings['office']}\nserial\t{data_settings['serial']}\nmodel\t{data_settings['model']}""",
							 admins=True)				
				values.update({'status': 'init'})
				values.update({'report': free_ip_run})
				values.update({'badge': 'warning'})
				values.update({'ip': data_settings['ipaddmgm']})
				values.update({'hostname': data_settings['networkname']})
				values.update({'network': data_settings['network']})
				values.update({'mgmvlan': data_settings['mgmvlan']})
				values.update({'vlans': data_settings['vlans']})
				values.update({'address': address[0][0]})
				t.sql_update(f"""UPDATE guspk.acds SET status = '{values['status']}', report = '{values['report']}' WHERE id like '{acds_id}'""")
				t.sql_update(f"""INSERT INTO guspk.acds_logs (id, status, user, message) VALUES ('{acds_id}', 'init', '{user}', 'Предоставлены реквизиты {data_settings['ipaddmgm']}\t{data_settings['networkname']}\t{data_settings['serial']}\t{data_settings['model']}')""")
				t.sql_update(f"UPDATE guspk.acds_logs SET ip = '{ip}' WHERE id like {acds_id}")
			else:
				mail_sender(f"""Заявка {acds_id} [ERROR]""",
							f"""free_ip_run  {free_ip_run}""",
							admins=True)
				t.sql_update(f"""UPDATE guspk.acds SET status = '{values['status']}', report = '{values['report']}' WHERE id like '{acds_id}'""")
				t.sql_update(f"""INSERT INTO guspk.acds_logs (id, status, user, message) VALUES ('{acds_id}', '{values['status']}', '{user}', '{values['report']}')""")

		# summary = json.dumps(values)
		t.sql_connect('disconnect')
	
	return JsonResponse(values, safe=False)

def device_configure(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group and not 'engineers' in group:
		return render(request, 'activator/access.html')
	user = request.user.username
	# email = request.user.email

	if request.GET:
		values = {}
		t = multimodule.FastModulAut()
		acds_id = ''.join(list(request.GET.get('id', str(False))))
		# ip = ''.join(list(request.GET.get('ip', str(False))))
		# model = ''.join(list(request.GET.get('model', str(False))))

		t.sql_connect('connect')
		preconf_check = t.sql_select(f"""SELECT host.IPADDMGM,  m.DEVICEMODELNAME, a.status, a.online, a.email, fr.region_code, a.argus, host.DEVICEID
						FROM guspk.acds a
						INNER JOIN guspk.host_model m ON a.modelid = m.MODELID
						LEFT JOIN guspk.host_acsw_node an ON a.acsw_node_id = an.ACSD_NODE_ID
						LEFT JOIN guspk.host host ON an.DEVICEID = host.DEVICEID
						LEFT JOIN guspk.acds_fias af ON af.id = a.id
						LEFT JOIN guspk.fias_region fr ON af.region_fias_id = fr.region_fias_id
						WHERE a.id like '{acds_id}'""", 'full')

		ip, model, status, online, email, region_code, argus, deviceid = preconf_check[0]

		if status == 'ok' and argus == 1:
			values.update({'status': 'finished'})
			t.sql_update(f"""INSERT into guspk.logs (scr_name, DEVICEID, WHO, message) VALUES ('device_configure', '{ip}', '{user}', 'device status changed 2->3 acds_id {acds_id} ip {ip}')""")
			t.sql_update(f"""INSERT INTO guspk.acds_logs (id, status, user, message) VALUES ('{acds_id}', '{status}', '{user}', 'Все работы по вводу завершены')""")
			t.sql_update(f"""UPDATE guspk.acds SET status = 'closed' WHERE id like '{acds_id}'""")
			t.sql_update(f"""UPDATE guspk.ahot SET DEVICESTATUSID = '3' WHERE IPADDMGM = '{ip}'""")
			send_mail(f"""Заявка на ввод № {acds_id}""", f"""Оборудование по заявке № {acds_id} введено в эксплуатацию.""", 'acds@ural.rt.ru', [f'{email}'])
		elif status == 'ok' and argus == 0:
				values.update({'status': 'ok'})
				values.update({'badge': 'success'})
				values.update({'report': 'not in argus'})
		elif status == 'init' and online == 1 or status == 'error(c)' and online == 1:
			conf_status = t.sql_select(f"""SELECT report from guspk.acds WHERE id like '{acds_id}'""", 'full')
			if conf_status[0][0] == 'configuring':
				values.update({'report': 'configuring'})
				values.update({'status': 'init'})
				values.update({'badge': 'warning'})
			else:
				t.sql_update(f"""INSERT into guspk.logs (scr_name, DEVICEID, WHO, message) VALUES ('device_configure', '{ip}', '{user}', 'acds_id {acds_id} pushed button')""")
				t.sql_update(f"""INSERT INTO guspk.acds_logs (id, status, user, message) VALUES ('{acds_id}', '{status}', '{user}', 'Запущено конфигурирование устройства')""")
				t.sql_update(f"""UPDATE guspk.acds SET report = 'configuring' WHERE id like '{acds_id}'""")
				conf_routing_run = conf_routing.start(acds_id, ip, model)
				if 'Error' in conf_routing_run:
					values.update({'status': 'error(c)'})
					values.update({'badge': 'danger'})
					values.update({'report': conf_routing_run})
					t.sql_update(f"""INSERT into guspk.logs (scr_name, DEVICEID, WHO, message) VALUES ('device_configure', '{ip}', '{user}', "acds_id {acds_id} configure error {conf_routing_run}")""")
					t.sql_update(f"""INSERT INTO guspk.acds_logs (id, status, user, message) VALUES ('{acds_id}', 'error(c)', '{user}', "{conf_routing_run}")""")
					t.sql_update(f"""UPDATE guspk.acds SET status = '{values['status']}', report = '{values['report']}' WHERE id like '{acds_id}'""")
					mail_admins(f"""Заявка {acds_id} [ERROR]""", f"""Конфигурирование не выполнено {conf_routing_run}""")
				elif conf_routing_run == 'ok':
					values.update({'status': 'ok'})
					values.update({'badge': 'success'})
					values.update({'report': 'configured'})
					t.sql_update(f"""INSERT into guspk.logs (scr_name, DEVICEID, WHO, message) VALUES ('device_configure', '{ip}', '{user}', "acds_id {acds_id} configure ok")""")
					t.sql_update(f"""INSERT INTO guspk.acds_logs (id, status, user, message) VALUES ('{acds_id}', 'ok', '{user}', 'Конфигурирование выполнено успешно, передано в Аргус')""")
					t.sql_update(f"""UPDATE guspk.acds SET status = '{values['status']}', report = '{values['report']}' WHERE id like '{acds_id}'""")
					# mail_admins(f"""Заявка {acds_id} [OK]""", f"""Конфигурирование выполнено успешно""")
					send_mail(f"""Заявка на ввод № {acds_id}""", f"""Поступила новая заявка № {acds_id}.""", 'acds@ural.rt.ru', ['zaripova-ak@ural.rt.ru'])
					time.sleep(4)
					send_mail(f"""Заявка на ввод в Аргус № {acds_id}""", f"""Ваша заявка № {acds_id} передана в Аргус.""", 'acds@ural.rt.ru', [f'{email}'])
		elif status == 'del' and argus == 3:
			values.update({'status': 'finished'})
			t.sql_update(f"""INSERT into guspk.logs (scr_name, DEVICEID, WHO, message) VALUES ('device_configure', '{ip}', '{user}', 'device status changed 3->6 acds_id {acds_id} ip {ip}')""")
			t.sql_update(f"""INSERT INTO guspk.acds_logs (id, status, user, message) VALUES ('{acds_id}', '{status}', '{user}', 'Устройство выведено из эксплуатации {ip}')""")
			t.sql_update(f"""UPDATE guspk.acds SET status = 'closed', report = 'removed' WHERE id like '{acds_id}'""")
			t.sql_update(f"""DELETE from guspk.host WHERE DEVICEID = '{deviceid}'""")
			# mail_admins(f"""Заявка {acds_id} [DEL]""", f"""Выведено успешно""")
			send_mail(f"""Заявка на вывод оборудования из Аргус № {acds_id}""", f"""Устройство по заявке № {acds_id} выведено из эксплуатации.""", 'acds@ural.rt.ru', [f'{email}'])
			time.sleep(2)
			send_mail(f"""Удалить из ИНИТИ""", f"""Устройство выведено из эксплуатации, прошу удалить из ИНИТИ. ip - {ip}.""", 'acds@ural.rt.ru', [f'monitoring@ural.rt.ru'])
		elif status == 'other': 
			t.sql_update(f"""INSERT INTO guspk.acds_logs (id, status, user, message) VALUES ('{acds_id}', '{status}', '{user}', 'Работы в ЗО ГУСД завершены, передана в Аргус.')""")
			t.sql_update(f"""UPDATE guspk.acds SET argus = '4' WHERE id like '{acds_id}'""")
			values.update({'status': 'finished'})
			send_mail(f"""Заявка № {acds_id}""", f"""Поступила новая заявка № {acds_id}.""", 'acds@ural.rt.ru', ['zaripova-ak@ural.rt.ru'])
			time.sleep(4)
			send_mail(f"""Заявка № {acds_id}""", f"""Работы по заявке {acds_id} в ЗО ГУСД завершены, передана в Аргус.""", 'acds@ural.rt.ru', [f'{email}'])
		else:
			values.update({'status': status})
			values.update({'badge': 'danger'})
			values.update({'report': f"free_ip in status {status}, online - {online}"})
			t.sql_update(f"""UPDATE guspk.acds SET status = '{values['status']}', report = '{values['report']}' WHERE id like '{acds_id}'""")

		t.sql_connect('disconnect')

	return JsonResponse(values, safe=False)

def get_ticket_info(request):
	t = multimodule.FastModulAut()
	# t.ws_connect('chat/test/')
	# t.ws_send_message(f"start")
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group and not 'argus' in group and not 'engineers' in group:
		return render(request, 'activator/access.html')

	t.sql_connect('connect')
	ip = request.META.get('HTTP_X_FORWARDED_FOR')
	user = request.user.username
	acds_id = ''.join(list(request.GET.get('id', str(False))))


	ticket_info_db = t.sql_select(f"""SELECT a.office, a.serial, a.reason, a.acsw_node_id, a.email, CONCAT(h.NETWORKNAME, "(", h.IPADDMGM, ")"), a.ticket
									FROM guspk.acds a
									LEFT JOIN guspk.host_acsw_node an ON an.ACSD_NODE_ID = a.acsw_node_id
									LEFT JOIN guspk.host_networks hn ON hn.NETWORK_ID = an.NETWORK_ID
									LEFT JOIN guspk.host h ON h.DEVICEID = hn.DEVICEID 
									WHERE id = '{acds_id}'""", 'full')
	# t.ws_send_message(f"ticket_info_db: {ticket_info_db}")

	ticket_vlans_db = t.sql_select(f"""SELECT ACSD_NODE_ID, vt.HSI, vt.IPTV, vt.IMS, vt.TR069, hn.NETWORK, CONCAT(h.NETWORKNAME, "(", h.IPADDMGM, ")")
									FROM guspk.host_acsw_node an
									LEFT JOIN guspk.host_vlan_template vt ON vt.VLAN_TEMPLATE_ID = an.VLAN_TEMPLATE_ID
									LEFT JOIN guspk.host_networks hn ON hn.NETWORK_ID = an.NETWORK_ID
									LEFT JOIN guspk.host h ON h.DEVICEID = hn.DEVICEID
									WHERE an.DEVICEID = (SELECT an.DEVICEID
									FROM guspk.acds a
									LEFT JOIN guspk.host_acsw_node an ON an.ACSD_NODE_ID = a.acsw_node_id
									WHERE id like {acds_id}) AND
									(an.VLAN_TEMPLATE_ID not like '206' or an.NETWORK_ID not like '860')""", 'full')
	ticket_info_db = ticket_info_db[0]
	ticket_info = {}
	vlans = {}
	# t.ws_send_message(f"ticket_vlans_db: {ticket_vlans_db}")
	for line in ticket_vlans_db:
		vlans.update({line[0]:{'hsi': line[1], 'iptv': line[2], 'ims': line[3], 'tr': line[4], 'network': line[5]}})

	ticket_info = {'office': ticket_info_db[0], 'serial': ticket_info_db[1], 'reason': ticket_info_db[2], 'acsw_node_id': ticket_info_db[3], 'email': ticket_info_db[4], 'vlans': vlans, 'termination': ticket_info_db[5], 'ticket': ticket_info_db[6]}
	t.sql_connect('disconnect')

	# t.ws_send_message(f"stop")
	# t.ws_close()
	return JsonResponse(ticket_info, safe=False)

def get_acsw_node_id_update(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group:
		return render(request, 'activator/access.html')

	t = multimodule.FastModulAut()
	t.sql_connect('connect')

	user = request.user.username
	acds_id = ''.join(list(request.GET.get('id', str(False))))
	acsw_node_id = ''.join(list(request.GET.get('acsw_node_id', str(False))))
	comment = ''.join(list(request.GET.get('comment', str(False))))
	acswnodeid = {}

	old_acsw_node_id = t.sql_select(f"""SELECT acsw_node_id from guspk.acds WHERE id = {acds_id}""", 'full')

	if comment != "False":
		db_comment = t.sql_select(f"SELECT ticket from guspk.acds WHERE id = {acds_id}", 'full')
		if comment != db_comment[0][0]:
			acswnodeid.update({'status': 'updated', 'message': f'comment changed old {db_comment[0][0]} new {comment}'})
			t.sql_update(f"""UPDATE guspk.acds SET ticket = '{comment}' WHERE id = {acds_id}""")
			t.sql_update(f"""INSERT INTO guspk.acds_logs (id, status, user, message) VALUES ('{acds_id}', 'init', '{user}', 'Изменен комментарий "{db_comment[0][0]}" to "{comment}"')""")

	print(f'{old_acsw_node_id[0][0]} - {type(old_acsw_node_id[0][0])} ; {acsw_node_id} {type(acsw_node_id)}')
	if acsw_node_id != "False" and old_acsw_node_id[0][0] != int(acsw_node_id):
		t.sql_update(f"""UPDATE guspk.acds SET acsw_node_id = {acsw_node_id} WHERE id = {acds_id}""")
		t.sql_update(f"""INSERT into guspk.logs (scr_name, DEVICEID, WHO, message) VALUES ('get_acsw_node_id_update', '{acds_id}', '{user}', 'update acsw_node_id {old_acsw_node_id[0][0]} to {acsw_node_id}')""")
		t.sql_update(f"""INSERT INTO guspk.acds_logs (id, status, user, message) VALUES ('{acds_id}', 'init', '{user}', 'Выполнена замена шаблонов - {old_acsw_node_id[0][0]} to {acsw_node_id}')""")
		acswnodeid.update({'status': 'updated', 'message': f'template changed {old_acsw_node_id[0][0]} to {acsw_node_id}'})

	t.sql_connect('disconnect')

	return JsonResponse(acswnodeid, safe=False)

def get_acds_id_remove(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group:
		return render(request, 'activator/access.html')

	t = multimodule.FastModulAut()
	t.sql_connect('connect')
	t.oracle_connect('connect')
	user = request.user.username
	acds_id = ''.join(list(request.GET.get('id', str(False))))
	# ipaddmgm = ''.join(list(request.GET.get('ip', str(False))))

	data = t.sql_select(f"""SELECT a.email, a.status, h.IPADDMGM
							FROM guspk.acds a
							LEFT JOIN guspk.host_acsw_node an on an.ACSD_NODE_ID = a.acsw_node_id
							LEFT JOIN guspk.host h on h.DEVICEID = an.DEVICEID
							WHERE id = {acds_id}""", 'full')
	email = data[0][0]
	status = data[0][1]
	ip = data[0][2]
	if status == 'new' or status == 'init':
		t.sql_update(f"""INSERT into guspk.logs (scr_name, DEVICEID, WHO, message) VALUES ('get_acds_id_remove', '{acds_id}', '{user}', 'delete acds_id {acds_id} ip {ip} in status {status}')""")
		t.sql_update(f"""INSERT INTO guspk.acds_logs (id, ip, status, user, message) VALUES ('{acds_id}', '{ip}', 'removed', '{user}', 'Заявка аннулирована')""")
		t.sql_update(f"""DELETE FROM guspk.acds WHERE id = {acds_id}""")
		t.sql_update(f"""DELETE FROM guspk.host WHERE IPADDMGM = '{ip}'""")
		send_mail(f"""Заявка на ввод в эксплуатацию № {acds_id}""", f"""Ваша заявка № {acds_id} аннулирована.""", 'acds@ural.rt.ru', [f'{email}'])
		answer = {'answer': 'deleted'}
	elif status == 'other' or status == 'error(f)' or status == 'error(c)':
		t.sql_update(f"""INSERT into guspk.logs (scr_name, DEVICEID, WHO, message) VALUES ('get_acds_id_remove', '{acds_id}', '{user}', 'delete acds_id {acds_id} ip {ip} in status {status}')""")
		t.sql_update(f"""INSERT INTO guspk.acds_logs (id, ip, status, user, message) VALUES ('{acds_id}', '{ip}', 'removed', '{user}', 'Заявка аннулирована')""")
		t.sql_update(f"""DELETE FROM guspk.acds WHERE id = {acds_id}""")
		answer = {'answer': 'deleted'}
	else:
		answer = {'answer': 'error'}

	t.sql_connect('disconnect')
	t.oracle_connect('disconnect')



	return JsonResponse(answer, safe=False)

def get_acds_argus_status(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group and not 'argus' in group:
		return render(request, 'activator/access.html')

	t = multimodule.FastModulAut()
	t.sql_connect('connect')
	# ip = request.META.get('HTTP_X_FORWARDED_FOR')
	user = request.user.username
	email = request.user.email	
	acds_id = ''.join(list(request.GET.get('id', str(False))))
	preconf_check = t.sql_select(f"""SELECT host.IPADDMGM,  m.DEVICEMODELNAME, a.status, a.online, a.email, fr.region_code, a.argus
					FROM guspk.acds a
					INNER JOIN guspk.host_model m ON a.modelid = m.MODELID
					LEFT JOIN guspk.host_acsw_node an ON a.acsw_node_id = an.ACSD_NODE_ID
					LEFT JOIN guspk.host host ON an.DEVICEID = host.DEVICEID
					LEFT JOIN guspk.acds_fias af ON af.id = a.id
					LEFT JOIN guspk.fias_region fr ON af.region_fias_id = fr.region_fias_id
					WHERE a.id like '{acds_id}'""", 'full')
	ip, model, status, online, email, region_code, argus = preconf_check[0]

	id_status = t.sql_select(f"""SELECT status, argus from guspk.acds WHERE id like {acds_id}""", 'full')
	status, argus = id_status[0]
	if status == 'ok':
		t.sql_update(f"""INSERT into guspk.logs (scr_name, DEVICEID, WHO, message) VALUES ('get_acds_argus_status', '{ip}', '{user}', 'device status changed 2->3 acds_id {acds_id} ip {ip}')""")
		t.sql_update(f"""INSERT INTO guspk.acds_logs (id, ip, status, user, message) VALUES ('{acds_id}', '{ip}', '{status}', '{user}', 'Все работы по вводу завершены')""")
		t.sql_update(f"""UPDATE guspk.acds SET status = 'closed', argus = '1' WHERE id like '{acds_id}'""")
		t.sql_update(f"""UPDATE guspk.host SET DEVICESTATUSID = '3' WHERE IPADDMGM like '{ip}'""")
		send_mail(f"""Заявка на ввод № {acds_id}""", f"""Оборудование по заявке № {acds_id} введено в эксплуатацию.""", 'acds@ural.rt.ru', [f'{email}'])

	elif status == 'del':
		t.sql_update(f"""INSERT into guspk.logs (scr_name, DEVICEID, WHO, message) VALUES ('get_acds_argus_status', '{ip}', '{user}', 'device deleted {acds_id} ip {ip}')""")
		t.sql_update(f"""INSERT INTO guspk.acds_logs (id, ip, status, user, message) VALUES ('{acds_id}', '{ip}', '{status}', '{user}', 'Устройство выведено из эксплуатации')""")
		t.sql_update(f"""DELETE FROM guspk.host WHERE IPADDMGM like '{ip}'""")
		# mail_admins(f"""Заявка {acds_id} [DEL]""", f"""Выведено успешно""")
		send_mail(f"""Удалить из ИНИТИ""", f"""Устройство выведено из эксплуатации, прошу удалить из ИНИТИ. ip - {ip}.""", 'acds@ural.rt.ru', [f'monitoring@ural.rt.ru'])
		time.sleep(4)
		send_mail(f"""Заявка на вывод оборудования из Аргус № {acds_id}""", f"""Устройство по заявке № {acds_id} выведено из эксплуатации.""", 'acds@ural.rt.ru', [f'{email}'])

	elif status == 'other':
		t.sql_update(f"""INSERT into guspk.logs (scr_name, DEVICEID, WHO, message) VALUES ('get_acds_argus_status', '{acds_id}', '{user}', 'argus status changed to 5 acds_id {acds_id}')""")
		t.sql_update(f"""INSERT INTO guspk.acds_logs (id, ip, status, user, message) VALUES ('{acds_id}', '{ip}', 'other', '{user}', 'Изменения внесены в Аргус, заявка закрыта')""")
		t.sql_update(f"""UPDATE guspk.acds SET argus = 5, status = 'closed' WHERE id = {acds_id}""")
		mail_admins(f"""Заявка {acds_id} [OTHER]""", f"""Устройство изменено в Аргус, заявка закрыта""")		

	t.sql_connect('disconnect')
	answer = {'answer': 'ok'}

	return JsonResponse(answer, safe=False)	

def admin(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group and not 'argus' in group and not 'engineers' in group:
		return render(request, 'activator/access.html')

	t = multimodule.FastModulAut()
	t.sql_connect('connect')
	ip = request.META.get('HTTP_X_FORWARDED_FOR')
	user = request.user.username
	email = request.user.email

	if 'admins' in group or 'engineers' in group:
		query_status = "WHERE status not like 'closed' AND status not like 'ok' AND argus != 2 AND argus != 4"
	elif 'argus' in group:
		query_status = "WHERE status like 'ok' AND argus != 1 or status like 'del' AND argus != 3 or status like 'other' AND argus = 4"

	tickets_db = t.sql_select(f"""SELECT host.IPADDMGM, host.NETWORKNAME, CONCAT(net.GW,'/',net.MASK, '; ', net.VLAN) AS net, a.id, a.ticket, a.reason, a.uplink, m.DEVICEMODELNAME, a.serial, CONCAT(COALESCE(fc.city, ''), COALESCE(fs.settlement, ''), COALESCE(CONCAT(' ул. ', fstr.street), ''), COALESCE(CONCAT(' д. ', fhouse.house), ''), COALESCE(CONCAT(' к. ', fhouse.block), '')) as address, a.office, CONCAT(vt.HSI, ';', vt.IPTV, ';', vt.IMS, ';', vt.TR069) AS vlans, a.status, a.online, a.email, a.time_create, a.report, a.argus
	FROM guspk.acds a
	INNER JOIN guspk.host_model m ON a.modelid = m.MODELID
	LEFT JOIN guspk.host_acsw_node an ON a.acsw_node_id = an.ACSD_NODE_ID
	LEFT JOIN guspk.host_vlan_template vt ON an.VLAN_TEMPLATE_ID = vt.VLAN_TEMPLATE_ID 
	LEFT JOIN guspk.host_networks net ON an.NETWORK_ID = net.NETWORK_ID
	LEFT JOIN guspk.host host ON an.DEVICEID = host.DEVICEID
	LEFT JOIN guspk.host_fias hf ON hf.id = host.DEVICEID
	LEFT JOIN guspk.fias_city fc ON hf.city_fias_id = fc.city_fias_id
	LEFT JOIN guspk.fias_settlement fs ON hf.settlement_fias_id = fs.settlement_fias_id
	LEFT JOIN guspk.fias_street fstr ON hf.street_fias_id = fstr.street_fias_id
	LEFT JOIN guspk.fias_house fhouse ON hf.house_fias_id = fhouse.house_fias_id
	{query_status}
	ORDER BY id DESC;
	""", 'full')

	tickets = {}
	device_info = {}
	for (ipaddmgm, networkname, network, ticket_id, sd, reason, uplink, model, serial, address, office, vlans, status, online, email, create, report, argus) in tickets_db:
		# if report == None: 
		# 	report = 'None'
		if (online == 1): 
			tickets[ticket_id] = {"online": "success"}
		else: 
			tickets[ticket_id] = {"online": "danger"}

		if (status == 'init'):
			tickets[ticket_id].update({'badge': 'warning'})
			tickets[ticket_id].update({'config': 'config'})
			tickets[ticket_id].update({'btn_conf': 'primary'})
		# elif (status == 'error'):
		elif re.match('error', status):
			tickets[ticket_id].update({'badge': 'danger'})
			tickets[ticket_id].update({'config': 'config'})
			tickets[ticket_id].update({'btn_conf': 'primary'})
		elif (status == 'ok'):
			if (argus == 1):
				tickets[ticket_id].update({'btn_conf': 'success'})
			else:
				tickets[ticket_id].update({'btn_conf': 'danger'})
			tickets[ticket_id].update({'badge': 'success'})
			tickets[ticket_id].update({'config': 'close'})
			tickets[ticket_id].update({'argus': 'занесено'})
			tickets[ticket_id].update({'btn_argus': 'info'})
		elif (status == 'new'):
			tickets[ticket_id].update({'badge': 'info'})
			tickets[ticket_id].update({'config': 'config'})
			tickets[ticket_id].update({'btn_conf': 'primary'})
		elif (status == 'closed'):
			tickets[ticket_id].update({'badge': 'secondary'})
		elif (status == 'other'):
			tickets[ticket_id].update({'online': 'info'})
			tickets[ticket_id].update({'badge': 'secondary'})	
			tickets[ticket_id].update({'config': 'done'})
			tickets[ticket_id].update({'btn_conf': 'primary'})
			tickets[ticket_id].update({'btn_argus': 'success'})
			tickets[ticket_id].update({'argus': 'изменено'})			
		elif (status == 'del'):
			if (argus == 2):
				tickets[ticket_id].update({'online': 'warning'})
				tickets[ticket_id].update({'badge': 'danger'})
				tickets[ticket_id].update({'config': 'close'})
				tickets[ticket_id].update({'btn_argus': 'danger'})
				tickets[ticket_id].update({'argus': 'удалено'})
			else:
				tickets[ticket_id].update({"online": "warning"})
				tickets[ticket_id].update({'badge': 'danger'})
				tickets[ticket_id].update({'config': 'remove'})
				tickets[ticket_id].update({'btn_conf': 'danger'})

		tickets[ticket_id].update({'sd': sd, 'reason': reason, 'uplink': uplink, 'model': model, 'serial': serial, 'address': address, 'office': office, 'vlans': vlans, 'network': network, 'status': status, 'email': email, 'create': create, 'report': report, 'ip': ipaddmgm, 'hostname': networkname})
		date =  (tickets[ticket_id]['create'].strftime("%d.%m.%Y"))
		time =  (tickets[ticket_id]['create'].strftime("%H:%M"))
		tickets[ticket_id].update({'create': date+' '+time})
		device_info.update({ticket_id: {"serial": serial, "reason": reason, "address": address}})

	# device_info = json.dumps(device_info)

	values = {}
	values['group'] = {'group': group}
	values['tickets'] = tickets
	values['device_info'] = device_info

	t.sql_connect('disconnect')
	
	return render(request, 'activator/admin.html', values)


def mail_generator(acds_id):
	main_path_template = 'scripts/jn_templates'
	port_uplink = None
	t = multimodule.FastModulAut()
	# t.ws_connect('chat/mail_generator/')
	t.sql_connect('connect')
	device_data = t.sql_select(f"""SELECT host.IPADDMGM, host.NETWORKNAME, CONCAT(net.GW,'/',net.MASK) AS network, net.VLAN, vt.HSI, vt.IPTV, vt.IMS, vt.TR069, m.DEVICEMODELNAME, a.SERIAL, a.OFFICE, a.email, a.ticket, CONCAT(COALESCE(fc.city, ''), COALESCE(fs.settlement, ''), COALESCE(CONCAT(' ул. ', fstr.street), ''), COALESCE(CONCAT(' д. ', fhouse.house), ''), COALESCE(CONCAT(' к. ', fhouse.block), '')) as address
					FROM guspk.acds a
					INNER JOIN guspk.host_model m ON a.modelid = m.MODELID
					LEFT JOIN guspk.host_acsw_node an ON a.acsw_node_id = an.ACSD_NODE_ID
					LEFT JOIN guspk.host_vlan_template vt ON an.VLAN_TEMPLATE_ID = vt.VLAN_TEMPLATE_ID 
					LEFT JOIN guspk.host_networks net ON an.NETWORK_ID = net.NETWORK_ID
					LEFT JOIN guspk.host host ON an.DEVICEID = host.DEVICEID
					LEFT JOIN guspk.host_fias hf ON hf.id = host.DEVICEID
					LEFT JOIN guspk.fias_city fc ON hf.city_fias_id = fc.city_fias_id
					LEFT JOIN guspk.fias_settlement fs ON hf.settlement_fias_id = fs.settlement_fias_id
					LEFT JOIN guspk.fias_street fstr ON hf.street_fias_id = fstr.street_fias_id
					LEFT JOIN guspk.fias_house fhouse ON hf.house_fias_id = fhouse.house_fias_id
					WHERE a.id like '{acds_id}'""", 'full')
	t.sql_connect('disconnect')
	
	data_settings = {}
	# t.ws_send_message(f"sql request - {device_data[0]}")
	ipaddmgm, networkname, network, mgmvlan, hsi, iptv, ims, tr069, model, serial, office, email, ticket, address = device_data[0]
	gw, mask = network.split('/')
		
	# t.ws_send_message(f"gw - {gw} | mask - {mask}")
	netaddress = IPv4Network(f"{network}", strict=False)
	netmask = str(netaddress.netmask)
	# netmask = IPv4Network(f'{network}').netmask
	# t.ws_send_message(f"netmask - {netmask}")

	vlans = f"{hsi};{iptv};{ims};{tr069}"

	header = f"""Настройки управления для оборудования в {address} по заявке ACDS {acds_id}
	серийный номер устройства {serial}
	Сетевое имя {networkname}
	Для настройки управления cкопировать и вставить в консоль эти команды."""

	footer = f"""Если что-то совсем не получается? то можно позвонить нам
	Борисов Сергей  +7(3452)599233
	Южаков Дмитрий  +7(3452)599357"""

	# t.ws_send_message(f"email - {email}")
#SWITCH
	if re.search(r'2124', model):
		port_uplink = 'gi1/0/28'
		path_file = f"{main_path_template}/template_commands_eltex_mes_all_mng.jn2"
	elif re.search(r'2208|2308', model):
		port_uplink = 'gi1/0/12'
		mask = netmask
		path_file = f"{main_path_template}/template_commands_eltex_mes_all_mng.jn2"
	elif re.search(r'3508', model):
		port_uplink = 'gi1/0/10'
		path_file = f"{main_path_template}/template_commands_eltex_mes_all_mng.jn2"
	elif re.search(r'1124', model):
		port_uplink = 'gi1/0/4'
		path_file = f"{main_path_template}/template_commands_eltex_mes_all_mng.jn2"
	elif re.search(r'2324|3324|3124', model):
		port_uplink = 'te1/0/4'
		path_file = f"{main_path_template}/template_commands_eltex_mes_all_mng.jn2"
	elif re.search(r'2428|2408', model):
		port_uplink = 'Gi 0/28'
		if re.search(r'2408', model):
			port_uplink = 'Gi 0/10'
		path_file = f"{main_path_template}/template_commands_eltex_mes_24xx_mng.jn2"
		mask = netmask
	elif re.search(r'3200', model):
		port_uplink = '28'
		path_file = f"{main_path_template}/template_commands_dlink_3200_mng.jn2"
	elif re.search(r'3400|3600', model):
		if re.search(r'3400', model):
			port_uplink = 'gi1/0/16'
			path_file = f"{main_path_template}/template_commands_cisco_ME3400_mng.jn2"
		if re.search(r'3600', model):
			port_uplink = 'Te0/2'
			path_file = f"{main_path_template}/template_commands_cisco_ME3600_mng.jn2"
	elif re.search(r'ES3528|ES3526', model):
		mask = netmask
		if '3528' in model:
			port_uplink = '1/28'
		if '3526' in model:
			port_uplink = '1/26'
		path_file = f"{main_path_template}/template_commands_edge_core_3528_mng.jn2"
#DSLAM
	elif re.search(r'1212|1248', model):
		path_file = f"{main_path_template}/template_commands_zyxel_1212_1248_mng.jn2"
	elif re.search(r'7330|7302', model):
		path_file = f"{main_path_template}/template_commands_alcatel_7302_mng.jn2"
#OLT
	elif re.search(r'4000', model):
		mask = netmask
		path_file = f"{main_path_template}/template_commands_ma4000_mng.jn2"
	elif re.search(r'LTP-4', model):
		mask = netmask
		path_file = f"{main_path_template}/template_commands_ltp-4x_mng.jn2"
	elif re.search(r'LTP-8', model):
		mask = netmask
		path_file = f"{main_path_template}/template_commands_ltp-8x_mng.jn2"
#VG
	elif re.search(r'MG-|TAU', model):
		path_file = f"{main_path_template}/template_commands_VG_all_mng.jn2"

	else:
		path_file = 'none'
	# t.ws_send_message(f"path_file - {path_file}")

	data_settings['acds_id'] = acds_id
	data_settings['ipaddmgm'] = ipaddmgm
	data_settings['networkname'] = networkname
	data_settings['gw'] = gw
	data_settings['mask'] = mask
	data_settings['network'] = network
	data_settings['mgmvlan'] = mgmvlan
	data_settings['vlans'] = vlans
	data_settings['hsi'] = hsi
	data_settings['iptv'] = iptv
	data_settings['ims'] = ims
	data_settings['tr069'] = tr069
	data_settings['serial'] = serial
	data_settings['office'] = office
	data_settings['port_uplink'] = port_uplink
	data_settings['ticket'] = ticket
	data_settings['model'] = model
	data_settings['address'] = address

	# t.ws_send_message(f"data_settings - {data_settings}")
	if path_file != 'none':
		with open (path_file) as f:
			device_template = f.read()
			template = jinja2.Template(device_template)
			mail_data = template.render(data_settings).splitlines()
	else:
		mail_data = f'ip - {ipaddmgm}, hostname - {networkname}, mgmvlan - {mgmvlan}\n network - {network}'.splitlines() #vlans - {vlans}
	# t.ws_send_message(f"mail_data - {mail_data}")
	# t.ws_close()
	return mail_data, email, data_settings, header, footer


def mail_sender(*args, admins=False):
	"""
	if need send to any user (['header', 'body', ['recipient1', 'recipient2'])
	if send only admins (['header', 'body', admins=True])
	"""
	def send_status(error):
		if admins == False:
			try:
				send_mail(f"""{args[0]}""", f"""{args[1]}""", 'acds@ural.rt.ru', [args[2]])
				error = 'ok'
			except:
				error = 'error'
		else:
			try:
				mail_admins(f"""{args[0]}""", f"""{args[1]}""")
				error = 'ok'
			except:
				error = 'error'
	
		return error

	error = 'try'
	while error != 'ok':
		error = send_status(error)
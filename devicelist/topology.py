from django.shortcuts import render
from django.conf import settings
from django.shortcuts import redirect
from django.core.mail import send_mail
from django.core.mail import mail_admins
from django.http import JsonResponse
from django.utils.safestring import mark_safe

import datetime
import sys, os, re, time
import jinja2
import json
import multimodule
import getpass
import ipaddress


def start(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

	return render(request, 'devicelist/topology.html')


def create_vlan(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

	return render(request, 'devicelist/create_vlan.html')

def get_create_vlan(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'engineers' in group and not 'admins' in group:
		return render(request, 'devicelist/access.html')

	if request.GET:
		all_data = json.loads(request.GET['all_data'])

		result = {
			'count': 1,
			'status': 'wait',
			'message_error': 'wait',
		}

		if not all_data.get('ip') or not all_data.get('vlan'):
			result.update({'status': 'error', 'message_error': "not IP or Vlan"})
			return result

		result.update({'vlan': all_data['vlan'], 1: {'ip': all_data['ip']}})

		t = multimodule.FastModulAut()
		t.sql_connect('connect')
		t.count_website(t, page='create_vlan', username=request.user.username)

		while True:
			count = result['count']
			query = f"""SELECT h.IPADDMGM, h.NETWORKNAME, m.DEVICEMODELNAME, top.child_port, 
					(SELECT IPADDMGM FROM guspk.host WHERE DEVICEID = top.parent), top.parent_port
					FROM guspk.host h
					LEFT JOIN guspk.host_model m ON m.MODELID = h.MODELID
					LEFT JOIN guspk.topology top ON top.child = h.DEVICEID
					WHERE h.IPADDMGM = '{result[count]['ip']}'"""

			data = t.sql_select(query, 'full')
			if not data or not data[0][4]:
				result.update({'status': 'end', 'message_error': 'end'})
				break

			result[count].update({
				'ip': data[0][0],
				'hostname': data[0][1],
				'model': data[0][2],
				'port_uplink': data[0][3],
				'create_vlan': 'No',
				'conf_child_port': 'No',
				'conf_port_uplink': 'No',
				'conf_list': [],
			})
			result[count + 1] = {
				'ip': data[0][4],
				'child_port': data[0][5],
			}

			result['count'] += 1
			if count >= 20:
				break
		c = CreateVlan()
		result = c.main(result, t)

		t.sql_connect('disconnect')

	return JsonResponse(result, safe=False)

class CreateVlan(object):

	def check_search(self, t, command, regular, desc, key=re.M, prompt='default', time=60):

		if prompt == 'default':
			t.new_sendline(command, timeout=time)
		else:
			t.new_sendline(command, timeout=time, prompt=prompt)

		data = t.data_split()
		print(f"check_search|data: {data}")
		print('======================================================================================')
		match = re.search(regular, data, key)
		if (match):
			print(f"check_search|match.groups: {match.groups()}")
			print('======================================================================================')
			return match.groups()
		else:
			print(f"check_search|status|{desc}")
			print('======================================================================================')
			return {"status": "error", "message_error": desc}

	def check_findall(self, t, command, regular, desc, key=re.M, prompt='default', time=60):

		if prompt == 'default':
			t.new_sendline(command, timeout=time)
		else:
			t.new_sendline(command, timeout=time, prompt=prompt)

		data = t.data_split()
		print(f"check_findall|data: {data}")
		print('======================================================================================')
		match = re.findall(regular, data, key)
		if (match):
			print(f"check_findall|match.groups: {match}")
			print('======================================================================================')
			return match
		else:
			print(f"check_findall|status|{desc}")
			print('======================================================================================')
			return {"status": "error", "message_error": desc}

	def compare_vlan(self, list_vlan, vlan):
		match = re.findall(r'([\d-]+)', list_vlan)
		for vlans in match:
			match = re.search(r'^(\d+)-(\d+)$', vlans)
			if match:
				if int(match[1]) <= vlan and vlan <= int(match[2]):
					return 'yes'
			else:
				if int(vlans) == vlan:
					return 'yes'
		return 'no'

	def switch(self, result, t):

		def bbagg_upe_juniper(result, count, t):
			return result

		def eltex_x3xx_x1xx(result, count, t):

			# apply config
			if result['status'] == 'apply_config':
				pass


			# проверка наличие влана
			if result[count]['create_vlan'] == 'No':
				check = self.check_search(t, f"show vlan tag 1111", r'(\d+)\s+\w+\s.+?\s+permanent', 'eltex_x3xx_x1xx|vlan не найден')
				if type(check) != dict:
					result[count]['create_vlan'] = 'Yes'

			# проверка портов на наличие влана
			for st in [['conf_child_port', 'child_port'], ['conf_port_uplink', 'port_uplink']]:
				if result[count][st[0]] == 'No' and st[1] in result[count]:
					check = self.check_findall(t, f"show running-config interfaces {result[count][st[1]]}", r'(\d+)\s+\w+\s.+?\s+permanent', f'eltex_x3xx_x1xx|{st[0]} vlan не найден')
					if type(check) != dict:
						result[count][st[0]] = self.compare_vlan(check, result['vlan'])


			# write config
			if result['status'] != 'apply_config':
				if any([result[count]['create_vlan'] == 'No', result[count]['conf_child_port'] == 'No', result[count]['conf_port_uplink'] == 'No']):
					result[count]['conf_list'].append('configure')

				if result[count]['create_vlan'] == 'No':
					result[count]['conf_list'].append('vlan database')
					result[count]['conf_list'].append(f"vlan {result['vlan']}")
					result[count]['conf_list'].append('exit')

				if result[count]['conf_port_uplink'] == 'No':
					result[count]['conf_list'].append(f"interface {result[count]['port_uplink']}")
					result[count]['conf_list'].append(f"vlan {result['vlan']}")
					result[count]['conf_list'].append('exit')

				if result[count]['conf_child_port'] == 'No' and 'child_port' in result[count]:
					result[count]['conf_list'].append(f"interface {result[count]['child_port']}")
					result[count]['conf_list'].append(f"vlan {result['vlan']}")
					result[count]['conf_list'].append('exit')

				if any([result[count]['create_vlan'] == 'No', result[count]['conf_child_port'] == 'No', result[count]['conf_port_uplink'] == 'No']):
					result[count]['conf_list'].append('exit')
					result[count]['conf_list'].append('write memory', prompt='press any key for no')
					result[count]['conf_list'].append('y')

			return result
			

		def eltex_24xx(result, count, t):
			return result


		def cisco_switch(result, count, t):
			return result


		def zyxel_switch(result, count, t):
			return result


		def edgecore_switch(result, count, t):
			return result


		def lumia_switch(result, count, t):
			return result


		def dlink_switch(result, count, t):
			return result


		def alcitec_switch(result, count, t):
			return result


		count = result['count']

		login, password = 'tum_support', 'hEreR2Mu3E'

		if re.search(r'BC|Lumia', result[count]['model']):
			login, password = 'admin', 'Cdbnx0AA'

		check_aut = t.aut(ip=result[count]['ip'], model=result[count]['model'], login=login, password=password)

		if re.search(r'MES-3528|MGS-3712|MES3500-24|4728|4012', result[count]['model']) and check_aut != 0:
			"""Дурацкие зиксиля, иногда авторизация не проходит с первого раза. 
				После успешного ввода логина и пароля - telnet сессия закрывается
				приходится лепить костыли"""
			check_aut = t.aut(ip=result[count]['ip'], model=result[count]['model'], login=login, password=password)

		if check_aut != 0:
			result.update({'status': 'error','message_error': f"Can't connect {result[count]['ip']}"})
			return result

		if re.search(r'EX4500-40F|EX9208|ACX2100|QFX5100', result[count]['model']):
			result = bbagg_upe_juniper(result, count, t)
		elif re.search(r'3324|3124|2324|2124|3508|2308|2208|1124', result[count]['model']):
			result = eltex_x3xx_x1xx(result, count, t)
		elif re.search(r'3400|3600|3750|2960|2950|3550|3560', result[count]['model']):
			result = cisco_switch(result, count, t)
		elif re.search(r'MES-3528|MGS-3712|MES3500-24|4728|4012', result[count]['model']):
			result = zyxel_switch(result, count, t)
		elif re.search(r'2428|2408', result[count]['model']):
			result = eltex_24xx(result, count, t)
		elif re.search(r'3526XA|3528M', result[count]['model']):
			result = edgecore_switch(result, count, t)
		elif re.search(r'BC|Lumia', result[count]['model']):
			result = lumia_switch(result, count, t)
		elif re.search(r'DES|DGS', result[count]['model']):
			result = dlink_switch(result, count, t)
		elif re.search(r'24100', result[count]['model']):
			result = alcitec_switch(result, count, t)
		else:
			result.update({'status': 'error','message_error': f"def switch | There is no algorithm for this model {result[count]['model']}"})
		
		return result

	def main(self, result, t):
		while True:			
			result = self.switch(result, t)

			result['count'] -= 1

		return result
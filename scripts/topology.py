#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, os, re, time
import jinja2
import json
import multimodule
import getpass
import ipaddress
import datetime
import asyncio
try:
	from acds import configuration
except:
	import configuration

class getTopology(object):

	def check_search(self, t, command, regular, desc, key=re.M, prompt='default', time=60):

		if prompt == 'default':
			t.new_sendline(command, timeout=time)
		else:
			t.new_sendline(command, timeout=time, prompt=prompt)

		data = t.data_split()
		print(f"check_search|data: {data} regex {regular}")
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
		# data = unicode(data, errors='replace')
		print(f"check_findall|data: {data}")
		print(f"check_findall|data_type: {type(data)}")
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


	def update_topology(self, t, id_child, mac, id_parent='NULL', child_port='NULL', parent_port='NULL'):
		print(f"id_child: {id_child} | id_parent: {id_parent} | child_port: {child_port} | parent_port: {parent_port};")
		print(f"SELECT parent, child_port, parent_port FROM guspk.topology WHERE child={id_child};")
		print('======================================================================================')
		match = t.sql_select(f'SELECT parent, child_port, parent_port FROM guspk.topology WHERE child={id_child};', 'full')
		if match:
			if id_parent != 'NULL' and id_parent != match[0][0]:
				print(f"UPDATE guspk.topology SET parent={id_parent} WHERE child={id_child};")
				print('======================================================================================')
				t.sql_update(f"UPDATE guspk.topology SET parent={id_parent} WHERE child={id_child};")
			if child_port != 'NULL' and child_port != match[0][1]:
				print(f"UPDATE guspk.topology SET child_port='{child_port}' WHERE child={id_child};")
				print('======================================================================================')
				t.sql_update(f"UPDATE guspk.topology SET child_port='{child_port}' WHERE child={id_child};")
			if parent_port != 'NULL' and parent_port != match[0][2]:
				print(f"UPDATE guspk.topology SET parent_port='{parent_port}' WHERE child={id_child};")
				print('======================================================================================')
				t.sql_update(f"UPDATE guspk.topology SET parent_port='{parent_port}' WHERE child={id_child};")

			# t.sql_update(f"UPDATE guspk.host SET mac = '{mac}' WHERE DEVICEID = {id_child}")
		else:
			if child_port != 'NULL':
				child_port = f"'{child_port}'"
			if parent_port != 'NULL':
				parent_port = f"'{parent_port}'"


			print(f"INSERT INTO guspk.topology (child, parent, child_port, parent_port) VALUES ({id_child}, {id_parent}, {child_port}, {parent_port});")
			print('======================================================================================')
			t.sql_update(f"INSERT INTO guspk.topology (child, parent, child_port, parent_port) VALUES ({id_child}, {id_parent}, {child_port}, {parent_port});")


	def select_topology(self, t, id_child):
		match = t.sql_select(f'SELECT parent, child_port, parent_port FROM guspk.topology WHERE child={id_child};', 'full')
		if match:
			return {'parent': match[0][0], 'child_port': match[0][1], 'parent_port': match[0][2]}
		else:
			return None



	def peagg(self, result, t, dir_name):

		def find_in_cisco(result, t):
			t.new_sendline('terminal length 0')
			vrf = ''
			if result['vrf'] and result['vrf'] != 'CORE':
				vrf = f"vrf {result['vrf']} "

			t.new_sendline(f"ping {vrf} {result['ip']} repeat 20 timeout 0", Timeout = 20)

			# Получить из arp MAC и Vlan управления
			check = self.check_search(t, f"show ip arp {vrf}| include {result['ip']} ", r'\d\s+([\w\.]+)\s+ARPA\s+Vlan(\d+)', 'peagg_cisco|не найден arp')
			if type(check) == dict:
				result.update(check)
				return result
			mac, vlan = check

			# Определяем порт в сторону нижестоящего коммутатора и сервисинстанс
			check = self.check_search(t, f"show mac address-table address {mac} | include {vlan}", r'Yes\s+\d+\s+(.*?)\s.+?\s(\d+)/?', 'peagg_cisco|не найден mac')
			if type(check) == dict:
				result.update(check)
				return result
			port_pe, serviceinstance = check
			
			# Определяем новый влан, если он перемаркировывается и если влан уходит в тунельный влан
			match = re.search(r'Po(\d+)', port_pe)
			if match:
				port_pe_full = f'Port-channel {match.group(1)}'
			check = self.check_search(t, f"show running-config interface {port_pe_full} | section  service instance {serviceinstance} ", r'encapsulation dot1q (\d+)( second-dot1q (\d+))?', 'peagg_cisco|show running-config')
			if type(check) == dict:
				result.update(check)
				return result

			if check[2]:
				print(f"*/*/*/*/*{check}*/*/*/*/*")
				vlan = check[2]
				tunnel_vlan = check[0]
			else:
				vlan = check[0]
				tunnel_vlan = None

			# Определяем хостнейм нижестоящего коммутатора
			check = self.check_search(t, f"show interfaces description | include {port_pe} ", r'(\d{2}-[-\da-z]+)', f"peagg_cisco|incorrect description port {port_pe}", re.I)
			if type(check) == dict:
				result.update(check)
				return result
			peportdesc = check[0]

			# меняем формат мак адреса и записываем в словарь полученные данные
			mac = re.sub(r'(\w\w)[:.-]?(\w\w)[:.-]?(\w\w)[:.-]?(\w\w)[:.-]?(\w\w)[:.-]?(\w\w)', r'\1:\2:\3:\4:\5:\6', mac)
			result.update({"mac": mac, "vlan": vlan})
			if tunnel_vlan != None and tunnel_vlan != '':
				print(f"****update result, insert tunnel vlan****")
				result.update({"tunnel_vlan": tunnel_vlan})
			result[1].update({"port": port_pe})
			result[2] = {"desc": peportdesc}

			return result


		def find_in_juniper(result, t):

			# Определяем MAC, порт в сторону нижестоящего коммутатора, Vlan
			check = self.check_search(t, f"show arp | match {result['ip']}", r'([\w:]+).+?(ae\d+)\.(\d+)', 'peagg_juniper|не найден arp', prompt = '>')
			if type(check) == dict:
				result.update(check)
				return result
			mac, port_pe, vlan = check


			# Определяем хостнейм нижестоящего коммутатора
			check = self.check_search(t, f'show interfaces descriptions | match "{port_pe} "', r'to\s+(\d{2}-[-\da-z]+)', 'peagg_juniper|не найден description', re.I, prompt = '>')
			if type(check) == dict:
				result.update(check)
				return result
			peportdesc = check[0]


			mac = re.sub(r'(\w\w)[:.-]?(\w\w)[:.-]?(\w\w)[:.-]?(\w\w)[:.-]?(\w\w)[:.-]?(\w\w)', r'\1:\2:\3:\4:\5:\6', mac)
			result.update({"mac": mac, "vlan": vlan})
			result[1].update({"port": port_pe})
			result[2] = {"desc": peportdesc}
			return result



		check_aut = t.aut(ip = result[1]['ip'], model = result[1]['model'], login = 'tum_support', password = 'hEreR2Mu3E', logs_dir = f"{getattr(configuration, 'LOGS_DIR')}/{dir_name}")
		if check_aut != 0:
			check_aut = t.aut(ip = result[1]['ip'], model = result[1]['model'], login = 'tum_support', password = 'hEreR2Mu3E', logs_dir = f"{getattr(configuration, 'LOGS_DIR')}/{dir_name}", proxy = True)
			if check_aut != 0:
				result.update({'status': 'error','message_error': f"Cant connect {result[1]['ip']}"})
				return result

		if result['ip']:
			if re.search(r'7606|7609', result[1]['model']):
				result = find_in_cisco(result, t)
			elif re.search(r'MX480|QFX', result[1]['model']):
				result = find_in_juniper(result, t)
			else:
				result.update({'status': 'error','message_error': "def peagg | no algorithm for this model"})
		else:
			result.update({'status': 'error','message_error': "def peagg | Algorithm not developed"})

		if result['status'] != 'wait':
			return result

		if 2 in result and 'desc' in result[2]:
			data = t.sql_select(f"SELECT h.IPADDMGM, m.DEVICEMODELNAME, h.DEVICEID FROM guspk.host h, guspk.host_model m WHERE h.MODELID = m.MODELID AND NETWORKNAME = '{result[2]['desc']}'", 'full')
			if data[0][0] != result[1]['ip']:
				result[2].update({"ip": data[0][0], "model": data[0][1], 'id': data[0][2]})
		else:
			result.update({'status': 'error','message_error': 'def peagg | not desc'})

		return result


	def switch(self, result, t, dir_name):

		def bbagg_upe_juniper(result, num, next_num, t):

			def find_port(port, num, next_num, result, t):
				t.new_sendline(f"show interfaces descriptions | match \"{port} \"", prompt='@')
				data = t.data_split()
				match = re.search(r"up\s+up.+?((\d+|[A-Z]+-UCN)-[A-Z0-9-]+)", data, re.M)
				if match and match[1] != result[1]['desc']:
					desc = match[1]
					result[num].update({'port': port})
					result[next_num] = {'desc': desc}
					result.update({'status': 'wait'})
					print(f"$$$$$$$$$$$ RESULT IN FIND_PORT_JUN $$$$$$$$$$$ {result} $")
					return result
				else:
					result.update({'status': 'next'})
					return result

			if result['status'] != 'end_device':
				if 'tunnel_vlan' in result:
					print(f"=== RESULT ==={result}")
					com_show_vlan = f"show vlans vlan_{result['tunnel_vlan']}"
					if re.search(r'ACX2100' ,result[num]['model']):
						com_show_vlan = f"show bridge domain vlan{result['tunnel_vlan']}"

					check = self.check_findall(t, com_show_vlan, rf"([\w\/-]+)\.\d+\*?", "bbagg_upe_juniper|Cant find description", prompt='@')
					print(f"-----check - {check}")
					if type(check) == dict:
						result.update(check)
						# return result

					elif len(check) == 2 and result['status'] != 'error':
						for m in check:
							result = find_port(m, num, next_num, result, t)
							if result['status'] == 'wait':
								break
					elif len(check) > 2 or len(check) < 2 or not check:
						com_show_mac = f"show ethernet-switching table vlan | match {result['mac']}" #vlan_{result['tunnel_vlan']}
						check = self.check_search(t, com_show_mac, rf"\s+{result['mac']}.+?([\w\/-]+)\.\d+", f"bbagg_upe_juniper {result[num]['ip']}|не найден mac(1)", prompt='@', time=60)
						result = find_port(check[0], num, next_num, result, t)
					else:
						result.update({'status': "error", 'message_error': "bbagg_upe_juniper|Cant find description"})


				if not 'tunnel_vlan' in result or result['message_error'] == "bbagg_upe_juniper|Cant find description":
					result.update({'status': "wait", 'message_error': "wait"})

					com_show_mac = f"show ethernet-switching table | match {result['mac']}"
					if re.search(r'ACX2100' ,result[num]['model']):
						com_show_mac = f"show bridge mac-table | match {result['mac']}"

					check = self.check_search(t, com_show_mac, rf"\s+{result['mac']}.+?([\w\/-]+)\.\d+", f"bbagg_upe_juniper {result[num]['ip']}|не найден mac(2)", prompt='@', time=60)
					if type(check) == dict:
						result.update(check)
						return result
					result = find_port(check[0], num, next_num, result, t)

					if result['status'] == 'next':
						result.update({'status': "error", 'message_error': "def bbagg_upe_juniper | Cant find description 2"})
						return result

			# определяем port Uplink
			check = self.check_findall(t, f"show interfaces descriptions | match {result[num - 1]['desc']} ", r"([\w\/-]+)\s+up\s+up", f"bbagg_upe_juniper {result[num]['ip']}|не удалось определить порт uplink", prompt='@')
			if type(check) == dict:
				result.update(check)
				return result

			if len(check) == 1:
				result[num].update({'port_uplink': check[0]})
			else:
				regex = re.compile(r'^(ae\d+)')
				check = list(filter(regex.search, check))
				if len(check) == 1:
					result[num].update({'port_uplink': check[0]})
				else:
					result.update({'status': "error", 'message_error': "def bbagg_upe_juniper | Cant find description 3"})

			return result
			

		def eltex_x3xx_x1xx(result, num, next_num, t):

			if result['status'] != 'end_device':
				# Определяем порт нижестоящего коммутатора
				check = self.check_search(t, f"show mac address-table address {result['mac']}", rf"\w+\s+{result['mac']}\s+([\w\/-]+)\s+dynamic", f"eltex {result[num]['ip']}|не найден mac")
				if type(check) == dict:
					result.update(check)
					return result
				result[num].update({'port': check[0]})

				# Определяем имя устройтсва
				check = self.check_search(t, f"show interfaces {result[num]['port']} | i Description", r"Description:.*?((\d+|[A-Z]+-UCN)-[A-Z0-9-]+)", f"eltex_x3xx {result[num]['ip']}|не найден description")
				# check = self.check_search(t, f"show interfaces description | include {result[num]['port']} ", rf"{result[num]['port']}.+Up.+?((\d+|[A-Z]+-UCN)-[A-Z0-9-]+)", 'eltex|не найден description')
				if type(check) == dict:
					result.update(check)
					return result
				result[next_num] = {'desc': check[0]}

			# Определяем IP адрес шлюза
			if re.search(r'2208', result[num]['model']):
				check = self.check_search(t, "sho ip interface | i Act", r"(1\S+)\s+", f"eltex2208 {result[num]['ip']}|не найден gateway")
			else:
				check = self.check_search(t, "show ip route static | include 0.0.0.0", r"[SA].+via\s+([\d\.]+).+vlan\s+\d+", f"eltex33xx {result[num]['ip']}|не найден gateway")
			if type(check) == dict:
				result.update(check)
				return result
			gateway = check[0]

			# определяем port Uplink
			check = self.check_search(t, f"show arp | include {gateway}", r"vlan\s+\d+\s+([\w\/]+)\s+", f"eltex {result[num]['ip']}|не удалось определить порт uplink")
			if type(check) == dict:
				result.update(check)
				return result
			result[num].update({'port_uplink': check[0]})

			return result
			

		def eltex_24xx(result, num, next_num, t):

			if result['status'] != 'end_device':
				# Определяем порт нижестоящего коммутатора
				check = self.check_search(t, f"show mac-address-table address {result['mac']}", rf"{result['mac']}\s+Learnt\s+([\w\/]+)", f"eltex_24xx {result[num]['ip']}|не найден mac")
				if type(check) == dict:
					result.update(check)
					return result
				result[num].update({'port': check[0]})

				# Определяем имя устройтсва
				check = self.check_search(t, f"""show interfaces description | grep "{result[num]['port']} " """, rf"{result[num]['port']}.+\$((\d+|[A-Z]+-UCN)-[A-Z0-9-]+)", 'eltex_24xx|не найден description')
				if type(check) == dict:
					result.update(check)
					return result
				result[next_num] = {'desc': check[0]}

			# Определяем IP адрес шлюза
			# check = self.check_search(t, "show ip route", r"[\d\.\/]+\s+\[1\/1\]\s+via\s+([\d\.]+)", 'eltex_24xx|не найден gateway')
			# if type(check) == dict:
			# 	result.update(check)
			# 	return result

			# определяем vlan, mac шлюза
			check = self.check_search(t, "show ip arp", rf"(\S+)\s+ARPA\s+vlan(\d+)", f"eltex_24xx {result[num]['ip']}|не найден mac шлюза")
			if type(check) == dict:
				result.update(check)
				return result

			# определяем port Uplink
			check = self.check_search(t, f"show mac-address-table vlan {check[1]} address {check[0]}", rf"{check[1]}\s+{check[0]}\s+Learnt\s+([\w\/]+)", f"eltex_24xx {result[num]['ip']}|не удалось определить порт uplink")
			if type(check) == dict:
				result.update(check)
				return result
			result[num].update({'port_uplink': check[0]})

			return result


		def cisco_switch(result, num, next_num, t):

			if result['status'] != 'end_device':
				# Определяем порт нижестоящего коммутатора
				check = self.check_search(t, f"show mac address-table address {result['mac']}", r"\d+[\s\w\.]+DYNAMIC\s+([\w\/]+)[\+]?", f"cisco {result[num]['ip']}|не найден mac")
				if type(check) == dict:
					result.update(check)
					return result
				result[num].update({'port': check[0]})

				# Определяем имя устройтсва
				check = self.check_search(t, f"show interfaces description | include {result[num]['port']} ", rf"{result[num]['port']}\s+up\s+up\s+.*?((\d+|[A-Z]+-UCN)-[A-Z0-9-]+)", 'cisco|не найден description')
				if type(check) == dict:
					result.update(check)
					return result
				result[next_num] = {'desc': check[0]}

			# Определяем IP адрес шлюза
			com_show_route = "show ip route | include gateway"
			if re.search(r'3750|3400' ,result[num]['model']):
				com_show_route = "show ip route static"
			if re.search(r'2950|2960' ,result[num]['model']):
				com_show_route = "show running-config | include default-gateway"

			check = self.check_search(t, com_show_route, r"[is|via|way]\s+(\d+\.\d+\.\d+\.\d+)", f"cisco {result[num]['ip']}|не найден gateway")
			if type(check) == dict:
				result.update(check)
				return result
			print(check)
			gateway = check[0]

			# определяем mac gateway и vlan управления
			com_show_ip_arp = f"show ip arp | include {gateway}"
			if re.search(r'2950' ,result[num]['model']):
				com_show_ip_arp = "show ip arp"

			check = self.check_search(t, f"show ip arp | include {gateway}", r"([\w\.]+)\s+ARPA\s+Vlan(\d+)", f"cisco {result[num]['ip']}|не найден arp")
			if type(check) == dict:
				result.update(check)
				return result
			mac_gateway, vlan_mng = check

			# определяем port Uplink
			check = self.check_search(t, f"show mac address-table address {mac_gateway} | include {vlan_mng}", r"DYNAMIC\s+(\S+)", f"cisco {result[num]['ip']}|не удалось определить порт uplink")
			if type(check) == dict:
				result.update(check)
				return result
			result[num].update({'port_uplink': check[0]})

			return result


		def zyxel_switch(result, num, next_num, t):

			if result['status'] != 'end_device':
				# Определяем порт нижестоящего коммутатора
				com_show_mac = f"show mac address-table mac {result['mac']}"
				if re.search(r'4012' ,result[num]['model']):
					com_show_mac = f"show mac address-table vlan {result['vlan']}"

				check = self.check_search(t, com_show_mac, rf"(\d+)\s+{result['vlan']}\s+{result['mac']}", f"zyxel {result[num]['ip']}|не найден mac", prompt='#')
				if type(check) == dict:
					result.update(check)
					return result
				result[num].update({'port': check[0]})

				# Определяем имя устройтсва
				check = self.check_search(t, f"show interfaces config {result[num]['port']}", r"Name\s+:.*?((\d+|[A-Z]+-UCN)-[A-Z0-9-]+)", f"zyxel {result[num]['ip']}|не найден description", prompt='#')
				if type(check) == dict:
					result.update(check)
					return result
				result[next_num] = {'desc': check[0]}

			# Определяем mac gateway, vlan mng
			if re.search(r'3124' ,result[num]['model']):
				t.new_sendline("enable", prompt = ':')
				t.new_sendline("Cdbnx0AA", prompt = '#')
			
			check = self.check_search(t, "show ip arp", r"\d+\.\d+\.\d+\.\d+\s+([\w:]+)\s+(\d+).+\s+dynamic", f"zyxel {result[num]['ip']}|не найден gateway", prompt='#')
			if type(check) == dict:
				result.update(check)
				return result
			mac_gateway, vlan_mng = check

			# определяем port Uplink
			com_show_mac = f"show mac address-table mac {mac_gateway}"
			if re.search(r'4012|3124' ,result[num]['model']):
				com_show_mac = f"show mac address-table vlan {result['vlan']}"

			check = self.check_search(t, com_show_mac, rf"(\d+)\s+{vlan_mng}\s+{mac_gateway}", f"zyxel {result[num]['ip']}|не найден mac", prompt='#')
			if type(check) == dict:
				result.update(check)
				return result
			result[num].update({'port_uplink': check[0]})

			return result


		def edgecore_switch(result, num, next_num, t):

			if re.search(r'3528M' ,result[num]['model']):
				t.new_sendline('terminal length 0')

			if result['status'] != 'end_device':
				# Определяем порт нижестоящего коммутатора
				format_mac = result['mac'].replace(':', '-')
				check = self.check_search(t, f"show mac-address-table address {format_mac}", rf"\d+\s+Eth\s+([\d\/]+ ?\d+)", f"edgecore {result[num]['ip']}|не найден mac")
				if type(check) == dict:
					result.update(check)
					return result
				port = check[0].replace(' ', '')
				result[num].update({'port': port})

				# Определяем имя устройтсва
				check = self.check_search(t, f"show interfaces status ethernet {port}", r"Name\s*:.*?((\d+|[A-Z]+-UCN)-[A-Z0-9-]+)", f"edgecore {result[num]['ip']}|не найден description")
				if type(check) == dict:
					result.update(check)
					return result
				result[next_num] = {'desc': check[0]}

			# Определяем mac gateway, vlan mng
			if re.search(r'3528M' ,result[num]['model']):
				check = self.check_search(t, "show arp", r"([\w-]+)\s+dynamic\s+(\d+)", f"edgecore {result[num]['ip']}|не найден gateway")
				if type(check) == dict:
					result.update(check)
					return result
				mac_gateway, vlan_mng = check

				# определяем port Uplink
				check = self.check_search(t, f"show mac-address-table address {mac_gateway}", rf"\s+{vlan_mng}\s+Eth\s+([\d\/]+ ?\d+)", f"edgecore {result[num]['ip']}|не найден mac")
				if type(check) == dict:
					result.update(check)
					return result
				port_uplink = check[0].replace(' ', '')
				result[num].update({'port_uplink': port_uplink})

			return result


		def lumia_switch(result, num, next_num, t):

			if result['status'] != 'end_device':
				
				# Определяем порт нижестоящего коммутатора
				check = self.check_search(t, f"show mac-addr-table {result['mac']} {result['vlan']}", r"\s+(\d+\/\d+)\s+", 'lumia|не найден mac')
				if type(check) == dict:
					result.update(check)
					return result
				result[num].update({'port': check[0]})

				# Определяем имя устройтсва
				check = self.check_search(t, f"show port description {result[num]['port']}", r"Description.+?((\d+|[A-Z]+-UCN)-[A-Z0-9-]+)", 'lumia|не найден description')
				if type(check) == dict:
					result.update(check)
					return result
				result[next_num] = {'desc': check[0]}

			# определяем port Uplink
			com = 'show arp'
			if re.search(r'BC' ,result[num]['model']):
				com = 'show arp switch'

			check = self.check_findall(t, com, r"[\w\.:]+\s+[\w\.:]+\s+([\d\/]+)", 'lumia|не найден gateway')
			if type(check) == dict:
				result.update(check)
				return result

			for port in check:

				check_up = self.check_search(t, f"show port description {port}", r"Description.+?((\d+|[A-Z]+-UCN)-[A-Z0-9-]+)", 'lumia|не найден description uplink')
				if type(check_up) == dict:
					result.update(check_up)
					return result
				if check_up[0] == result[num - 1]['desc']:
					result[num].update({'port_uplink': port})
					break
			else:
				result.update({'status': "error", 'message_error': "lumia|не определён description uplink"})


			return result


		def dlink_switch(result, num, next_num, t):

			if result['status'] != 'end_device':
				
				# Определяем порт нижестоящего коммутатора
				check = self.check_search(t, f"show fdb mac_address {result['mac']}", r"(\d+)\s+Dynamic", 'dlink|не найден mac')
				if type(check) == dict:
					result.update(check)
					return result
				result[num].update({'port': check[0]})

				# Определяем имя устройтсва
				com = f"show config active include \"config ports {result[num]['port']} \""
				if re.search(r'DES' ,result[num]['model']):
					com = f"show config current_config include \"config ports {result[num]['port']} \""

				check = self.check_search(t, com, r"description.+?((\d+|[A-Z]+-UCN)-[A-Z0-9-]+)", 'dlink|не найден description')
				if type(check) == dict:
					result.update(check)
					return result
				result[next_num] = {'desc': check[0]}

			# определяем gateway
			check = self.check_findall(t, 'show iproute', r"0\.0\.0\.0/0\s+([\d\.]+)\s+System\s+\d+\s+Default", 'dlink|не найден gateway')
			if type(check) == dict:
				result.update(check)
				return result
			gateway = check[0]

			# определяем mac gateway
			check = self.check_findall(t, 'show arpentry', rf"{gateway}\s+([\w-]+)\s+Dynamic", 'dlink|не найден mac gateway')
			if type(check) == dict:
				result.update(check)
				return result
			mac_gateway = check[0]

			# определяем port Uplink
			check = self.check_search(t, f"show fdb mac_address {mac_gateway}", rf"{mac_gateway}\s+(\d+)\s+Dynamic", 'dlink|не найден port Uplink', re.I)
			if type(check) == dict:
				result.update(check)
				return result
			result[num].update({'port_uplink': check[0]})

			return result


		def alcitec_switch(result, num, next_num, t):

			if result['status'] != 'end_device':
				
				# Определяем порт нижестоящего коммутатора
				check = self.check_search(t, f"show bridge address-table address {result['mac']}", r"(\d+)\s+dynamic", 'alcitec|не найден mac')
				if type(check) == dict:
					result.update(check)
					return result
				result[num].update({'port': check[0]})

				# Определяем имя устройтсва
				check = self.check_search(t, f"show interfaces description ethernet {result[num]['port']}", rf"{result[num]['port']}.+?((\d+|[A-Z]+-UCN)-[A-Z0-9-]+)", 'alcitec|не найден description')
				if type(check) == dict:
					result.update(check)
					return result
				result[next_num] = {'desc': check[0]}

			# определяем gateway
			check = self.check_findall(t, 'show ip interface', r"([\d\.]+)\s+Active\s+static", 'alcitec|не найден gateway')
			if type(check) == dict:
				result.update(check)
				return result
			gateway = check[0]

			# определяем port Uplink
			check = self.check_search(t, f"show arp", rf"(\w+)\s+{gateway}", 'alcitec|не найден mac')
			if type(check) == dict:
				result.update(check)
				return result
			result[num].update({'port_uplink': check[0]})

			return result

		def zyxel_dslam(result, num, next_num, t):


			if result['status'] != 'end_device':
				
				# Определяем порт нижестоящего коммутатора
				for n in range(1,3):
					check = self.check_search(t, f"statistics mac enet{n} {result['vlan']}", rf"{result['mac']}", f"zyxel_dslam {result[num]['ip']}|не найден mac downlink")
					if type(check) == dict:
						if n == 2:
							result.update(check)
							return result
					else:
						result[num].update({'port': f'enet{n}'})
						break

				# Определяем имя устройтсва
				check = self.check_search(t, f"switch enet show", rf"{result[num]['port']}.+auto\s+((\d+|[A-Z]+-UCN)-[A-Z0-9-]+)", f"zyxel_dslam {result[num]['ip']}|не найден description")
				if type(check) == dict:
					result.update(check)
					return result
				result[next_num] = {'desc': check[0]}

			# определяем gateway
			check = self.check_findall(t, 'ip show', r"gateway:\s+(\S+)", f"zyxel_dslam {result[num]['ip']}|не найден gateway")
			if type(check) == dict:
				result.update(check)
				return result
			gateway = check[0]

			# определяем vlan mgn
			check = self.check_findall(t, 'ip show', rf"{result[num]['ip']}\s+\S+\s+(\d+)", f"zyxel_dslam {result[num]['ip']}|не найден gateway")
			if type(check) == dict:
				result.update(check)
				return result
			vlan = check[0]			

			check = self.check_findall(t, 'ip arp show', rf"{gateway}\s+(\S+)", f"zyxel_dslam {result[num]['ip']}|не найден mac gateway")
			if type(check) == dict:
				result.update(check)
				return result
			mac_gateway = check[0]

			# определяем port Uplink
			for n in range(1,3):
				check = self.check_search(t, f"statistics mac enet{n} {vlan}", rf"{vlan}\s+{mac_gateway}", f"zyxel_dslam {result[num]['ip']}|не найден mac uplink{n}")
				if type(check) == dict:
					if n == 2:
						result.update(check)
						return result
				else:
					result[num].update({'port_uplink': f'enet{n}'})
					break

			return result

		def alcatel_dslam(result, num, next_num, t):


			if result['status'] != 'end_device':
				
				# Определяем порт нижестоящего коммутатора
				for n in range(1,3):
					check = self.check_search(t, f"statistics mac enet{n} {result['vlan']}", rf"{result['mac']}", f"alcatel_dslam {result[num]['ip']}|не найден mac downlink")
					if type(check) == dict:
						if n == 2:
							result.update(check)
							return result
					else:
						result[num].update({'port': f'enet{n}'})
						break


			# определяем vlan mgn
			check = self.check_findall(t, 'info configure system shub entry vlan flat', rf"id\s+(\d+)", f"alcatel_dslam {result[num]['ip']}|не найден vlan mgm")
			if type(check) == dict:
				result.update(check)
				return result
			vlan = check[0]			

			# определяем port Uplink
			check = self.check_findall(t, f'show vlan shub-fdb {vlan}', rf"network:(\d+)", f"alcatel_dslam {result[num]['ip']}|не найден mac gateway")
			if type(check) == dict:
				result.update(check)
				return result
			result[num].update({'port_uplink': f'{check[0]}'})


			return result



		num = result['count']
		next_num = num + 1

		login, password = 'tum_support', 'hEreR2Mu3E'

		if re.search(r'BC|Lumia', result[num]['model']):
			login, password = 'admin', 'Cdbnx0AA'
		if re.search(r'UCN', result[num]['desc']):
			login, password = 'admin', 'admin'
		if re.search(r'LTP', result[num]['model']):
			login, password = 'admin', 'password'

		# print(f"---- AUT IN {result[num]['ip']} ----")
		check_aut = t.aut(ip = result[num]['ip'], model = result[num]['model'], login = login, password = password, logs_dir = f"{getattr(configuration, 'LOGS_DIR')}/{dir_name}")
		if check_aut != 0:
			check_aut = t.aut(ip = result[num]['ip'], model = result[num]['model'], login = login, password = password, logs_dir = f"{getattr(configuration, 'LOGS_DIR')}/{dir_name}", proxy = True)
			if check_aut != 0:
				if re.search(r'1212|1248', result[num]['model']):
					login, password = 'admin', '1234'
				else:
					login, password = 'admin', 'admin'
				check_aut = t.aut(ip=result[num]['ip'], model=result[num]['model'], login = login, password = password, logs_dir = f"{getattr(configuration, 'LOGS_DIR')}/{dir_name}")
				if check_aut != 0:
					check_aut = t.aut(ip=result[num]['ip'], model=result[num]['model'], login = login, password = password, logs_dir = f"{getattr(configuration, 'LOGS_DIR')}/{dir_name}",proxy = True)
					if check_aut != 0:
						result.update({'status': 'error','message_error': f"Cant connect {result[result['count']]['ip']}"})
						return result

		if re.search(r'MES-3528|MGS-3712|MES3500-24|4728|4012', result[num]['model']) and check_aut != 0:
			"""Дурацкие зиксиля, иногда авторизация не проходит с первого раза. 
				После успешного ввода логина и пароля - telnet сессия закрывается
				приходится лепить костыли"""
			check_aut = t.aut(ip=result[num]['ip'], model=result[num]['model'], login=login, password=password)


			
			if check_aut != 0:
				result.update({'status': 'error','message_error': f"Cant connect {result[num]['ip']}"})
				return result

		if re.search(r'EX4500-40F|EX4550|EX9208|ACX2100|QFX5100', result[num]['model']):
			result = bbagg_upe_juniper(result, num, next_num, t)
		elif re.search(r'3324|3348|MES3124|3116|2324|2124|3508|2308|2208|1124', result[num]['model']):
			result = eltex_x3xx_x1xx(result, num, next_num, t)
		elif re.search(r'3400|3600|3750|2960|2950|3550|3560', result[num]['model']):
			result = cisco_switch(result, num, next_num, t)
		elif re.search(r'MES-3528|MGS-3712|MES3500-24|4728|4012|ES-3124', result[num]['model']):
			result = zyxel_switch(result, num, next_num, t)
		elif re.search(r'2428|2408', result[num]['model']):
			result = eltex_24xx(result, num, next_num, t)
		elif re.search(r'3526XA|3528M', result[num]['model']):
			result = edgecore_switch(result, num, next_num, t)
		elif re.search(r'BC|Lumia', result[num]['model']):
			result = lumia_switch(result, num, next_num, t)
		elif re.search(r'DES|DGS', result[num]['model']):
			result = dlink_switch(result, num, next_num, t)
		elif re.search(r'24100', result[num]['model']):
			result = alcitec_switch(result, num, next_num, t)
		elif re.search(r'1212|1248', result[num]['model']):
			result = zyxel_dslam(result, num, next_num, t)
		elif re.search(r'7330|7302', result[num]['model']):
			result = alcatel_dslam(result, num, next_num, t)
		else:
			result.update({'status': 'error','message_error': f"def switch | no algorithm for this model {result[num]['model']}"})

		if next_num in result and 'desc' in result[next_num]:
			data = t.sql_select(f"SELECT h.IPADDMGM, m.DEVICEMODELNAME, h.DEVICEID FROM guspk.host h, guspk.host_model m WHERE h.MODELID = m.MODELID AND NETWORKNAME = '{result[next_num]['desc']}'", 'full')
			if data and data[0][0] != result[num]['ip']:
				result[next_num].update({"ip": data[0][0], "model": data[0][1], 'id': data[0][2]})
			else:
				result.update({'status': "error", 'message_error': f"не найден в базе: {result[next_num]['desc']}"})

		port_uplink = None
		if 'port_uplink' in result[num]:
			port_uplink = result[num]['port_uplink']

		self.update_topology(t, result[num]['id'], result['mac'], id_parent=result[num - 1]['id'], child_port=port_uplink, parent_port=result[num - 1]['port'])
		
		t.disconnect()

		return result


	async def main(self, result, t, dir_name):
		await asyncio.sleep(0.01)

		# result['ip'] = 10.224.1.135
		if result['count'] == 1:
			result = self.peagg(result, t, dir_name)

		elif result['count'] >= 2:
			result = self.switch(result, t, dir_name)
		# print(result)
		return result
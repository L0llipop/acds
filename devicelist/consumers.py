from channels.generic.websocket import AsyncWebsocketConsumer
from channels.consumer import AsyncConsumer
from django.utils import timezone
from channels.generic.websocket import WebsocketConsumer

import sys, os, re, time
import jinja2
import json
import multimodule
import getpass
import ipaddress
import datetime
import asyncio
import topology
import network_find

from acds import configuration


class TopologyConsumer(AsyncWebsocketConsumer):
	async def connect(self):
		await self.accept()

	async def disconnect(self, close_code):
		pass

	async def receive(self, text_data):
		text_data_json = json.loads(text_data)
		message = text_data_json['message']
		online = text_data_json['online']
		username = text_data_json['username']

		t = multimodule.FastModulAut()
		t.sql_connect('connect', server = getattr(configuration, 'SERVER_IP'), login = getattr(configuration, 'MYSQL_LOGIN'), password = getattr(configuration, 'MYSQL_PASS'))
		t.count_website(t, page='topology', username=username)

		message = re.sub(r'\s+', '', message)

		if re.search(r'[0-9a-f]{2}[:.-]?[0-9a-f]{2}[:.-]?[0-9a-f]{2}[:.-]?[0-9a-f]{2}[:.-]?[0-9a-f]{2}[:.-]?[0-9a-f]{2}', message, re.I):
			message = re.sub(r'(\w\w)[:.-]?(\w\w)[:.-]?(\w\w)[:.-]?(\w\w)[:.-]?(\w\w)[:.-]?(\w\w)', r'\1:\2:\3:\4:\5:\6', message)

		if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', message):
			input_type = 'ip'
		elif re.search(r'((\d+|[A-Z]+-UCN)-[A-Z0-9-]+)', message):
			input_type = 'hostname'
		else:
			input_type = 'error'


		result = {
			'count': 1,
			'ip': '', 
			'status': 'wait',
			'message_error': 'wait',
			'hostname': '',
			'model': '',
			'vrf': '',
			'mac': '',
			'vlan': '',
			'input_type': input_type,
			'input_data': message,
			# 'tunnel_vlan': '',
		}

		data = t.sql_select(f"""SELECT h.NETWORKNAME, m.DEVICEMODELNAME, h.DEVICEID, h.MAC, h.IPADDMGM
			FROM guspk.host h, guspk.host_model m 
			WHERE h.MODELID = m.MODELID 
			AND (h.IPADDMGM = '{message}'
				OR h.NETWORKNAME = '{message}'
				OR h.DEVICEID = '{message}'
				OR h.MAC = '{message}')""", 'full')

		if data:
			result.update({
				'hostname': data[0][0], 
				'model': data[0][1],
				'mac': data[0][3],
				'ip': data[0][4],
			})

			temp_topology = {
				1: {
					'desc': data[0][0],
					'model': data[0][1],
					'id': data[0][2],
					'ip': data[0][4],
				},
			}
			temp_count = 1
			while True and not online:

				temp = t.sql_select(f"""SELECT t.parent, h.IPADDMGM, h.NETWORKNAME, m.DEVICEMODELNAME, t.parent_port, t.child_port
										FROM guspk.topology t
										LEFT JOIN guspk.host h ON h.DEVICEID = t.parent
										LEFT JOIN guspk.host_model m ON m.MODELID = h.MODELID
										WHERE t.child={temp_topology[temp_count]['id']};
										""", 'full')

				if temp:
					temp_topology[temp_count + 1] = {
						'id': temp[0][0],
						'ip': temp[0][1],
						'desc': temp[0][2],
						'model': temp[0][3],
						'port': temp[0][4],
					}
					if temp[0][5]:
						temp_topology[temp_count].update({'port_uplink': temp[0][5]})

					temp_count += 1

				else:
					break


			# Берём все сети, по адресу сети и маске определяем нужную
			query = """SELECT n.NETWORK_ID, CONCAT(n.NETWORK, "/", n.MASK), n.VRF, n.VLAN, h.IPADDMGM, h.NETWORKNAME, m.DEVICEMODELNAME, h.DEVICEID
								FROM guspk.host_networks n, guspk.host h, guspk.host_model m
								WHERE n.DEVICEID = h.DEVICEID
								AND h.MODELID = m.MODELID
							"""
			all_network = t.sql_select(query, 'full')

			for network in all_network:
				if ipaddress.ip_address(result['ip']) in ipaddress.ip_network(network[1]):
					result.update({
							'network_id': network[0],
							'network': network[1],
							'vrf': network[2],
							'vlan': network[3],
						})
					result[1] = {
							'ip': network[4],
							'desc': network[5],
							'model': network[6],
							'id': network[7],
						}
					break

			else:
				res = network_find.start(result['ip'])
				if res['ok']:
					vrf = None
					if res.get('vrf'):
						vrf = res['vrf']['vrfname']

					result.update({
							'network_id': '',
							'network': res['results']['network'],
							'vrf': vrf,
							'vlan': res['results']['intvlan'],
						})

					result[1] = {
							'ip': res['results']['routerip'],
							'desc': res['results']['routername'],
							'model': res['results']['model'],
							'id': res['results']['deviceid'],
						}


				else:
					result.update({'status': 'error', 'message_error': res['error'], 'vrf': res['vrf']})
		
		else:
			if input_type == 'ip':
				result['ip'] = message
			elif input_type == 'hostname':
				result['hostname'] = message
			result.update({'status': 'error', 'message_error': f"def main | Don't find {result['input_data']} in devicelist"})


		top = topology.getTopology()
		print(f"===== online: {online}")


		if result['status'] != 'error':
			while True and data:
				count = result['count']
				if count > 12:
					result.update({'status': 'error', 'message_error': 'loop detected'})
					return result
				# if result['status'] == 'error':
				# 	await self.send(text_data=json.dumps({
				# 		'message': json.dumps(result)
				# 	}))
				# 	break

				if not online and temp_count in temp_topology and result[count]['id'] == temp_topology[temp_count]['id'] and result['status'] != 'full_topology':
					# заполняет словарь данными из базы
					result.update({'status': 'full_topology'})
					while True:

						result[count] = temp_topology[temp_count]

						temp_count -= 1
						if temp_count == 0:
							break

						count += 1
					continue
				print(f"RESULT EVERY HOP {result['count']} {result}")
				if result[count]['ip'] == result['ip']:
					result.update({'status': 'end_device'})
					if online:
						t.sql_update(f"UPDATE guspk.host SET mac = '{result['mac']}' WHERE IPADDMGM = '{result['ip']}'") ##

				if not result[result['count']].get('port_uplink') and result['status'] != 'full_topology':
					result = await top.main(result, t, 'consumer')
					if result['status'] == 'error':
						self.send(text_data=json.dumps({
							'message': json.dumps(result)
						}))
						break

				print(f"TopologyConsumer {result['count']}|{result} ===== temp_topology: {temp_count}|{temp_topology}")
				print('======================================================================================')

				result['time'] = str(datetime.datetime.now().time())
				await self.send(text_data=json.dumps({
					'message': json.dumps(result)
				}))

				if result[count]['ip'] == result['ip']:
					result['status'] = 'ok'
					break

				result['count'] += 1

				if not re.search(r'wait|next|full_topology|end_device', result['status']):
					break

				if count > 20:
					break


		# port_uplink = None
		# if 'port_uplink' in result[count]:
		# 	port_uplink = result[count]['port_uplink']
		# top.update_topology(t, result[count]['id'], id_parent=result[count - 1]['id'], child_port=port_uplink, parent_port=result[count - 1]['port'])

		print(f"TopologyConsumer {result['count']}|{result}")
		print('======================================================================================')
		if result['status'] != 'error':
			result.update({'message_error': 'End'})

		await self.send(text_data=json.dumps({
			'message': json.dumps(result)
		}))


		t.sql_connect('disconnect')



#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import time
import datetime
import multimodule
import ipaddress
import topology
import asyncio

multi = multimodule.FastModulAut()
top = topology.getTopology()


def select_net_template(ip):

	ip = '10.228.62.231'
	
	
	multi.sql_connect('connect')
	all_network = multi.sql_select(f"""SELECT hn.NETWORK, hn.MASK, hn.NETWORK_ID
						FROM guspk.host_networks as hn""", "full")
	
	for network in all_network:
		if ipaddress.ip_address(ip) in ipaddress.ip_network(f'{network[0]}/{network[1]}'):
			print(True, network[0])
			print(f'{network[0]}/{network[1]}')
		# print(network)
	
	multi.sql_connect('disconnect')


result = {'count': 1, 'ip': '10.225.78.34', 'status': 'wait', 'message_error': 'wait', 'hostname': '45-KRG-AGG26-ACSW-4', 'model': 'ES-3124', 
'vrf': 'CORE', 'input_type': 'ip', 'input_data': '10.225.78.34', 'network_id': 39, 'network': '10.225.78.0/24', 'mac':'',
1: {'desc': '45-KURGAN-AGG26-PEAGG-1', 'ip': '10.225.128.60', 'model': 'CISCO7606-S', 'id': 12417},
# 'tunnel_vlan': '180',
}


def main(result):
	"""петля нулевых событий для запуска асинхронной топологии"""
	multi.sql_connect('connect')
	loop = asyncio.new_event_loop()
	asyncio.set_event_loop(loop)
	result = loop.run_until_complete(top.main(result, multi))
	multi.sql_connect('disconnect')

	return result

# result = main(result)
# print(f" result - {result}")
ip = result['ip']
while result['status'] == 'wait':
	if result[result['count']]['ip'] == ip:
		result['status'] = 'end_device'

	result = main(result)
	print(f" result - {result}")
	result['count'] += 1
	
	if result['status'] == 'error':
		print(result['message_error'])
		break



#10.225.78.34  после error еще один хоп?
import multimodule
import topology
import asyncio
import ipaddress


# result = {'count': 1, 'ip': '10.225.78.34', 'status': 'wait', 'message_error': 'wait', 'hostname': '45-KRG-AGG26-ACSW-4', 'model': 'ES-3124', 
# 'vrf': 'CORE', 'input_type': 'ip', 'input_data': '10.225.78.34', 'network_id': 39, 'network': '10.225.78.0/24', 'mac': '',
# 1: {'desc': '45-KURGAN-AGG26-PEAGG-1', 'ip': '10.225.128.60', 'model': 'CISCO7606-S', 'id': 12417},
# 'tunnel_vlan': '180',
# }

def select_net_template(ip, multi):
	# multi.sql_connect('connect')
	all_network = multi.sql_select(f"""SELECT hn.NETWORK, hn.MASK, hn.NETWORK_ID, h.NETWORKNAME, h.IPADDMGM, hm.DEVICEMODELNAME, hn.DEVICEID, hn.VRF
						FROM guspk.host_networks as hn
						RIGHT JOIN guspk.host h on h.DEVICEID = hn.DEVICEID
						RIGHT JOIN guspk.host_model hm on hm.MODELID = h.MODELID
						WHERE mask >= 22""", "full")

	for network, mask, network_id, router_desc, router_ip, router_model, router_id, vrf in all_network:
		if ipaddress.ip_address(ip) in ipaddress.ip_network(f'{network}/{mask}'):
			router = {'network_id': network_id, 'network': f'{network}/{mask}', 'vrf': vrf , 1: {'desc': router_desc, 'ip': router_ip, 'model': router_model, 'id': router_id}}
			# multi.sql_connect('disconnect')
			return router

def main(result, multi, top):
	loop = asyncio.new_event_loop()
	asyncio.set_event_loop(loop)
	result = loop.run_until_complete(top.main(result, multi, 'start_topology'))

	return result

# result = main(result)
# print(f" result - {result}")
def loop(ip):
	multi = multimodule.FastModulAut()
	top = topology.getTopology()
	result = {'count': 1, 'ip': ip, 'status': 'wait', 'message_error': 'wait', 'mac' : '',} #проверить когда появляется mac

	multi.sql_connect('connect')
	device_data = multi.sql_select(f"""SELECT h.NETWORKNAME, hm.DEVICEMODELNAME
										FROM guspk.host h
										RIGHT JOIN guspk.host_model hm on hm.MODELID = h.MODELID
										WHERE h.IPADDMGM = '{ip}' """, "full")
	try:
		hostname, model = device_data[0]
	except:
		result.update({'status': 'error', 'message_error': 'ip not found in hosts table'})
		return result

	result.update({'hostname': hostname, 'model': model})
	router = select_net_template(ip, multi)
	if not router.get('vrf'):
		result.update({'status': 'error', 'message_error': 'network template not found'})
		return result

	result.update(router)
	# print(result)

	while result['status'] == 'wait':
		if result[result['count']]['ip'] == ip:
			result['status'] = 'end_device'

		result = main(result, multi, top)
		print(f" result - {result}")
		result['count'] += 1

		if result['status'] == 'error':
			return result

	
	multi.sql_connect('disconnect')

	return result

#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import time
import datetime
import multimodule
import json
import pexpect
import ipaddress
# from ipaddress import IPv4Network


rr = {72: '10.234.128.1', 45: '10.225.128.13', 59: '10.222.240.121', 86: '10.236.128.136', 74: '10.223.80.12', 66: '10.231.0.13'}
t = multimodule.FastModulAut(login='yuzhakov-da')
# answer = dict.fromkeys(['ok', 'results'])
# answer['results'] = dict.fromkeys(['routerip'])

def error_handler(text, answer):
	# answer = {}
	answer.update({'ok': False, 'error': f'{text}'})
	return answer


def peagg_cisco(t, answer):
	intvlan = t.data_split() 
	intvlan = intvlan.split('\n')
	match_intvlan = re.search(rf"""via Vlan(\d+)""", intvlan[1])
	if match_intvlan:
		# print(f'{match_intvlan[1]}')
		answer['results'].update({'intvlan': match_intvlan[1]})
	else:
		return error_handler(f'intvlan not found', answer)
	t.new_sendline(f"""show running-config interface vlan {answer['results']['intvlan']}""")
	runvlan = t.data_split() 
	runvlan = runvlan.split('\n')
	for vline in runvlan:
		# print(vline)
		vlan_network = re.search(rf"""address\s(\S+)\s(\S+)""", vline)
		if vlan_network:
			search_network = ipaddress.IPv4Interface(f'{vlan_network[1]}/{vlan_network[2]}')
			# print(search_network.network)
			if str(search_network.network) == answer['results']['network']:
				# print(f'gw finded {vlan_network[1]}')
				answer['results'].update({'gw': vlan_network[1]})
				break
			# else:
				# return error_handler(f'gw not found', answer)
	return answer


def select_pe(ip):
	answer = {}
	t.sql_connect('connect')
	data = t.sql_select(f"""SELECT h.NETWORKNAME, fr.region_code
								FROM guspk.host h
								LEFT JOIN guspk.host_fias hf ON hf.id = h.DEVICEID
								LEFT JOIN guspk.fias_region fr ON fr.region_fias_id = hf.region_fias_id
								WHERE h.IPADDMGM = '{ip}'
								LIMIT 1""", 'full')
	if not data:
		return error_handler('device not found', answer)
	if not data[0][0]:
		return error_handler('hostname not found', answer)
	if not data[0][1]:
		return error_handler('region in host_fias not found', answer)
	hostname, region = data[0]
	mask = 0
	telnet = t.aut(f'{rr[region]}')
	if telnet != 0:
		return error_handler(f"""telnet connection error {rr[region]}""", answer) 

	t.new_sendline('terminal length 0')
#search for ip in core
	t.new_sendline(f'sh ip route {ip}')
	routes = t.data_split()
	routes = routes.split('\n')
	for route in routes:
		match_network = re.search(rf'for\s+(\S+)\/(\d+)', route)
		match_routerip = re.search(r'from\s(\d+\.\d+\.\d+\.\d+)\,', route)
		if match_network:
			network = match_network[1]
			mask = match_network[2]
		if match_routerip:
			routerip = match_routerip[1]
			answer.update({'ok': True, 'ip': ip, 'results': {'routerip': routerip, 'network': f'{network}/{mask}', 'net': network, 'mask': mask, 'region': region}})
			break

#search for ip in vpn
	if not answer.get('results'):
		t.new_sendline(f'sh ip bgp vpnv4 all {ip}', prompt='#$', timeout=30)
		routes_all = t.data_split()
		routes_all = routes_all.split('\n')
		for route in routes_all:
			match = re.search(r'(\d+)\:(\d+)\:([\d\.]+)\/(\d+)', route)
			# mask = match.group(4)
			if match and mask < int(match[4]):
				mask = int(match[4])
				# print(mask)
		netaddress = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
		netmask = str(netaddress.netmask)
		# print(netmask)
		t.new_sendline(f'sh ip bgp vpnv4 all {ip} {netmask}', prompt=r"#$")
		routes = t.data_split()
		# print(routes)
		routes = routes.split('\n')
		for route in routes:
			match_vrf = re.search(r'(\d+)\:(\d+)\:([\d\.]+)\/\d+', route)
			match_routerip = re.search(r'(\d+\.\d+\.\d+\.\d+)\s\(metric', route)
			if match_vrf:
				asid = match_vrf[1]
				vrfid = match_vrf[2]
				network = match_vrf[3]
			if match_routerip:
				routerip = match_routerip[1]
				answer.update({'ok': True, 'ip': ip, 'results': {'routerip': routerip, 'network': f'{network}/{mask}', 'net': network, 'mask': mask, 'region': region}, 'vrf': {'asid': asid, 'vrfid': vrfid}})
				break

	t.disconnect()
	t.sql_connect('disconnect')

	return answer

	
def peagg_data(answer):
	t.sql_connect('connect')
	i = t.aut(answer['results']['routerip'])
	if i != 0:
		return error_handler(f"""{answer['results']['routerip']} not connected""", answer)

	prompt = t.data_split()
	match = re.search(r'(\d+-[A-Z0-9-]+-\d+)', prompt)
	answer['results'].update({'routername': match[1]})
	data = t.sql_select(f"""SELECT hm.DEVICEMODELNAME, h.DEVICEID
					FROM guspk.host h
					LEFT JOIN guspk.host_model hm on hm.MODELID = h.MODELID
					WHERE h.NETWORKNAME = '{answer['results']['routername']}'""", 'full')
	if not data:
		return error_handler(f"""{answer['results']['routername']} not found in db""", answer)
	if not data[0][0]:
		return error_handler(f"""{answer['results']['routername']} model not found""", answer)
	if not data[0][1]:
		return error_handler(f"""{answer['results']['routername']} deviceid not found""", answer)

	model, deviceid = data[0]
	answer['results'].update({'deviceid': deviceid, 'model': model})
	if model == 'CISCO7606' or model == 'CISCO7606-S' or model == 'ASR1006':
		t.new_sendline('terminal length 0')
		if answer.get('vrf'):
			t.new_sendline(f"""show ip vrf | i {answer['vrf']['asid']}:{answer['vrf']['vrfid']}""")
			vrf = t.data_split() 
			vrf = vrf.split('\n')
			match_vrf = re.search(rf"""(\S+)\s+{answer['vrf']['asid']}:{answer['vrf']['vrfid']}""", vrf[1])
			if match_vrf:
				answer['vrf'].update({'vrfname': match_vrf[1]})
			else:
				return error_handler(f'vrfname not found', answer)
			t.new_sendline(f"""show ip route vrf {answer['vrf']['vrfname']} {answer['ip']} | i Vla""")
			answer = peagg_cisco(t, answer)
		else:
			t.new_sendline(f"""show ip route {answer['ip']} | i Vla""")
			answer = peagg_cisco(t, answer)

	elif model == 'MX480':
		return error_handler(f'MX480 not support now', answer)
	elif model == 'Nokia-7750-SR-7':
		return error_handler(f'Nokia not support now', answer)
	else:
		return error_handler(f'{model} not support now', answer)

	t.disconnect()
	t.sql_connect('disconnect')

	return answer

def start(ip):
	answer = select_pe(ip)
	if not answer['ok']:
		return answer
	summary = peagg_data(answer)
	if summary['ok']:
		t.sql_connect('connect')
		if summary['results'].get('gw'):
			net_id = t.sql_select(f"""SELECT NETWORK_ID FROM guspk.host_networks WHERE GW = '{summary['results']['gw']}'""", 'full')
			if not net_id:
				if summary.get('vrf'):
					vrf = summary['vrf']['vrfname']
				else:
					vrf = 'CORE'
				data = summary['results']
				net_id = t.sql_update(f"""INSERT INTO guspk.host_networks (VLAN, VRF, GW, NETWORK, MASK, DEVICEID, REGION) VALUES ('{data['intvlan']}', '{vrf}', '{data['gw']}', '{data['net']}', '{data['mask']}', '{data['deviceid']}', '{data['region']}')""")
			else:
				net_id = net_id[0]
		summary.update({'netid': net_id})
		t.sql_connect('disconnect')

	return summary


# testip = ['10.228.130.6', '10.224.1.23', '10.224.69.34', '10.232.240.18', '10.228.21.20'] #, '10.224.1.23'
# testip = ['10.229.168.43'] #, '10.224.1.23'
# for ip in testip:
# 	print(ip.center(20, '='))
# 	a = start(ip)
# 	print(a)

if __name__ == "__main__":
	# start('10.4.31.24')
	start('10.228.130.6')

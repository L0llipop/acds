#!/usr/bin/python3
# -*- coding: utf-8 -*-
import multimodule
import re

import start_config_eltex_mes_all as eltexsw
import start_config_eltex_mes_24xx as eltexsw24xx
import start_config_dlink_3200 as dlinksw
import start_config_ma4000 as eltexolt
import start_config_zyxel_12xx as zyxeladsl



def start(acds_id, ip, model):
	device = {'ip': ip}
	t = multimodule.FastModulAut()
	t.ws_connect('chat/log_configure/')
	t.ws_send_message(f"conf_routing: acds_id: {acds_id} | ip: {ip} | model: {model}")

	if re.search(r'MES1124|MES2124|MES2308|MES2324|MES3124|MES3324|MES3348|MES3508', model):
		t.ws_send_message(f"conf_routing: start_config_eltex_mes_all")
		answer = eltexsw.start_config(device)
		# answer = 'ok'
	elif re.search(r'MES2428|MES2408', model):
		t.ws_send_message(f"conf_routing: start_config_eltex_mes_24xx")
		answer = eltexsw24xx.start_config(device)
		# answer = 'ok'
	elif re.search(r'MA4000|LTP-8X|LTP-4X', model):
		t.ws_send_message(f"conf_routing: start_config_ma4000")
		answer = eltexolt.start_config(device)
	elif re.search(r'WOP-2AC-LR5|ePMP 1000', model):
		t.ws_send_message(f"conf_routing: WBS - no script to configure")
		answer = 'ok'
	elif re.search(r'AAM1212|IES-1248', model):
		t.ws_send_message(f"conf_routing: start_config_zyxel_12xx")
		answer = zyxeladsl.start_config(device)
		# answer = 'ok'
	elif re.search(r'AAM-1008', model):
		t.ws_send_message(f"conf_routing: ADSL Zyxel - no script to configure")
		answer = 'ok'
	elif re.search(r'7330|7302', model):
		t.ws_send_message(f"conf_routing: ADSL Alcatel - no script to configure")
		answer = 'ok'
	elif re.search(r'C300|C350', model):
		t.ws_send_message(f"conf_routing: ADSL ZTE - no script to configure")
		answer = 'ok'
	elif re.search(r'MA5603', model):
		t.ws_send_message(f"conf_routing: ADSL Huawei - no script to configure")
		answer = 'ok'		
	elif re.search(r'DES-3200-18|DES-3200-28|DES-3200-58', model):
		# t.ws_send_message(f"conf_routing: start_config_dlinksw_all")
		t.ws_send_message(f"conf_routing: Dlink - need to rewrite script")
		# answer = dlinksw.start_config(device)
		answer = 'ok'
	elif re.search(r'MG-16FXS|MG-24FXS|MG-36FXS|MG-44FXS|MG-52FXS|MG-60FXS|MG-72FXS|MG-8FXS|MG-32FXS|TAU-72.IP|TAU-24.IP|TAU-16.IP|TAU-36.IP|TAU-8.IP|TAU-4.IP', model):
		t.ws_send_message(f"conf_routing: Voice - no script to configure")
		answer = 'ok'
	elif re.search(r'ES-2024a|MGS-3712', model):
		t.ws_send_message(f"conf_routing: Zyxel SW - no script to configure")
		answer = 'ok'
	elif re.search(r'ES3528M|ES3526XA', model):
		t.ws_send_message(f"conf_routing: Edge-Core SW - no script to configure")
		answer = 'ok'
	elif re.search(r'3400|3600|3560|2950|2960', model):
		t.ws_send_message(f"conf_routing: Cisco SW - no script to configure")
		answer = 'ok'
	elif re.search(r'ACX2100', model):
		t.ws_send_message(f"conf_routing: juniper SW - no script to configure")
		answer = 'ok'
	elif re.search(r'MA5800', model):
		t.ws_send_message(f"conf_routing: OLT Huawei - no script to configure")
		answer = 'ok'
	elif re.search(r'КУБ-Микро', model):
		t.ws_send_message(f"conf_routing: CNTR - no script to configure")
		answer = 'ok'				
	elif re.search(r'SNR', model):
		t.ws_send_message(f"conf_routing: CNTR - no script to configure")
		answer = 'ok'				
	else:
		t.ws_send_message(f"conf_routing: Error: dont know this model {model}")
		answer = f"Error: dont know this model {model}"

	t.ws_send_message(f"conf_routing: res: {answer}")
	t.ws_close()
	return(answer)
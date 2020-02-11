#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import time
import datetime
import multimodule
import json
import ipaddress

def port_finder(ip):
	multi = multimodule.FastModulAut()
	multi.sql_connect('connect')
	device_data = multi.sql_select(f"""SELECT h.NETWORKNAME, m.DEVICEMODELNAME
					FROM guspk.host h
					LEFT JOIN guspk.host_model m ON h.MODELID = m.MODELID
					WHERE h.IPADDMGM like '{ip}'""", 'full')
	hostname, model = device_data[0]
	print(hostname, model)






	multi.sql_connect('disconnect')

















port_finder('10.225.254.10')
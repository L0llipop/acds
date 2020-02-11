from django.shortcuts import render
from django.conf import settings
from django.shortcuts import redirect
from django.core.mail import send_mail
from django.core.mail import mail_admins
from django.http import JsonResponse

import sys, os, re, time
import datetime
import jinja2
import json
import multimodule



def mainmap (request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]

	if not 'admins' in group and not 'users' in group: 

		return render(request, 'devicelist/access.html')

	return render(request, 'maps/maps.html', locals())

def get_data_for_map(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group and not 'users' in group:
		return render(request, 'devicelist/access.html')

	geo = {}
	t = multimodule.FastModulAut()
	t.sql_connect('connect')
	devices = t.sql_select(f"""SELECT h.DEVICEID, hf.geo_lat, hf.geo_lon, m.DEVICEMODELNAME, h.IPADDMGM
	FROM guspk.host_fias hf
	LEFT JOIN guspk.host h ON h.DEVICEID = hf.id
	LEFT JOIN guspk.host_model m on h.MODELID = m.MODELID
	LEFT JOIN guspk.fias_city c ON c.city_fias_id = hf.city_fias_id
	WHERE h.DEVICESTATUSID = 3 and 
	hf.geo_lat is not null
	""", 'full')
	for n in devices:
		deviceid, lat, lon, model, ipaddmgm = n
		geo.update({deviceid: {"lat": lat, "lon": lon, "model": model, "ip": ipaddmgm}})
	t.sql_connect('disconnect')
	
	return JsonResponse(geo, safe=False)
def get_service_for_map(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group and not 'users' in group:
		return render(request, 'devicelist/access.html')

	geo = {}
	t = multimodule.FastModulAut()
	t.sql_connect('connect')
	services = t.sql_select(f"""SELECT id, geo_lat, geo_lon,  inet, IPTV, IMS, cap FROM guspk.clients_fias_view""", 'full')
	for n in services:
		id, lat, lon, inet, iptv, ims, cap = n
		geo.update({id: {"lat": lat, "lon": lon, "inet": inet, "iptv": iptv, "ims": ims, "cap":cap}})
	t.sql_connect('disconnect')
	
	return JsonResponse(geo, safe=False)


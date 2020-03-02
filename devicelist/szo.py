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
import fias_import
import astu_data
import subprocess
from collections import Counter

def start(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

	contractors = {
		'Лебяжьевский': 'ПМК',
		'Варгашинский': 'ПМК',
		'Макушинский': 'ПМК',
		'Макушино': 'ПМК',
		'Притобольный': 'ПМК',
		'Шадринский': 'ПМК',
		'Шадринск': 'ПМК',
		'Кетовский': 'ПМК',
		'Целинный': 'ССС',
		'Шумихинский': 'ССС',
		'Звериноголовский': 'ССС',
		'Далматовский': 'ИнГео',
		'Далматово': 'ИнГео',
		'Альменевский': 'ССС',
		'Каргапольский': 'ССС',
		'Щучанский': 'ССС',
		'Щучье': 'ССС',
		'Половинский': 'ССС',
		'Катайский': 'ИнГео',
		'Сафакулевский': 'ССС',
		'Белозерский': 'ПМК',
		'Юргамышский': 'ССС',
		'Куртамышский': 'ССС',
		'Куртамыш': 'ССС',
		'Мокроусовский': 'ИнГео',
		'Частоозерский': 'ПМК',
		'Петуховский': 'ПМК',
		'Шатровский': 'ИнГео',
		'Мишкинский': 'ССС',
		'Курган': 'ССС',
	}

	t = multimodule.FastModulAut()
	t.sql_connect('connect')
	query_astu = """SELECT h.DEVICEID, h.IPADDMGM, h.NETWORKNAME, hm.DEVICEMODELNAME, a.id, h.DATEMODIFY, h.DATEMODIFY, hs.status_name, h.SERIALNUMBER, 
			CONCAT(COALESCE(fc.city_with_type,''), COALESCE(fs.settlement_with_type,''),'; ', COALESCE(fst.street_with_type,''),'; ', COALESCE(fh.house,''), 
			COALESCE(CONCAT('; ',fh.block_type_full),''), COALESCE(fh.block,'')), fa.geo_lat, fa.geo_lon, a.email,
			COALESCE(fc.city, far.area), a.report, a.status
			FROM guspk.host h
			LEFT JOIN guspk.host_status hs ON h.DEVICESTATUSID = hs.status_id
			LEFT JOIN guspk.host_model hm ON h.MODELID = hm.MODELID
			LEFT JOIN guspk.topology top ON top.child = h.DEVICEID
			LEFT JOIN guspk.host_fias fa ON h.DEVICEID = fa.id
			LEFT JOIN guspk.fias_region fr ON fa.region_fias_id = fr.region_fias_id
			LEFT JOIN guspk.fias_area far ON fa.area_fias_id = far.area_fias_id
			LEFT JOIN guspk.fias_city fc ON fa.city_fias_id = fc.city_fias_id
			LEFT JOIN guspk.fias_settlement fs ON fa.settlement_fias_id = fs.settlement_fias_id
			LEFT JOIN guspk.fias_street fst ON fa.street_fias_id = fst.street_fias_id
			LEFT JOIN guspk.fias_house fh ON fa.house_fias_id = fh.house_fias_id
			LEFT JOIN guspk.host_acsw_node an ON an.DEVICEID = h.DEVICEID
			LEFT JOIN guspk.acds a ON a.acsw_node_id = an.ACSD_NODE_ID 
			WHERE a.reason LIKE '%СЗО%';
			"""

	key = ['ip','hostname','model','id','date','time','status','serial','addres','geolat','geolon','user','area','stat']

	stat_list = []

	request_sql = t.sql_select(query_astu, 'full')
	values = {'key': key}
	values['data'] = {}
	for col in request_sql:
		values['data'][col[0]] = {}
		for i, k in enumerate(key, 1):
			if isinstance(col[i], datetime.datetime):
				if k == 'date':
					values['data'][col[0]].update({k: col[i].strftime("%Y-%m-%d")})
				else:
					values['data'][col[0]].update({k: col[i].strftime("%H:%M:%S")})
			else:
				values['data'][col[0]].update({k: col[i]})
				if k == 'user': 
					values['data'][col[0]].update({'user': col[i].split('@')[0]})
					
				if k == 'area': 
					if col[i] in contractors:
						values['data'][col[0]].update({'contractor': contractors[col[i]]})
						if col[i] == 'Курган' and re.search(r'Спортивная|Советская', col[9]):
							values['data'][col[0]].update({'contractor': 'ПМК'})
					else:
						values['data'][col[0]].update({'contractor': 'None'})

				if k == 'stat':
					if col[i + 1] == 'closed':
						values['data'][col[0]].update({'stat': 'Настроен, занесён в Аргус'})
					elif col[i] == 'configured':
						values['data'][col[0]].update({'stat': 'Настроен, ожидание занесения в Аргус'})
					else:
						values['data'][col[0]].update({'stat': 'Не установлен'})

					stat_list.append(values['data'][col[0]]['stat'])


	values['count_stat'] = dict(Counter(stat_list))

	request_sql_count = t.sql_select("""SELECT DISTINCT(a.email), COUNT(a.email) FROM guspk.acds a WHERE a.reason like '%СЗО%' GROUP by a.email ORDER BY COUNT(a.email) DESC""", 'full')
	values['count'] = {}
	for r in request_sql_count:
		values['count'][r[0]] = r[1]



	t.sql_connect('disconnect')
	return render(request, 'devicelist/szo.html', values)
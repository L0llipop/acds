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
import mysql.connector

def db_model_search(query):
    try:
        conn = mysql.connector.connect(host='10.180.7.34',
                                    database='guspk',
                                    user='borisov-sv',
                                    password='1234')
    except Error as e:
        print(e)
        return
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        row = cursor.fetchall()
        return row
    except Error as e:
        print(e)
    
    finally:
        cursor.close()
        conn.close()

def db_insert(query):
    try:
        conn = mysql.connector.connect(host='10.180.7.34',
                                    database='guspk',
                                    user='borisov-sv',
                                    password='1234')
    except Error as e:
        print(e)
        return
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        #row = cursor.fetchall()
        return 
    except Error as e:
        print(e)
    
    finally:
        cursor.close()
        conn.close()


def wbsdevicelist(request):
  if not request.user.is_authenticated:
    return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
  t = multimodule.FastModulAut()
  t.sql_connect('connect')
<<<<<<< HEAD
  sqldata= t.sql_select("select address, IPADDMGM, NETWORKNAME, MAC, DEVICEMODELNAME, wlan0_fr, wlan0_ssid, wlan0_azimuth, wlan0_mac, wlan1_fr, wlan1_ssid, wlan1_azimuth, wlan1_mac, wlan2_fr, wlan2_ssid, wlan2_azimuth, wlan2_mac, geo_lat, geo_lon, serial  from guspk.WBS_Frecuency", "full")
=======
  sqldata= t.sql_select("select IPADDMGM, NETWORKNAME, MAC, DEVICEMODELNAME, wlan0_fr, wlan0_ssid, wlan0_azimuth, wlan0_mac, wlan1_fr, wlan1_ssid, wlan1_azimuth, wlan1_mac, wlan2_fr, wlan2_ssid, wlan2_azimuth, wlan2_mac, geo_lat, geo_lon, serial  from guspk.WBS_Frecuency", "full")
>>>>>>> f3f42faeaa62660dc0e97136c8e3c4464dd9807e
  t.count_website(t, page='wbsdevicelist', username=request.user.username)
  t.sql_connect('disconnect')
  return render(request, 'wbs/wbs_list.html', locals())

def set_wbs_data(request):
  if not (request.user.is_authenticated):
    return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
  group = [ x.name for x in request.user.groups.all()]
  if not('admins' in group or 'engineers' in group):
    return JsonResponse({'error': 'You have not permission'}, safe=False)

  if request.method == 'GET':
    ip_address = request.GET.get("ip_address", "")
    wlan0_ssid = request.GET.get("wlan0_ssid", "")
    wlan0_azimuth = request.GET.get("wlan0_azimuth", "")
    wlan0_mac = request.GET.get("wlan0_mac", "")
    wlan1_ssid = request.GET.get("wlan1_ssid", "")
    wlan1_azimuth = request.GET.get("wlan1_azimuth", "")
    wlan1_mac = request.GET.get("wlan1_mac", "")
    wlan2_ssid = request.GET.get("wlan2_ssid", "")
    wlan2_azimuth = request.GET.get("wlan2_azimuth", "")
    wlan2_mac = request.GET.get("wlan2_mac", "")
    #t.count_website(t, page='set_wbs_data', username=request.user.username)
  else:
    return JsonResponse({'error': 'wrong method'}, safe=False)
    
  if ip_address == "":
    return JsonResponse({'error': 'missing ip'}, safe=False)# Если в запросе нет IP адреса, то обновлять нечего
  query21 = "SELECT count(IPADDMGM)  from guspk.WBS_Frecuency where IPADDMGM = '"+ip_address+"'"  # есть ли IP адрес среди РРЛ WBS
    
  f21 = db_model_search(query21)
  if f21[0][0] == 0:
    return JsonResponse({'error': 'wrong ip'}, safe=False) # Если IP адреса нет в нашей выборке, то ни чего не делать
  qq112 = "SELECT DEVICEID  from guspk.host  where IPADDMGM = '"+ip_address+"'"  # выбираем ID так как связи в таблицах по ID сделаны
  qq11 = db_model_search(qq112)
  devid = str(qq11[0][0])
  query2 = "SELECT count(DEVICEID)  from guspk.wbs where DEVICEID = '"+devid+"'"  # есть ли ID в таблице WBS, если устройство новое, то создаём для него базовую пустую запись, чтобы update потом нормально работали
  f22 = db_model_search(query2)
  if f22[0][0] == 0:  # если в таблице WBS нет записей, то создаём
    bb1=db_insert("insert into guspk.wbs (DEVICEID) VALUES ("+devid+")")   
#   все проверки сделали, теперь обновляем записи в таблице

  if wlan0_ssid !="":
    bb2 = db_insert("update guspk.wbs set wlan0_ssid ='"+wlan0_ssid+"' where DEVICEID = '"+devid+"'")
  if wlan0_azimuth !="":
    bb=db_insert("update guspk.wbs set wlan0_azimuth ='"+wlan0_azimuth+"' where DEVICEID = '"+devid+"'")
  if wlan0_mac !="": 
    sq55 = "update guspk.wbs set wlan0_mac ='"+wlan0_mac+"' where DEVICEID = '"+devid+"'"
    bb=db_insert(sq55)
  if wlan1_ssid !="": 
    sq55 = "update guspk.wbs set wlan1_ssid ='"+wlan1_ssid+"' where DEVICEID = '"+devid+"'"
    bb=db_insert(sq55)
  if wlan1_azimuth !="": 
    sq55 = "update guspk.wbs set wlan1_azimuth ='"+wlan1_azimuth+"' where DEVICEID = '"+devid+"'"
    bb=db_insert(sq55)
  if wlan1_mac !="": 
    sq55 = "update guspk.wbs set wlan1_mac ='"+wlan1_mac+"' where DEVICEID = '"+devid+"'"
    bb=db_insert(sq55)
  if wlan2_ssid !="": 
    sq55 = "update guspk.wbs set wlan2_ssid ='"+wlan2_ssid+"' where DEVICEID = '"+devid+"'"
    bb=db_insert(sq55)
  if wlan2_azimuth !="": 
    sq55 = "update guspk.wbs set wlan2_azimuth ='"+wlan2_azimuth+"' where DEVICEID = '"+devid+"'"
    bb=db_insert(sq55)
  if wlan2_mac !="": 
    sq55 = "update guspk.wbs set wlan2_mac ='"+wlan2_mac+"' where DEVICEID = '"+devid+"'"
    bb=db_insert(sq55)

  return JsonResponse({'update': 'Ok'}, safe=False)


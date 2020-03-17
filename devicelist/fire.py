from django.shortcuts import render
from django.conf import settings
from django.shortcuts import redirect
from django.core.mail import send_mail
from django.core.mail import mail_admins
from django.http import JsonResponse, FileResponse
from openpyxl import load_workbook

import sys, os, re, time, io
import datetime
import json
import mysql.connector
import fire_fias
try:
	from acds import configuration
except:
	import configuration

def db_model_search(query):
    try:
        conn = mysql.connector.connect(host=configuration.FIRE_HOST,
                                    database=configuration.FIRE_DB,
                                    user=configuration.FIRE_USER,
                                    password=configuration.FIRE_PASS)
    except Exception as e:
        print(e)
        return
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        row = cursor.fetchall()
        return row
    except Exception as e:
        print(e)
    
    finally:
        cursor.close()
        conn.close()

def db_insert(query):
    try:
        conn = mysql.connector.connect(host=configuration.FIRE_HOST,
                                    database=configuration.FIRE_DB,
                                    user=configuration.FIRE_USER,
                                    password=configuration.FIRE_PASS)
    except Exception as e:
        return str(e)
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        lastid = cursor.lastrowid
        conn.commit()
        return lastid
    except Exception as e:
        return str(e)
    
    finally:
        cursor.close()
        conn.close()

def firelist(request):
  if not request.user.is_authenticated:
    return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
  if request.method == 'GET':
    fire_address = request.GET.get("fire_address", "")
    fire_serial = request.GET.get("fire_serial", "")
    fire_inventory = request.GET.get("fire_inventory", "")

  firedic={}
  sqldata= db_model_search("select fireid, type, serial, inventory, room, fullweight, status, comandor, address, ClassList from FireSupressor.FireList")
  for iii in sqldata:
    querycheck =  "select fc.chargeid, fc.Chargedata, fc.Checkdata, fc.weight, fc.userwho from FireCheck as fc where fc.fireid = " + str(iii[0])
    checklist = db_model_search(querycheck)
    firedic[iii[0]]=({"fire":iii, "check":checklist})
  
  
  return render(request, 'wbs/fire.html', locals())


#self.sql = mysql.connector.connect(host = server, user = login_sql, password = p_sql, charset='utf8', use_unicode = True)
#			self.cursor_mysql = self.sql.cursor(buffered=True) 
  
  
  
  
def set_fire_data(request):
  if not (request.user.is_authenticated):
    return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
  group = [ x.name for x in request.user.groups.all()]
  if not('admins' in group or 'engineers' in group):
    return JsonResponse({'error': 'You have not permission'}, safe=False)

  firedic = {"carbonic":"ОУ", "powdery":"ОП", "water":"ОВМ", "ready":"Готов", "backup":"на складе", "lost":"потерян", "empty":"разряжен", "broken":"сломан", "fireA":"1", "fireB":"2", "fireC":"3","fireD":"4", "fireE":"5"}
  if request.method == 'GET':
    all_data = json.loads(request.GET['all_data'])
    if all_data['action'] =="insertnew":
      address = all_data['address']
      room = all_data['room']
      comandor = all_data['comandor']
      serial = all_data['serial']
      inventory = all_data['inventory']
      weight = all_data['weight']
      firetype = firedic[all_data['firetype']]
      firestatus = firedic[all_data['firestatus']]
      fireclass = all_data['fireclass'].split(',')
      if weight =="":
        insertquery = "INSERT INTO FireSupressor.FireSupressor (serial, inventory, type,  room, comandor, status) VALUES ('"+serial+"', '"+inventory+"', '"+firetype+"', '"+room+"', '"+comandor+"', '"+firestatus+"')"
      else:
        insertquery = "INSERT INTO FireSupressor.FireSupressor (serial, inventory, type, fullweight, room, comandor, status) VALUES ('"+serial+"', '"+inventory+"', '"+firetype+"', '"+weight+"', '"+room+"', '"+comandor+"', '"+firestatus+"')"
      lastid_ee=db_insert(insertquery)
      fias_rez=fire_fias.fire_fias_insert(lastid_ee,address)

      
      for ttt in fireclass:
        insertclass = "INSERT INTO FireSupressor.FireClassAndFireID (fireid, classid) VALUES ('"+str(lastid_ee)+"', '"+firedic[ttt]+"')"
        print(insertclass)
        db_insert(insertclass)
      
      return JsonResponse({'insert': 'ok', "result":lastid_ee, "fias":fias_rez}, safe=False)
      

    #t.count_website(t, page='set_wbs_data', username=request.user.username)
  else:
    return JsonResponse({'error': 'wrong method'}, safe=False)

  if request.method == 'GET':
    all_data = json.loads(request.GET['all_data'])
    if all_data['action'] =="insertcheck":
      fireid = all_data['fireid']
      weight = all_data['weight']
      data_check = all_data['data']
      comandor = all_data['comandor']
      firecheck_type = all_data['firecheck_type']
      if weight =="":
        if firecheck_type == "chardged":
          insertcheck = "INSERT INTO FireSupressor.FireCheck (fireid, Chargedata, userwho) VALUES ('"+fireid+"', '"+data_check+"', '"+comandor+"')"
        else:
          insertcheck = "INSERT INTO FireSupressor.FireCheck (fireid, Checkdata, userwho) VALUES ('"+fireid+"', '"+data_check+"', '"+comandor+"')"
      else:
        if firecheck_type == "chardged":
          insertcheck = "INSERT INTO FireSupressor.FireCheck (fireid, Chargedata, userwho, weight) VALUES ('"+fireid+"', '"+data_check+"', '"+comandor+"', '"+weight+"')"
        else:
          insertcheck = "INSERT INTO FireSupressor.FireCheck (fireid, Checkdata, userwho, weight) VALUES ('"+fireid+"', '"+data_check+"', '"+comandor+"', '"+weight+"')"
    eecheck=db_insert(insertcheck)
    return JsonResponse({'insert': 'ok', "last_id":eecheck}, safe=False)
    

  return JsonResponse({'update': 'unknown'}, safe=False)
  
def firejornal(request):
  if not request.user.is_authenticated:
    return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

  try:
    wb1 = load_workbook('static/devicelist/firejornal.xlsx')
  except Exception as e:
    return JsonResponse({'error': str(e)}, safe=False)

  buffer = io.BytesIO()

  sheet1 = wb1['fire1']
  firedic={}
  sqldata= db_model_search("select fireid, type, serial, inventory, room, fullweight, status, comandor, address, ClassList from FireSupressor.FireList")
  cellnn=0
  for iii in sqldata:
    querycheck =  "select fc.chargeid, fc.Chargedata, fc.Checkdata, fc.weight, fc.userwho from FireCheck as fc where fc.fireid = " + str(iii[0])
    checklist = db_model_search(querycheck)
    sheet1.cell(column=1, row=5+cellnn, value=str(iii[2])+str(iii[3]))
    sheet1.cell(column=5, row=5+cellnn, value=str(checklist))
    cellnn+=1
  wb1.save(buffer)
  buffer.seek(0)
  
  return FileResponse(buffer,as_attachment=True, filename='firejornal.xlsx')

  
  
  
  
  
  
  
  
  
  
  
  

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

# sudo systemctl restart gunicorn 

def massconfig(request):

  if not request.user.is_authenticated:
    return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))


  return render(request, 'activator/massconfig.html', locals())

def configsend(request):
  values = {}
  group = [ x.name for x in request.user.groups.all()]
  if not request.user.is_authenticated and not 'admins' in group:
    return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

  if request.GET:
   net_login = request.GET.get('net_login', str(False))
   net_password = request.GET.get('net_password', str(False))
   iplist =  request.GET.get('ip_list', str(False)).split('\n')
   findtext = request.GET.get('findtext', str(False))
   command_list = request.GET.get('command_list', str(False)).split('\n')
   ipmodel = {}
   t = multimodule.FastModulAut()
   t.sql_connect('connect')
   for ipp in iplist:
     sqlrez = t.sql_select(f"""SELECT hm.DEVICEMODELNAME FROM guspk.host_model as hm
                          left JOIN guspk.host as h ON h.modelid = hm.MODELID
                          WHERE h.IPADDMGM = '{ipp}'""", 'full')
     try:
      ipmodel[ipp]=(sqlrez[0][0])
     except:
      ipmodel[ipp]="unknown"
   t.sql_connect('disconnect')
   t.login = request.GET.get('net_login', str(False))
   t.password = request.GET.get('net_password', str(False))
   t.ws_connect('chat/massconfig/')
   findtextyes = []
   findtextno = []
   for key, items in ipmodel.items():
     i = t.aut(key, items, False, timeout=5)
     if i != 0:
       values.update({key: "Login fail"})
       continue
     t.ws_send_message(f"================= START {key} =====================")
     for command in command_list:
       t.new_sendline(command)
       ipshow = t.data_split()
       if ipshow.find(findtext) == -1:
           findtextyes.append(key)
       else:
           findtextno.append(key)
       t.ws_send_message(f"{ipshow}")
     t.disconnect(False)
     t.ws_send_message("================================")
   values.update({"Результат работы смотри ": "http://10.180.7.34/chat/massconfig/"})
   values.update({"Строка не найдена ": findtextyes })
   values.update({"Строка найдена ": findtextno })
   t.ws_close() 
   
  return JsonResponse(values, safe=False)



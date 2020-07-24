import getpass
import sys, os, re, time
import mysql.connector 
import cx_Oracle
from mysql.connector import Error
from configparser import ConfigParser
import pexpect
import datetime
import threading
import websocket
import requests
import json
import topology
import ipaddress
try:
	from acds import configuration
except:
	import configuration

# from django.contrib.staticfiles.templatetags.staticfiles import static

class FastModulAut:
	""" Модуль дополняет библиотеку pexpect для упрощённого написание скриптов """
	def __init__(self, prompt = '# ?$', timeout = 10, login='default'):
		""" Задаём глобальный промт и подтягиваем конфиг """

		self.login = login
		self.file_config()

		self.errors = True
		self.prompt = [prompt]
		self.timeout = timeout
		self.temp_data = ''
		self.hash_promt = {
			'AAM1212' : ['> ?$', 'nopause'], 
			'DSL IES-1248-51' : ['> ?$', 'nopause'],
			'IES-1248' : ['> ?$', 'nopause'],
			'BC9569x-024' : ['# ?$', 'More|continue'],
			'BC9569x-012' : ['# ?$', 'More|continue'],
			'BC95645-024' : ['# ?$', 'More|continue'],
			'BCM-56519' : ['# ?$', 'More|continue'],
			'Lumia' : ['# ?$', 'More|continue'],
			'AAM1008' : ['> ?$'],
			'ePMP 1000' : ['>'],
			'7324' : ['> ?$'],
			'7324 Pizza Box' : ['> ?$'],
			'7302_7330' : ['[#$] ?$'],
			'DSL IES-5000' : ['# ?$|> ?$'],
			'DSL IES-5005' : ['# ?$|> ?$'],
			'ACX2100' : ['> ?$'],
		}
		# os.environ['LINES'] = "25"		borisov-sv
		# os.environ['COLUMNS'] = "150"		borisov-sv

	def file_config(self):
		""" Читаем индивидуальный файл конфигураций для доступа на оборудоание под своими учётными данными """
		if self.login == 'default':
			self.login = getpass.getuser()
		
		ini_local = getattr(configuration, 'CONFIG_PATH')+'config_data_local.ini'
		# pathini = "/home/"+self.login+"/.config/config_data.ini"
		# ini_local = "/var/scripts/system/config_data_local.ini"
		# ini_local = static('config_data_local.ini')
	
		self.password = getattr(configuration, 'TACACS_PASS')
		self.logs_dir = f'/tmp/scripts/log_pexpect_authorization/{self.login}/'

		""" Читаем общий фаил конфигурации для доступа на оборудоание под локальными учётными данными """
		self.config = ConfigParser()
		if os.path.exists(ini_local):
			self.config.read(ini_local)
		else:
			print ("Отсутствует общий конфигурационный файл:", ini_local)

	def oracle_connect(self, dis_connect, **hash_config_sql):
		if dis_connect == 'connect':
			if 'server' in hash_config_sql:
				server = hash_config_sql['server']
			else:
				server = getattr(configuration, 'ASTU_SERVER')

			if 'login' in hash_config_sql:
				login_sql = hash_config_sql['login']
			else:
				login_sql = getattr(configuration, 'ASTU_LOGIN')

			if 'password' in hash_config_sql:
				p_sql	= hash_config_sql['password']
			else:
				p_sql = getattr(configuration, 'ASTU_LOGIN')

			self.connection = cx_Oracle.connect(f"{login_sql}/{p_sql}@{server}", encoding = 'UTF-8')
			self.cursor_oracle = self.connection.cursor()

		elif dis_connect == 'disconnect':
			self.cursor_oracle.close()
			self.connection.close()

	def oracle_select(self, request):
		aa = self.cursor_oracle.execute(request)
		select = []
		for a in aa:
			select.append(list(a))

		return select

	def oracle_update(self, request):
		self.cursor_oracle.execute(request)
		self.connection.commit()
		return 

	def sql_connect(self, dis_connect, **hash_config_sql):
		""" Подключение к базе MySql и отключение от неё
		Для использоваия настроек по умолчпнию, достаточно вызвать функцию с указание необходимой от него задачи

		Пример:
			sql_connect('connect')
			sql_connect('disconnect')

		По умолчанию будет использовать данные из персонального файла конфига
		Так же можно использовать свои значения при вызове данной функции.

		Пример:
			sql_connect('connect', server = '10.10.10.10', login = 'myloginsql', password = 'mypasswordsql'):
		"""
		if dis_connect == 'connect':
			if 'server' in hash_config_sql:
				server = hash_config_sql['server']
			else:
				server = getattr(configuration, 'MYSQL_DB')

			if 'login' in hash_config_sql:
				login_sql = hash_config_sql['login']
			else:
				login_sql = getattr(configuration, 'MYSQL_LOGIN')

			if 'password' in hash_config_sql:
				p_sql	= hash_config_sql['password']
			else:
				p_sql = getattr(configuration, 'MYSQL_PASS')

			self.sql = mysql.connector.connect(host = server, user = login_sql, password = p_sql, charset='utf8', use_unicode = True)
			self.cursor_mysql = self.sql.cursor(buffered=True)
			# self.cursor_mysql = self.sql.cursor()

		elif dis_connect == 'disconnect':
			self.sql.close()

	def sql_select(self, request, *full):
		""" Запрос в базу данных и формирование словаря словарей где IP - это ключ, а значение - это словарь
		Внутренний словарь состоит из ключей - это значение столбцов из БД
		Значение этих ключей - это данные из БД
		"""
		if full and full[0] == 'full':
			free_select = []
			self.cursor_mysql.execute(request)
			for return_sql in self.cursor_mysql:
				temp = []
				for r in return_sql:
					temp.append(r)
				free_select.append(temp)
			return free_select

		else:
			alldic = {}
			try:
				select_query = f"""SELECT h.DEVICEID, h.IPADDMGM, h.NETWORKNAME, m.DEVICEMODELNAME, h.DEVICEDESCR, h.OFFICE, h.DATEMODIFY, h.DEVICESTATUSID, h.MAC
					FROM guspk.host h, guspk.host_model m
					WHERE h.MODELID LIKE m.MODELID AND {request}"""
				# print (select_query)
				self.cursor_mysql.execute(select_query)
				for (DEVICEID, IPADDMGM, NETWORKNAME, DEVICEMODELNAME, DEVICEDESCR, OFFICE, DATEMODIFY, DEVICESTATUSID, MAC) in self.cursor_mysql:
					alldic[IPADDMGM] = {'id':DEVICEID, 'hostname':NETWORKNAME, 'model':DEVICEMODELNAME, 'ticket':DEVICEDESCR, 'office':OFFICE, 'datemodify':DATEMODIFY, 'status':DEVICESTATUSID, 'mac':MAC}
			except Error as e:
				print(e)
			finally:
				return alldic

	def sql_update(self, request):
		""" Запрос в БД для обновления данных """
		self.sql.commit()
		self.cursor_mysql.execute(request)
		# print(self.cursor_mysql.lastrowid)
		self.sql.commit()
		return self.cursor_mysql.lastrowid
				
		# last_insert_id = []
		# results = self.cursor_mysql.execute(request, multi=True)
		# for return_sql in results:
		# 	for r in return_sql:
		# 		last_insert_id.append(r)
		# # last_insert_id = self.cursor_mysql.execute("SELECT LAST_INSERT_ID();")
		# self.sql.commit()
		# return last_insert_id

	def sql_update_2(self, request):
		""" Зарос в БД для обновления данных """
		self.sql.commit()
		self.cursor_mysql.execute(request)
		# print(self.cursor_mysql.lastrowid)
		self.sql.commit()
		return self.cursor_mysql.lastrowid

	def disconnect(self, logging = True):
		""" Завершение сеанса telnet """
		if logging == True:
			self.new_telnet.logfile_read.close()
		self.new_telnet.close()

	def check_telnet_connect(self, i, errors = True):
		""" Проверка telnet подключения """
		# print ('check_telnet_connect {}'.format(i))
		error = ""
		if i == 1:
			if errors == True:
				# print ('{:45}{:20}'.format(' == check_telnet_connect_No telnet == ', self.ip))
				error = "telnet_connect_No telnet"
		elif i == 2:
			if errors == True:
				# print ('{:45}{:20}'.format(' == check_telnet_connect_Timeout == ', self.ip))
				error = "telnet_connect_Timeout"
		elif i == 3:
			if errors == True:
				# print ('{:45}{:20}'.format(' == check_telnet_connect_No_route_to_host == ', self.ip))
				error = "telnet_connect_No_route_to_host"
		elif i == 4:
			if errors == True:
				# print ('{:45}{:20}'.format(' == check_telnet_connect_Connection_refused == ', self.ip))
				error = "telnet_connect_Connection_refused"
		elif i != 0:
			if errors == True:
				# print ('{:45}{:20}'.format(' == check_telnet_connect_Other == ', self.ip))
				error = "telnet_connect_Other"

		return error

	def check_authentication(self, i, errors = True):
		""" Проверка авторизации """
		# print ('check_authentication {}'.format(i))
		error = ""
		if i == 1:
			if errors == True:
				# print ('{:45}{:20}'.format(' == check_authentication_Login incorrect == ', self.ip))
				error = "authentication_Login incorrect"
		elif i == 2:
			if errors == True:
				# print ('{:45}{:20}'.format(' == check_authentication_Timeout == ', self.ip))
				error = "authentication_Timeout"
		elif i == 3:
			if errors == True:
				# print ('{:45}{:20}'.format(' == check_authentication_Connection_closed == ', self.ip))
				error = "authentication_Connection_closed"
		elif i != 0:
			if errors == True:
				# print ('{:45}{:20}'.format(' == check_authentication_Other == ', self.ip))
				error = "authentication_Other"

		return error

	def new_send(self, command):
		self.new_telnet.send(command)

	def new_sendline(self, command, **hash_prompt):
		""" Ввод комманд в telnet сеансе
		Команды sendline и expect обеденены в одну функцию, для упрощения написания основного скрипта
		"""
		if 'timeout' in hash_prompt:
			timeout_sendline = hash_prompt['timeout']
		else:
			timeout_sendline = self.timeout

		timeout_expect = 0
		if 'timeout_expect' in hash_prompt:
			timeout_expect = hash_prompt['timeout_expect']

		if 'prompt' in hash_prompt:
			if type(hash_prompt['prompt']) is list:
				prompt = hash_prompt['prompt']
			else:
				prompt = [hash_prompt['prompt']]
		else:
			prompt = self.hash_promt.get(self.model, self.prompt)	# 12.03.18_изменил self.model на self.model_ini
			# prompt = self.hash_promt.get(self.model_ini, self.prompt)	# если в первом значении нет данных, берёт из второго значения
		if not pexpect.TIMEOUT in prompt:
			prompt.append(pexpect.TIMEOUT)

		# print (f" =============== prompt: {prompt} ================")
		if re.search(r'Lumia', self.model): 
			self.new_telnet.send(command+self.dop)
		else:
			self.new_telnet.sendline(command+self.dop)

		if 'timeout_expect' in hash_prompt:
			time.sleep(timeout_expect)

		try:
			i = self.new_telnet.expect(prompt, timeout=timeout_sendline)
		except:
			return 'error decode'

		if re.search(r'1212|1248', self.model): 
			self.full_print('n', i, prompt)
		if re.search(r'BC9569x|BC95645-024|BCM-56519|Lumia', self.model):
			self.full_print(' ', i, prompt)

		if i == len(prompt)-1:
			print ('{:45}{:20} | IP: {:20}'.format(' == Command_Timeout == ', command, self.ip))
			return i

	def full_print(self, com_next, i, prompt):	# если требует нажатие клавиши для большего вывода
		n = 0
		while i == len(prompt)-2:
			if n == 100:
				break
			n += 1
			self.temp_data = self.data_split()
			# print(self.temp_data)
			self.new_telnet.send(com_next)
			i = self.new_telnet.expect(prompt)

	def data_split(self, *hash_data_split):
		""" Для того что бы взять вывод команды, 
		разбить её настроки, обрезать первую строку с командой, 
		последнюю с именем коммутатора и сложить это в list
		"""
		if hash_data_split and hash_data_split[0] == 'list':
			data = self.new_telnet.before.splitlines()
			if data:
				# data.pop()
				# if len(data) > 0:
				# 	del data[0]
				if self.temp_data:
					data = self.temp_data + data
					self.temp_data = ''
		else:
			data = self.new_telnet.before
			if self.temp_data:
				data = self.temp_data + data
				self.temp_data = ''

		return data

	def aut(self, ip, model='default', logging=True, errors = True, proxy = False, **hash_aut):
		""" Для авторизации на оборудоваии достаточно передать IP и model.
		Остальные данные подтягиваются из конфигурационных файлов
		В данной функции реализован метод telnet авторизации для: 
		дсламов: zyxel (1212, 1248, 5000, 5005), alcatel (7324, 7330, 7303, Pizza Box)
		коммутаторов: eltex, zyxel, dlink, alcitec, cisco, juniper
		gpon: ericsson, eltex
		Для записи логов в конкретную директорию < logs_dir = f"{getattr(configuration, 'LOGS_DIR')}/{dir_name}" >


		"""
		# print(f"*****----- AUT IN {ip} -----*****")

		if 'login' in hash_aut and hash_aut['login'] != 'tacacs':
			telnet_login = hash_aut['login']
		else:
			telnet_login = getattr(configuration, 'TACACS_LOGIN')

		if 'password' in hash_aut and hash_aut['password'] != 'tacacs':
			telnet_password	= hash_aut['password']
		else:
			telnet_password = getattr(configuration, 'TACACS_PASS')

		self.ip = ip
		self.model = model
		if proxy == False:
			self.new_telnet = pexpect.spawn('telnet ' + self.ip, encoding='utf-8', timeout=self.timeout)
		else:
			self.new_telnet = pexpect.spawn('socksify telnet ' + self.ip, encoding='utf-8', timeout=self.timeout)
		self.new_telnet.setwinsize(50,150)
		# print (f"""/tmp/scripts/log_pexpect_authorization/{self.login}/{self.ip}.txt""")
		""" Проверка пути до каталога для telnet логов, и создание каталога в случае его отсутствия """
		if logging == True:
			if 'logs_dir' in hash_aut:
				if not os.path.exists(hash_aut['logs_dir']):
					os.makedirs(hash_aut['logs_dir'])
				self.new_telnet.logfile_read = open(f"{hash_aut['logs_dir']}/{ip}.txt", 'w')
			else:
				if not os.path.exists(self.logs_dir):
					os.makedirs(self.logs_dir)
				self.new_telnet.logfile_read = open(f"{self.logs_dir}{ip}.txt", 'w')


		self.model_ini = 'other'
		if re.search(r'WOP-12ac-LR|ePMP 1000|NMU-WF-BS-5|WOP-2AC-LR5', self.model):					# WBS WOP-12ac-LR
			self.model_ini = 'WBS'
		elif re.search(r'1500', self.model):								# Ericsson
			self.model_ini = 'Ericsson'
		elif re.search(r'Pizza Box|500[05]', self.model):					# ZyXel 5000, 5005 and Pizza Box
			self.model_ini = 'Pizza_Box_5000'
		elif re.search(r'7302|7330', self.model):							# Alcatel
			self.model_ini = '7302_7330'
		elif re.search(r'BC9569x|BC95645-024|BCM-56519', self.model):		# MSAN FAIBER
			self.model_ini = 'MSAN_FAIBER'
		elif re.search(r'Lumia', self.model):								# MSAN FAIBER
			self.model_ini = 'Lumia'
		elif re.search(r'1008', self.model):								# Zyxel
			self.model_ini = '1008'
		elif re.search(r'7324', self.model):								# Alcatel 7324
			self.model_ini = '7324'

		# print ("ip: {}\nMODEL: {}\nLogin: {}\npass: {}".format(ip, model, self.login, self.password))

		if self.model_ini == 'other':
			login = telnet_login
			password = telnet_password
		else:
			login = self.config.get(self.model_ini, 'local_login')
			if self.model_ini != '7324' and self.model_ini != '1008':
				password = self.config.get(self.model_ini, 'local_password')

		# print (f"2 - login: {login}, password: {password}")

		expect_login = self.config.get(self.model_ini, 'expect_login')

		# print (f"3 - expect_login: {expect_login}")

		if self.model_ini != '7324' and self.model_ini != '1008':
			expect_password = self.config.get(self.model_ini, 'expect_password')
		prompt_1 = self.config.get(self.model_ini, 'prompt_1')
		prompt_2 = self.config.get(self.model_ini, 'prompt_2')

		# print ("login: {}\npassword: {}\nexpect_login: {}\nexpect_password: {}\nprompt_1: {}\nprompt_2: {}".format(login, password, expect_login, expect_password, prompt_1, prompt_2))
		expects = [expect_login, 'Connection closed', pexpect.TIMEOUT, '[Nn]o route to host', '[Cc]onnection refused']
		i = self.new_telnet.expect(expects, timeout=self.timeout)
		# print(f"*****----- I - {i} -----*****")
		error_con = self.check_telnet_connect(i, errors)
		if i != 0:
			return error_con

		self.dop = ''
		if self.model_ini == 'Ericsson' or self.model == 'LTP-8X' or self.model == 'LTP-4X': # костыль для Ericsson, потому что он требует ввода дополнительного символа "\r" для работоспособности скрипта
			self.dop = '\r'

		mes31xx_21xx_11xx = 'yes pass' # добавлено для того что бы авторизовываться на оборудование которое не требует ввода пароля

		self.new_telnet.sendline(login+self.dop) # self.login
		if self.model_ini != '7324' and self.model_ini != '1008':
			i = self.new_telnet.expect([expect_password, '[>#]', pexpect.TIMEOUT])
			if i == 0:
				self.new_telnet.sendline(password+self.dop)
			if i == 1: # добавлено для того что бы авторизовываться на оборудование которое не требует ввода пароля
				mes31xx_21xx_11xx = 'no pass'
			if i == 2:
				# print ('{:45}{:20}'.format(' == password_Timeout == ', self.ip))
				return i

		if i == 0: # проверка авторизации
			i = self.new_telnet.expect([prompt_1, prompt_2, pexpect.TIMEOUT, 'Connection closed'])
			error_aut = self.check_authentication(i, errors)
			if re.search(r'MA5800', self.model):
				self.new_sendline('enable')
				self.new_sendline('undo smart')
				self.new_sendline('scroll')

		if mes31xx_21xx_11xx == 'no pass': # добавлено для того что бы авторизовываться на оборудование которое не требует ввода пароля
			i = 0

		if i != 0:
			return error_aut

		if self.model_ini == '1008' or self.model_ini == 'MSAN_FAIBER' or self.model_ini == 'Ericsson':
			self.new_telnet.sendline(self.config.get(self.model_ini, 'comm_1')+self.dop)
			self.new_telnet.expect('>|assword:|#|%')
		if self.model_ini == 'MSAN_FAIBER':
			self.new_telnet.sendline('')
			self.new_telnet.expect('#')
		if self.model_ini == 'Ericsson':
			self.new_telnet.sendline(self.config.get(self.model_ini, 'comm_2')+self.dop)
			self.new_telnet.expect('#')
		if self.model_ini == 'Ericsson':
			self.new_telnet.sendline(self.config.get(self.model_ini, 'comm_3')+self.dop)
			self.new_telnet.expect('#')
		# print ('GOOD')

		if self.model == 'Lumia':
			self.dop = '\r'

		return i



	""" Web socket client """

	def ws_connect(self, chat):
		websocket.enableTrace(False)
		self.ws = websocket.WebSocketApp(f"{getattr(configuration, 'WS_PATH')}/{chat}")
		self.wst = threading.Thread(target=self.ws.run_forever)
		self.wst.daemon = True
		self.wst.start()
		conn_timeout = 3
		while not self.ws.sock.connected and conn_timeout:
			time.sleep(1)
			conn_timeout -= 1
		if not self.ws.sock.connected:
			return 'ws is not connected'

		# return ws, wst

	def ws_send_message(self, message):
		if self.ws.sock.connected:
			# for n in range(10):
			self.ws.send(f'{message}')
				# sleep(120)
		else:
			return 'ws connection was be terminated'

	def ws_close(self):
		self.ws.close()
		self.wst.join()
		# print('thread killed') 


	""" Example """

	# chat = 'chat/log_free_ip/'
	# message1 = 'test1'
	# message2 = 'test2'
	# ws, wst = ws_connect(chat)
	# ws_send_message(ws, message1)
	# ws_send_message(ws, message2)
	# ws_close(ws, wst)

	""" === END WS === """


	""" FIAS adress """

	def fias_suggest(self, query, count = 1):
		url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address"
		headers = {"Authorization": f"Token {getattr(configuration, 'DADATA_TOKEN')}", "Content-Type": "application/json"}
		data = {"query": query, "count": count, "geoLocation": "True"}
		suggestions = requests.post(url, data=json.dumps(data), headers=headers)
		suggestions = suggestions.json()
		# print(suggestions)
		if suggestions['suggestions']:
			suggestions = (suggestions['suggestions'][0]['data'])
		else:
			# print(suggestions)
			suggestions = 'error'
		return suggestions

	""" === END FIAS === """


	""" Count Website """

	def count_website(self, t, page, username):

		# t.sql_connect('connect', server='10.180.7.34', login='kolov-aa', password='ten1024')
		count_generator = t.sql_select(f"SELECT count FROM guspk.count WHERE name = '{page}' and user = '{username}'", 'full')
		if count_generator:
			count_generator[0][0] += 1
			t.sql_update(f"UPDATE guspk.count SET count={count_generator[0][0]} WHERE name='{page}' and user='{username}';")
		else:
			t.sql_update(f"INSERT INTO guspk.count (name, `user`, count) VALUES('{page}', '{username}', 1);")

		# t.sql_connect('disconnect')

	""" === END Count === """
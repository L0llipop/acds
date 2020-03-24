import multimodule
import configuration


def error_handler(text, answer):
	# answer = {}
	answer.update({'ok': False, 'error': f'{text}'})
	return answer

def get_argus_data(multi):
	answer = dict.fromkeys(['argus'], {})
	multi.sql_connect('connect')
	summ = multi.sql_select("""SELECT ip, title, hostname, model FROM guspk.host_argus""", "full")
	for n in summ:
		answer['argus'].update({n[0]: {'title': n[1], 'hostname': n[2], 'model': n[3]}})
	multi.sql_connect('disconnect')

	return answer

def get_host_data(multi):
	answer = dict.fromkeys(['host'], {})
	multi.sql_connect('connect')
	summ = multi.sql_select("""SELECT h.IPADDMGM, h.NETWORKNAME, hm.DEVICEMODELNAME 
							FROM guspk.host h
							LEFT JOIN  guspk.host_model hm on hm.MODELID = h.MODELID
							WHERE h.DEVICESTATUSID = 3 or h.DEVICESTATUSID = 2""", "full")
	for n in summ:
		answer['host'].update({n[0]: {'title': n[1], 'model': n[2]}})
	multi.sql_connect('disconnect')
	
	return answer

def guspk_sync():
	n = 0
	multi = multimodule.FastModulAut()
	answer = {}
	# answer = dict.fromkeys(['update', 'insert', 'delete'], {})
	guspk_data = get_argus_data(multi)
	host_data = get_host_data(multi)
	answer.update(guspk_data)
	answer.update(host_data)
	answer.update({'update': {}})
	answer.update({'insert': {}})
	answer.update({'delete': {}})

	for ip in answer['host']:
		n += 1
		if answer['argus'].get(ip):
			for value in answer['host'][ip]:
				if answer['host'][ip][value] != answer['argus'][ip][value]:
					answer['update'].update({ip: {'host': answer['host'][ip], 'argus': answer['argus'][ip]}})
					continue

			del answer['argus'][ip]
		else:
			answer['insert'].update({ip: {'host': answer['host'][ip], 'argus': None}})

	for ip in answer['argus']:
		answer['delete'].update({ip: {'argus': answer['argus'][ip], 'host': None}})


	for key in list(answer.keys()):
		if key != 'update' and key != 'insert' and key != 'delete':
			del answer[key]

	answer['lenght'] = {'update': len(answer['update']), 'insert': len(answer['insert']), 'delete': len(answer['delete'])}

	return answer
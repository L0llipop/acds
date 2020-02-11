from django.shortcuts import render
from django.utils.safestring import mark_safe
import json
# from datetime import date
import datetime
# import time
# from datetime import date

def index(request):
	now = datetime.datetime.now()
	return render(request, 'chat/index.html', {
		'datetime': datetime.datetime.now(),
	})

def room(request, room_name):
	return render(request, 'chat/room.html', {
		'room_name_json': mark_safe(json.dumps(room_name)),
	})


# def topology(request):
# 	user = request.user.username
# 	return render(request, 'chat/topology.html', {
# 		'room_name_json': mark_safe(json.dumps(user)),
# 	})
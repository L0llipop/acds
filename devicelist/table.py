from django.shortcuts import render
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse

def start(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))

	group = [ x.name for x in request.user.groups.all()]
	if not 'admins' in group and not 'table_google' in group:
		return render(request, 'activator/access.html')


	return render(request, 'devicelist/table.html')
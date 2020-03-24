from django.shortcuts import render
from django.conf import settings
from django.shortcuts import redirect
from django.core.mail import send_mail
from django.core.mail import mail_admins
from django.http import JsonResponse

#
import jinja2
import sys, os, re, time
import json
import time
import multimodule


def main(request):
	if not request.user.is_authenticated:
		return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
	if not 'admins' in group:
		return render(request, 'activator/access.html')

	return render(request, 'activator/vpn.html')
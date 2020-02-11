from django import forms

class UserForm(forms.Form):
	required_css_class = "form-control"
	ip_address = forms.CharField(label='IP', max_length=100, required=False)
	hostname = forms.CharField(label='hostname', max_length=100, required=False)
	model = forms.CharField(label='model', max_length=100, required=False)
	# name = forms.CharField()
	# age = forms.IntegerField()

	# subject = forms.CharField(max_length=100)
 #    message = forms.CharField(widget=forms.Textarea)
 #    sender = forms.EmailField()
 #    cc_myself = forms.BooleanField(required=False)

# class NameForm(forms.Form):
#	your_name = forms.CharField(label='Your name', max_length=100)

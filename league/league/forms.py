
from django import forms
from django.forms import fields, widgets, ModelForm
from django_localflavor_us.forms import USZipCodeField, USPhoneNumberField
from django.contrib.auth.models import User

from league.models import Player, Team

class EmailForm(forms.Form):
	subject = forms.CharField(label="Subject")
	to_emails = forms.CharField(disabled=True, label="Send To")
	message = forms.CharField(widget=forms.Textarea, required=False)
	bcc = forms.BooleanField(required=False)
	attachment = forms.FileField(required=False)

class PlayerProfileForm(ModelForm):

	class Meta:
		model = Player
		fields = ('first_name', 'last_name', 'state', 'zip', 'contact_phone', 'gender', 'experience_level', 'emergency_contact_name', 'emergency_contact_phone',)


class RegistrationForm(ModelForm):
	
	email = forms.EmailField(label="Email")
	email_confirm = forms.EmailField(label="Confirm Email", required=True)
	password = forms.CharField(max_length=24, label="Password", widget=widgets.PasswordInput(render_value=False))
	password_confirm = forms.CharField(max_length=24, label="Password (confirm)", widget=widgets.PasswordInput(render_value=False))

	class Meta:
		model = Player
		fields = ('first_name', 'last_name', 'state', 'zip', 'email', 'email_confirm', 'contact_phone', 'gender', 'experience_level', 'emergency_contact_name', 'emergency_contact_phone', 'password', 'password_confirm',)

	def clean(self):
		cleaned_data = self.cleaned_data
		if cleaned_data.get('email') is not None and cleaned_data.get('email_confirm') is not None:
			if cleaned_data['email'] != cleaned_data['email_confirm']:
				#self._errors['email_confirm'] = [u"The email addresses you have entered do not match each other."]
				raise forms.ValidationError('The email addresses you have entered do not match each other.')
		return cleaned_data

	def clean_zip(self):
		self.cleaned_data['zip'] = self.cleaned_data['zip'].replace(' ', '')
		return self.cleaned_data['zip']
	
	def clean_email(self):
		if not self.instance.pk and len(User.objects.filter(email=self.cleaned_data['email'])) > 0:
			raise forms.ValidationError("This email address is already in use by another player.")
		return self.cleaned_data['email']
	
	def clean_password_confirm(self):
		if self.cleaned_data['password'] != self.cleaned_data['password_confirm']:
			raise forms.ValidationError("The passwords you have entered do not match each other.")
	
	def save(self, commit=True):
		if not self.instance or not self.instance.pk or not self.instance.user:
			user = User(username=self.cleaned_data['email'], email=self.cleaned_data['email'])
			user.set_password(self.cleaned_data['password'])
			user.save()
			self.instance.user = user
		elif self.cleaned_data['email'] != self.instance.user.email or self.cleaned_data['password']:
			self.instance.user.email = self.cleaned_data['email']
			if self.cleaned_data['password']:
				self.instance.user.set_password(self.cleaned_data['password'])
			self.instance.user.save()
		return super(RegistrationForm, self).save(commit=commit)
	


class PlayerAdminForm(ModelForm):
	zip = USZipCodeField(label="Zip")
	email = forms.EmailField(label="Email")
	password = forms.CharField(max_length=24, label="Password", widget=widgets.PasswordInput(render_value=False), required=False)
	password_confirm = forms.CharField(max_length=24, label="Password (confirm)", widget=widgets.PasswordInput(render_value=False), required=False)
	
	def clean_zip(self):
		self.cleaned_data['zip'] = self.cleaned_data['zip'].replace(' ', '')
		return self.cleaned_data['zip']
	
	def clean_email(self):
		if not self.instance.pk and len(User.objects.filter(email=self.cleaned_data['email'])) > 0:
			raise forms.ValidationError("This email address is already in use by another player.")
		return self.cleaned_data['email']
	
	def clean_password_confirm(self):
		if self.cleaned_data['password'] != self.cleaned_data['password_confirm']:
			raise forms.ValidationError("The passwords you have entered do not match each other.")
	
	def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=None, label_suffix=':', empty_permitted=False, instance=None):
		if instance:
			if not initial:
				initial = {}
			initial['email'] = instance.user.email
		super(PlayerAdminForm, self).__init__(data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, instance)
	
	def save(self, commit=True):
		if not self.instance or not self.instance.pk or not self.instance.user:
			user = User(username=self.cleaned_data['email'].replace('@', '_').replace('.', '_')[:30], email=self.cleaned_data['email'])
			user.set_password(self.cleaned_data['password'])
			user.save()
			self.instance.user = user
		elif self.cleaned_data['email'] != self.instance.user.email or self.cleaned_data['password']:
			self.instance.user.email = self.cleaned_data['email']
			if self.cleaned_data['password']:
				self.instance.user.set_password(self.cleaned_data['password'])
			self.instance.user.save()
		return super(PlayerAdminForm, self).save(commit=commit)
	
	class Meta:
		model = Player
		exclude = ('user',)



class RegistrationForm2(PlayerAdminForm):
	#zip = USZipCodeField(label="Zip", required=True)
	email_confirm = forms.EmailField(label="Confirm Email", required=True)
	#first_name = forms.CharField(max_length=40, label="First Name", required=True)
	#last_name = forms.CharField(max_length=40, label="Last Name", required=True)
	#password = forms.CharField(max_length=24, label="Password", widget=forms.PasswordInput(render_value=False), required=True)
	#password_confirm = forms.CharField(max_length=24, label="Password (confirm)", widget=forms.PasswordInput(render_value=False), required=True)
	#gender = forms.ChoiceField(choices=Player.GENDER,widget=forms.RadioSelect(), required=True)
	#emergency_contact_name = forms.CharField(max_length=80, label="Emergency contact name", required=True)
	#emergency_contact_phone = USPhoneNumberField(label="Emergency contact phone", required=True)
	#address = forms.CharField(max_length=80, required=True)
	#city = forms.CharField(max_length=80, required=True)
	#contact_phone = USPhoneNumberField(required=True)
	
	def clean(self):
		cleaned_data = self.cleaned_data
		if cleaned_data.get('email') is not None and cleaned_data.get('email_confirm') is not None:
			if cleaned_data['email'] != cleaned_data['email_confirm']:
				self._errors['email_confirm'] = [u"The email addresses you have entered do not match each other."]
		return cleaned_data
	
	class Meta:
		model = Player
		fields = ('first_name', 'last_name', 'state', 'zip', 'email', 'email_confirm', 'contact_phone', 'gender', 'experience_level', 'emergency_contact_name', 'emergency_contact_phone', 'password', 'password_confirm',)
		#'address', 'city', 'interested_in_soccer_school'
		
class InfoForm(PlayerAdminForm):
	zip = USZipCodeField(label="Zip")
	first_name = forms.CharField(max_length=40, label="First Name", required=True)
	last_name = forms.CharField(max_length=40, label="Last Name", required=True)
	password = forms.CharField(max_length=24, label="Password", widget=forms.PasswordInput(render_value=False), required=False)
	password_confirm = forms.CharField(max_length=24, label="Password (confirm)", widget=forms.PasswordInput(render_value=False), required=False)
	gender = forms.ChoiceField(choices=Player.GENDER,widget=forms.RadioSelect(), required=True)
	emergency_contact_name = forms.CharField(max_length=80, label="Emergency contact name", required=True)
	emergency_contact_phone = USPhoneNumberField(label="Emergency contact phone", required=True)
	#address = forms.CharField(max_length=80, required=True)
	#city = forms.CharField(max_length=80, required=True)
	contact_phone = USPhoneNumberField(required=True)
	
	class Meta:
		model = Player
		fields = ('first_name', 'last_name', 'state', 'zip', 'email', 'contact_phone', 'gender', 'experience_level', 'emergency_contact_name', 'emergency_contact_phone', 'password', 'password_confirm')
		#'address', 'city', 'interested_in_soccer_school'


class TeamForm(ModelForm):
	
	class Meta:
		model = Team
		fields = '__all__'

	# def __init__(self, *args, **kwargs):
	# 	super(TeamForm, self).__init__(*args, **kwargs)
	# 	self.fields['division'].widget = widgets.Select()
	# 	self.fields['division'].queryset = Division.objects.none()
	# 	if (self.instance.pk):
	# 		if (self.instance.league):
	# 			self.fields['division'].queryset = Division.objects.filter(
	# 				league=self.instance.league)

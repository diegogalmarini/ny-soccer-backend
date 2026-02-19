from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.dates import WEEKDAYS, MONTHS

from datetime import datetime
from datetime import date
from datetime import timedelta

from localflavor.us.models import USStateField
from paypal.standard.ipn.models import PayPalIPN

from phonenumber_field.modelfields import PhoneNumberField
from tinymce import models as tinymce_models

from multiselectfield import MultiSelectField
from colorfield.fields import ColorField

import hashlib
import uuid
# Create your models here.

STATUS_RECRUIT = 1
STATUS_ACTIVE = 2
STATUS_FINISHED = 3
STATUS_DISABLED = 4
STATUS_FORMER = 5
STATUS_PRIORITY = 13

STATUS_INACTIVE = 6
STATUS_INVITED = 7
STATUS_EMAIL = 8
STATUS_EXPIRED = 9
STATUS_PAYPEND = 10
STATUS_XPLAYERS = 11
STATUS_XMEN = 12


POOL_STAGE_COMPETITION = 'Pool Stage Competition' 
LEAGUE_COMPETITION = 'League' 
TOURNAMENT_COMPETITION = 'Tournament' 
SOCCER_SCHOOL_COMPETITION = 'Soccer School'

COMPETITION_TYPE= (
	(LEAGUE_COMPETITION, 'League Competition'),
	(TOURNAMENT_COMPETITION, 'Tournament Competition'),
	(SOCCER_SCHOOL_COMPETITION, 'Soccer School Competition'),
	(POOL_STAGE_COMPETITION, 'Pool Stage Competition (Multiple Groups)')
)

LEAGUE_STATUS = (
	(STATUS_PRIORITY, 'Priority Registration'),
	(STATUS_RECRUIT,'Open Registration'),
	(STATUS_ACTIVE,'Active Season'),					 
	(STATUS_FINISHED,'Season Complete'),
	(STATUS_DISABLED,'Disabled'),
)

COED_LEAGUE = "COED"
MENS_LEAGUE = "Men's"
LEAGUE_TYPE = (
	(COED_LEAGUE, "COED"),
	(MENS_LEAGUE, "Men's")
)

MATCH_STATUS_COMPLETED = 'Completed'
MATCH_STATUS_CANCELED= 'Canceled'
MATCH_STATUS_SCHEDULED = 'Scheduled'
MATCH_STATUS_DRAFT = 'Draft'

MATCH_STATUS = (
	(MATCH_STATUS_COMPLETED, 'Completed'),
	(MATCH_STATUS_CANCELED, 'Canceled'),
	(MATCH_STATUS_SCHEDULED, 'Scheduled'),
	(MATCH_STATUS_DRAFT, 'Draft'),
)

SEASON_STATUS = (
	(STATUS_ACTIVE, 'Active'),
	(STATUS_INACTIVE, 'Inactive')
)

RECRUIT_F="F"
RECRUIT_MF="MF"
RECRUIT_SLOT_STATUS = (
	(RECRUIT_F,'Female-only'),
	(RECRUIT_MF,'Either'),
)

PLAYER_STATUS = (
	(STATUS_ACTIVE,'Active'),
	(STATUS_DISABLED,'Disabled'),
)

PAYMENT_INDIVIDUAL = 1
PAYMENT_TEAM_EXISTING_TEAM = 2
PAYMENT_TEAM_EXISTING_INDIVIDUAL = 3
PAYMENT_TEAM_NEW_TEAM = 4
PAYMENT_TEAM_NEW_INDIVIDUAL = 5
PAYMENT_OPEN = 6

PAYMENT_TEAM = PAYMENT_TEAM_NEW_TEAM

PAYMENT_PLACEHOLDER_TYPE = (
	(PAYMENT_TEAM_EXISTING_TEAM, 'Existing team, team payment'),
	(PAYMENT_TEAM_EXISTING_INDIVIDUAL, 'Existing team, individual payment'),
	(PAYMENT_TEAM_NEW_TEAM, 'New team, team payment'),
	(PAYMENT_TEAM_NEW_INDIVIDUAL, 'New team, individual payment'),
	(PAYMENT_INDIVIDUAL, 'Individual'),
	(PAYMENT_OPEN, 'Open'),
)

PAYMENT_TYPE = (
	(PAYMENT_TEAM, 'Team'),
	(PAYMENT_INDIVIDUAL, 'Individual'),
)

PAYMENT_UNPAID = 0
PAYMENT_PENDING = 1
PAYMENT_REJECTED = 2
PAYMENT_APPROVED = 3

PAYMENT_STATUS = (
	(PAYMENT_UNPAID, 'Unpaid'),
	(PAYMENT_PENDING, 'Pending'),
	(PAYMENT_APPROVED, 'Approved'),
	(PAYMENT_REJECTED, 'Rejected')
)

EXPERIENCE_LEVEL_CHOICES = (
	('Beginner', 'Beginner'),
	('Advanced Beginner', 'Advanced Beginner'),
	('Intermediate', 'Intermediate'),
	('Experienced', 'Experienced')
)

class WebsiteIncludeText(models.Model):
	name = models.CharField(max_length=80)
	text = tinymce_models.HTMLField()

	def __str__(self):
		return self.name


class Season(models.Model):
	name = models.CharField(max_length=80)
	start_date = models.DateField()
	status = models.IntegerField(choices=SEASON_STATUS)

	def seasonabbrev(self):
		return	" (" + MONTHS[self.start_date.month].title() + " " + str(self.start_date.year) + ")"
	
	def __str__(self):
		return self.name + self.seasonabbrev()
	

class ExternalLeague(models.Model):
	season = models.ForeignKey(Season, on_delete=models.CASCADE)
	name = models.CharField(max_length=128)
	location = models.CharField(max_length=128)
	day_of_week = MultiSelectField(choices=WEEKDAYS.items(), max_choices=3)
	slug = models.SlugField(unique=True, default='do-not-fill', max_length=150, editable=False)
	external_url = models.URLField(default="http://www.")
	active = models.BooleanField(default=True)

	def save(self):
		from django.utils.text import slugify
		self.slug = slugify("%s-%s-%s-%s" % (self.season.pk, self.name, self.day_of_week[0], self.location))
		super(ExternalLeague, self).save()

	def get_absolute_url(self):
		return self.external_url

	def get_day_of_week(self):
		return str.join(' & ', map(lambda x: x[:3].upper(), self.get_day_of_week_list()))

	@property
	def featured_at_homepage(self):
		return True

class LegacyLeague(models.Model):
	season = models.ForeignKey(Season, on_delete=models.CASCADE)
	name = models.CharField(max_length=128)
	location = models.CharField(max_length=128)
	day_of_week = MultiSelectField(choices=WEEKDAYS.items(), max_choices=3)
	page = models.TextField()
	slug = models.SlugField(unique=True, default='do-not-fill', max_length=150, editable=False)
	active = models.BooleanField(default=True)

	def save(self):
		from django.utils.text import slugify
		self.slug = slugify("%s-%s-%s-%s" % (self.season.pk, self.name, self.day_of_week[0], self.location))
		super(LegacyLeague, self).save()

	def get_absolute_url(self):
		from django.urls import reverse
		return reverse('legacy_schedule', args=[self.slug])

	def get_day_of_week(self):
		return str.join(' & ', map(lambda x: x[:3].upper(), self.get_day_of_week_list()))

class League(models.Model):
	season = models.ForeignKey(Season, on_delete=models.CASCADE)
	name = models.CharField(max_length=80)
	day_of_week = MultiSelectField(choices=WEEKDAYS.items(), max_choices=3)

	team_registration_credit = models.PositiveIntegerField(default=0, blank=True, null=True)
	registration_cost = models.PositiveIntegerField()
	team_cost = models.PositiveIntegerField()
	num_players_on_field = models.PositiveSmallIntegerField(default=5, blank=True, null=True, verbose_name="number of players on the field")
	minimum_roster_size = models.PositiveSmallIntegerField(default=5, null=True,blank=True)
	minimum_num_women_on_field = models.PositiveSmallIntegerField(default=0, blank=True, null=True, verbose_name="minimum number of women on the field")
	status = models.IntegerField(choices=LEAGUE_STATUS,default=STATUS_ACTIVE)
	league_description = tinymce_models.HTMLField()
	game_location = tinymce_models.HTMLField(blank=True, null=True)
	game_time = models.CharField(max_length=80)
	registration_deadline = models.DateField()
	open_team_count = models.PositiveSmallIntegerField(default=0, blank=True, null=True, verbose_name="number of new teams accepted")
	open_female_slot = models.PositiveSmallIntegerField(default=0, blank=True, null=True, verbose_name="number of free-agent women accepted")
	open_male_slot = models.PositiveSmallIntegerField(default=0, blank=True, null=True, verbose_name="number of free-agent men accepted")
	######## NEW FIELDS FROM HERE ##########
	location = models.ForeignKey('Venue', null=True, blank=True, on_delete=models.SET_NULL)
	cover_description = models.CharField(max_length=80, null=True, blank=True)
	image = models.ImageField(upload_to = 'leagues/', default = '/static/img/leagues/league-1.jpg')
	game_duration = models.PositiveSmallIntegerField(default=30, null=True, blank=True)
	order = models.PositiveIntegerField(default=5)
	league_type = models.CharField(max_length=128, default=COED_LEAGUE, choices=LEAGUE_TYPE)
	competition_type = models.CharField(max_length=128, default=LEAGUE_COMPETITION, choices=COMPETITION_TYPE)
	featured_at_homepage = models.BooleanField(default=False)
	paypal_account = models.ForeignKey('PayPalAccount', null=True, blank=True, on_delete=models.SET_NULL)

	class Meta:
		ordering = ('-order',)
	
	def __str__(self):
		return self.name + " " + self.get_day_of_week_display() + self.season.seasonabbrev()
	
	def get_day_of_week(self):
		return str.join(' & ', map(lambda x: x[:3].upper(), self.get_day_of_week_list()))

	def slot_display(self):
		if ((self.open_female_slot>0) and (self.open_male_slot>0)):
			return '(' + str(self.open_female_slot) + ' female slots, ' + str(self.open_male_slot) + ' male slots)'
		if (self.open_female_slot>0):
			return '(' + str(self.open_female_slot) + ' female slots)'
		if (self.open_male_slot>0):
			return '(' + str(self.open_male_slot) + ' male slots)'
		return ''

	def is_coed(self):
		return self.league_type == COED_LEAGUE

	def is_league(self):
		return self.competition_type == LEAGUE_COMPETITION

	def is_pool_competition(self):
		return self.competition_type == POOL_STAGE_COMPETITION

	def is_tournament(self):
		return self.competition_type == TOURNAMENT_COMPETITION

	def is_soccer_school(self):
		return self.competition_type == SOCCER_SCHOOL_COMPETITION

	def is_active(self):
		return self.status == STATUS_ACTIVE

	def get_absolute_url(self):
		from django.urls import reverse
		return reverse('league_schedule', args=[self.pk])


class Division(models.Model):
	name = models.CharField(max_length=80)
	league = models.ForeignKey(League, related_name='divisions', on_delete=models.CASCADE)
	order = models.PositiveIntegerField(default=5)
	
	class Meta:
		ordering = ('order',)

	def __str__(self):
		return "%s - %s" % (self.name, self.league)
	
	def season(self):
		return self.league.season
	
	def get_absolute_url(self):
		from django.urls import reverse
		return reverse('league_division_schedule', args=[self.league.pk, self.pk])

	season.short_description='Season'
		
class HistoricalTeam(models.Model):	 
	permanent_name=models.CharField(max_length=80)
	
	def __str__(self):
		return self.permanent_name
		
class Team(models.Model):
	name = models.CharField(max_length=80)
	league = models.ForeignKey(League, related_name='teams', on_delete=models.CASCADE)
	division = models.ForeignKey(Division, blank=True, null=True, on_delete=models.SET_NULL)
	color_name = ColorField(max_length=40,blank=True)
	historical_team = models.ForeignKey(HistoricalTeam, verbose_name="Historical Team Name", help_text="The historical team record allows a team's stats to be tracked from season to season without requiring the team's name to remain constant.	If none is specified, a new one will automatically be created.", blank=True, null=True, on_delete=models.SET_NULL)
	administrator_notes = models.TextField(max_length=2000,blank=True)
	players = models.ManyToManyField("Player", through="TeamPlayer")
	
	payment_transaction = models.ForeignKey(PayPalIPN, null=True, blank=True, on_delete=models.SET_NULL)
	payment_status = models.IntegerField(choices=PAYMENT_STATUS, default=PAYMENT_UNPAID)
	payment_type = models.IntegerField(choices=PAYMENT_TYPE, null=True, blank=True)
	override_payment = models.BooleanField(default=False, help_text="By default, the 'Payment status' option is a reflection of the data the system has received from PayPal, and will be updated as PayPal receives new information about this payment. To manually specify payment status, check this box to keep the system from overwriting your input.")
	payment_notes = models.TextField(blank=True, help_text="If you manually change the payment information, this field provides an opportunity for you to make internal notes about payment status.  It is not publicly visible.")
	uuid = models.UUIDField(default=uuid.uuid4, editable=False)

	def team_name(self):
		return self.name + self.league.season.seasonabbrev()
	
	def __str__(self):
		return self.team_name()
	
	def save(self):
		#payment stuff
		if self.payment_transaction is not None and not self.override_payment:
			if self.payment_transaction.payment_status == "Completed" and not self.payment_transaction.flag:
				self.payment_status = PAYMENT_APPROVED
			elif self.payment_transaction.payment_status == "Pending" or (self.payment_transaction.payment_status == "Completed" and self.payment_transaction.flag):
				self.payment_status = PAYMENT_PENDING
			else:
				self.payment_status = PAYMENT_REJECTED
		
		#historical team stuff
		if not self.historical_team:
			historical_team = HistoricalTeam(permanent_name=self.name)
			historical_team.save()
			self.historical_team = historical_team
		
		super(Team, self).save()
	
	def season(self):
		return self.league.season
	season.short_description='Season'

	
	def gender_information(self):
		num_men = self.players.filter(gender=Player.GENDER_M).count()
		num_women = self.players.filter(gender=Player.GENDER_F).count()
		quota = self.league.minimum_num_women_on_field
		if num_women < quota:
			s = str(quota - num_women) + " below"
		elif num_women > quota:
			s = str(num_women - quota) + " above"
		else:
			s = "at"
		return "%d men, %d women (%s quota)" % (num_men, num_women, s)

	def status(self):
		##
		# Matches Played | Match Won | Match Even | Match Lost | GA | GD | POINTS
		#
		mp = self.match_local.count() + self.match_visitor.count() 
		return (mp, 1, 1, 1, 4, 2, 4)

class Player(models.Model):
	GENDER_M="M"
	GENDER_F="F"

	GENDER = (
		(GENDER_M,'Male'),
		(GENDER_F,'Female'),
	)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	status = models.IntegerField(choices=PLAYER_STATUS, default=STATUS_ACTIVE, null=True, blank=True)
	first_name = models.CharField(max_length=40)
	last_name = models.CharField(max_length=40)
	gender = models.CharField(max_length=40,choices=GENDER)
	address = models.CharField(max_length=80,blank=True)
	city = models.CharField(max_length=80,blank=True)
	state = USStateField(blank=True, default="NY")
	zip = models.CharField(max_length=12)
	contact_phone = models.CharField(max_length=20)#PhoneNumberField(blank=True)
	emergency_contact_name = models.CharField(max_length=80)
	emergency_contact_phone = models.CharField(max_length=20)#PhoneNumberField()
	interested_in_brooklyn_leagues = models.BooleanField(default=False)
	interested_in_manhattan_leagues = models.BooleanField(default=False)
	interested_in_soccer_school = models.BooleanField(default=False, verbose_name="soccer school", help_text="I would like to know more about NY Coed Soccer School")
	administrator_notes = models.TextField(max_length=2000,blank=True)
	experience_level = models.CharField(max_length=40, choices=EXPERIENCE_LEVEL_CHOICES)
	
	def full_name(self):
		return self.first_name + " " + self.last_name
	
	def email(self):
		return self.user.email

	def __str__(self):
		return self.full_name()	
	
	
class TeamPlayer(models.Model):	 
	team = models.ForeignKey(Team,null=True,blank=True, on_delete=models.CASCADE)
	player = models.ForeignKey(Player, on_delete=models.CASCADE)
	is_captain = models.BooleanField(default=False)
	league = models.ForeignKey(League, on_delete=models.CASCADE)
	payment_transaction = models.ForeignKey(PayPalIPN, null=True, blank=True, on_delete=models.SET_NULL)
	payment_status = models.IntegerField(choices=PAYMENT_STATUS, default=PAYMENT_UNPAID)
	override_payment = models.BooleanField(default=False, help_text="By default, the 'Payment status' option is a reflection of the data the system has received from PayPal, and will be updated as PayPal receives new information about this payment. To manually specify payment status, check this box to keep the system from overwriting your input.")
	payment_notes = models.TextField(blank=True, help_text="If you manually change the payment information, this field provides an opportunity for you to make internal notes about payment status.  It is not publicly visible.")
	
	class Meta:
		verbose_name = 'Team roster record'
		verbose_name_plural = 'Team Roster'
	
	def __str__(self):
		if self.team:
			return self.player.first_name[:1] + ". " + self.player.last_name + " on team " + self.team.name
		else:
			return self.player.first_name[:1] + ". " + self.player.last_name + " in league " + self.league.name
	
	def player_name(self):
		return '<a href="../player/' + str(self.player.pk) + '">' + str(self.player) + '</a>'
	player_name.allow_tags = True
	player_name.admin_order_field = 'player__last_name'
	
	def team_name(self):
		if self.team:
			return '<a href="../team/' + str(self.team.pk) + '">' + str(self.team.name) + '</a>'
		else:
			return "(None)"
	team_name.allow_tags = True
	team_name.admin_order_field = 'team'
	
	def save(self):
		#payment stuff
		if self.payment_transaction is not None and not self.override_payment:
			if self.payment_transaction.payment_status == "Completed" and not self.payment_transaction.flag:
				self.payment_status = PAYMENT_APPROVED
			elif self.payment_transaction.payment_status == "Pending" or (self.payment_transaction.payment_status == "Completed" and self.payment_transaction.flag):
				self.payment_status = PAYMENT_PENDING
			else:
				self.payment_status = PAYMENT_REJECTED
		
		#team stuff
		if self.team:
			self.league=self.team.league
		
		#call the real save
		super(TeamPlayer, self).save()

	def season(self):
		if not self.league:
			return self.team.league.season 
		return self.league.season 
	
	def has_paid(self):
		return self.payment_status == PAYMENT_APPROVED or (self.team and self.team.payment_status == PAYMENT_APPROVED)
	
	def has_paid_or_pending(self):
		return self.payment_status == PAYMENT_APPROVED or self.payment_status == PAYMENT_PENDING or (self.team and (self.team.payment_status == PAYMENT_APPROVED or self.team.payment_status == PAYMENT_PENDING))
	
	def pretty_payment_status(self):
		if self.team and self.team.payment_status == PAYMENT_APPROVED and self.team.payment_type == PAYMENT_TEAM:
			return "Approved (team)"
		else:
			return dict(PAYMENT_STATUS)[self.payment_status]
	def gender(self):
		return dict(Player.GENDER)[self.player.gender]

class PaymentPlaceholder(models.Model):
	placeholder_type = models.IntegerField(choices=PAYMENT_PLACEHOLDER_TYPE)
	player = models.ForeignKey(Player, on_delete=models.CASCADE)
	league = models.ForeignKey(League, on_delete=models.CASCADE)
	team = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL)
	team_name = models.CharField(max_length=80, blank=True)
	cost = models.CharField(max_length=20)
	timestamp = models.DateTimeField(auto_now_add=True)
	
	def get_name(self):
		name = self.league.paypal_account.company
		if self.placeholder_type == PAYMENT_INDIVIDUAL or self.placeholder_type == PAYMENT_OPEN:
			name = name + " payment for"
		else:
			name = name + " captain's payment for"
		
		if self.placeholder_type == PAYMENT_OPEN:
			name += " " + self.league.name + " league"
		elif self.placeholder_type == PAYMENT_TEAM_NEW_TEAM or self.placeholder_type == PAYMENT_TEAM_NEW_INDIVIDUAL:
			name += " team " + self.team_name
		else:
			name += " team " + self.team.name
		
		if self.placeholder_type == PAYMENT_TEAM_NEW_TEAM or self.placeholder_type == PAYMENT_TEAM_EXISTING_TEAM:
			name += " (whole-team fee)"
		
		return name
	
	def save(self):
		if not self.pk:
			if self.placeholder_type == PAYMENT_TEAM_NEW_TEAM or self.placeholder_type == PAYMENT_TEAM_NEW_INDIVIDUAL:
				self.league.open_team_count -= 1
				self.league.save()
			elif self.placeholder_type == PAYMENT_OPEN:
				if self.player.gender == Player.GENDER_M:
					self.league.open_male_slot -= 1
				else:
					self.league.open_female_slot -= 1
				self.league.save()
			
			self.timestamp = datetime.now()
		super(PaymentPlaceholder, self).save()
	
	def purge(self):
		if self.placeholder_type == PAYMENT_TEAM_NEW_TEAM or self.placeholder_type == PAYMENT_TEAM_NEW_INDIVIDUAL:
			self.league.open_team_count += 1
			self.league.save()
		elif self.placeholder_type == PAYMENT_OPEN:
			if self.player.gender == Player.GENDER_M:
				self.league.open_male_slot += 1
			else:
				self.league.open_female_slot += 1
			self.league.save()
		
		self.delete()
	
	def fulfill(self, payment):
		if self.placeholder_type == PAYMENT_TEAM_EXISTING_TEAM:
			self.team.payment_transaction = payment
			self.team.payment_type = PAYMENT_TEAM
			self.team.payment_status = PAYMENT_APPROVED
			self.team.save()
		
		elif self.placeholder_type == PAYMENT_TEAM_EXISTING_INDIVIDUAL:
			self.team.payment_transaction = payment
			self.team.payment_type = PAYMENT_INDIVIDUAL
			self.team.payment_status = PAYMENT_APPROVED
			self.team.save()
			
			tp = TeamPlayer.objects.filter(player=self.player, team=self.team)
			if len(tp) > 0:
				tp[0].payment_transaction = payment
				tp[0].payment_status = PAYMENT_APPROVED
				tp[0].save()
		
		elif self.placeholder_type == PAYMENT_TEAM_NEW_TEAM:
			team = Team(name=self.team_name, league=self.league, payment_transaction=payment, payment_type=PAYMENT_TEAM, payment_status=PAYMENT_APPROVED)
			team.save()
			
			teamplayer = TeamPlayer(player=self.player, team=team, is_captain=True, payment_status=PAYMENT_APPROVED)
			teamplayer.save()

		elif self.placeholder_type == PAYMENT_TEAM_NEW_INDIVIDUAL:
			team = Team(name=self.team_name, league=self.league, payment_transaction=payment, payment_type=PAYMENT_INDIVIDUAL, payment_status=PAYMENT_APPROVED)
			team.save()
			
			teamplayer = TeamPlayer(player=self.player, team=team, payment_transaction=payment, is_captain=True, payment_status=PAYMENT_APPROVED)
			teamplayer.save()
		
		elif self.placeholder_type == PAYMENT_INDIVIDUAL:
			teamplayer = TeamPlayer(player=self.player, team=self.team, payment_transaction=payment, payment_status=PAYMENT_APPROVED)
			teamplayer.save()
			
		elif self.placeholder_type == PAYMENT_OPEN:
			teamplayer = TeamPlayer(player=self.player, league=self.league, payment_transaction=payment, payment_status=PAYMENT_APPROVED)
			teamplayer.save()
		
		self.delete()
	
	def get_payment_form(self):
		from django.urls import reverse
		from paypal.standard.forms import PayPalPaymentsForm
		from time import time
		
		#make sure we've saved
		if not self.pk:
			self.save()
		
		business_account = self.league.paypal_account.receiver_email if self.league.paypal_account else 'no-reply@nycoedsoccer.com'
		
		cancel_payment = reverse('player_payment_cancel', args=[self.pk]) 
		invoice_num = str(self.pk) + '_' + str(int(time()))
		s = settings.SECRET_KEY + invoice_num
		invoice_num = invoice_num + '_' + hashlib.md5(s.encode('utf-8')).hexdigest()[:5]
		paypal_dict = {
			"business": business_account,
			"amount": str(self.cost) + ".00",
			"item_name": self.get_name(),
			"invoice": invoice_num,
			"notify_url": "http://" + settings.SERVER_URL + "/payment/",
			"return_url": "http://" + settings.SERVER_URL + "/player/teams",
			"cancel_return": "http://" + settings.SERVER_URL + cancel_payment,
		}
		return PayPalPaymentsForm(initial=paypal_dict)

	@classmethod
	def process_payment(cls, sender, **kwargs):
		invoice_parts = sender.invoice.split("_")
		
		invoice_id = invoice_parts[0]
		invoice_time = invoice_parts[1]
		invoice_hash = invoice_parts[2]
		
		#hash check
		s = settings.SECRET_KEY + invoice_id + "_" + invoice_time
		if hashlib.md5(s.encode('utf-8')).hexdigest()[:5] != invoice_hash:
			#hash failure
			sender.response += "\nHash failure"
			sender.save()
			return
		
		#placeholder exists check
		placeholder_query = cls.objects.filter(pk=invoice_id)
		if len(placeholder_query) == 0:
			#couldn't find the record
			sender.response += "\nNo placeholder match"
			sender.save()
			return
		
		#cost check
		placeholder = placeholder_query[0]
		if str(placeholder.cost) + ".00" != str(sender.payment_gross):
			sender.response += "\nCost mismatch"
			sender.save()
			return
		
		placeholder.fulfill(sender)
	
	@classmethod
	def purge_outdated(cls):
		for placeholder in cls.objects.filter(timestamp__lte=(datetime.now() - timedelta(minutes=settings.PAYMENT_TIMEOUT))):
			placeholder.purge()


class Round(models.Model):
 	league = models.ForeignKey(League, on_delete=models.CASCADE)
 	date = models.DateTimeField()
 	division = models.ForeignKey(Division, null=True, blank=True, on_delete=models.SET_NULL)
 	name = models.CharField(max_length=128, default='ROUND')
 	order = models.PositiveIntegerField(default=1)
 	short_description = models.CharField(max_length=255, null=True, blank=True)

 	def __unicode__(self):
 		return "%s - %s" % (self.league, self.name)


 	def __str__(self):
 		return "%s - %s" % (self.league, self.name)


class Match(models.Model):
	#league = models.ForeignKey(League)
	round = models.ForeignKey(Round, related_name='matches', null=True, blank=True, on_delete=models.SET_NULL)
	team_a = models.ForeignKey(Team, related_name='match_local', null=True, blank=True, on_delete=models.SET_NULL)
	team_b = models.ForeignKey(Team, related_name='match_visitor', null=True, blank=True, on_delete=models.SET_NULL)
	team_a_placeholder = models.CharField(max_length=128, null=True, blank=True)
	team_b_placeholder = models.CharField(max_length=128, null=True, blank=True)
	date = models.DateField()
	time = models.TimeField()
	team_a_score = models.IntegerField(default=0)
	team_b_score = models.IntegerField(default=0)
	status = models.CharField(choices=MATCH_STATUS, max_length=40, default=MATCH_STATUS_SCHEDULED)
	rescheduled = models.BooleanField(default=False)
	reprogramming_reason = models.TextField(blank=True, null=True)
	comment = models.CharField(max_length=255, null=True, blank=True)

	@property
	def duration(self):
		return self.round.league.game_duration

	def local(self):
		return self.team_a.name if self.team_a else self.team_a_placeholder

	def visitor(self):
		return self.team_b.name if self.team_b else self.team_b_placeholder

	def was_cancelled(self):
		return self.status == MATCH_STATUS_CANCELED

	def is_draft(self):
		return self.status == MATCH_STATUS_DRAFT

	def was_played(self):
		return self.status == MATCH_STATUS_COMPLETED

	def score_local(self):
		if self.status == MATCH_STATUS_COMPLETED: return self.team_a_score
		return '-'

	def score_visitor(self):
		if self.status == MATCH_STATUS_COMPLETED: return self.team_b_score
		return '-'

class Venue(models.Model):
	name = models.CharField(max_length=80)
	location = models.CharField(max_length=255)
	short_description = models.TextField()
	tag = models.SlugField()
	address = models.CharField(max_length=255)
	lat = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal(0.0))
	lon = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal(0.0))
	image = models.ImageField(upload_to = 'venues/', default = '/static/img/venues/venue-1.jpg')
	google_map_link = models.URLField(blank=True, null=True)
	order = models.PositiveIntegerField(default=5)

	@property
	def image_url(self):
		"""Return correct URL whether image is a static default or an uploaded file."""
		if self.image and self.image.name and 'static/' not in self.image.name:
			return self.image.url
		return '/static/img/venues/venue-1.jpg'

	def __str__(self):
		return self.name
		

class GoalScorer(models.Model):
	league = models.ForeignKey(League, on_delete=models.CASCADE)
	division = models.ForeignKey(Division, blank=True, null=True, on_delete=models.SET_NULL)
	player = models.ForeignKey(TeamPlayer, on_delete=models.CASCADE)
	goals = models.IntegerField(default=0)


class PayPalAccount(models.Model):
	name = models.CharField(max_length=50)
	company = models.CharField(max_length=128, default='[Company Name]') 
	description = models.TextField(null=True, blank=True)
	receiver_email = models.CharField(max_length=128, null=False, blank=False)
	secondary_email = models.CharField(max_length=128, null=True, blank=True)

	def __str__(self):
		return self.name 
		
def process_payment(sender, **kwargs):
	PaymentPlaceholder.process_payment(sender, **kwargs)

from paypal.standard.ipn.signals import payment_was_successful, payment_was_flagged
payment_was_successful.connect(process_payment)
payment_was_flagged.connect(process_payment)

# Sticking an extra monkey patch in here
from django.contrib.auth.forms import AuthenticationForm
AuthenticationForm.base_fields['username'].max_length = 75
AuthenticationForm.base_fields['username'].widget.attrs['maxlength'] = 75

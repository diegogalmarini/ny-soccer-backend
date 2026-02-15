from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME
from league.models import *

def get_openleagues(player):
	openleagues_query = League.objects.filter(Q(status=STATUS_RECRUIT) | Q(status=STATUS_PRIORITY))
	openleagues = []
	for league in openleagues_query:
		openleagues.append({
			'id' : league.id,
			'name' : str(league),
			'priority' : league.status == STATUS_PRIORITY,
			'open' : league.status == STATUS_RECRUIT,
			'teams' : league.open_team_count,
			'men' : league.open_male_slot,
			'women' : league.open_female_slot,
			'season': league.season.name,
			'is_coed': league.is_coed(),
			'is_tournament': league.is_tournament(),
			'is_league': league.is_league(),
			'is_pool_competition': league.is_pool_competition(),
			'is_soccer_school': league.is_soccer_school(),
			'registered' : len(TeamPlayer.objects.filter(Q(player=player) & (Q(league=league) | Q(team__league=league)))) > 0,
		})
	return openleagues


def get_payment_messages(player):
	messages = []
	# individual invites
	placeholders = PaymentPlaceholder.objects.filter(player=player)
	existing_teams = []
	for placeholder in placeholders:
		if placeholder.placeholder_type == PAYMENT_INDIVIDUAL:
			messages.append("You have a pending invitation for the team <em>" + placeholder.team.name + "</em>. <a href='/player/pay/" + str(placeholder.pk) + "'>Click here to make payment</a> and complete your registration.")
		elif placeholder.placeholder_type == PAYMENT_TEAM_EXISTING_TEAM  or placeholder.placeholder_type == PAYMENT_TEAM_EXISTING_INDIVIDUAL:
			messages.append("You have started the payment process for the team <em>" + placeholder.team.name + "</em>. If you have closed the payment window, <a href='/player/pay/" + str(placeholder.pk) + "'>click here to resume payment</a> and complete your registration, or <a href='/player/pay/" + str(placeholder.pk) + "/cancel'>click here to cancel payment</a>.")
			existing_teams.append(placeholder.team.pk)
		elif placeholder.placeholder_type == PAYMENT_TEAM_NEW_TEAM  or placeholder.placeholder_type == PAYMENT_TEAM_NEW_INDIVIDUAL:
			messages.append("You have started the payment process for the team <em>" + placeholder.team_name + "</em>. If you have closed the payment window, <a href='/player/pay/" + str(placeholder.pk) + "'>click here to resume payment</a> and complete your registration, or <a href='/player/pay/" + str(placeholder.pk) + "/cancel'>click here to cancel payment</a> and free up your slot for another team captain.")
		elif placeholder.placeholder_type == PAYMENT_OPEN:
			messages.append("You have started the payment process for the league <em>" + placeholder.league.name + "</em>. If you have closed the payment window, <a href='/player/pay/" + str(placeholder.pk) + "'>click here to resume payment</a> and complete your registration, or <a href='/player/pay/" + str(placeholder.pk) + "/cancel'>click here to cancel payment</a> and free up your slot for another registrant.")
	
	# created teams
	teamplayers = TeamPlayer.objects.filter(player=player, is_captain=True, team__payment_status=PAYMENT_UNPAID)
	for tp in teamplayers:
		if tp.team.pk not in existing_teams:
			messages.append("You have been made captain of a team for which payment has not yet been made. <a href='/player/teams/" + str(tp.team.pk) + "/pay'>Click here to make payment</a> for this team.")
	
	return messages
	
def player_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
	"""
	Decorator for views that checks that the user is logged in, redirecting
	to the log-in page if necessary.
	"""
	actual_decorator = user_passes_test(
		lambda u: u.is_authenticated and  Player.objects.filter(user=u).exists(),
		login_url=login_url,
		redirect_field_name=redirect_field_name
	)
	if function:
		return actual_decorator(function)
	return actual_decorator
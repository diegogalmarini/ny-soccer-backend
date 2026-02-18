import datetime
import hashlib
import simplejson as json
import base64

from time import time

from django import forms

from django.db.models import Q, Count
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.template import Context, loader
from django.utils.encoding import smart_str
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

from league.forms import *
from league.models import GoalScorer, Venue, Division, Round, Player, League, Team, Match, \
    TeamPlayer, PaymentPlaceholder, WebsiteIncludeText, ExternalLeague, \
    STATUS_FINISHED, STATUS_ACTIVE, STATUS_RECRUIT, STATUS_PRIORITY, STATUS_DISABLED,\
    MATCH_STATUS_SCHEDULED, LegacyLeague, MENS_LEAGUE
from league.models import PAYMENT_UNPAID, PAYMENT_PENDING, PAYMENT_REJECTED, PAYMENT_APPROVED, \
    PAYMENT_OPEN, PAYMENT_TEAM, PAYMENT_INDIVIDUAL, PAYMENT_TEAM_NEW_INDIVIDUAL, \
    PAYMENT_TEAM_NEW_TEAM, MATCH_STATUS_COMPLETED, MATCH_STATUS_CANCELED, \
    PAYMENT_TEAM_EXISTING_TEAM, PAYMENT_TEAM_EXISTING_INDIVIDUAL
from league.utils import player_required
from import_export import resources

class TeamPlayerResource(resources.ModelResource):
    class Meta:
        model = TeamPlayer
        fields = ('player__first_name', 'player__last_name', \
                'player__user__email', 'player__gender', 'team__name', \
                'is_captain', 'league__name')

    #def dehydrate_full_title(self, obj):
    #    return '%s by %s' % (book.name, book.author.name)


@user_passes_test(lambda x: x in ['martinriva@gmail.com'] or x.email.endswith('@nycoedsoccer.com'))
def mens_admin(request):
    from .filters import TeamRosterFilter

    qs = TeamPlayer.objects.filter(league__league_type=MENS_LEAGUE)
    roster = TeamRosterFilter(request.GET, queryset=qs)
    if request.GET.get('export', False):
        import csv

        dataset = TeamPlayerResource().export(queryset=roster.qs)
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'

        writer = csv.writer(response)
        writer.writerow(['Captain', 'FName', 'LName', 'Email', 'Gender', 'Team', 'League'])
        for d in dataset:
            writer.writerow(d)

        return response

    else:
        return render(request, 'admin/admin_mens.html', {'filter': roster})

def getIncludeDict(keys=[]):
    from django.utils.text import slugify
    wits = WebsiteIncludeText.objects.filter(name__in=keys)
    idict=dict()
    for wit in wits:
        idict[slugify(wit.name)] = wit.text
    return idict


@staff_member_required
def export_players_csv(request):
    import csv

    dt = datetime.datetime.utcnow().isoformat()[:16]
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="players-%s.csv"' % dt

    writer = csv.writer(response)
    writer.writerow(
        [
            "Pk", "First Name", "Last Name", "Email", "Gender", "Experience Level", "Status", "Phone"
        ]
    )
    players = Player.objects.all()
    for p in players:
        data = [
            p.pk,
            p.first_name,
            p.last_name,
            p.user.email,
            p.gender,
            p.experience_level,
            p.status,
            p.contact_phone
        ]
        writer.writerow(data)

    return response


@staff_member_required
def process_matches_import(request):
    """
    id|league__id|division__id| round | team_a__name        |team_b__name       |Date      |Time  |Status
    --|----------|------------|-------|------------------  -|----------|------|------
    1 |2         |Division One| 1     |Top 40 Greatest Kicks|Olympique Manhattan|01/06/2017|8:30pm|Draft 
    2 |4         |Division Two| 2     |Irn Bru              |Gotham Goonies     |01/06/2017|8:30pm|Draft 
    3 |4         |Division Two| 3     |Old & Rowdy          |Fighting Quackers  |01/06/2017|9:15pm|Draft 
    4 |4         |Division One| 3     |Footy McFooty Face   |GTFC               |01/06/2017|9:15pm|Draft 
    """

    from tablib import Dataset
    from datetime import datetime
    from .models import Round

    if request.method == 'POST':

        matches = request.FILES['import_file']
        
        data = matches.read()       
        data = data.decode('utf-8')
        
        imported_data = Dataset().load(data)
        #print(imported_data)
        order = 1
        for row in imported_data:
            league_id = row[0]
            league = get_object_or_404(League, pk=league_id)
            division_name = row[1]
            round_id = row[2]
            team_a_name = row[3]
            team_b_name = row[4]
            try:
                match_date = datetime.strptime(row[5], "%m/%d/%Y")
            except ValueError:
                match_date = datetime.strptime(row[5], "%m/%d/%y")
                
            match_time = datetime.strptime(row[6], "%I:%M%p")
            status = row[7]

            division = None
            dcreated = False
            if division_name not in [u'', '', ' ', None]:
                print('############# division is not none!!!!')
                division, dcreated = Division.objects.get_or_create(league=league, name=division_name)

            round = None
            created = False
            if league.is_league() and division:
                round, created = Round.objects.get_or_create(league=league, division=division, name='ROUND %s' % round_id, date=match_date)
            else:
                round, created = Round.objects.get_or_create(league=league, name='ROUND %s' % round_id, date=match_date)
            
            if created:
                if dcreated:
                    round.division = division
                round.order = order
                round.save()
                order = order + 1
            
            team_a = None
            team_b = None
            try:
                team_a = Team.objects.get(name=team_a_name, league=league)
                team_b = Team.objects.get(name=team_b_name, league=league)
                m, _ = Match.objects.get_or_create(round=round, team_a=team_a, team_b=team_b, date=match_date, time=match_time)
                m.status = status
                m.save()
        
            except Team.DoesNotExist:
                m, _ = Match.objects.get_or_create(round=round, team_a_placeholder=team_a_name, team_b_placeholder=team_b_name, date=match_date, time=match_time)
                m.status = status
                m.save()
         
        return redirect('/admin/league/match/')

    return render(request, 'core/simple_upload.html')

#@cache_page(60 * 15) #15 minutes
def legacy_schedule(request, slug):
    league = get_object_or_404(LegacyLeague, slug=slug)
    return render(request, 'base_legacy_league.html', {'league': league})


#@cache_page(60 * 15) #15 minutes
def welcome(request):
    leagues_qs = League.objects.exclude(status__in=[STATUS_DISABLED, STATUS_FINISHED])
    open_registrations = {}
    league_list = {}
    
    # CORRECCIÓN: Eliminamos la línea 'leagues = []' que sobreescribía los datos.
    # Usamos leagues_qs para el loop.
    for league in leagues_qs:
        if league.location:
            nb = league.location.location
        else:
            nb = "Unknown Location"
        if league.featured_at_homepage: # SHOULD WE CHECK For league.is_active as well?
            if nb in league_list.keys():
                league_list[nb].append(league)
            else:
                league_list[nb] = [league]
        if league.status == STATUS_RECRUIT:
            if nb in open_registrations.keys():
                open_registrations[nb].append(league)
            else:
                open_registrations[nb] = [league]
    
    for league in ExternalLeague.objects.filter(active=True):
        nb = league.location
        if nb in league_list.keys():
            league_list[nb].append(league)
        else:
            league_list[nb] = [league]

    # CORRECCIÓN: Usamos el QuerySet para obtener la temporada de forma segura.
    season = leagues_qs[0].season if leagues_qs.exists() else None
    
    # lets sort it.
    sorted_list = []
    locations = set(Venue.objects.values_list('location', flat=True).order_by('order')) 
    locations.update(set(ExternalLeague.objects.values_list('location', flat=True)))
    for loc in locations:
        if loc in league_list:
            sorted_list.append({'location': loc, 'leagues': league_list[loc]})
    
    
    return render(request, 'main.html', {
        'active_leagues': sorted_list,
        'open_registrations': open_registrations,
        'season': season,
        'flat_texts': getIncludeDict(['Tournaments', 'About', 'Registration'])
    })


def terms(request):
    waiver = getIncludeDict(['Waiver'])
    return render(request, 'terms.html', {
        'websiteIncludes': waiver
    })

def register(request): 
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            player = form.save(commit=False)
            player.status = STATUS_ACTIVE
            player.save()
            
            from django.contrib.auth import authenticate, login
            login(request, player.user)

            return redirect('player')
        else:
            print(form.errors)
    else:
        form = RegistrationForm()
    return render(request, 'registration/signup.html',{'form': form, 'websiteIncludes':getIncludeDict(['Waiver'])})


@player_required
def player_dashboard(request):
    from league.utils import get_openleagues, get_payment_messages 
    player = Player.objects.get(user=request.user)
    openleagues = get_openleagues(player)
    return render(request, 'league/player.html', {'openleagues': openleagues, 'extra_messages': get_payment_messages(player)})


@player_required
def player_teams(request):
    from league.utils import get_payment_messages, get_openleagues
    player = Player.objects.get(user=request.user)
    teamplayers = TeamPlayer.objects.filter(player=player).select_related()
    openleagues = get_openleagues(player)

    return render(request, 'league/teams.html', {
            'teamplayers':teamplayers,
            'openleagues': openleagues,
            'extra_messages': get_payment_messages(player)
            }
    )
    

@player_required
def player_team_info(request, team_id):
    team = Team.objects.get(pk=team_id)
    player = Player.objects.get(user=request.user)
    try:
        teamplayer = TeamPlayer.objects.get(team=team, player=player)
        am_i_captain = teamplayer.is_captain
        teamplayers = team.teamplayer_set.all().select_related().order_by('is_captain', 'player__last_name')
        invitation = "http://%s/invitation/%s" % (settings.SERVER_URL, team.uuid)
        paid = team.payment_status == PAYMENT_APPROVED

        today = datetime.date.today()
        upcoming_matches = Match.objects.filter(Q(team_a=team) | Q(team_b=team)).filter(status=MATCH_STATUS_SCHEDULED, date__gte=today).order_by('date')
        matches = []
        for m in upcoming_matches:
            matches.append(
                {
                'team': m.visitor() if m.team_a.pk == team.pk else m.local(),
                'location': m.round.league.location.location if m.round.league.location else "TBD",
                'date': m.date,
                    'time': m.time,
                }
            )
        return render(request, 'league/team.html', {
            'team': team, 
            'teamplayers': teamplayers, 
            'invitation': invitation,
            'is_captain': am_i_captain,
            'paid' : paid,
            'matches': matches
        })
    except TeamPlayer.DoesNotExist:
        messages.add_message(request, messages.INFO, 'You are not member of team %s' % team.name)
        return redirect('player')

@player_required
def player_profile(request):
    player = Player.objects.get(user=request.user)
    if request.method == 'POST':
        form = PlayerProfileForm(request.POST or None, instance=player) 
        if form.is_valid():
            player = form.save()
            return redirect("player")
    else:
        form = PlayerProfileForm(instance=player)

    return render(request, 'registration/edit_profile.html', {'form': form})


@player_required
def join_league(request, league_id):
    player = Player.objects.get(user=request.user)
    league = League.objects.get(pk=league_id)
    has_joined = TeamPlayer.objects.filter(player=player, league=league)
    slot_available = False
    if player.gender == Player.GENDER_F:
        slot_available = league.open_female_slot > 0
    else:
        slot_available = league.open_male_slot > 0
    return render(request, 'league/league.html', {
        'league': league,
        'teams': league.teams,
        'has_joined': has_joined, 
        'slot_available': slot_available,
        'team_available': league.open_team_count > 0,
        'PRIORITY': STATUS_PRIORITY
    })


@player_required
def reserve_league(request, league_id):
    player = Player.objects.get(user=request.user)
    my_league = League.objects.get(pk=league_id)
    teamplayers = TeamPlayer.objects.filter(player=player, league=my_league)
    if teamplayers:
        request.user.message_set.create(message="Your request to join the league " + my_league.name + " was already accepted")
        return redirect('player_teams')
    else:
        # generate the form
        class OpenRegForm(forms.Form):
            pass
                
        #parse response
        if request.method == 'POST':
            form = OpenRegForm(request.POST)
            if form.is_valid():
                placeholder = PaymentPlaceholder(placeholder_type=PAYMENT_OPEN, player=player, league=my_league, cost=my_league.registration_cost)
                placeholder.save()
                return redirect('player_pay', pk=str(placeholder.pk))
        else:
            form = OpenRegForm()
        return render(request, 'league/team_open.html', {'form': form, 'league': my_league})


@player_required
def player_pay(request, pk):
    player = Player.objects.get(user=request.user)
    placeholder = get_object_or_404(PaymentPlaceholder, player=player, pk=pk)
    form = placeholder.get_payment_form()
    return render(request, 'league/pay.html', {'form': form, 'placeholder': placeholder})


@player_required
def player_payment_cancel(request, pk):
    player = Player.objects.get(user=request.user)
    try:
        placeholder = PaymentPlaceholder.objects.get(player=player, pk=pk)
        placeholder.purge()
        messages.add_message(request, messages.INFO, 'Your payment was canceled.')
        return redirect('player_teams')
    except PaymentPlaceholder.DoesNotExist:
        return redirect('player')

@player_required
def create_team(request, league_id):
    league = get_object_or_404(League, pk=league_id)
    player = Player.objects.get(user=request.user)
    
    # generate the form
    if league.is_tournament():
        PAYMENT_TYPE = (
            (PAYMENT_TEAM, 'Team payment: $' + str(league.team_cost)),
        )
    else:
        PAYMENT_TYPE = (
            (PAYMENT_TEAM, 'Team payment: $' + str(league.team_cost)),
            (PAYMENT_INDIVIDUAL, 'Individual: $' + str(league.registration_cost)),
        )
    class TeamCreateForm(forms.Form):
        team_name = forms.CharField(max_length=80)
        payment_type = forms.ChoiceField(PAYMENT_TYPE, widget=forms.RadioSelect())

    if request.method == 'POST':
        form = TeamCreateForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['payment_type'] == str(PAYMENT_TEAM):
                placeholder = PaymentPlaceholder(placeholder_type=PAYMENT_TEAM_NEW_TEAM, player=player, league=league, team_name=form.cleaned_data['team_name'], cost=league.team_cost)
            else:
                placeholder = PaymentPlaceholder(placeholder_type=PAYMENT_TEAM_NEW_INDIVIDUAL, player=player, league=league, team_name=form.cleaned_data['team_name'], cost=league.registration_cost)
            placeholder.save()
            return redirect('player_pay', pk=str(placeholder.pk))
    else:
        form = TeamCreateForm()
    return render(request, 'league/team_create.html', {'form': form, 'league': league})


@staff_member_required
def league_clone(request, league_id):
    league = get_object_or_404(League, pk=league_id)
    league.pk = None
    league.name += ' [CLONED]'
    league.status = STATUS_DISABLED
    league.save()
    return redirect('admin:league_league_changelist')


@staff_member_required
def league_create_premiership(request, league_id):
    from copy import deepcopy
    from league.models import STATUS_FINISHED, STATUS_DISABLED
    league = get_object_or_404(League, pk=league_id)
    if league.is_pool_competition():
        # Update Current League Status
        league.status = STATUS_FINISHED
        league.save()

        new_league = deepcopy(league)

        # Create a new League based on current one.
        new_league.pk = None
        new_league.name += ' [PREMIER]'
        new_league.status = STATUS_DISABLED
        new_league.save()

        # for division in league.divisions.all():
        #      new_division = division
        #      new_division.pk = None
        #      new_division.league = new_league
        #      new_division.save()

        # Clone Teams & Players
        for team in league.teams.all():
            new_team = deepcopy(team)
            new_team.pk = None
            new_team.league = new_league
            new_team.division = None
            new_team.save()

            for player in team.teamplayer_set.all():
                new_player = deepcopy(player)
                new_player.pk = None
                new_player.team = new_team
                new_player.save()

    return redirect('admin:league_league_changelist')


@staff_member_required
def league_fixture(request, league_id):
    league = get_object_or_404(League, pk=league_id)
    for local in league.teams.all():
        pass

    return redirect('admin:league_league_changelist')

### UTILS ####
def get_league_table(teams, matches, league):
    table = []
    for team in teams:
        team_matches = matches.filter(Q(team_a=team) | Q(team_b=team), status=MATCH_STATUS_COMPLETED)
        goal_for = 0
        goal_against = 0
        match_won = 0
        match_lost = 0
        match_drawn = 0
        points = 0
        for my_match in team_matches:
            if my_match.team_a == team:
                #calc_stats(team, my_match.team_b)
                goal_for += my_match.team_a_score
                goal_against += my_match.team_b_score
                if my_match.team_a_score > my_match.team_b_score:
                    match_won += 1
                    points += 3
                elif my_match.team_a_score < my_match.team_b_score:
                    match_lost += 1
                else:
                    match_drawn += 1
                    points += 1

            else:
                goal_for += my_match.team_b_score
                goal_against += my_match.team_a_score
                if my_match.team_b_score > my_match.team_a_score:
                    match_won += 1
                    points += 3
                elif my_match.team_b_score < my_match.team_a_score:
                    match_lost += 1
                else:
                    match_drawn += 1
                    points += 1
        table.append([team.color_name, team.name, match_won, match_drawn, match_lost, goal_for, goal_against, goal_for-goal_against, points])
    if league.open_team_count:
        for p in range(league.open_team_count):
            table.append(['#fff', '<Team Slot Available>', 0, 0, 0, 0, 0, 0, 0])
    return table
    ####### End of get_league_table ######
    

def league_schedule(request, league_id):
    """
    Team    W (won) D (drawn) L (lost)  GF (goal for) GA (goal against) GD (goal diff) P (points)       
    """
    import operator

    league = get_object_or_404(League, pk=league_id)

    rounds = Round.objects.filter(league=league).order_by('order')

    divisions = []

    matches = Match.objects.filter(round__league=league, status=MATCH_STATUS_COMPLETED).order_by('date')
    if league.divisions.count():
        for division in league.divisions.all().order_by('order'):
            teams = Team.objects.filter(league=league, division=division)
            table = get_league_table(teams, matches, league)
            divisions.append({'name': division.name, 'table': table})
        
        # Check for teams without division
        teams_no_div = Team.objects.filter(league=league, division__isnull=True)
        if teams_no_div.exists():
            table = get_league_table(teams_no_div, matches, league)
            divisions.append({'name': 'Unassigned', 'table': table})
    else:
        teams = Team.objects.filter(league=league)
        table = get_league_table(teams, matches, league)
        divisions.append({'name': '', 'table': table})

    leading_scorers = GoalScorer.objects.filter(league=league).order_by('-goals')
    
    # Temporary fix for display parity: Remove Day prefix from name if present
    import re
    # Remove "Tues/Thursday " or generic day prefixes
    clean_name = re.sub(r'^(Mon|Tues|Wed|Thurs|Fri|Sat|Sun)[a-zA-Z/]*\s+', '', league.name)
    league.name = clean_name

    return render(request, 'league/schedule.html', {
        'show_division_title': False, 
        'divisions': divisions,
        'league': league,
        'rounds': rounds,       
        'leading_scorers': leading_scorers
    })


def league_division_schedule(request, league_id, division_id):
    """
    Team    W (won) D (drawn) L (lost)  GF (goal for) GA (goal against) GD (goal diff) P (points)       
    """
    import operator

    league = get_object_or_404(League, pk=league_id)
    division = get_object_or_404(Division, pk=division_id)

    rounds = Round.objects.filter(league=league, division=division).order_by('order')

    matches = Match.objects.filter(round__league=league, status=MATCH_STATUS_COMPLETED).order_by('date')

    teams = Team.objects.filter(league=league, division=division)
    table = get_league_table(teams, matches, league)
    
    divisions = [{'name' : division.name, 'table': table}]
    leading_scorers = GoalScorer.objects.filter(league=league, division=division).order_by('-goals')
    
    return render(request, 'league/schedule.html', {
        'show_division_title': True, 
        'divisions': divisions, 
        'league': league, 
        'rounds': rounds,
        'leading_scorers': leading_scorers
    })


@player_required
def player_join_team(request, uuid):
    import uuid as u
    invitation = u.UUID(uuid)
    player = Player.objects.get(user=request.user)
    try:
        team = Team.objects.get(uuid=invitation)
    except (Team.DoesNotExist, ValueError):
        messages.add_message(request, messages.INFO, "The invitation code used is not valid.")
        return redirect('player')

    try:
        teamplayer = TeamPlayer.objects.get(player=player, team=team)
        msg = "Your invitation to join team %s was already accepted." % team.name
        messages.add_message(request, messages.INFO, msg)
        return redirect('player_teams')
    
    except TeamPlayer.DoesNotExist:
        placeholders = PaymentPlaceholder.objects.filter(player=player, team=team)
        if placeholders:
            return redirect('player_pay', pk=placeholders[0].pk)
        
        if team.payment_type == PAYMENT_TEAM and team.payment_status == PAYMENT_APPROVED:
            teamplayer = TeamPlayer(team=team, player=player)
            teamplayer.payment_status = PAYMENT_APPROVED
            teamplayer.save()
            msg = "Your invitation to join team %s was accepted. Payment was previously made by your team captain." % team.name
            messages.add_message(request, messages.INFO, msg)
            return redirect('player_teams')
        
        else:
            placeholder=PaymentPlaceholder(placeholder_type=PAYMENT_INDIVIDUAL, team=team, league=team.league, cost=team.league.registration_cost, player=player)
            placeholder.save()
            return redirect('player_pay', pk=placeholder.pk)
    

@player_required
def player_schedules(request):
    from dateutil import tz
    
    utc_zone = tz.gettz('UTC')
    est_zone = tz.gettz('America/New_York')
    
    try:
        from urllib.parse import quote
    except ImportError:
        from urllib import quote

    player = Player.objects.get(user=request.user)
    team_ids = TeamPlayer.objects.filter(player=player).values_list('team__id', flat=True)
    my_teams = Team.objects.filter(id__in=team_ids)
    today = datetime.date.today()
    matches_qs = Match.objects.filter(Q(team_a__in=my_teams) | Q(team_b__in=my_teams)).filter(status=MATCH_STATUS_SCHEDULED, date__gte=today).order_by('date')
    
    matches = []
    for r in matches_qs:
        text = quote('%s vs %s' % (r.team_a.name, r.team_b.name))
        #date = '20140127T224000Z/20140320T221500Z'
        
        utc_finish_time = datetime.datetime(r.date.year, r.date.month, r.date.day, r.time.hour, r.time.minute) + datetime.timedelta(minutes=int(r.duration)) 
        utc_finish_time = utc_finish_time.replace(tzinfo=est_zone)
        
        utc_starting_time = datetime.datetime(r.date.year, r.date.month, r.date.day, r.time.hour, r.time.minute)
        utc_starting_time = utc_starting_time.replace(tzinfo=est_zone)

        finish_time = utc_finish_time.astimezone(utc_zone)
        starting_time = utc_starting_time.astimezone(utc_zone)

        date = '%sT%s/%sT%s' % (starting_time.strftime('%Y%m%d'), starting_time.strftime('%H%M00Z'), finish_time.strftime('%Y%m%d'), finish_time.strftime('%H%M00Z'))
        details = quote('League: %s | Location: %s' % (r.round.league.name, r.round.league.location.location if r.round.league.location else "TBD"))
        location = quote(r.round.league.location.address if r.round.league.location else "TBD")
        calendar_link = "https://calendar.google.com/calendar/render?action=TEMPLATE&text=%s&dates=%s&details=%s&location=%s&sf=true&output=xml" % (text, date, details, location)
        if r.round.league.is_league():
            league_url = reverse('league_schedule', args=[r.round.league.id]) if r.round.division is None else reverse('league_division_schedule', args=[r.round.league.id, r.round.division.id])
        else:
            league_url = reverse('league_schedule', args=[r.round.league.id]) 
        matches.append(
            {   
                'league_is_active': r.round.league.is_active(),
                'league_id': r.round.league.id,
                'league_url': league_url,
                'league_name': r.round.league.name,
                'location': r.round.league.location.location if r.round.league.location else "TBD",
                'team_a': r.team_a.name,
                'team_b': r.team_b.name,
                'date': r.date,
                'time': r.time,
                'calendar_link': calendar_link 
            }
        )
    return render(request, 'league/upcoming_matches.html', {'matches': matches})


@player_required
def player_team_pay(request, team_id):
    player = Player.objects.get(user=request.user)
    teamplayer = get_object_or_404(TeamPlayer, player=player, team__pk=team_id)
    team = teamplayer.team
    league = team.league
    
    # generate the form
    PAYMENT_TYPE = (
        (PAYMENT_TEAM, 'Team payment: $ %s' % league.team_cost),
        (PAYMENT_INDIVIDUAL, 'Individual: $ %s' %league.registration_cost),
    )
    
    class TeamCreateForm(forms.Form):
        payment_type = forms.ChoiceField(PAYMENT_TYPE, widget=forms.RadioSelect())
    
    #parse response
    if request.method == 'POST':
        form = TeamCreateForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['payment_type'] == str(PAYMENT_TEAM):
                placeholder = PaymentPlaceholder(placeholder_type=PAYMENT_TEAM_EXISTING_TEAM, player=player, league=league, team=team, cost=league.team_cost)
            else:
                placeholder = PaymentPlaceholder(placeholder_type=PAYMENT_TEAM_EXISTING_INDIVIDUAL, player=player, league=league, team=team, cost=league.registration_cost)

            placeholder.save()
            return redirect('player_pay', pk=placeholder.pk)
        else:
            print(forms.errors)
    else:
        form = TeamCreateForm()

    return render(request, 'league/team_create.html', {'form': form})

@csrf_exempt
def send_email(request):
    from django.core.mail import EmailMessage

    to_email = settings.DEFAULT_EMAIL
    message = request.POST.get('message', 'no-message')
    from_email = request.POST.get('email', 'unknown@email.com')
    
    email = EmailMessage(
        '[NYCS SITE] New Contact',
        message,
        from_email,
        [to_email],
        [],
        reply_to=[from_email],
        headers=None,
    )
    email.send(fail_silently=False)
    return HttpResponse()


def send_custom_email(request):
    from django.contrib.contenttypes.models import ContentType
    from .forms import EmailForm
    import time

    def parse_emails(ctid, ids):
        emails = []
        ct = ContentType.objects.get(pk=ctid)
        
        obj_list = ct.model_class().objects.filter(id__in=ids)
        
        if ct.model == 'teamplayer':
            emails = obj_list.values_list('player__user__email', flat=True)
        
        if ct.model == 'user':
            emails = obj_list.values_list('email', flat=True)

        if ct.model == 'team':
            for team in obj_list.all():
                emails = emails + list(TeamPlayer.objects.filter(team=team).values_list('player__user__email', flat=True))

        if ct.model == 'player':
            emails = obj_list.values_list('user__email', flat=True)

        if ct.model == 'match':
            for match in obj_list.all():
                emails = emails + list(TeamPlayer.objects.filter(team=match.team_a).values_list('player__user__email', flat=True))
                emails = emails + list(TeamPlayer.objects.filter(team=match.team_b).values_list('player__user__email', flat=True))

        return emails

        
    if request.method == 'GET':
        ctid = request.GET['ct']
        ids = request.GET['ids']
        nids = base64.b64decode(bytes(ids.encode('ascii'))).decode('ascii')
        nids = list(map(lambda x: int(x), nids.split(',')))
        emails = parse_emails(ctid, nids)
    
        form = EmailForm(initial={'to_emails': ", ".join(emails) }) 
        return render(request, 'admin/custom_email.html', {'form': form, 'total_emails': len(nids),'ct': ctid, 'ids': request.GET['ids']})
    
    else:
        ctid = request.POST['ct']
        ids = request.POST['ids']
        nids = base64.b64decode(bytes(ids.encode('ascii'))).decode('ascii')
        nids = list(map(lambda x: int(x), nids.split(',')))
        emails = parse_emails(ctid, nids)
    
        message = request.POST['message']
        subject = request.POST['subject']
        bcc = True if request.POST.get('bcc', None) else False 
        attachment = request.FILES.get('attachment', None)
    
        l = len(emails)
        rounds = (l // 90) + 1
        for r in range(rounds):
            s = r*90
            e = r*90+90
            send_sendinblue_email(subject, message, emails[s:e], bcc, attachment)
            time.sleep(2)

        return redirect('/admin')

    return HttpResponse()


def send_sendinblue_email(subject, message, to_emails=[], bcc=False, attachment=None):
    import base64
    from django.conf import settings
    from utils.sendinblue import Mailin

    print('#### Subject', subject)
    print('#### Amount', len(to_emails))
    print('#### Emails', to_emails)
    
    m = Mailin("https://api.sendinblue.com/v2.0", settings.SENDINBLUE_API_KEY)
    dict_emails = {}
    for email in to_emails:
        dict_emails[email] = ''

    data ={
            "from" : [settings.DEFAULT_EMAIL, "NY Coed Soccer"],
            "subject" : subject,
            "html" : message
    }
    if bcc:
        data.update({
            "to" : {settings.DEFAULT_EMAIL: "NY Coed Soccer"},
            "bcc": dict_emails,
        })
    else:
        data.update({
            "to" : dict_emails,
            "replyto" : [settings.DEFAULT_EMAIL, "NY Coed Soccer"],
        })

    print('#### row data ####', data)
    if attachment:
        b64 = base64.b64encode(attachment.file.read())
        data['attachment'] = {attachment.name : b64.decode('utf-8')}

    result = m.send_email(data)
    print(result)
    return

def send_mailgun_email(subject, message, to_emails=[]):
    from django.conf import settings
    import requests

    html_message = message
    return requests.post(
        "https://api.mailgun.net/v3/%s/messages" % settings.DOMAIN_NAME,
        auth=("api", settings.MAILGUN_API_KEY),
        #files=[("attachment", ("test.jpg", open("files/test.jpg","rb").read())),
        #("attachment", ("test.txt", open("files/test.txt","rb").read()))],
        data={
            "from": settings.DEFAULT_EMAIL,
            "to": to_emails,
            "subject": subject,
            "text": message,
            "html": html_message,
            "recipient-variables": (
                '{"bob@example.com": {"first":"Bob", "id":1}, '
                '"alice@example.com": {"first":"Alice", "id": 2}}'
            )
        }
    )

#####################################################################################
#
#------- Legacy Code
#
#####################################################################################


def roster(request): 
    return render(request, 'roster.html', {'players': Player.objects.all()})


def player_team_summary(request, team):
    player = Player.objects.get(user=request.user)
    my_team = Team.objects.get(pk=team)
    my_league = my_team.league
    is_on_team = TeamPlayer.objects.filter(player=player,team=my_team)
    captain_tps = TeamPlayer.objects.filter(team=my_team, is_captain=True)
    captains = map(lambda tp: tp.player, captain_tps)
    return render(request, 'league/team_summary.html', 
        extra_context={'league': my_league, 'team': my_team,'is_on_team': is_on_team, 'captains': captains})


#
# more hackery
#

@user_passes_test(lambda u: u.is_staff)
def all_teams(request):
    if 'league' in request.GET:
        teams = Team.objects.filter(league__pk = request.GET['league']).order_by('-league__season__start_date', 'name')
    else:
        teams = Team.objects.all().order_by('-league__season__start_date', 'name')
    
    out = [{'pk' : team.pk, 'name' : str(team)} for team in teams]
    
    return HttpResponse(json.dumps(out))

def crunch_params(request):
    #poached from the admin
    params = dict(request.GET.items())
    from django.contrib.admin.views.main import PAGE_VAR, TO_FIELD_VAR, ERROR_FLAG, ALL_VAR, ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR, IS_POPUP_VAR
    for i in (PAGE_VAR, TO_FIELD_VAR, ERROR_FLAG, ALL_VAR, ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR, IS_POPUP_VAR):
        if i in params:
            del params[i]
    
    for key, value in params.items():
        if not isinstance(key, str):
            # 'key' will be used as a keyword argument later, so Python
            # requires it to be a string.
            del params[key]
            params[smart_str(key)] = value

        # if key ends with __in, split parameter into separate values
        if key.endswith('__in'):
            params[key] = value.split(',')
    
    return params

@user_passes_test(lambda u: u.is_staff)
def team_player_emails(request):
    params = crunch_params(request)
    
    emails = []
    for tp in TeamPlayer.objects.filter(**params).select_related().order_by('player__last_name', 'player__first_name'):
        emails.append((tp.player.full_name(), tp.player.user.email))
    emails = list(set(emails))
    return HttpResponse(json.dumps(emails))
    
@user_passes_test(lambda u: u.is_staff)
def player_emails(request):
    params = crunch_params(request)
    
    emails = []
    for player in Player.objects.annotate(num_tps=Count('teamplayer')).filter(**params).order_by('last_name', 'first_name'):
        emails.append((player.full_name(), player.user.email))
    emails = list(set(emails))
    return HttpResponse(json.dumps(emails))
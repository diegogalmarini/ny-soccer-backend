from datetime import date

#from multiselectfield.admin import msf_filter

from django import forms
from django.db.models import Count
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.core.urlresolvers import reverse
from django.forms import fields, widgets, forms
from league.forms import TeamForm, PlayerAdminForm
from django.forms.fields import RegexField
from django.utils.dates import WEEKDAYS
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from league.models import *
from league.widgets import MonthYearWidget
from django.http import HttpResponseRedirect

from tinymce.widgets import TinyMCE

from import_export import resources
from import_export.admin import ImportExportModelAdmin, ImportMixin, ExportMixin


#***************************************
# Custom Filters
#

class ActiveLeaguesFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Active Leagues')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'league'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        from .models import STATUS_ACTIVE
        leagues = League.objects.filter(status=STATUS_ACTIVE)
        return map(lambda x: (x.pk, x.name), leagues)

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value():
            return queryset.filter(round__league__pk=self.value())

class SeasonYearListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Year')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'decade'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        import datetime
        years = []
        for y in range(2004, datetime.date.today().year + 2):
            years.append((y, y))
        return years

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value():
            return queryset.filter(season__start_date__year=self.value())

class PlayerRegisteredListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Is Registered?')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'registered'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return [(True, True),(False, False)]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either 'True' or 'False')
        # to decide how to filter the queryset.
        if self.value() is not None:
            b = not(self.value() == 'True')
            return queryset.filter(teamplayer__isnull=b)


class DayOfWeekFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('day of week')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'day'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return WEEKDAYS.items()

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value():
            if queryset.model == TeamPlayer:
                return queryset.filter(league__day_of_week__contains=self.value())
            elif queryset.model == League:
                return queryset.filter(day_of_week__contains=self.value())

#***************************************
# Import/Export Resource
#
#

class RosterResource(resources.ModelResource):

    class Meta:
        model = TeamPlayer
        fields = ('league__name', 'team__name', 'player__first_name', \
                'player__last_name', 'player__user__email', 'player__contact_phone', )
        #export_order = ('id', 'price', 'author', 'name')

#
# End Import/Export Resource
#***************************************


admin.site.site_header = 'NY Coed Soccer Administration'
admin.site.site_url = '/player/'


class ExternalLeagueAdmin(admin.ModelAdmin):
    list_display=('name', 'season', 'day_of_week', 'location')

class LegacyLeagueAdmin(admin.ModelAdmin):
    list_display=('name', 'season', 'day_of_week', 'location')


class RoundAdmin(admin.ModelAdmin):
    list_filter = ['league', 'date']
    list_display = ('name', 'league', 'division_name', 'order', 'short_description', 'matches')
    ordering = ['league', 'order']
    date_hierarchy = 'date'

    def division_name(self, obj):
        if obj.division:
            return obj.division.name
        return '--'

    def matches(self, obj):
        return mark_safe("<a href='http://%s/admin/league/match/?round=%s'>Go To Matches</a>" % (settings.SERVER_URL, obj.pk))
    matches.short_description = 'Actions'

admin.site.register(LegacyLeague, LegacyLeagueAdmin)
admin.site.register(ExternalLeague, ExternalLeagueAdmin)
admin.site.register(Round, RoundAdmin)
admin.site.register(Venue)
admin.site.register(WebsiteIncludeText)


class MatchAdmin(ImportMixin, admin.ModelAdmin):
    list_display = ('round', 'date', 'team_a', 'team_a_score', 'team_b_score', 'team_b', 'status')
    list_filter = [ActiveLeaguesFilter, 'date', 'time']
    ordering = ('date',)
    date_hierarchy = 'date'
    raw_id_fields = ('team_a', 'team_b')
    actions = ['set_draft', 'set_scheduled', 'set_canceled', 'set_completed']

    def set_scheduled(self, request, queryset):
        queryset.update(status=MATCH_STATUS_SCHEDULED)
    set_scheduled.short_description = "Mark selected Matches as Scheduled"

    def set_draft(self, request, queryset):
        queryset.update(status=MATCH_STATUS_DRAFT)
    set_draft.short_description = "Mark selected Matches as Draft"

    def set_completed(self, request, queryset):
        queryset.update(status=MATCH_STATUS_COMPLETED)
    set_completed.short_description = "Mark selected Matches as Completed"

    def set_canceled(self, request, queryset):
        queryset.update(status=MATCH_STATUS_CANCELED)
    set_canceled.short_description = "Mark selected Matches as Canceled"

admin.site.register(Match, MatchAdmin)


class TinyMCEFlatPageAdmin(FlatPageAdmin):
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'content':
            return db_field.formfield(widget=TinyMCE(
                attrs={'cols': 60, 'rows': 20},
                mce_attrs={'external_link_list_url': reverse('tinymce-linklist')},
            ))
        return super(TinyMCEFlatPageAdmin, self).formfield_for_dbfield(db_field, **kwargs)

admin.site.unregister(FlatPage)
admin.site.register(FlatPage, TinyMCEFlatPageAdmin)


class SeasonAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date')
    list_filter = ['start_date']
    ordering = ('start_date',)
    # formfield_overrides = {
    # 	models.DateField: {'widget': MonthYearWidget},
    # }


admin.site.register(Season, SeasonAdmin)

class GoalScorerInline(admin.TabularInline):
    model = GoalScorer
    #exclude = ('league',)
    raw_id_fields = ("player",)

    # def get_queryset(self, request):
    #     qs = super(GoalScorerInline, self).get_queryset(request)
    #     return qs.filter(league=request.league)

class LeagueAdmin(admin.ModelAdmin):
    list_display = ('order', 'name', 'season', 'days_of_week', 'league_type', 'competition_type', 'featured_at_homepage', 'status', 'custom_actions')
    list_display_links = ('name',)
    list_filter = ('season', DayOfWeekFilter, 'league_type', 'competition_type', SeasonYearListFilter,)
    #date_hierarchy = 'season__start_date'
    inlines = [GoalScorerInline]
    fieldsets = [
        (None, {'fields':['season','name', 'paypal_account', 'featured_at_homepage', 'day_of_week', 'league_type', 'competition_type', 'status', 'order', 'location']}),
        ('Cost information',
        {
            'fields':['registration_cost', 'team_cost'],
        }),
        ('League Logistics', 
        {
            'fields':['league_description', 'registration_deadline', 'game_location', 'game_time', 'game_duration'],
        }),
        ('League Slots', 
        {
            'fields':['open_team_count', 'open_female_slot', 'open_male_slot'],
        }),
        ('Team Size', 
        {
            'fields':['num_players_on_field', 'minimum_roster_size', 'minimum_num_women_on_field'],
        }),
    ]

    def days_of_week(self, obj):
        return obj.get_day_of_week_display()

    def custom_actions(self, obj):
        li1 = "<li><a href='%s'>Clone</a></li>" % (reverse('league_clone', args=[obj.pk]))
        li2 = "<li><a href='%s'>Create Premiership</a></li>" % (reverse('league_create_premiership', args=[obj.pk]))
        return mark_safe("<ul>%s %s</ul>" % (li1, li2))
    custom_actions.short_description = 'Actions'

    def fixture(self, obj):
        return mark_safe("<a href='%s'>Auto Create</a>" % (reverse('league_auto_fixture', args=[obj.pk])))
    fixture.short_description = 'Fixture'
    
        
admin.site.register(League,LeagueAdmin)

class DivisionAdmin(admin.ModelAdmin):
    list_display=('name','league','season', 'order')
    list_filter=['league']
    ordering=('-league__season__start_date','league__name','name') 
    fieldsets=[
        (None,{'fields':['league','name','order']}),
    ]
    search_fields=['name','league__name']

admin.site.register(Division,DivisionAdmin) 


class TeamPlayerAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = RosterResource
    list_display=('__str__', 'player_name','gender','team_name','is_captain','league','season')
    list_display_links = ('__str__',)
    list_filter=['league__season', 'league__league_type', DayOfWeekFilter, 'league__location', 'is_captain', 'player__gender']
    ordering=('player__last_name', 'player__first_name') 
    search_fields=['team__name','player__first_name','player__last_name']
    actions = ['export_emails']

    def export_emails(self, request, queryset):
        emails = list(map(lambda x: "%s <%s>" % (x.player.full_name(), x.player.user.email), queryset.all()))
        self.message_user(request, "%s" % ', '.join(emails))

    class Media:
        js = ("jquery.js", "jquery-ui.js", "js/admin/filter-colapse.js")
        css = {
            "all": ("ui-lightness/jquery-ui-1.8rc3.custom.css",)
        }
    
    def save_model(self, request, obj, form, change):
        if change:
            orig_obj = TeamPlayer.objects.get(pk=obj.id)
            if orig_obj.team != obj.team and obj.team is not None:
                #they've changed the team
                pronouns = {'M':'him', 'F':'her'}
                possessives = {'M':'his', 'F':'her'}
                subjects = {'M':'he', 'F':'she'}
                request.user.message_set.create(message=("%s's team has been changed.  You can contact %s via email at %s to inform %s that %s that he has been assigned to the team \"%s\" on the league \"%s\"." % (obj.player.full_name(), pronouns[obj.player.gender], obj.player.email(), pronouns[obj.player.gender], subjects[obj.player.gender], obj.team.name, obj.team.league.name)))
        obj.save()
    
admin.site.register(TeamPlayer,TeamPlayerAdmin)



class TeamPlayerInline(admin.TabularInline):
    model = TeamPlayer
    exclude = ('payment_transaction', 'payment_notes')
    raw_id_fields = ("team", "league", )

    def __init__(self, parent_model, admin_site):
        super(TeamPlayerInline, self).__init__(parent_model, admin_site)
        if parent_model == Team:
            self.verbose_name = 'player'
            self.verbose_name_plural = 'players'
            self.exclude = ('payment_transaction', 'payment_notes', 'league')
        else:
            self.verbose_name = 'team'
            self.verbose_name_plural = 'teams'


class TeamAdmin(admin.ModelAdmin):
    form=TeamForm
    list_display=('name', 'season_name', 'league','division_name','gender_information')
    list_filter=['league__season', 'division']
    search_fields=['name']
    inlines = [TeamPlayerInline]
    fieldsets = [
        ('Basic Information', {'fields' : ['league', 'name', 'historical_team']}),
        ('Admin Information', {'fields' : ['color_name', 'administrator_notes', 'division']}),
        ('Payment Information', {'fields' : ['payment_type', 'payment_status', 'override_payment', 'payment_notes']}),
    ]
    ordering=('name',)

    def season_name(self, obj):
        return obj.league.season
    season_name.short_description = 'Season'
    season_name.admin_order_field = 'league__season'


    def division_name(self, obj):
        if obj.division:
            return obj.division.name
        return '--'
        
admin.site.register(Team, TeamAdmin)

class USZipCodeField(RegexField):
    default_error_messages = {
        'invalid': 'Enter a zip code in the format XXXXX or XXXXX-XXXX.',
    }
    
    def __init__(self, *args, **kwargs):
        super(USZipCodeField, self).__init__(r'^\s*\d{5}(?:-\d{4})?\s*$',
            max_length=None, min_length=None, *args, **kwargs)


class PlayerAdmin(admin.ModelAdmin):
#	form = PlayerAdminForm
    inlines = [TeamPlayerInline]
    list_display = ('last_name','first_name','email','gender','experience_level')
    search_fields=['last_name','first_name', 'user__email']
    list_filter = ('experience_level', 'gender', PlayerRegisteredListFilter, )
    
    def queryset(self, request):
        return super(PlayerAdmin, self).queryset(request).annotate(num_tps=Count('teamplayer'))
    
    class Media:
        js = (
            "jquery.js", 
            "jquery-ui.js", 
            "js/admin/export-trainer.js"
        )
        css = {
            "all": ("ui-lightness/jquery-ui-1.8rc3.custom.css",)
        }
admin.site.register(Player, PlayerAdmin)
admin.site.register(PayPalAccount)

def send_custom_email(modeladmin, request, queryset):
    import base64
    ct = ContentType.objects.get_for_model(queryset.model)
    ids = list(queryset.values_list('id', flat=True))
    selected = base64.b64encode(bytes(','.join(str(i) for i in ids).encode('ascii')))
    return HttpResponseRedirect("/custom-email/?ct=%s&ids=%s" % (ct.pk, selected.decode("ascii") ))

admin.site.add_action(send_custom_email, "Send Custom Email")
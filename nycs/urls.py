"""nycs URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
#from league.admin import admin_site
from league import views as league_views


urlpatterns = [
    url(r'^$', league_views.welcome, name='home'),
    
    #url(r'^404/$', TemplateView.as_view(template_name='404.html'), name='404'),
    #url(r'^admin/mens/', league_views.mens_admin),
    url(r'^admin/process_matches_import/', league_views.process_matches_import, name='process_matches_import'),
    url(r'^admin/', admin.site.urls),
    url(r'^impersonate/', include('impersonate.urls')),
    url(r'^terms/$', league_views.terms, name="terms"),
    url(r'^custom-email/$', league_views.send_custom_email, name="custom-email"),
    
    # league schedule
    url(r'^league/(?P<league_id>\d+)/schedule/$', league_views.league_schedule, name="league_schedule"),
    url(r'^league/(?P<league_id>\d+)/division/(?P<division_id>\d+)/schedule/$', league_views.league_division_schedule, name="league_division_schedule"),
    url(r'^league/(?P<league_id>\d+)/clone/$', league_views.league_clone, name="league_clone"),
    url(r'^league/(?P<league_id>\d+)/clone-premiership/$', league_views.league_create_premiership, name="league_create_premiership"),
    url(r'^league/(?P<league_id>\d+)/fixture/$', league_views.league_fixture, name="league_auto_fixture"),
    
    url(r'^player/$', league_views.player_dashboard, name='player'),
    url(r'^player/info/$', league_views.player_profile, name='player_profile'),
    url(r'^player/teams/$', league_views.player_teams, name='player_teams'),
    url(r'^player/teams/(?P<team_id>\d+)/pay/$', league_views.player_team_pay, name='player_team_pay'),
    url(r'^player/teams/(?P<team_id>\d+)/$', league_views.player_team_info, name='player_team_info'),
    url(r'^player/export/$', league_views.export_players_csv, name='export_players_csv'),
    
    url(r'^invitation/(?P<uuid>[0-9a-f-]+)', league_views.player_join_team, name='player_join_team'),
    url(r'^player/schedules/$', league_views.player_schedules, name="player_schedules"),
    
    url(r'^player/pay/(?P<pk>\d+)/cancel$', league_views.player_payment_cancel, name="player_payment_cancel"),
    url(r'^player/pay/(?P<pk>\d+)', league_views.player_pay, name='player_pay'),
    # join the league as free agent
    url(r'^player/league/(?P<league_id>\d+)/reserve/$', league_views.reserve_league, name="player_reserve_league"),
    # create a new team
    url(r'^player/league/(?P<league_id>\d+)/create/$', league_views.create_team, name="player_create_team"),
    url(r'^player/league/(?P<league_id>\d+)/', league_views.join_league, name="player_join_league"),


    url(r'^league/(?P<slug>[-\w]+)/$', league_views.legacy_schedule, name='legacy_schedule'),
    url(r'^send-email/$', league_views.send_email, name='send_email'),
    url(r'^rules/$', TemplateView.as_view(template_name="rules.html"), name='rules'),

]

urlpatterns += [
    url(r'^payment/.*', include('paypal.standard.ipn.urls')),
]

urlpatterns += [
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout, name='logout'),
    url(r'^register/$', league_views.register, name='signup'),
    url(r'^password_change/$', auth_views.password_change, name='password_change'),
    url(r'^password_change/done/$', auth_views.password_change_done, name='password_change_done'),
    url(r'^password_reset/$', auth_views.password_reset, name='password_reset'),
    url(r'^password_reset/done/$', auth_views.password_reset_done, name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', auth_views.password_reset_confirm, name='password_reset_confirm'),
    url(r'^reset/done/$', auth_views.password_reset_complete, name='password_reset_complete')
]

urlpatterns += [
    url(r'^pages/', include('django.contrib.flatpages.urls')),
    url(r'^tinymce/', include('tinymce.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
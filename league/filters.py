import django_filters

from .models import Player, TeamPlayer

class TeamRosterFilter(django_filters.FilterSet):
    team__name = django_filters.CharFilter(lookup_expr='icontains')
    player__user__email = django_filters.CharFilter(lookup_expr='icontains')
    #league__name = django_filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = TeamPlayer
        fields = ('league__season', 'league__day_of_week', 'league__location', 'is_captain',)
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nycs.settings')
django.setup()

from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site

# FAQ content from SQL dump
faq_content = """
<p>Below is a general FAQ. It isn't exhaustive, so if you have any questions feel free to send us an <a href="http://www.nycoedsoccer.com/#contact">email</a>.</p>
<div class="panel-group" id="accordion">
  <div class="panel panel-default">
    <div class="panel-heading">
      <h4 class="panel-title"> <a data-toggle="collapse" data-parent="#accordion" href="#collapseOne">What should I bring to the game?</a> </h4>
    </div>
    <div id="collapseOne" class="panel-collapse collapse in">
      <div class="panel-body">Your shirt, shinguards and a lot of energy! Different venues have different requirements for footwear, so be sure to check our <a href="http://www.nycoedsoccer.com/registration/">Venues</a> page before heading to the field. </div>
    </div>
  </div>
  <div class="panel panel-default">
    <div class="panel-heading">
      <h4 class="panel-title"> <a data-toggle="collapse" data-parent="#accordion" href="#collapseTwo">Do I need to check in?</a> </h4>
    </div>
    <div id="collapseTwo" class="panel-collapse collapse">
      <div class="panel-body">No. Show up, find your captain, and get ready to play. </div>
    </div>
  </div>
  <div class="panel panel-default">
    <div class="panel-heading">
      <h4 class="panel-title"> <a data-toggle="collapse" data-parent="#accordion" href="#collapseThree">How many players on the field?</a> </h4>
    </div>
    <div id="collapseThree" class="panel-collapse collapse">
      <div class="panel-body">Most of our coed leagues follow a 5v5 or 6v6 format, but check your individual league for specifics on roster size and gender ratios. </div>
    </div>
  </div>
  <div class="panel panel-default">
    <div class="panel-heading">
      <h4 class="panel-title"> <a data-toggle="collapse" data-parent="#accordion" href="#collapseTwelve">How do I find out if a game is canceled?</a> </h4>
    </div>
    <div id="collapseTwelve" class="panel-collapse collapse">
      <div class="panel-body">Cancellations are rare, but in the case of severe weather, we will notify captains and post updates on our website at least two hours before kickoff. </div>
    </div>
  </div>
</div>
"""

# Create the FAQ page if it doesn't exist
site = Site.objects.get_current()
page, created = FlatPage.objects.get_or_create(
    url='/faq/',
    defaults={
        'title': 'FAQ',
        'content': faq_content,
        'template_name': 'faq.html' # Assuming a simple template or use default
    }
)

if not created:
    page.content = faq_content
    page.save()

page.sites.add(site)
print(f"FAQ page {'created' if created else 'updated'} on site {site.domain}")

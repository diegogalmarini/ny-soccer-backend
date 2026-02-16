import sqlite3

# FAQ content
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

conn = sqlite3.connect('nycoedsoccer.db')
cursor = conn.cursor()

# Ensure Site 4 exists
cursor.execute("INSERT OR IGNORE INTO django_site (id, domain, name) VALUES (?, ?, ?)",
               (4, 'nycoedsoccer.com', 'nycoedsoccer.com'))

# Insert FlatPage
# (url, title, content, enable_comments, template_name, registration_required)
cursor.execute("INSERT OR REPLACE INTO django_flatpage (id, url, title, content, enable_comments, template_name, registration_required) VALUES (?, ?, ?, ?, ?, ?, ?)",
               (1, '/faq/', 'FAQ', faq_content, 0, 'flatpages/faq.html', 0))

# Link to Site 4
cursor.execute("INSERT OR IGNORE INTO django_flatpage_sites (flatpage_id, site_id) VALUES (?, ?)", (1, 4))

conn.commit()
print("FAQ restored successfully via raw SQL.")
conn.close()

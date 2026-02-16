import sqlite3

# Original content extracted from nycoedsoccer.com
tournaments_html = """<p>The <strong>CHAMPIONS CUP</strong> is our annual all-day Summer Tournament that originated in 2009. The competition is held each July and provides an opportunity for teams across the NY Coed Leagues and beyond to come together to compete for the one trophy.</p>
<p>&nbsp;</p>
<p><strong>The Champions Cup: Indoor Edition</strong> was first held in 2013 is played in March of each year.</p>
<p>&nbsp;</p>
<p><strong>Summer 2025 tournament happened on July 26th in Chelsea. We'll see you in 2026!<br></strong></p>
<p>&nbsp;</p>
<p>NY Coed Soccer is a main sponsor of the <a href="https://www.facebook.com/LuisRojasFoundation/">Luis Rojas Foundation</a>, a not-for-profit organization whose aim is to promote a healthy lifestyle for underprivileged children through soccer in New York City.</p>
<p>&nbsp;</p>
<p>The Luis Rojas Cup is hosted each June.</p>"""

about_html = """<p><strong>NY Coed Soccer</strong> was established in November 2004.</p>
<p>&nbsp;</p>
<p>From our debut season on a Friday evening in Chelsea we've become one of the city's premier recreational leagues. We offer divisions for those just discovering their love of the game and opportunities for those with more experience of soccer.</p>
<p>&nbsp;</p>
<p><strong>NY Coed</strong> provides a welcoming environment for you to develop and hone your skills, exercise and meet new people. We play all-year round in various Indoor and Outdoor locations in New York City. While we're primarily Coed, we also offer limited Men's Divisions.</p>
<p>&nbsp;</p>
<p>In Summer 2019, we began <a style="font-weight: 600;" href="/NYCoedKids/">NY Coed Kids</a>.</p>
<p>&nbsp;</p>
<p>We are a main sponsor of the <a style="font-weight: 600;" href="https://www.facebook.com/LuisRojasFoundation/">Luis Rojas Foundation</a>, a not-for-profit organization whose aim is to promote a healthy lifestyle for underprivileged children through soccer in New York City, as well as <a style="font-weight: 600;" href="https://www.facebook.com/BarnstonworthRoversFC/photos/a.361616287222852.95007.168213139896502/1325523060832165/?type=3&amp;theater">Barnstonworth Rovers Old Boys</a>, an amateur team in the Cosmopolitan League.</p>"""

registration_html = """<p>Registration is currently open for our upcoming seasons.</p>"""

conn = sqlite3.connect('nycoedsoccer.db')
cursor = conn.cursor()

# Insert or update content
contents = [
    ('Tournaments', tournaments_html),
    ('About', about_html),
    ('Registration', registration_html)
]

for name, text in contents:
    cursor.execute("INSERT OR REPLACE INTO league_websiteincludetext (name, text) VALUES (?, ?)", (name, text))

conn.commit()
conn.close()
print("Website content restored successfully.")

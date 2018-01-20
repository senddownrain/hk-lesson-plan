import requests
from icalendar import Calendar, Event
import re
import dateutil.parser

import sys


def repl(regex, repl, text, count=0):
	return re.sub(regex, repl, text, count, flags= re.DOTALL | re.UNICODE)

print('connecting to db.hochschule-heiligenkreuz.at')

r = requests.get('https://db.hochschule-heiligenkreuz.at/index.php')
cookie = r.headers['Set-Cookie'].split("=")[1].split(";")[0]



username = ''
password = ''
target_directory = '~/Dropbox/calendars'
dropbox_start_command = "open /Applications/Dropbox.app"
dropbox_kill_command = "killall Dropbox"

#	for exams, my ID
#	https://dl.dropboxusercontent.com/s/i93g3ilplr2k4yp/exams.ics
me = 392


users = [

	#	Katja...
	
	#	Ivan
	#	https://dl.dropboxusercontent.com/s/xi2jya1gpcj47no/435.ics
	435,

	#	Franz Linzmeier
	#	https://dl.dropboxusercontent.com/s/x6j8hswtfbg4pgy/518.ics
	518,
	
	#	Simon Karl
	#	https://dl.dropboxusercontent.com/s/xht7vsmfvbpfuak/524.ics
	524,
	
	#	Br. Nickel
	#	https://dl.dropboxusercontent.com/s/a1chnpwtprjfxru/210.ics
	210,

	#	P. Matthäus Hasslinger
	#	https://dl.dropboxusercontent.com/s/ustl5vle20k02ts/133.ics
	133,

	#	Hector de A. Brunete
	#	https://dl.dropboxusercontent.com/s/6x8tv1quio4rat1/438.ics
	438,

	#	Andreas Metzger
	#	https://dl.dropboxusercontent.com/s/gsnk8a9k191min2/324.ics
	324,

	#	Fr. Jacobus
	#	https://dl.dropboxusercontent.com/s/oa5z8c1r5hyyh56/328.ics
	328,

	#	Patrick Krizmanic
	#	https://dl.dropboxusercontent.com/s/u2mvnph0626zpty/320.ics
	320,

	#	Thomas Ban
	#	https://dl.dropboxusercontent.com/s/7kvtyibnlom61un/304.ics
	304,

	#	Женя (Eugen)
	#	https://dl.dropboxusercontent.com/s/2crgoikv2v45vmk/392.ics
	392,

	#	bruder benedikt
	#	https://dl.dropboxusercontent.com/s/owwm5lqrhcm985w/505.ics
	505,

	#	leo skorczyk
	#	https://dl.dropboxusercontent.com/s/iixtvjlx2x2byk8/342.ics
	342,

	#	andreas neubauer
	#	https://dl.dropboxusercontent.com/s/8a5wy76b4mj9kv1/459.ics
	459, 

	#	vladi
	#	https://dl.dropboxusercontent.com/s/aezoeqxox76i3uv/512.ics
	512,

	#	me
	#	https://dl.dropboxusercontent.com/s/mmcisfajz2ac5rc/467.ics
	467
]


print('cookie: ' + cookie)

if len(sys.argv) > 1:
	try:
	    value = int(sys.argv[1])
	    users = [value]
	except ValueError:
	    if sys.argv[1] == 'me':
	    	users = [me]



print("logging in...")
headers = {
	"Cookie": 'PHPSESSID=' + cookie
}
data = {
	'username': username,
	'password': password,
	'stay': 'false',
	'login': '1'
}
r = requests.post('https://db.hochschule-heiligenkreuz.at/index.php?module=main&view=login', headers = headers, data = data)

r.raise_for_status()
print("success.")


print('getting request token and sid...')
r = requests.get('https://db.hochschule-heiligenkreuz.at/index.php?module=calendar&view=viewtimeline', headers = headers)
r.raise_for_status()

pattern = re.compile('var token = "([^\"]+)"', re.DOTALL | re.MULTILINE)

token = None
for match in re.finditer(pattern, r.text):
	token = match.group(1)
	print('token: ' + token)
	break
else:
	print(r.text)
	print('error: token not found. quitting...')
	quit()

pattern = re.compile('sid=(\w+)')

sid = None
for match in re.finditer(pattern, r.text):
	sid = match.group(1)
	print('sid: ' + sid)
	break
else:
	print(r.text)
	print('error: sid not found. quitting...')
	quit()

print('requesting calendar events...')

from datetime import datetime, timedelta


import time

exams = Calendar()
exams.add('prodid', '-//My calendar product//mxm.dk//')
exams.add('version', '2.0')

write_exams = len(sys.argv) > 1 and sys.argv[1] == 'exams'

uid = 1
for user in users:

	if write_exams and user != me:
		continue

	cal = Calendar()
	cal.add('prodid', '-//My calendar product//mxm.dk//')
	cal.add('version', '2.0')

	dt = datetime.now()
	start = dt - timedelta(days=dt.weekday() + 1)

	end = start + timedelta(days=150)
	cur = start

	print('requesting calendar events for: ' + str(user))

	while True and cur < end:
		
		print('.', end = '', flush = True)

		first_day = cur.date()
		#print("requesting week from: " + str(first_day))
		cur = cur + timedelta(days=7)



		params = {
			'token': token, 'iduser': user, 'sid': sid, 'firstday': str(first_day)
		}
		#print(params)

		r = requests.get('https://db.hochschule-heiligenkreuz.at/modules/calendar/gettimeline.php', params = params, headers = headers)
		#print(r.url)
		r.raise_for_status()

		#print(r.headers)


		#print('parsing events...')
		#print(r.text)


		result = r.json()
		token = result['token']

		for event in result['data']:
			if event['status'] == 'ACTIVE':
				dtstart = dateutil.parser.parse(event['start'])
				delta = timedelta(hours=1)
				if time.localtime((dtstart - datetime(1970,1,1)).total_seconds()).tm_isdst:
					delta = timedelta(hours=2)
				tgt = Event()
				uid += 1
				tgt.add('uid', 'myuid' + str(uid))
				if write_exams and event['title'].endswith('(Prüfung)'):
					tgt.add('summary', repl('^[^:]+:\s*', '', repl('\(Prüfung\)$', '', event['title'], 1), 1))
					print("exam detected")
					exams.add_component(tgt)
				else:
					tgt.add('summary', event['title'])
				tgt.add('dtstart', dateutil.parser.parse(event['start'] + 'UTC') - delta)
				tgt.add('dtend', dateutil.parser.parse(event['end'] + 'UTC') - delta)
				cal.add_component(tgt)
		#time.sleep(1)

	from os.path import expanduser

	if not write_exams:
		print()
		print('writing your calendar to: ' + expanduser(target_directory + '/' + str(user) + '.ics'))


		with open(expanduser(target_directory + '/' + str(user) + '.ics'), 'wb') as target:
			target.write(cal.to_ical())

if write_exams:
	print()
	print('writing exam list to: ' + expanduser(target_directory + '/exams.ics'))
	with open(expanduser(target_directory + '/exams.ics'), 'wb') as target:
		target.write(exams.to_ical())

from subprocess import call

call(dropbox_start_command, shell=True)

time.sleep(21)

call(dropbox_kill_command, shell=True)
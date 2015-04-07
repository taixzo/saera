#! /usr/bin/env python

from datetime import datetime, timedelta
from pyparsing import *
import calendar
 
# string conversion parse actions
def convertToTimedelta(toks):
	unit = toks.timeunit.lower().rstrip("s")
	td = {
		'week'    : timedelta(7),
		'day'    : timedelta(1),
		'hour'   : timedelta(0,0,0,0,0,1),
		'minute' : timedelta(0,0,0,0,1),
		'second' : timedelta(0,1),
		}[unit]
	if toks.qty:
		td *= int(toks.qty)
	if toks.dir:
		td *= toks.dir
	toks["timeOffset"] = td
 
def convertToDay(toks):
	now = datetime.now()
	if "wkdayRef" in toks:
		todaynum = now.weekday()
		daynames = [n.lower() for n in calendar.day_name]
		nameddaynum = daynames.index(toks.wkdayRef.day.lower())
		if toks.wkdayRef.dir > 0:
			daydiff = (nameddaynum + 7 - todaynum) % 7
		else:
			daydiff = -((todaynum + 7 - nameddaynum) % 7)
		toks["absTime"] = datetime(now.year, now.month, now.day)+timedelta(daydiff)
	else:
		name = toks.name.lower()
		toks["absTime"] = {
			"now"       : now,
			"today"     : datetime(now.year, now.month, now.day),
			"yesterday" : datetime(now.year, now.month, now.day)+timedelta(-1),
			"tomorrow"  : datetime(now.year, now.month, now.day)+timedelta(+1),
			}[name]
 
def convertToAbsTime(toks):
	now = datetime.now()
	if "dayRef" in toks:
		day = toks.dayRef.absTime
		day = datetime(day.year, day.month, day.day)
	else:
		day = datetime(now.year, now.month, now.day)
	if "timeOfDay" in toks:
		try:
			isstring = isinstance(toks.timeOfDay,basestring)
		except NameError:
			isstring = isinstance(toks.timeOfDay,str)
		if isstring:
			timeOfDay = {
				"now"      : timedelta(0, (now.hour*60+now.minute)*60+now.second, now.microsecond),
				"noon"     : timedelta(0,0,0,0,0,12),
				"midnight" : timedelta(),
				}[toks.timeOfDay]

		else:
			hhmmss = toks.timeparts
			if hhmmss.miltime:
				hh,mm = hhmmss.miltime
				ss = 0
			else:            
				hh,mm,ss = (hhmmss.HH % 12), hhmmss.MM, hhmmss.SS
				if not mm: mm = 0
				if not ss: ss = 0
				if toks.timeOfDay.ampm == 'pm':
					hh += 12
			timeOfDay = timedelta(0, (hh*60+mm)*60+ss, 0)
	else:
		timeOfDay = timedelta(0, (now.hour*60+now.minute)*60+now.second, now.microsecond)
	toks["absTime"] = day + timeOfDay
 
def calculateTime(toks):
	if toks.absTime:
		absTime = toks.absTime
	else:
		absTime = datetime.now()
	if toks.timeOffset:
		absTime += toks.timeOffset
	toks["calculatedTime"] = absTime
 
# grammar definitions
CL = CaselessLiteral
today, tomorrow, yesterday, noon, midnight, now = map( CL,
	"today tomorrow yesterday noon midnight now".split())
plural = lambda s : Combine(CL(s) + Optional(CL("s")))
week, day, hour, minute, second = map( plural,
	"week day hour minute second".split())
am = CL("am")
pm = CL("pm")
COLON = Suppress(':')
 
# are these actually operators?
in_ = CL("in").setParseAction(replaceWith(1))
from_ = CL("from").setParseAction(replaceWith(1))
before = CL("before").setParseAction(replaceWith(-1))
after = CL("after").setParseAction(replaceWith(1))
till = CL("till").setParseAction(replaceWith(-1))
until = CL("until").setParseAction(replaceWith(-1))
past = CL("past").setParseAction(replaceWith(1))
ago = CL("ago").setParseAction(replaceWith(-1))
next_ = CL("next").setParseAction(replaceWith(1))
last_ = CL("last").setParseAction(replaceWith(-1))
 
couple = (Optional(CL("a")) + CL("couple") + Optional(CL("of"))).setParseAction(replaceWith(2))
one = CL("one").setParseAction(replaceWith(1))
two = CL("two").setParseAction(replaceWith(2))
three = CL("three").setParseAction(replaceWith(3))
four = CL("four").setParseAction(replaceWith(4))
five = CL("five").setParseAction(replaceWith(5))
six = CL("six").setParseAction(replaceWith(6))
seven = CL("seven").setParseAction(replaceWith(7))
eight = CL("eight").setParseAction(replaceWith(8))
nine = CL("nine").setParseAction(replaceWith(9))
ten = CL("ten").setParseAction(replaceWith(10))
eleven = CL("eleven").setParseAction(replaceWith(11))
twelve = CL("twelve").setParseAction(replaceWith(12))
a_qty = CL("a").setParseAction(replaceWith(1))
integer = Word(nums).setParseAction(lambda t:int(t[0]))
int4 = Group(Word(nums,exact=4).setParseAction(lambda t: [int(t[0][:2]),int(t[0][2:])] ))
qty = integer | couple | a_qty | one | two | three | four | five | six | seven | eight | nine | ten | eleven | twelve
dayName = oneOf( list(calendar.day_name) )
 
dayOffset = (qty("qty") + (week | day)("timeunit"))
dayFwdBack = (from_ + now.suppress() | ago)("dir")
weekdayRef = (Optional(next_ | last_,1)("dir") + dayName("day"))
dayRef = Optional( (dayOffset + (before | after | till | until | past | from_)("dir") ).setParseAction(convertToTimedelta) ) + \
			((yesterday | today | tomorrow)("name")|
			 weekdayRef("wkdayRef")).setParseAction(convertToDay)
todayRef = (dayOffset + dayFwdBack).setParseAction(convertToTimedelta) | \
			(in_("dir") + qty("qty") + day("timeunit")).setParseAction(convertToTimedelta)
 
dayTimeSpec = dayRef | todayRef
dayTimeSpec.setParseAction(calculateTime)
 
hourMinuteOrSecond = (hour | minute | second)
 
timespec = Group(int4("miltime") |
				 integer("HH") + 
				 Optional(Optional(COLON) + integer("MM")) + 
				 Optional(COLON + integer("SS")) + Optional((am | pm)("ampm"))
				 )
absTimeSpec = ((noon | midnight | now | timespec("timeparts"))("timeOfDay") + 
				Optional(dayRef)("dayRef"))
absTimeSpec.setParseAction(convertToAbsTime,calculateTime)
 
relTimeSpec = qty("qty") + hourMinuteOrSecond("timeunit") + \
				(from_ | before | after | till | until | past)("dir") + \
				absTimeSpec("absTime") | \
			  qty("qty") + hourMinuteOrSecond("timeunit") + ago("dir") | \
			  in_ + qty("qty") + hourMinuteOrSecond("timeunit")
relTimeSpec.setParseAction(convertToTimedelta,calculateTime)
 
nlTimeExpression = (absTimeSpec | dayTimeSpec | relTimeSpec)

def parse(t):
	numbers = {'zero':0,'oh':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12,'thirteen':13,'fourteen':14,'fifteen':15,'sixteen':16,
				'seventeen':17,'eighteen':18,'nineteen':19,'twenty':20,'thirty':30,'forty':40,'fifty':50}
	words = t.split()
	for index in range(len(words)):
		i = words[index]
		if i in numbers:
			if numbers[i]>19:
				words[index] = str(numbers[i])
			elif index>0 and words[index-1].isdigit() and int(words[index-1])>19 and int(words[index-1])%10==0:
				words[index-1] = str(int(words[index-1]) + numbers[i])
				words[index] = ''
			else:
				words[index] = str(numbers[i])
	return nlTimeExpression.parseString(' '.join(words))
 
# test grammar
tests = """\
today
tomorrow
yesterday
in a couple of days
a couple of days from now
a couple of days from today
in a day
3 days ago
3 days from now
a day ago
now
10 minutes ago
10 minutes from now
in 10 minutes
in a minute
in a couple of minutes
20 seconds ago
in 30 seconds
20 seconds before noon
20 seconds before noon tomorrow
noon
midnight
noon tomorrow
6am tomorrow
0800 yesterday
12:15 AM today
3pm 2 days from today
a week from today
a week from now
3 weeks ago
noon next Sunday
noon Sunday
noon last Sunday
three days ago
twelve thirty""".splitlines()
 
if __name__=="__main__":
	for t in tests:
		print (t, "(relative to %s)" % datetime.now())
		# res = nlTimeExpression.parseString(t)
		res = parse(t)
		if "calculatedTime" in res:
			print (res.calculatedTime)
		else:
			print ("???")
		print
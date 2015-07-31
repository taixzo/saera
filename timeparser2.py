from datetime import datetime, timedelta

def parse(tokens):
	tokens = [i.lower() for i in tokens]
	numbers = {'zero':0,'oh':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12,'thirteen':13,'fourteen':14,'fifteen':15,'sixteen':16,
				'seventeen':17,'eighteen':18,'nineteen':19,'twenty':20,'thirty':30,'forty':40,'fifty':50}
	bells = {'quarter':15,'half':30}
	days = {'tomorrow':1,'day':1,'yesterday':-1}
	weekdays = {'monday':0,'tuesday':1,'wednesday':2,'thursday':3,'friday':4,'saturday':5,'sunday':6}
	signs = {'past':1,'after':1,'til':-1,'till':-1,'before':-1,'to':-1,'of':-1}
	daytimes = {'morning':9,'noon':12,'afternoon':15,'evening':18,'night':21,'midnight':24}
	for index in range(len(tokens)):
		i = tokens[index]
		if i in numbers:
			if numbers[i]>19:
				tokens[index] = str(numbers[i])
			elif index>0 and tokens[index-1].isdigit() and (int(tokens[index-1])>19 or int(tokens[index-1])==0) and int(tokens[index-1])%10==0:
				tokens[index-1] = str(int(tokens[index-1]) + numbers[i])
				tokens[index] = ''
			else:
				tokens[index] = str(numbers[i])
	now = datetime.now()

	hour = None
	minute = None
	temptime = None

	minutetimeadjustment = 0
	timeadjustment = 0
	addedtimeadjustment = 0
	dateadjustment = 0

	for token in tokens:
		if token.isdigit():
			if hour is None and addedtimeadjustment == 0:
				hour = int(token)
				minute = minute or 0
			else:
				if minute in (None, 0) and addedtimeadjustment == 0:
					minute = int(token)
		elif token in ['a','an']:
			temptime = 1
		elif (token=='hours' and hour) or (token=='hour' and (hour==1 or temptime)):
			addedtimeadjustment = hour*60 if hour is not None else 60
			hour = None
			minute = None
		elif (token=='minutes' and hour) or (token=='minute' and (hour==1 or temptime)):
			addedtimeadjustment = hour if hour is not None else 1
			hour = None
			minute = None
		elif token in bells:
			minutetimeadjustment = bells[token]
		elif token in signs and minutetimeadjustment!=0:
			timeadjustment = abs(minutetimeadjustment)*signs[token] # double negatives should not cancel out
			minutetimeadjustment = 0
		elif token in days:
			dateadjustment = days[token]
		elif token in signs and dateadjustment!=0:
			dateadjustment = abs(dateadjustment)*signs[token] # double negatives should not cancel out
		elif token in weekdays:
			dateadjustment += (weekdays[token]-now.weekday()+7) % 7
		elif token in daytimes:
			hour = daytimes[token]
	if minutetimeadjustment:
		addedtimeadjustment += minutetimeadjustment

	adjustmentdelta = timedelta(days = dateadjustment, minutes = timeadjustment)
	adjustmentdelta2 = timedelta(minutes = addedtimeadjustment)
	# print (hour, minute, timeadjustment,addedtimeadjustment)
	then = now.replace(hour = hour if hour is not None else now.hour, minute = minute if minute is not None else now.minute if adjustmentdelta.days==adjustmentdelta.seconds==0 else 0, second = 0, microsecond = 0) + adjustmentdelta + adjustmentdelta2
	if then.date()==now.date():
		if then<now:
			then = then+timedelta(days=1)

	print (then, tokens)

	return then


if __name__=="__main__":
	parse("A quarter to twelve".split()) # Pass
	parse("Half past one".split()) # Pass
	parse("Nine thirty".split()) # Pass
	parse("Six twenty one".split()) # Pass
	parse("January second".split()) # Fail
	parse("The day after tomorrow".split()) # Fail
	parse("Sunday".split()) # Pass
	parse("Tuesday".split()) # Pass
	parse("One oh nine".split()) # Pass

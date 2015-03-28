from datetime import datetime, timedelta

def parse(tokens):
	tokens = [i.lower() for i in tokens]
	numbers = {'zero':0,'oh':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12,'thirteen':13,'fourteen':14,'fifteen':15,'sixteen':16,
				'seventeen':17,'eighteen':18,'nineteen':19,'twenty':20,'thirty':30,'forty':40,'fifty':50}
	bells = {'quarter':15,'half':30}
	signs = {'past':1,'after':1,'til':-1,'till':-1,'before':-1,'to':-1,'of':-1}
	for index in range(len(tokens)):
		i = tokens[index]
		if i in numbers:
			if numbers[i]>19:
				tokens[index] = str(numbers[i])
			elif index>0 and tokens[index-1].isdigit() and int(tokens[index-1])>19 and int(tokens[index-1])%10==0:
				tokens[index-1] = str(int(tokens[index-1]) + numbers[i])
				tokens[index] = ''
			else:
				tokens[index] = str(numbers[i])
	now = datetime.now()

	hour = None
	minute = None

	adjustment = 0

	for token in tokens:
		if token.isdigit():
			if hour is None:
				hour = int(token)
			else:
				if minute is None:
					minute = int(token)
		elif token in bells:
			adjustment = bells[token]
		elif token in signs and adjustment!=0:
			adjustment = abs(adjustment)*signs[token] # double negatives should not cancel out

	adjustmentdelta = timedelta(minutes = adjustment)
	# print hour, minute
	now = now.replace(hour = hour if hour is not None else now.hour, minute = minute if minute is not None else now.minute if adjustmentdelta==0 else 0, second = 0, microsecond = 0) + adjustmentdelta

	print now, tokens


if __name__=="__main__":
	parse("A quarter to twelve".split())
	parse("Half past one".split())
	parse("Nine thirty".split())
	parse("Six twenty one".split())
	parse("January second".split())
	parse("The day after tomorrow".split())
	parse("Sunday".split())
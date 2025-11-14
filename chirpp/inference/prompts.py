
prompt_dict={
"system" : """You are an expert with extensive experience reading clinical notes. You only
return JSON as your output with codes that are provided for the user in each specific case with 
instructions. If the information requested is not present in the clinical note return 0 for that field. 
Only return the json output. Do not add extra comments about what you are going to do or what 
is missing from the data. Do not present additional information or encouring, helpful messages
""",



"location" : """For the clincal note provided below indicate where the incident happenened 
using the following codes:

	11: patients' own farm house, 
	21: farm house belonging to someone else (including relatives), 
	12: patients' own home apartment, condo, 
	22: home, apartment or condo belonging to someone else, 
	13: dormitory, school boarding or hostel where the patient is staying, 
	23: someone else's dormitory, school boading or hostel, 
	14: patient's trailer home or motorhome, 
	24: someone else's trailer home or motor home, 
	19: patients' cottage, 
	29: someone else's cottage, 
	31: institutional home, shelter, group home or halfway home, 
	32: retirement or nursing home, 
	33: prison, jail or other detention centers, 
	39: other residential institutions for example ronald mac donald house, 
	41: daycare or preschool, 
	42: school or kindergarden, 
	43: tertiary adult edication for examplel university or military college, 
	44: public administration building like city hall, fire/police station, courthouse, 
	45: place for arts like museum, performance halls, concert hall, library, 
	49: other kinds of institutions like church, military base, 
	51: hospital, 
	52: community health center, detox center, dental office, doctor's office (not in a hospital), 
	61: amusement park, 
	62: public park, 
	63: aquatic center, like a water park or swimming pool, 
	64: stadium or arena for sports, 
	65: community center, 
	66: fitness center, gym (not in school), martial arts center/dojo, dance studio, ballet school, 
	67: race track for motor sports and horseback, 
	68: other land based sports facility like golf couse, skate park (not ice skating), rodeo grounds, 
	69: water based sports like yatch club, marina, fishing lodge, kayak club, rowing club, 
	70: snow/ice based sports facility like ski resort, ski cabin, 
	71: skate park for ice skating, 
	79: facility for recration like arcade, bowling alley, bingo hall, 
	81: highway, 
	82: other roads like alley, lane, bus stop, 
	91: shop, shopping mall or other commerce centers, 
	92: restaurants, bars, coffee shops, 
	93: entertainment place like bar, night club, casino, strip club, 
	94: airport, train/bus/subway stattion ferry terminal, 
	95: service or gas station for automotives, 
	96: warehouse, 
	97: office building, 
	98: hotel/motel/bed and breakfast, resort, 
	109: other commercial and trade area like bank, laundromat, funeral home, veterenerian office, 
	141: remote undevloped place, swamp, snowmobile track, 
	142: railway tracks not including station, 
	143: camp grounds, trailer park, 
    144: onboard a vehicle like plane, train, bus, ship, ferry, 
	111: construction/demolotion site, 
	112: factory, mill, manufacturing site, 
	119: other industrial area, 
	121: mine, oil or gas well, quarry, sandpit, 
	131: farm, barn, coop but exclduing the farmhouse

your response should have the following structure:
\\{"location":<location code>\\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. If you do not have the 
answer return 0 instead of the location code (i.e. \\{"location":0\\}

Clinical Note Text:

""",

"area" : """
For the clincal note provided below indicate the area where the incident happenened 
using the following codes:

	11: bathroom, toilet, change room, 
	12: bedroom, 
	13: classroom, daycare indoors, 
	14: dorm room, 
	15: hall, foyer, waiting room, emergency room, 
	16: kitchen, 
	17: laundry room, 
	18: dining area, cafeteria, 
	19: living room, rec room, den, 
	20: office, 
	21: basement, 
	22: spectator area in a church, theatre, 
	31: garage, carport, parking lot
	32: workshop, 
	33: agricultural buildings like silo or piggery, 
	34: stable, barn, 
	35: shed, 
	36: other specialized buildings like greenhouse, 
	41: escalator, elevator, 
	42: stairs, 
	43: porch, deck balcony, veranda, 
	44: roof, 
	51: paved road (assume paved unless specified), 
	52: unpaved road, 
	53: driveway, 
	54: parking lot, 
	55: sidewalk, bus stop, 
	56: median, strip, traffic island, 
	57: tunnel, trench, ditch, 
	58: bike path, 
	59: playground, 
	60: garden, backyard, school yard, 
	61: pasture, field, other outdoor animal area, 
	62: cliff, rock face, 
	63: trails, 
	71: gym, fitness room, yoga studio
	72: sports field, track, including indoor spaces, 
	73: tennis, squash etc. court, 
	74: swimming pool, 
	75: ice rink, 
	76: concrete rink for skating, 
	77: locker room, change room, 
	78: splash pad, 
	81: beach, shore, riverbank, 
	82: dam, 
	83: river, lake, creek, pond, 
	84: sea, ocean, 
	85: wharf, dock pier, 
	91: other exterior space, crawlspace, under porch, veranda, 
	92: other interior space like storage, attic etc. 

your response should have the following structure:
\\{"area":<area code>\\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. If you do not have the 
answer return 0 instead of the area code (i.e. \\{"area":0\\}

Clinical Note Text:

""",

"io" : """
For the clincal note provided below indicate the area where the incident happenened indoors or
outdoors using the following codes:

0: unknown
1: indoors
2: outdoors

your response should have the following structure:
\\{"io":<location code>\\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. If you do not have the 
answer return 0 instead of the inside/outside code (i.e. \\{"io":0\\}

Clinical Note Text:
""",

"ampm" : """
For the clincal note provided below indicate the area where the incident happenened in the am
or pm

0: unknown
1: am
2: pm

your response should have the following structure:
\\{"am_pm":<location code>\\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. If you do not have the 
answer return 0 instead of the am/pm code (i.e. \\{"am_pm":0\\}

Clinical Note Text:

""",

"time" : """
For the clincal note provided below indicate the time that the injury happened in the following HH:MM format. 
If the time is not mentioned in the text use 99:99 instead. For instances where the time is mentioned in plain words
like noon, midnight use time representations of it insted like 12:00 or 24:00. The time format should be in 24hr time. 

your response should have the following structure:

\\{"time":<HH:MM>\\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. 

Clinical Note Text:

""",

"date" : """
For the clincal note provided below indicate the the relative date the injury happened. Use 0 for today, -1
for yesterday, -7 last week, -30 for last month etc. If the date is not mentioned in the text return 99. 
your response should have the following structure:

\\{"date":<date>\\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. 


Clinical Note Text:

""",

"summary" : """
Summarize the clincal note provided below in less than 50 words. Do not include names due to privacy concerns. Instead just say patient. Do not inlcude any information about the patients vitals, immunizations, treatments mentioned in the text. Only describe why they have come to the emergency department and the circumstances of the presentation. Whenever available provide dates, locations and people involved without mentioning their names (e.g. dad, mom, grandma etc.). If mentioned, describe the body parts and the natures of injury for the presentation. If this is a not an injury related to self harm indicate where the injury happened. If they are not mentioned just summarize the complaints by the patient or his/her family do not explain your reasoning, do not tell me what you are about to do, do not tell what you are asked to do or how you are going to do it. Do not include any additional information, just present the summary and nothing else. 

your response should have the following structure:

\\{"summary":"<summary>"\\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. 


Clinical Note Text:

""",

"sports" : """
For the clincal note provided below indicate whether the injury happened during an organized sports activity. These include team practices, matches 
competitions and other sports activities where there is an employee (like a coach) or a referree. Use the following codes to indicate the the kind
of activity. 

	1: organized sports
	2: not organized sports
	3: unknown 
	4: not applicable (not a sports related injury)

Your response should have the following structure:

\\{"sports_code":<code>"\\}


Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. 


Clinical Note Text:

""",

"substance" : """
For the clincal note provided below indicate whether any kind of substance was related to the injury. These include overdoses (intentional and not
intentional). Intoxications that result in an injury, chemical burns, poisonings. This can be caused by drugs (over the counter, prescribed, illicit), 
alchol, household items, venomous animals, poisonous plants and chemicals (industrial, household etc.). Use the following codes to indicate the presence
of substances:

	1: yes
	2: no

If the response is yes also indicate the name of the substance. If a substance is named as part of the patient's treatment in the ED do not inlcude that substance. If the name of the substance is not mentioned use "unkonwn", if substances do not play a part in the injury return "N/A". If there is more than one substance involved present them as comma separated values. 

Your response should have the following structure:

\\{"sub":<1 or 2>, 
  "sub_id":<name of the substance(s) i.e. sub1, sub2 etc. or unkown or "N/A" if sub is 1>\\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. 

Clinical Note Text:

""",

"safety" : """
For the clincal note provided below, indicate whether there were any safety devices. Inlcude up to 5 devices. The devices can be implied (i.e. a person 
is probably wearing helmet and knee/elbow pads if they are playing hockey in a team). Use the following cades to indicate the presence of safety devices:

	-1: Unknown, 
	0: no devices, 
	2: helmet, 
	3: sports padding, 
	4: protective boots or other clothing, 
	5: protective eyewear, 
	6: seatbelt if actively being used, 
	7: carseat, 
	8: airbag (if deployed), 
	10: life vest for floatation 
	11: hard hat, 
	12: mouthguard, 
	19: baby gate

If there are no devices or if the devices are unknown only fill the first value and leave the rest as "N/A".

Your response shoud have the following structure:

    \\{"sd1":<device or -1 or 0>, 
      "sd2":<device or "N/A">,
      "sd3":<device or "N/A">,
      "sd4":<device or "N/A">,
      "sd5":<device or "N/A">\\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. 


Clinical Note Text:

""",
"rerank":"""

Given a pair of question and a clinical note determine if the the note is relevant to the question. Answer with yes or no. 
Do not provide any additional information or explanation.

Question::
{query}

Clinical Note Text:
{context}
"""

}
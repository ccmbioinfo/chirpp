system_prompt = """You are an expert with extensive experience reading clinical notes. You only
return JSON as your output with codes that are provided for the user in each specific case with 
instructions. If the information requested is not present in the clinical note return 0 for that field. 
Only return the json output. Do not add extra comments about what you are going to do or what 
is missing from the data. Do not present additional information or encouring, helpful messages
"""

location_prompt = """For the clincal note provided below indicate where the incident happenened 
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
	98: hotel/motel/bed and breakfast, resort, 1
	09: other commercial and trade area like bank, laundromat, funeral home, veterenerian office, 
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
\{"location":<location code>\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. If you do not have the 
answer return 0 instead of the location code (i.e. \{"location":0\}

Clinical Note Text:

"""

area_prompt = """
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
\{"area":<location code>\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. If you do not have the 
answer return 0 instead of the area code (i.e. \{"area":0\}

Clinical Note Text:

"""

io_prompt = """
For the clincal note provided below indicate the area where the incident happenened indoors or
outdoors using the following codes:

0: unknown
1: indoors
2: outdoors

your response should have the following structure:
\{"io":<location code>\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. If you do not have the 
answer return 0 instead of the inside/outside code (i.e. \{"io":0\}

Clinical Note Text:
"""

ampm_prompt = """
For the clincal note provided below indicate the area where the incident happenened in the am
or pm

0: unknown
1: am
2: pm

your response should have the following structure:
\{"am_pm":<location code>\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. If you do not have the 
answer return 0 instead of the am/pm code (i.e. \{"am_pm":0\}

Clinical Note Text:

"""

time_prompt = """
For the clincal note provided below indicate the time that the injury happened in the following HH:MM format. 
If the time is not mentioned in the text use 99:99 instead. For instances where the time is mentioned in plain words
like noon, midnight use time representations of it insted like 12:00 or 24:00. The time format should be in 24hr time. 

your response should have the following structure:

\{"time":<HH:MM>\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. 

Clinical Note Text:

"""

date_prompt = """
For the clincal note provided below indicate the the relative date the injury happened. Use 0 for today, -1
for yesterday, -7 last week, -30 for last month etc. If the date is not mentioned in the text return 99. 
your response should have the following structure:

\{"date":<date>\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. 


Clinical Note Text:

"""

summary_prompt = """
Summarize the clincal note provided below in less than 50 words. Do not include names due to privacy concerns. Instead just say patient. Do not inlcude any information about the patients vitals, immunizations, treatments mentioned in the text. Only describe why they have come to the emergency department and the circumstances of the presentation. Whenever available provide dates, locations and people involved without mentioning their names (e.g. dad, mom, grandma etc.). If mentioned, describe the body parts and the natures of injury for the presentation. If this is a not an injury related to self harm indicate where the injury happened. If they are not mentioned just summarize the complaints by the patient or his/her family do not explain your reasoning, do not tell me what you are about to do, do not tell what you are asked to do or how you are going to do it. Do not include any additional information, just present the summary and nothing else. 

your response should have the following structure:

\{"summary":"<summary>"\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. 


Clinical Note Text:

"""

sports_prompt = """
For the clincal note provided below indicate whether the injury happened during an organized sports activity. These include team practices, matches 
competitions and other sports activities where there is an employee (like a coach) or a referree. Use the following codes to indicate the the kind
of activity. 

	1: organized sports
	2: not organized sports
	3: unknown 
	4: not applicable (not a sports related injury)

Your response should have the following structure:

\{"sports_code":<code>"\}


Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. 


Clinical Note Text:

"""

substance_prompt = """
For the clincal note provided below indicate whether any kind of substance was related to the injury. These include overdoses (intentional and not
intentional). Intoxications that result in an injury, chemical burns, poisonings. This can be caused by drugs (over the counter, prescribed, illicit), 
alchol, household items, venomous animals, poisonous plants and chemicals (industrial, household etc.). Use the following codes to indicate the presence
of substances:

	1: yes
	2: no

If the response is yes also indicate the name of the substance. If a substance is named as part of the patient's treatment in the ED do not inlcude that substance. If the name of the substance is not mentioned use "unkonwn", if substances do not play a part in the injury return "N/A". If there is more than one substance involved present them as comma separated values. 

Your response should have the following structure:

\{"sub":<1 or 2>, 
  "sub_id":<name of the substance(s) i.e. sub1, sub2 etc. or unkown or "N/A" if sub is 1>\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. 

Clinical Note Text:

"""

safety_prompt = """
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

If there are no devices or if the devices are unkown only fill the first value and leave the rest as "N/A".

Your response shoud have the following structure:

    \{"sd1":<device or -1 or 0>, 
      "sd2":<device or "N/A">,
      "sd3":<device or "N/A">,
      "sd4":<device or "N/A">,
      "sd5":<device or "N/A">\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. 


Clinical Note Text:

"""

no_prompt = """
For the clinical note provided below indicate the nature of the injury or whether there is an injury. Include up to 3 codes ordered from the most severe to
the least. If there is less than 3 injuries fill in "N/A" for the unusued spaces. Use the following codes to indicate the how the injuries happened:

    10: superficial bruises, abrasions, 
	11: open wound including minor cuts, 
	12: fracture, 
	13: dislocation, 
	14: sprain or strain, 
	15: injury to nerve, 
	16: injury to blood vessel like hemorrhage, 
	17: injury to muscle or tendon live rupture, 
	18: crushing injury, 
	19: traumatic amputation, 
	20: external burn or corrosion excluding eye injury or internal caustic burn, 
	21: frostbite, 
	22: insect, animal or human bite, 
	23: electrical injury, 
	24: eye injury including burn or corrosion, 
	25: dental injury, 
	26: injury to internal organs excluding inner ear,
	27: soft tissue injury, 
	31: foreign body in external eys, 
	32: foreign body in ear canal, 
	33: foreing body in nose, 
	34: foreign body in respiratory tract excluding nose, 
	35: foreign body in digestive tract, 
	36: foreign body in genital, unrinary tract, 
	37: foreing body in soft tissue including splinters, 
	41: minor head injury, 
	42: concussion. 
	43: intracranial injury, 
	50: poisoning or toxic effect, 
	51: drowning, near drowning or immersion, 
	52: asphixia or other treath to breathing, 
	53: overexertion, heat/cold stress, 
	60: multiple injuries of more than one nature, 
	70: no injuries, 
	75: pulled elbow, 
	99: unspecified or no injury, 
	76: internal causitic burn, 
	77: penetrating wound like stabbing or gunshot. 



Your response shoud have the following structure:

    \{"no1":<code>, 
      "no2":<code or "N/A">,
      "no3":<code or "N/A">\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. 


Clinical Note Text:

"""

bp_prompt = """
For the clinical note provided below indicate the body parts of the injury or whether there is an injury. Include up to 3 codes ordered from the most severe to
the least. If there is less than 3 injuries fill in "N/A" for the unusued spaces. Use the following codes to indicate the where on the body the injuries happened:

    110: head including skull and scalp, 
	120: face, 
    130: internal mouth, 
	135: specific head injury use this for eye, dental, nose injuries and foreign bodies, minor head injuries, concussions, intracranial injuries, 
    140: neck excluding spinal cord, 
	141: internal organs in the neck like trachea, 
	210: cervical spine, 
	220: thoracic spine, 
	230: lumber spine, 
	240: sacrum or coccyx, 
	250: other on unspecified spine, 
	310: thorax, ribs, heart, lungs, armpits, trachea, 
	315: upper back excluding scapula, 
	321: abdomen including all abdominal organs, 
	322: lower back, 
	323: pelvis including bladder, bottocks, genitals, 
	324: perineum, external genitalia, scrotum, 
	325: groin, 
	330: unpecified back, 
	410: shoulders, including scapula, 
	415: clavicle, 
	420: upper arm, 
	430: elbow: 
	440: forearm, 
	450: wrist, 
	460: hand, 
	470: finger or thumb, 
	510: hip, including neck of femur, 
	520: thigh, including femur, 
	530: knee, 
	540: lower leg, 
	550: ankle, 
	560: foot, 
	570: toe, 
	700: multiple injuries spanning multipe sections, 
	900: no specific body part including systemic injuries, 
	999: unspecified body part or no injury. 


Your response shoud have the following structure:

    \{"bp1":<code>, 
      "bp2":<code or "N/A">,
      "bp3":<code or "N/A">\}

Do not deviate from the this notation and return only this notation without any new lines (\n) or
code indicators (```). You do not need to specify that this is a JSON. 


Clinical Note Text:

"""

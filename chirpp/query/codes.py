# the goal is to use some sort of 0 shot to determine which code to use then build a sql query to search for those in the
# chirpp_report table
location_codes = {"11": "patients' own farm house", "21": "farm house belonging to someone else (including relatives)",
    "12": "patients' own home apartment, condo", "22": "home, apartment or condo belonging to someone else",
    "13": "dormitory, school boarding or hostel where the patient is staying",
    "23": "someone else's dormitory, school boarding or hostel", "14": "patient's trailer home or motorhome",
    "24": "someone else's trailer home or motor home", "19": "patients' cottage", "29": "someone else's cottage",
    "31": "institutional home, shelter, group home or halfway home", "32": "retirement or nursing home",
    "33": "prison, jail or other detention centers",
    "39": "other residential institutions for example ronald mac donald house", "41": "daycare or preschool",
    "42": "school or kindergarten", "43": "tertiary adult education for example university or military college",
    "44": "public administration building like city hall, fire/police station, courthouse",
    "45": "place for arts like museum, performance halls, concert hall, library",
    "49": "other kinds of institutions like church, military base", "51": "hospital",
    "52": "community health center, detox center, dental office, doctor's office (not in a hospital)",
    "61": "amusement park", "62": "public park", "63": "aquatic center, like a water park or swimming pool",
    "64": "stadium or arena for sports", "65": "community center",
    "66": "fitness center, gym (not in school), martial arts center/dojo, dance studio, ballet school",
    "67": "race track for motor sports and horseback",
    "68": "other land based sports facility like golf course, skate park (not ice skating), rodeo grounds",
    "69": "water based sports like yacht club, marina, fishing lodge, kayak club, rowing club",
    "70": "snow/ice based sports facility like ski resort, ski cabin", "71": "skate park for ice skating",
    "79": "facility for recreation like arcade, bowling alley, bingo hall", "81": "highway",
    "82": "other roads like alley, lane, bus stop", "91": "shop, shopping mall or other commerce centers",
    "92": "restaurants, bars, coffee shops", "93": "entertainment place like bar, night club, casino, strip club",
    "94": "airport, train/bus/subway station ferry terminal", "95": "service or gas station for automotive",
    "96": "warehouse", "97": "office building", "98": "hotel/motel/bed and breakfast, resort",
    "109": "other commercial and trade area like bank, laundromat, funeral home, veterinarian office",
    "141": "remote undeveloped place, swamp, snowmobile track", "142": "railway tracks not including station",
    "143": "camp grounds, trailer park", "144": "onboard a vehicle like plane, train, bus, ship, ferry",
    "111": "construction/demolition site", "112": "factory, mill, manufacturing site", "119": "other industrial area",
    "121": "mine, oil or gas well, quarry, sandpit", "131": "farm, barn, coop but excluding the farmhouse"}

area_codes = {"11": "bathroom, toilet, change room", "12": "bedroom", "13": "classroom, daycare indoors",
              "14": "dorm room", "15": "hall, foyer, waiting room, emergency room", "16": "kitchen",
              "17": "laundry room", "18": "dining area, cafeteria", "19": "living room, rec room, den", "20": "office",
              "21": "basement", "22": "spectator area in a church, theatre", "31": "garage, carport, parking lot",
              "32": "workshop", "33": "agricultural buildings like silo or piggery", "34": "stable, barn", "35": "shed",
              "36": "other specialized buildings like greenhouse", "41": "escalator, elevator", "42": "stairs",
              "43": "porch, deck balcony, veranda", "44": "roof", "51": "paved road (assume paved unless specified)",
              "52": "unpaved road", "53": "driveway", "54": "parking lot", "55": "sidewalk, bus stop",
              "56": "median, strip, traffic island", "57": "tunnel, trench, ditch", "58": "bike path",
              "59": "playground", "60": "garden, backyard, school yard",
              "61": "pasture, field, other outdoor animal area", "62": "cliff, rock face", "63": "trails",
              "71": "gym, fitness room, yoga studio", "72": "sports field, track, including indoor spaces",
              "73": "tennis, squash etc. court", "74": "swimming pool", "75": "ice rink",
              "76": "concrete rink for skating", "77": "locker room, change room", "78": "splash pad",
              "81": "beach, shore, riverbank", "82": "dam", "83": "river, lake, creek, pond", "84": "sea, ocean",
              "85": "wharf, dock pier", "91": "other exterior space, crawlspace, under porch, veranda",
              "92": "other interior space like storage, attic etc."}

i_o_codes = {"I": "indoors", "O": "outdoors"}

am_pm_codes = {"a": "am", "p": "pm"}

intent_codes = {}

sports_codes = {"1": "organized sports", "2": "not organized sports", "3": "unknown","4": "not applicable (not a sports related injury)"}

safety_codes = {
    "-1": "Unknown",
	"0": "no devices",
	"2": "helmet",
	"3": "sports padding",
	"4": protective boots or other clothing,
	"5": protective eyewear,
	"6": seatbelt if actively being used,
	"7": carseat,
	"8": airbag (if deployed),
	"10": life vest for floatation
	"11": hard hat,
	"12": mouthguard,
	"19": baby gate}

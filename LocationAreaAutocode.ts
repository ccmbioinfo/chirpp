function locationCodeFromPlace(loc: string): number | null {
    loc = loc.toLowerCase();
  
    if ((loc.includes("farm") && loc.includes("house")) && (!loc.includes("other"))) {
      return 11;
    } else if ((loc.includes("house")) && (!loc.includes("other"))) {
      return 12;
    } else if (((loc.includes("boarding")) || (loc.includes("hostel")) || (loc.includes("residence"))) && (!loc.includes("other"))) {
      return 13;
    } else if (((loc.includes("trailer") && !loc.includes("park")) || (loc.includes("motorhome"))) && (!loc.includes("other"))) {
      return 14;
    } else if ((loc.includes("cottage")) && (!loc.includes("other"))) {
      return 19;
    } else if ((loc.includes("farm") && loc.includes("house")) && (loc.includes("other"))) {
      return 21;
    } else if ((loc.includes("house")) && (loc.includes("other"))) {
      return 22;
    } else if (((loc.includes("boarding")) || (loc.includes("hostel")) || (loc.includes("residence"))) && (loc.includes("other"))) {
      return 23;
    } else if (((loc.includes("trailer") && !loc.includes("park")) || (loc.includes("motorhome"))) && (loc.includes("other"))) {
      return 24;
    } else if ((loc.includes("cottage")) && (loc.includes("other"))) {
      return 29;
    } else if ((loc.includes("daycare")) || (loc.includes("school") && loc.includes("pre")) || (loc.includes("ontario early years"))) {
      return 41;
    } else if ((loc.includes("school")) || (loc.includes("kindergarten"))) {
      return 42;
    } else if ((loc.includes("tertiary")) || (loc.includes("adult education")) || (loc.includes("community college")) || (loc.includes("university")) || (loc.includes("royal military college"))) {
      return 43;
    } else if ((loc.includes("public administration")) || (loc.includes("government")) || (loc.includes("city hall")) || (loc.includes("cour")) || (loc.includes("police")) || (loc.includes("experimental farm"))) {
      return 44;
    } else if ((loc.includes("place for arts")) || (loc.includes("theatre")) || (loc.includes("concert hall")) || (loc.includes("museum")) || (loc.includes("gallery")) || (loc.includes("library")) || (loc.includes("botanical"))) {
      return 45;
    } else if (((loc.includes("military base")) || (loc.includes("church")))) {
      return 49;
    } else if ((loc.includes("hospital"))) {
      return 51;
    } else if ((loc.includes("community health centre")) || (loc.includes("medical office")) || (loc.includes("dental office")) || (loc.includes("detox centre")) || (loc.includes("crisis centre"))) {
      return 52;
    } else if ((loc.includes("shop")) || (loc.includes("shopping centre")) || (loc.includes("pet shop"))) {
      return 91;
    } else if ((loc.includes("restaurant")) || (loc.includes("commercial eating place")) || (loc.includes("snack bar")) || (loc.includes("coffee shop"))) {
      return 92;
    } else if ((loc.includes("entertainment")) || (loc.includes("drinking place")) || (loc.includes("night club")) || (loc.includes("bar")) || (loc.includes("casino"))) {
      return 93;
    } else if ((loc.includes("airport")) || (loc.includes("bus")) || (loc.includes("railway")) || (loc.includes("subway")) || (loc.includes("transit station")) || (loc.includes("ferry terminal"))) {
      return 94;
    } else if ((loc.includes("service station")) || (loc.includes("gas station"))) {
      return 95;
    } else if ((loc.includes("ware"))) {
      return 96;
    } else if ((loc.includes("office building"))) {
      return 97;
    } else if ((loc.includes("hotel")) || (loc.includes("resort")) || (loc.includes("bed and breakfast")) || (loc.includes("motel"))) {
      return 98;
    } else if ((loc.includes("service area")) || (loc.includes("trade area")) || (loc.includes("bank")) || (loc.includes("laundromat")) || (loc.includes("CN tower")) || (loc.includes("funeral home")) || (loc.includes("vet")) || (loc.includes("car wash")) || (loc.includes("legion")) || (loc.includes("salon"))) {
      return 109;
    } else if ((loc.includes("bush")) || (loc.includes("remote")) || (loc.includes("undeveloped")) || (loc.includes("snowmobile trail")) || (loc.includes("swamp"))) {
      return 141;
    } else if ((loc.includes("railway tracks"))) {
      return 142;
    } else if ((loc.includes("camping ground")) || (loc.includes("trailer park"))) {
      return 143;
    } else if ((loc.includes("on board a vehicle")) || (loc.includes("train")) || (loc.includes("plane")) || (loc.includes("car")) || (loc.includes("ship"))) {
      return 144;
    } else if ((loc.includes("unspecified"))) {
      return 145;
    } else if ((loc.includes("cemetery")) || (loc.includes("scrapyard")) || (loc.includes("dump"))) {
      return 149;
    } else if ((loc.includes("lake")) || (loc.includes("pond")) || (loc.includes("river")) || (loc.includes("day camp")) || (loc.includes("summer camp"))) {
      return 150;
    } else if ((loc.includes("institutional home")) || (loc.includes("group home")) || (loc.includes("halfway")) || (loc.includes("shelter"))) {
      return 31;
    } else if ((loc.includes("home for elderly")) || (loc.includes("nursing home")) || (loc.includes("retirement home"))) {
      return 32;
    } else if ((loc.includes("prison")) || (loc.includes("detention for youth")) || (loc.includes("detention for adults"))) {
      return 33;
    } else if ((loc.includes("residential institution")) || (loc.includes("ronald macdonald house"))) {
      return 39;
    } else if ((loc.includes("amusement park")) || (loc.includes("zoo")) || (loc.includes("ontario place")) || (loc.includes("fair")) || (loc.includes("knott's berry farm"))) {
      return 61;
    } else if ((loc.includes("public park")) || (loc.includes("provincial park")) || (loc.includes("national park")) || (loc.includes("conservation area")) || (loc.includes("peggy's cove")) || (loc.includes("fort henry")) || (loc.includes("mount-royal"))) {
      return 62;
    } else if (loc.includes("aquatic recreation centre") || loc.includes("water park") || loc.includes("wave pool") || loc.includes("community pool")) {
      return 63;
    } else if (loc.includes("stadium") || loc.includes("arena") || loc.includes("civic centre") || loc.includes("corel centre") || loc.includes("bell centre")) {
      return 64;
    } else if (loc.includes("community centre") || loc.includes("YMCA")) {
      return 65;
    } else if (loc.includes("fitness training club") || loc.includes("fitness facility") || loc.includes("martial arts") || loc.includes("dance studio") || loc.includes("gymnastics club") || loc.includes("ballet")) {
      return 66;
    } else if (loc.includes("race track") || loc.includes("horse") || loc.includes("motorcycle") || loc.includes("cart") || loc.includes("go-kart") || loc.includes("motocross camp")) {
      return 67;
    } else if (loc.includes("golf course") || loc.includes("facility for land-based sport") || loc.includes("equestrian centre") || loc.includes("rodeo grounds")) {
      return 68;
    } else if (loc.includes("marina") || loc.includes("yacht club") || loc.includes("kayak club") || loc.includes("fishing lodge")) {
      return 69;
    } else if (loc.includes("ski hill") || loc.includes("rideau canal") || loc.includes("skin cabin") || loc.includes("rink")) {
      return 70;
    } else if (loc.includes("skate park")) {
      return 71;
    } else if (loc.includes("bowling alley") || loc.includes("facility for recreation") || loc.includes("pool hall") || loc.includes("arcade") || loc.includes("bingo hall") || loc.includes("cosmic adventures") || loc.includes("boys and girls club")) {
      return 79;
    } else if (loc.includes("highway")) {
      return 81;
    } else if (loc.includes("road") || loc.includes("lane") || loc.includes("alley") || loc.includes("bus stop") || loc.includes("bridge")) {
      return 82;
    } else if (loc.includes("construction site") || loc.includes("demolition site")) {
      return 111;
    } else if (loc.includes("factory") || loc.includes("mill") || loc.includes("manufactur")) {
      return 112;
    } else if (loc.includes("industrial") || loc.includes("construction area")) {
      return 119;
    } else if (loc.includes("mine") || loc.includes("oil well") || loc.includes("gas well") || loc.includes("quarry") || loc.includes("sandpit")) {
      return 121;
    } else if (loc.includes("farm") && !loc.includes("farm-house") && !loc.includes("barn") && !loc.includes("chicken coop")) {
      return 131;
    } else {
      return null;
    }
  }
  
  
  function areaCodeFromPlace(area: string): number | null {
    area = area.toLowerCase();
  
    if (area.includes("bathroom") || area.includes("toilet") || (area.includes("change room") && !area.includes("sports")) || area.includes("washroom")) {
      return 11;
    } else if (area.includes("bedroom")) {
      return 12;
    } else if (area.includes("classroom") || area.includes("daycare indoors")) {
      return 13;
    } else if (area.includes("dorm") || area.includes("worker's quarters") || area.includes("ward")) {
      return 14;
    } else if (area.includes("hall") || area.includes("foyer") || area.includes("waiting room") || area.includes("emergency room")) {
      return 15;
    } else if (area.includes("kitchen")) {
      return 16;
    } else if (area.includes("laundry")) {
      return 17;
    } else if (area.includes("dining") || area.includes("cafeteria")) {
      return 18;
    } else if (area.includes("living") || area.includes("family room") || area.includes("rec room") || area.includes("den")) {
      return 19;
    } else if (area.includes("office")) {
      return 20;
    } else if (area.includes("basement")) {
      return 21;
    } else if (area.includes("spectator") || area.includes("church") || area.includes("auditorium")) {
      return 22;
    } else if ((area.includes("garage") && !area.includes("parking")) || area.includes("carport")) {
      return 31;
    } else if (area.includes("workshop") || area.includes("separate building") || area.includes("separate rooom")) {
      return 32;
    } else if (area.includes("agricultural") || area.includes("dairy") || area.includes("silo") || area.includes("piggery")) {
      return 33;
    } else if (area.includes("stable") || area.includes("barn")) {
      return 34;
    } else if (area.includes("shed")) {
      return 35;
    } else if (area.includes("greenhouse") || area.includes("specialized")) {
      return 36;
    } else if (area.includes("escalator") || area.includes("elevator")) {
      return 41;
    } else if (area.includes("stair")) {
      return 42;
    } else if ((area.includes("porch") && !area.includes("under")) || area.includes("deck") || area.includes("balcony") || area.includes("verandah")) {
      return 43;
    } else if (area.includes("roof")) {
      return 44;
    } else if (area.includes("roadway") && area.includes("unpaved")) {
      return 52;
    } else if (area.includes("roadway") && area.includes("paved")) {
      return 51;
    } else if (area.includes("driveway")) {
      return 53;
    } else if (area.includes("parking")) {
      return 54;
    } else if (area.includes("sidewalk") || area.includes("bus stop")) {
      return 55;
    } else if (area.includes("median strip") || area.includes("traffic island")) {
      return 56;
    } else if (area.includes("tunnel") || area.includes("trench") || area.includes("ditch")) {
      return 57;
    } else if (area.includes("bike")) {
      return 58;
    } else if (area.includes("playground")) {
      return 59;
    } else if (area.includes("garden") || area.includes("yard")) {
      return 60;
    } else if (area.includes("pasture") || (area.includes("field") && !area.includes("sport")) || area.includes("animal area")) {
      return 61;
    } else if (area.includes("cliff") || area.includes("rock face")) {
      return 62;
    } else if (area.includes("trails")) {
      return 63;
    } else if (area.includes("gym") || area.includes("weight") || area.includes("fitness")) {
      return 71;
    } else if (area.includes("sports field") || area.includes("track")) {
      return 72;
    } else if (area.includes("court")) {
      return 73;
    } else if (area.includes("pool")) {
      return 74;
    } else if (area.includes("ice rink")) {
      return 75;
    } else if (area.includes("concrete rink")) {
      return 76;
    } else if (area.includes("locker") || area.includes("change room") || area.includes("sportsplex shower")) {
      return 77;
    } else if (area.includes("splash pad")) {
      return 78;
    } else if (area.includes("beach") || area.includes("shore") || area.includes("riverbank")) {
      return 81;
    } else if (area.includes("dam")) {
      return 82;
    } else if ((area.includes("river") && !area.includes("bank")) || area.includes("lake") || area.includes("creek") || area.includes("pond") || area.includes("swamp")) {
      return 83;
    } else if (area.includes("sea") || area.includes("ocean") || area.includes("estuary")) {
      return 84;
    } else if (area.includes("wharf") || area.includes("dock") || area.includes("pier")) {
      return 85;
    } else if (area.includes("exterior") || area.includes("crawlspace") || area.includes("dump") || area.includes("under porch")) {
      return 91;
    } else if (area.includes("interior") || area.includes("lab") || area.includes("cell") || area.includes("stage") || area.includes("storage")) {
      return 92;
    } else if (area.includes("unspecified")) {
      return 99;
    } else {
      return null;
    }
  }
  
  
  function processLocColumn(sheet: ExcelScript.Worksheet, placelocColumnIndex: number, locColumnIndex: number): void {
    const range = sheet.getUsedRange();
    const rowCount = range.getRowCount();
  
    for (let i = 1; i < rowCount; i++) {
      const placelocCell = range.getCell(i, placelocColumnIndex);
      const placelocCellValue = placelocCell.getValue() as string;
  
      if (placelocCellValue) {
        const locCode = locationCodeFromPlace(placelocCellValue);
        const locCell = range.getCell(i, locColumnIndex);
        locCell.setValue(locCode);
      }
    }
  }
  
  function processAreaColumn(sheet: ExcelScript.Worksheet, placeareaColumnIndex: number, areaColumnIndex: number): void {
    const range = sheet.getUsedRange();
    const rowCount = range.getRowCount();
  
    for (let i = 1; i < rowCount; i++) {
      const placeareaCell = range.getCell(i, placeareaColumnIndex);
      const placeareaCellValue = placeareaCell.getValue() as string;
  
      if (placeareaCellValue) {
        const areaCode = areaCodeFromPlace(placeareaCellValue);
        const areaCell = range.getCell(i, areaColumnIndex);
        areaCell.setValue(areaCode);
      }
    }
  }
  
  
  function main(workbook: ExcelScript.Workbook) {
    const sheet = workbook.getActiveWorksheet();
  
    const placelocColumnIndex = 14; // Replace with the index of the column you want to process
    const locColumnIndex = 12;
    processLocColumn(sheet, placelocColumnIndex, locColumnIndex);
  
    const placeareaColumnIndex = 15; // Replace with the index of the column you want to process
    const areaColumnIndex = 13;
    processAreaColumn(sheet, placeareaColumnIndex, areaColumnIndex);
  }
  
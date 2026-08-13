import uuid
from math import floor
import pandas as pd

from uuid import uuid4

def scramble_mrn(mrn):
    """
    takes the mrn value of the note and runs a simple scramble
    :param mrn: mrn
    :return: scrambled mrn
    """
    mrn = str(mrn).strip()
    last_digit = (int(mrn[-1]) + int(mrn[-2])) % 10
    return mrn[:-2] + mrn[-1] + mrn[-2] + str(last_digit)

def process_postal(postal):
    """
    remove the last 3 digits of postal code to increase privacy
    :param postal: postal code
    :return: truncated postal code
    """
    if type(postal) == str and len(postal) == 7 and postal[3] == " ":
        postal = str(postal).split(" ")[0]
    return postal

def calculate_age(arrival, dob):
    td = arrival - dob
    td = td.days
    td = int(td)
    age = floor(td / 365)
    return age

def process_ctas(CTAS):
    """
    process ctas from epic dumps
    :param CTAS: ctas
    :return: returns ctas that's processed
    """
    processed_ctas = ""
    if pd.isna(CTAS) or CTAS == "":
        processed_ctas = ""
    else:
        processed_ctas = int(CTAS)

    return processed_ctas

def process_sex(sex):
    """
    chang M/F to male, female
    :param sex:
    :return: sex
    """
    if sex.lower() == "male":
        sex = "M"
    elif sex.lower() == "female":
        sex = "F"
    else:
        sex = sex
    return sex

def get_report_note(df):
    """
    fill in the Notes column with some relevant information, this is a legacy function, not sure what the notes column
    entail in this case will need to clarify
    :param df: all notes for a specific visit determined by "Arrival Date" and "MRN"
    :return: string with relevant information
    """
    disposition = df["Disposition"].drop_duplicates().astype(str).tolist()[0].lower()
    texts = [str(text) for text in df["Note Text"].to_list()]
    merged_text = " ".join(texts)
    if disposition in [
        'admit',
        'deceased',
        'lama',
        'lwbr',
        'lwbs',
        'send to or',
        'transfer to another facility'
    ]:
        return disposition
    elif "Consults" in merged_text or 'Consult Follow Up' in merged_text:
        return "Consult"
    elif "ED Provider Notes" in df["Note Type"].tolist():
        provider_notes = [str(text) for text in df["Note Text"][df["Note Type"] == "ED Provider Notes"].to_list()]
        provider_note = " ".join(provider_notes)
        idx = provider_note.lower().find("assessment and plan")
        if idx == -1:
            return ""
        return provider_note[idx:]
    else:
        return ""

def body_parts(dx):
    """
    take diagnosis and extract body parts
    :param dx: diagnosis string
    """

    # for specific case of foreign body in soft tissue with no body part found
    noBp = False

    if (("foot" in dx and "phalan" not in dx) or ("metatarsal" in dx)) and ("toe" not in dx):
        return 560
    elif ((("head" in dx) and ("radial" not in dx and "forehead" not in dx)) or ("scalp" in dx) or ("skull" in dx)):
        return 110
    elif (("mandible" in dx) or ("face" in dx and "surface" not in dx) or ("eyelid" in dx) or ("periocular" in dx) or (
            "area" in dx) or (("ear" in dx) and ("forearm" not in dx) and ("frenulum" not in dx)) or ("nose" in dx) or (
                  "mouth" in dx) or ("jaw" in dx) or ("nasal" in dx)) or ("facial" in dx) or ("chin" in dx) or (
            "cheek" in dx) or ("eyebrow" in dx) or ("lip" in dx and "slipped" not in dx and "frenulum" not in dx) or (
            "forehead" in dx) or ("sinus" in dx) or ("orbital" in dx) or ("epistaxis" in dx) or (
            "nose" in dx and "bleed" in dx) or ("palsy" in dx) or ("tympanic" in dx and "membrane" in dx):
        return 120
    elif (("internal" in dx) and ("mouth" in dx)) or ("palate" in dx) or ("tongue" in dx) or (
            "tear" in dx and "frenulum" in dx and "lip" in dx):
        return 130
    elif ("neck" in dx) and (
            "femur" not in dx and "radial" not in dx and "fibula" not in dx and "tibula" not in dx and "fib" not in dx and "tib" not in dx and "tibia" not in dx):
        return 140
    elif (("upper" in dx or "impact" in dx) and ("esophag" in dx)) or ("trachea" in dx) or ("pharyngeal" in dx) or (
            "laryngeal" in dx):
        return 141
    elif ("cervical" in dx):
        return 210
    elif ("thoracic" in dx):
        return 220
    elif ("lumbar" in dx):
        return 230
    elif (("sacrum" in dx) or ("coccyx" in dx)):
        return 240
    elif ("spine" in dx):
        return 250
    elif (("thorax" in dx) or ("ribs" in dx) or ("lungs" in dx) or ("armpits" in dx) or ("lower esophagus" in dx) or (
            "trachea" in dx) or ("chest" in dx) or ("aspirat" in dx)):
        return 310
    elif ("upper back" in dx) or ("trapeziu" in dx):
        return 315
    elif ("abdom" in dx) or ("colon" in dx) or ("foreign" in dx and ("ingestion" in dx or "intestine" in dx)) or (
            "stomach" in dx) or ("kidney" in dx) or (
            "sple" in dx and "cyst" not in dx and "splenomegaly" not in dx and "disease" not in dx) or (
            "gastrointestinal tract" in dx) or ("liver" in dx):
        return 321
    elif ("lower back" in dx) or ("flank" in dx):
        return 322
    elif (("pelvis" in dx) or ("bladder" in dx) or ("buttocks" in dx) or ("rectum" in dx) or ("vagina" in dx) or (
            "anal" in dx)):
        return 323
    elif (("penis" in dx) or ("circumcision" in dx) or ("penile" in dx) or ("scrot" in dx) or ("testic" in dx)):
        return 324
    elif ("groin" in dx):
        return 325
    elif ("back" in dx):
        return 330
    elif (("shoulder" in dx) or ("scapula" in dx)) or ("proximal" in dx and ("humerus" in dx or "humeral" in dx)):
        return 410
    elif ("clavic" in dx):
        return 415
    elif ((
                  "upper arm" in dx or "humerus" in dx or "humeral" in dx) and "condyl" not in dx and "distal" not in dx and "proximal" not in dx):
        return 420
    elif ("elbow" in dx) or ("distal" in dx and ("humerus" in dx or "humeral" in dx)) or ("condyl" in dx) or (
            "radial" in dx and ("head" in dx or "neck" in dx)) or ("ulna" in dx and ("head" in dx or "neck" in dx)) or (
            "olecranon" in dx) or ("proximal" in dx and ("radius" in dx or "radial" in dx or "ulna" in dx)):
        return 430
    elif ((("forearm" in dx) or ("radius" in dx) or ("ulna" in dx)) or ("monteggia" in dx) or (
            "lower" in dx and "arm" in dx) or ("radial" in dx)) and (
            "distal" not in dx and "proximal" not in dx and "upper" not in dx):
        return 440
    elif ((("wrist" in dx) or ("carpal" in dx)) and ("metacarpal" not in dx)) or (
            "distal" in dx and ("radius" in dx or "radial" in dx or "ulna" in dx)) or "scaphoid" in dx or (
            "forearm" in dx and "lower" in dx):
        return 450
    elif (("hand" in dx and "phalan" not in dx) or ("metacarpal" in dx)) or ("boxer" in dx):
        return 460
    elif (("finger" in dx) or ("thumb" in dx) or "phalan" in dx) and ("foot" not in dx or "toe" not in dx):
        return 470
    elif ("hip" in dx) or (
            ("neck" in dx) and ("femur" in dx) or ("proximal" in dx and ("femur" in dx or "femoral" in dx))) or (
            "fem" in dx and "neck" in dx) or ("slipped" in dx and "femoral" in dx):
        return 510
    elif (("thigh" in dx) or ("distal" not in dx and "proximal" not in dx and ("femur" in dx or "femoral" in dx))):
        return 520
    elif (("knee" in dx) or ("patella" in dx) or ("distal" in dx and ("femur" in dx or "femoral" in dx)) or (
            ("proximal" in dx) and ("tibia" in dx or "fibula" in dx)) or ("tibia" in dx and "plateau" in dx)):
        return 530
    elif (("lower leg" in dx) or ("tibia" in dx) or ("fibula" in dx)) and ("distal" not in dx and "proximal" not in dx):
        return 540
    elif (("ankle" in dx) or ("tarsal" in dx) or (("distal" in dx) and ("tibia" in dx or "fibula" in dx))) or (
            "tillaux" in dx):
        return 550
    elif ("toe" in dx or "phalan" in dx):
        return 570
    else:
        noBP = True
    # For specific soft tissue foreign body case
    if ("foreign" in dx or "fb" in dx) and noBP != True:
        return False


# TODO same as body parts
def injuries(dx):
    """
    extract injury type from the diagnosis, then the body part depending will come from the body_parts function
    :param dx: diagnosis string
    """
    no = None
    bp = None

    if (("facial" in dx or "skull" in dx) and "fracture" in dx):
        no = 42
        bp = 135
    elif ("subungual" in dx and "hematoma" in dx):
        no = 10
        bp = body_parts(dx)

    if (("abrasion" in dx) and (
            "globe" not in dx and "cornea" not in dx and "eye" not in dx and "ocular" not in dx and "canal" not in dx)) or (
            ("bruis" in dx or "contusion" in dx or (
                    "hematoma" in dx and "subdural" not in dx)) and "subungual" not in dx) or (
            ("superficial" in dx) and (
            "cut" not in dx and "laceration" not in dx and "burn" not in dx and "swelling" not in dx)) and (
            ("kidney" not in dx) or ("spleen" not in dx) or ("splenic" not in dx)) or (
            "abrasion" in dx and "eyelid" in dx):
        no = 10
        bp = body_parts(dx)
    elif (("open wound" in dx or "laceration" in dx or ("minor" in dx and "cut" in dx) or (
            "nail" in dx and "avulsion" in dx) or ("circumcision" in dx)) or ("fissure" in dx) or (
                  "epistaxis" in dx) or ("self" in dx and "cut" in dx) or ("dehiscence" in dx and "wound" in dx) or (
                  "nose" in dx and "bleed" in dx)) and (("liver" not in dx) and ("splenic" not in dx)) or (
            "tear" in dx and "frenulum" in dx and "lip" in dx):
        no = 11
        bp = body_parts(dx)
    elif (("fracture" in dx or "fx" in dx or "broken" in dx) and ("tooth" not in dx and "patholog" not in dx)):
        no = natureOfInjury = 12
        bp = body_parts(dx)
    elif ("dislocation" in dx or "subluxation" in dx or ("slipped" in dx and "femoral" in dx)):
        no = natureOfInjury = 13
        bp = body_parts(dx)
    elif ("sprain" in dx or "strain" in dx):
        no = 14
        bp = body_parts(dx)
    elif ("nerve" in dx or "palsy" in dx) and ("oedema" not in dx):
        no = 15
        bp = body_parts(dx)
    elif "blood vessel" in dx or "subungual" in dx:
        no = 16
        bp = body_parts(dx)
    elif ("tendon" in dx or "muscle" in dx) and ("injury" in dx or "rupture" in dx or "sever" in dx):
        no = 17
        bp = body_parts(dx)
    elif "crush" in dx:
        no = 18
        bp = body_parts(dx)
    elif "amputation" in dx:
        no = 19
        bp = body_parts(dx)
    elif (("burn" in dx or "corrosion" in dx) and (
            "globe" not in dx and "cornea" not in dx and "eye" not in dx and "ocular" not in dx)):
        no = 20
        bp = body_parts(dx)
    elif "frostbite" in dx:
        no = 21
        bp = body_parts(dx)
    elif (("bite" in dx and "insect" not in dx) or (
            "dog" in dx or "squirrel" in dx or "racoon" in dx or "cat" in dx or "human" in dx) and "medication" not in dx and "complication" not in dx):
        no = 22
        bp = body_parts(dx)
    elif "electric" in dx:
        no = 23
        bp = body_parts(dx)
    elif ((
                  "corrosion" in dx or "chemical" in dx or "injur" in dx or "burn" in dx or "abrasion" in dx or "trauma" in dx or "hyphema" in dx) and (
                  "globe" in dx or "cornea" in dx or "eye" in dx or "ocular" in dx)) or (
            ("eye" in dx or "ocular" in dx) and "pain" in dx) or ("visual" in dx and "disturbance" in dx) or (
            "conjunctival" in dx and ("haemorrhage" in dx or "hemorrhage" in dx)):
        no = 24
        bp = 135
    elif (("dental" in dx or "tooth" in dx or "teeth" in dx) and (
            "injury" in dx or "fracture" in dx or "trauma" in dx or "chip" in dx or "pain" in dx or "implant" in dx or "device" in dx or "avulsion" in dx or "impact" in dx)):
        no = 25
        bp = 135
    elif (("kidney" in dx) or ("spleen" in dx) or ("splenic" in dx) or ("ear" in dx and "canal" in dx) or (
            "liver" in dx) and ("injury" in dx or "abrasion" in dx or "laceration" in dx)) or (
            "perforated tympanic membrane" in dx):
        no = 26
        bp = body_parts(dx)
    elif (("pain" in dx and "sickle" not in dx and "disorder" not in dx) or (
            "soft" in dx and "tissue" in dx and "cyst" not in dx and "mass" not in dx) or (
                  "swelling" in dx and "eye" not in dx) or ("testicular" in dx and "torsion" in dx) or (
                  "injury" in dx)) and ("infection" not in dx and "foreign" not in dx and "fb" not in dx):
        no = 27
        bp = body_parts(dx)
    elif ("foreign" in dx and ("globe" in dx or "cornea" in dx or "eye" in dx or "ocular" in dx)):
        no = 31
        bp = 135
    elif ((("foreign" in dx) and "ear" in dx or (
            "auditory" in dx and "hallucination" not in dx)) and "earlobe" not in dx) or ("fb" in dx and "ear" in dx):
        no = 32
        bp = 135
    elif ("foreign" in dx or "fb" in dx) and (
            "nose" in dx or "nasal" in dx or "nostril" in dx or "sinus" in dx or "nare" in dx):
        no = 33
        bp = 135
    elif (("foreign" in dx or "fb" in dx) and (
            "respira" in dx or "aspiration" in dx or "choking" in dx or "air" in dx or "laryngeal" in dx)) or (
            "gagging" in dx):
        no = 34
        bp = body_parts(dx)
    elif ("foreign" in dx or "fb" in dx) and (
            "pharyngeal" in dx or "intestine" in dx or "digestive" in dx or "stomach" in dx or "ingestion" in dx or "colon" in dx or "alimentary" in dx or "esophag" in dx or "swallow" in dx) or (
            "impaction" in dx and "esophagus" in dx):
        no = 35
        bp = body_parts(dx)
    elif (("foreign" in dx and "genito-urinary" in dx) or ("foreign" in dx and "bladder" in dx) or (
            "foreign" in dx and "penis" in dx) or ("foreign" in dx and "urethra" in dx) or (
                  "foreign" in dx and "vagina" in dx)):
        no = 36
        bp = body_parts(dx)
    elif ("foreign" in dx or "fb" in dx) and (
            "soft" in dx or "earlobe" in dx or "skin" in dx or (body_parts(dx) != False)) or ("splinter" in dx):
        no = 37
        bp = body_parts(dx)
    elif ("minor" in dx and "head" in dx) or ("head" in dx and "injury" in dx) or ("head" in dx and "trauma" in dx):
        no = 41
        bp = 135
    elif "concussion" in dx:
        no = 42
        bp = 135
    elif ("intracranial" in dx) or (
            "brain" in dx and ("tumor" not in dx and "tumour" not in dx and "cancer" not in dx)) or (
            "subarachnoid" in dx) or ("subdural" in dx and "hematoma" in dx) or (
            ("intraventricular" in dx) and ("haemorrhage" in dx or "hemorrhage" in dx)):
        no = 43
        bp = 135
    elif ("poison" in dx or "toxic" in dx or "overdose" in dx or "ingestion" in dx):
        no = 50
        bp = 900
    elif ("drown" in dx or "immersion" in dx):
        no = 51
        bp = 900
    elif ("asphyxia" in dx) or ("choking" in dx):
        no = 52
        bp = 900
    elif ("overexertion" in dx or ("heat" in dx and "stress" in dx) or ("cold" in dx and "stress" in dx)):
        no = 53
        bp = 900
    elif ("no" in dx and "injury" in dx and "nose" not in dx):
        no = 70
        bp = 900
    elif ("mania" in dx) or ("depressi" in dx) or ("aggressi" in dx) or ("psychosis" in dx) or (
            "tic" in dx and len(dx) == 3) or (
            ("stress" in dx or "anxiety" in dx) and ("fracture" not in dx and "respira" not in dx)) or (
            "overdose" in dx) or ("hallucination" in dx) or ("anorexia" in dx) or ("poison" in dx) or (
            "intoxication" in dx) or ((
                                              "medication" in dx or "anger" in dx or "night" in dx or "behavi" in dx or "mental" in dx or "disorder" in dx or "social" in dx or "sleep" in dx or "learning" in dx or "mood" in dx or "weight" in dx) and (
                                              "adjustment" in dx or "management" in dx or "terror" in dx or "reaction" in dx or "depressed" in dx or "concern" in dx or "bizarre" in dx or "mood" in dx or "food" in dx or "conversion" in dx or "eat" in dx or "depress" in dx or "motor" in dx or "tic" in dx or "compulsive" in dx or "problem" in dx or "change" in dx or "health" in dx or "abnormal" in dx or "aggressive" in dx or "disturbance" in dx or "difficult" in dx or "change" in dx or "loss" in dx)) or (
            ("tic" in dx) and ("facial" in dx or "simple" in dx)) or ("suicid" in dx) or ("violent" in dx) or (
            "ocd" in dx) or ("drug" in dx and "ingestion" in dx) or ("self" in dx and "harm" in dx) or (
            "panic" in dx) or ("emotional" in dx) or ("disruptive" in dx) or ("temper" in dx) or (
            "food" in dx and "refusal" in dx) or ("banging" in dx) or (
            "behavi" in dx and ("change" in dx or "concern" in dx)) and ("neurologic" not in dx) or (
            ("mental" in dx or "behavi" in dx) and "disorder" in dx):
        no = 71
        bp = 900
    elif ("pulled" in dx and "elbow" in dx) or ("nursemaid" in dx):
        no = 75
        bp = 430
    elif "caustic" in dx:
        no = 76
        bp = body_parts(dx)
    elif (("stab" in dx and "instability" not in dx) or "bullet" in dx or "penetrat" in dx):
        no = 77
        bp = body_parts(dx)
    elif ("injury" in dx or "trauma" in dx):
        bp = body_parts(dx)

    if ("tibia" in dx and "fibula" in dx):
        no = natureOfInjury
        bp = body_parts(dx)

    return no, bp

def get_disposition(merged_notes, disposition, no1, bp1):
    """
    return the disposition that is defined in the chirpp requirements, some of these are very hard to figure out
    and those are ignored for the time being
    :param merged_notes: merged notes from the raw files, this is a long piece of text
    :param disposition: disposition from the raw files, this contains some of the codes that we are using in chirpp
    :return: an integer that is the chirpp disp code
    """
    if disposition in ["LAMA", "LBT2", "LWBR", "LWBS"]:
        disp_code = 1
    elif disposition in ["Admit", "Transfer to Another Facility", "Send to OR", "Send to Clinic"]:
        if no1 == 71 and bp1 == 900:
            disp_code = 8
        else:
            disp_code = 7
    elif disposition == "Deceased":
        disp_code = 9
    elif "consult" in merged_notes or "consult follow up" in merged_notes.lower():
        disp_code = 6
    else:
        disp_code = None

    return disp_code


def get_patients(inference_notes):
    patients = inference_notes[["MRN", "Date of Birth"]].drop_duplicates()
    patients["Date of Birth"] = pd.to_datetime(patients["Date of Birth"])
    patients["scrmrn"]=patients["MRN"].apply(scramble_mrn)
    return patients

def get_visit_notes(inference_notes):
    merged_grouped = inference_notes.groupby("CSN")
    notes=[]
    for csn, data in merged_grouped:
        notes.append({"CSN":csn, "notes":get_report_note(data)})
    notes=pd.DataFrame(notes)
    #notes["CSN"]=notes["CSN"].astype(int)
    return notes


#the notes colum does not contain the doctors notes but these are notes for the chirpp team.
def get_visits(raw_notes, processed_notes, note_types):
    raw_notes = raw_notes[~pd.isna(raw_notes["Note Text"])]

    visits = raw_notes[["CSN", "Sex", "MRN", "Arrival Date", "Date of Birth", "Arrival Time", "Postal Code",
                          "Chief Complaint", "Diagnosis", "Disposition", "CTAS", "Address", "City", "LOS",
                          "Province"]].drop_duplicates()

    visits["Arrival Date"] = pd.to_datetime(visits["Arrival Date"])
    visits["Date of Birth"] = pd.to_datetime(visits["Date of Birth"])

    ages = []
    for arrival, dob in zip(visits["Arrival Date"].tolist(), visits["Date of Birth"].tolist()):
        ages.append(calculate_age(arrival, dob))
    visits["age"] = ages
    visits = visits.drop(columns=["Date of Birth"])
    visits["day_of_week"] = visits["Arrival Date"].dt.day_name()

    for_narrative = raw_notes[raw_notes["Note Type"].isin(note_types)]
    for_narrative["Note Type"] = pd.Categorical(for_narrative["Note Type"],
                                                categories=note_types)

    for_narrative = for_narrative.sort_values(by="Note Type")
    for_narrative_grouped=for_narrative.groupby("CSN")
    narratives=[]
    for csn, group in for_narrative_grouped:
        narrative = []
        for note_type, note_text in zip(group["Note Type"].tolist(), group["Note Text"].tolist()):
            if not pd.isna(note_text):
                narrative.append(str(note_type) + "\n\n" + str(note_text))
        narrative = "\n\n".join(narrative)
        narratives.append({"CSN":csn, "sk_narrative":narrative})

    narratives=pd.DataFrame(narratives)
    visits=visits.merge(narratives, how="inner", on="CSN")
    # some touchups requested by the chirpp team

    visits["Sex"]=visits["Sex"].apply(process_sex)
    visits["CTAS"]=visits["CTAS"].apply(process_ctas)
    notes=get_visit_notes(raw_notes)
    visits=visits.merge(notes, how="inner", on="CSN")
    visits=visits.merge(processed_notes[["CSN", "probs"]], how="left", on="CSN")

    visits = visits.rename(columns={"CSN": "csn", "Sex": "sex", "MRN": "mrn",
                                    "Arrival Date": "arrival_date",
                                    "Arrival Time": "arrival_time",
                                    "Postal Code": "postal_code",
                                    "Chief Complaint": "chief_complaint",
                                    "Diagnosis": "diagnosis",
                                    "Disposition": "disposition", "LOS": "los",
                                    "CTAS": "ctas", "Address": "address", "City": "city",
                                    "Province": "province"})
    return visits


def get_referrals(inference_notes):
    referrals = inference_notes[["CSN", "Referral Order"]].dropna().drop_duplicates()
    referrals = referrals.rename(columns={"CSN": "csn", "Referral Order": "referrals"})
    referrals = referrals[referrals["referrals"] != ""]
    return referrals

# now these are the doctor notes for a specific patient, this can be just one thing or pages and pages of notes
# it really depends on why that patient is there
def get_epic_notes(inference_notes):
    if "Note ID" in inference_notes.columns:
        notes_df = inference_notes[
            ["CSN", "Note Type", "Author Type", "Author's Service", "Note Text", "LINE", "Note ID"]].drop_duplicates()
        notes_grouped = notes_df.groupby(["Note ID"])

        notes_merged = []
        for _, group in notes_grouped:
            df = group[["CSN", "Note Type", "Author Type", "Author's Service", ]].drop_duplicates()
            note_text = " ".join(
                [str(x) for x in
                 group.sort_values(by=["LINE"], ignore_index=True)["Note Text"].tolist()])
            df["Note Text"] = note_text
            notes_merged.append(df)
        notes_df = pd.concat(notes_merged)

    else:
        notes_df = inference_notes[
            ["CSN", "Note Type", "Author Type", "Author Service", "Note Text"]].drop_duplicates()

    notes_df = notes_df.rename(columns={"CSN": "csn", "Note Type": "note_type",
                                       "Author Type": "author_type",
                                       "Author's Service": "author_service",
                                       "Note Text": "note_text", })
    notes_df["id"]=[uuid4() for i in range(notes_df.shape[0])]

    return notes_df

def get_problems(inference_notes):
    problems = inference_notes[["CSN", "Problem List"]].drop_duplicates().dropna()
    problems['Problem List'] = [str(x).split(',') for x in problems['Problem List'].dropna()]
    problems = problems.explode("Problem List")
    problems = problems[problems["Problem List"] != " "]
    problems["Problem List"] = problems["Problem List"].str.replace("^ ", "", regex=True)
    problems = problems.rename(columns={"CSN": "csn", "Problem List": "problem"})
    problems=problems[problems["problem"]!=""]
    return problems


def get_summaries(inference_notes):
    summaries=inference_notes[["CSN", "phac_narrative", "phac_embeddings"]]
    summaries=summaries.rename(columns={"CSN":"csn"})
    summaries["version"]=1
    return summaries


def get_chunked_notes(notes, inference, small=True):
    """
    :param notes: notes are the same dataframe from the get_epic_notes function,
    :param inference: chirpp.inference.Inference class instance
    :return:
    """
    note_chunks = []
    chunks = inference.chunk(notes["note_text"])
    for idx, chunk in zip(notes["id"], chunks):
        chunk_numbers = list(range(len(chunk)))
        chunk_df = pd.DataFrame({"chunk_number": chunk_numbers, "chunk_text": chunk})
        chunk_df["note_id"] = idx
        note_chunks.append(chunk_df)

    note_chunks = pd.concat(note_chunks)
    embeddings = inference.embed(note_chunks["chunk_text"].tolist(), small=small)
    note_chunks["embeddings"] = embeddings
    return note_chunks

def get_processed_notes(processed_notes):
    processed_notes=processed_notes[["CSN", "processed_notes", "processed_embeddings", "is_chirpp"]]
    processed_notes=processed_notes.rename(columns={"CSN": "csn"})
    return processed_notes


def get_cases(processed_notes, visits):
    cols = ['csn', 'intent', 'sub', 'sub_id',
            'i_o', 'location', 'area', 'injury_date', 'injury_hour', 'injury_min',
            'am_pm', 'sports_code', 'sd1', 'sd2', 'sd3', 'sd4', 'sd5', 'veh',
            'veh_p', 'place', 'w4p', 'no1', 'bp1', 'no2', 'bp2', 'no3', 'bp3',
            'disp']

    processed_notes = processed_notes.rename(columns={"CSN": "csn"})
    cases = processed_notes[processed_notes["is_chirpp"]]
    joined = cases.merge(visits[["csn", "chief_complaint", "diagnosis", "disposition", "notes"]], on="csn", how="inner")

    complaints = joined["chief_complaint"]
    diagnosis = joined["diagnosis"]
    disposition = joined["disposition"]
    notes = joined["notes"]

    no1s = []
    bp1s = []
    disps = []

    for complaint, note, diag, disp in zip(complaints, notes, diagnosis, disposition):
        diag = str(diag).lower()
        if complaint == "Medical Device Problem":
            no1 = 99
            bp1 = 999
        else:
            no1, bp1 = injuries(diag)
        report_disposition = get_disposition(note, disp, no1, bp1)

        no1s.append(no1)
        bp1s.append(bp1)
        disps.append(report_disposition)

    #TODO there are some issues with this and couple of other columns that needs to be fixed here
    for i in range(joined.shape[0]):
        if joined["i_o"].iloc[i] == "1" or joined["i_o"].iloc[i] == 1:
            joined["i_o"].iloc[i] = "I"
        elif joined["i_o"].iloc[i] == "2" or joined["i_o"].iloc[i] == 2:
            joined["i_o"].iloc[i] = "O"
        elif joined["i_o"].iloc[i] == "0" or joined["i_o"].iloc[i] == 0:
            joined["i_o"].iloc[i] = None
        else:
            joined["i_o"].iloc[i] = None

        if joined["am_pm"][i] == "1" or joined["am_pm"][i] == 1:
            joined["am_pm"][i] = "a"
        elif joined["am_pm"][i] == "2" or joined["am_pm"][i] == 2:
            joined["am_pm"] = "p"

    joined["injury_min"]=joined["injury_min"].str.replace(".", "")
    joined["injury_min"][joined["injury_min"] == ""] = None

    joined["injury_min"][~pd.isna(joined["injury_min"])] = joined["injury_min"][
        ~pd.isna(joined["injury_min"])].astype(int)

    dates = joined["injury_date"].tolist()
    for i in range(len(dates)):
        if dates[i] is None:
            continue
        else:
            try:
                int(dates[i])
            except:
                dates[i] = None

    joined["injury_date"] = dates

    joined["no1"] = no1s
    joined["bp1"] = bp1s
    joined["disp"] = disps

    # some manual touchups
    joined["area"][joined["phac_narrative"].str.contains("monkey bar")] = 59
    joined["i_o"][joined["phac_narrative"].str.contains("laminate floor")] = "I"
    joined["i_o"][joined["phac_narrative"].str.contains("snow")] = "O"
    joined["i_o"][joined["phac_narrative"].str.contains("washroom")] = "I"
    joined["i_o"][joined["phac_narrative"].str.contains("bathroom")] = "O"
    joined["i_o"][joined["phac_narrative"].str.lower() == "pulled elbow"] = 3
    joined["i_o"][joined["no1"] == 71] = 16

    joined["no2"][(joined["no1"] == 12) & (joined["bp1"] == 110)] = 41
    joined["bp2"][(joined["no1"] == 12) & (joined["bp1"] == 110)] = 135
    joined["bp1"][joined["disp"] == 1] = 999
    joined["no1"][joined["disp"] == 1] = 99
    joined["intent"][joined["no1"] == 71] = 16
    joined["no2"][joined["diagnosis"].astype(str).str.lower().str.contains("monteggia")] = 13
    joined["no2"][joined["diagnosis"].astype(str).str.lower().str.contains("monteggia")] = 430

    return joined[cols]








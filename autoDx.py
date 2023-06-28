import pandas

def bodyParts(diagnosis):
    """
    Function that matches the injury with the corresponding bodypart.

    Args:
        diagnosis (str): Discharge diagnosis of the patient

    Returns:
        The return value (int): The corresponding code for the body part that was injured

    Example usage:
        >>> bodyParts(Concussion)
        135
    
    Body Part Codes:
    - 560: Foot without toe
    - 110: Head (excluding forehead and radial)
    - 120: Facial regions (including face, eyelid, periocular area, ear, nose, mouth, jaw, and related conditions)
    - 130: Internal mouth regions (including internal mouth, palate, and tongue)
    - 140: Neck (excluding femur, radial, fibula, tibula, fib, tib, tibia)
    - 141: Upper esophagus and trachea
    - 210: Cervical region
    - 220: Thoracic region
    - 230: Lumbar region
    - 240: Sacrum or coccyx
    - 250: Spine
    - 310: Thorax (including ribs, lungs, armpits, lower esophagus, trachea, chest, aspiration)
    - 315: Upper back
    - 321: Abdomen (including colon, foreign body ingestion, stomach, kidney, and related conditions)
    - 322: Lower back or flank
    - 323: Pelvis (including bladder, buttocks, rectum, vagina, anal)
    - 324: Male genitalia (including penis, circumcision, penile, scrotum, testicles)
    - 325: Groin
    - 330: Back
    - 410: Shoulder or scapula
    - 415: Clavicle
    - 420: Upper arm (excluding condyle, distal, and proximal)
    - 430: Elbow (including distal humerus, condyle, radial head, neck, ulna, olecranon, and proximal radius or ulna)
    - 440: Forearm (including radius, ulna, Monteggia, lower arm, radial; excluding distal, proximal, and upper)
    - 450: Wrist or carpal (excluding metacarpal; including distal radius, radial, ulna, scaphoid, forearm lower)
    - 460: Hand without finger (including metacarpal; excluding phalanx)
    - 470: Finger or thumb (including phalanx; excluding foot or toe)
    - 510: Hip (including neck and proximal femur; excluding slipped femoral)
    - 520: Thigh (including femur and proximal or distal femur; excluding knee, patella, and tibia plateau)
    - 530: Knee (including patella, distal femur, proximal tibia or fibula, and tibia plateau)
    - 540: Lower leg (including tibia and fibula; excluding distal or proximal)
    - 550: Ankle or tarsal (including distal tibia or fibula)
    - 570: Toe or phalanx
    """
    
    #Makes all diagnoses lowercase for consistency
    dx = diagnosis.lower()

    #for specific case of foreign body in soft tissue with no body part found
    noBp = False

    if (("foot" in dx and "phalan" not in dx) or ("metatarsal" in dx)) and ("toe" not in dx):
        return 560
    elif ((("head" in dx) and ("radial" not in dx and "forehead" not in dx)) or ("scalp" in dx) or ("skull" in dx)):
        return 110
    elif (("face" in dx) or ("eyelid" in dx) or ("periocular" in dx) or ("area" in dx) or (("ear" in dx) and ("forearm" not in dx)) or ("nose" in dx) or ("mouth" in dx) or ("jaw" in dx) or ("nasal" in dx)) or ("facial" in dx) or ("chin" in dx) or ("cheek" in dx) or ("eyebrow" in dx) or ("lip" in dx and "slipped" not in dx) or ("forehead" in dx) or ("sinus" in dx) or ("orbital" in dx) or ("epistaxis" in dx) or ("nose" in dx and "bleed" in dx) or ("palsy" in dx):
        return 120
    elif (("internal" in dx) and ("mouth" in dx)) or ("palate" in dx) or ("tongue" in dx):
        return 130
    elif ("neck" in dx) and ("femur" not in dx and "radial" not in dx and "fibula" not in dx and "tibula" not in dx and "fib" not in dx and "tib" not in dx and "tibia" not in dx):
        return 140
    elif (("upper" in dx) and ("esophag" in dx)) or ("trachea" in dx):
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
    elif (("thorax" in dx) or ("ribs" in dx) or ("lungs" in dx) or ("armpits" in dx) or ("lower esophagus" in dx) or ("trachea" in dx) or ("chest" in dx) or ("aspirat" in dx)):
        return 310
    elif ("upper back" in dx):
        return 315
    elif ("abdom" in dx) or ("colon" in dx) or ("foreign" in dx and "ingestion" in dx) or ("stomach" in dx) or ("kidney" in dx) or ("sple" in dx and "cyst" not in dx and "splenomegaly" not in dx and "disease" not in dx):
        return 321
    elif ("lower back" in dx) or ("flank" in dx):
        return 322
    elif (("pelvis" in dx) or ("bladder" in dx) or ("buttocks" in dx) or ("rectum" in dx) or ("vagina" in dx) or ("anal" in dx)):
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
    elif (("upper arm" in dx or "humerus" in dx or "humeral" in dx) and "condyl" not in dx and "distal" not in dx and "proximal" not in dx):
        return 420
    elif ("elbow" in dx) or ("distal" in dx and ("humerus" in dx or "humeral" in dx)) or ("condyl" in dx) or ("radial" in dx and ("head" in dx or "neck" in dx)) or ("ulna" in dx and ("head" in dx or "neck" in dx)) or ("olecranon" in dx) or ("proximal" in dx and ("radius" in dx or "radial" in dx or "ulna" in dx)):
        return 430
    elif ((("forearm" in dx) or ("radius" in dx) or ("ulna" in dx)) or ("monteggia" in dx) or ("lower" in dx and "arm" in dx) or ("radial" in dx)) and ("distal" not in dx and "proximal" not in dx and "upper" not in dx):
        return 440
    elif ((("wrist" in dx) or ("carpal" in dx)) and ("metacarpal" not in dx)) or ("distal" in dx and ("radius" in dx or "radial" in dx or "ulna" in dx)) or "scaphoid" in dx or ("forearm" in dx and "lower" in dx):
        return 450
    elif (("hand" in dx and "phalan" not in dx) or ("metacarpal" in dx)) or ("boxer"in dx):
        return 460
    elif (("finger" in dx) or ("thumb" in dx) or "phalan" in dx) and ("foot" not in dx or "toe" not in dx):
        return 470
    elif ("hip" in dx) or (("neck" in dx) and ("femur" in dx) or ("proximal" in dx and ("femur" in dx or "femoral" in dx))) or ("fem" in dx and "neck" in dx) or ("slipped" in dx and "femoral" in dx):
        return 510
    elif (("thigh" in dx) or ("distal" not in dx and "proximal" not in dx and ("femur" in dx or "femoral" in dx))):
        return 520
    elif (("knee" in dx) or ("patella" in dx) or ("distal" in dx and ("femur" in dx or "femoral" in dx)) or (("proximal" in dx) and ("tibia" in dx or "fibula" in dx)) or ("tibia" in dx and "plateau" in dx)):
        return 530
    elif (("lower leg" in dx) or ("tibia" in dx) or ("fibula" in dx)) and ("distal" not in dx and "proximal" not in dx):
        return 540
    elif (("ankle" in dx) or ("tarsal" in dx) or (("distal" in dx) and ("tibia" in dx or "fibula" in dx))):
        return 550
    elif ("toe" in dx or "phalan" in dx):
        return 570
    else:
        noBP = True
    #For specific soft tissue foreign body case
    if ("foreign" in dx or "fb" in dx) and noBP != True:
        return False

#Takes input from user for a file at any location
# Sample output:
# Enter your file address: C:\Users\Username\Desktop
# Enter your file name: April 2022
# Enter the excel sheet that you want to autofill: 1
address = input("Enter your file address: ")
name = input("Enter your file name: ")
sheetNumber = input("Enter the excel sheet that you want to autofill: ")

sheetNumber = int(sheetNumber)-1
fullFileAddress = address+'\\'+name+".xlsx"
file = r''+fullFileAddress
sheet2 = pandas.read_excel(file, sheet_name=sheetNumber)

#loops through each row and codes NO1 and BP1 based on the diagnosis
for index, row in sheet2.iterrows():

    #checks if diagnosis is actually a string and isn't empty
    if type(row['Diagnosis']) == str:

        #for multiple injuries like tib and fib fracture (WIP)
        natureOfInjury = 0

        # Read the diagnosis from the diagnosis column in the current row and makes it all lowercase for consistency
        dx = row['Diagnosis'].lower()

        #check for all possible codes and assigns the proper CHIRPP code to the case (VERY hardcoded)
        if (("facial" in dx or "skull" in dx) and "fracture" in dx):
            sheet2.at[index, 'NO2'] = 42
            sheet2.at[index, 'BP2'] = 135
        elif ("subungual" in dx and "hematoma" in dx):
            sheet2.at[index, 'NO2'] = 10
            sheet2.at[index, 'BP2'] = bodyParts(dx)

        if (("abrasion" in dx) and ("globe" not in dx and "cornea" not in dx and "eye" not in dx and "ocular" not in dx and "canal" not in dx)) or (("bruis" in dx or "contusion" in dx or ("hematoma" in dx and "subdural" not in dx)) and "subungual" not in dx) or (("superficial" in dx) and ("cut" not in dx and "laceration" not in dx and "burn" not in dx and "swelling" not in dx)) and (("kidney" not in dx) or ("spleen" not in dx) or ("splenic" not in dx)) or ("abrasion" in dx and "eyelid" in dx):
            sheet2.at[index, 'NO1'] = 10
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif ("open wound" in dx or "laceration" in dx or ("minor" in dx and "cut" in dx) or ("nail" in dx and "avulsion" in dx) or ("circumcision" in dx)) or ("fissure" in dx) or ("epistaxis" in dx) or ("self" in dx and "cut" in dx) or ("dehiscence" in dx and "wound" in dx) or ("nose" in dx and "bleed" in dx):
            sheet2.at[index, 'NO1'] = 11
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif (("fracture" in dx or "fx" in dx or "broken" in dx) and ("tooth" not in dx and "patholog" not in dx)):
            sheet2.at[index, 'NO1'] = natureOfInjury = 12
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif ("dislocation" in dx or "subluxation" in dx or ("slipped" in dx and "femoral" in dx)):
            sheet2.at[index, 'NO1'] = natureOfInjury = 13
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif ("sprain" in dx or "strain" in dx):
            sheet2.at[index, 'NO1'] = 14
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif "nerve" in dx or "palsy" in dx:
            sheet2.at[index, 'NO1'] = 15
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif "blood vessel" in dx or "subungual" in dx:
            sheet2.at[index, 'NO1'] = 16
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif ("tendon" in dx or "muscle" in dx) and ("injury" in dx or "rupture" in dx or "sever" in dx):
            sheet2.at[index, 'NO1'] = 17
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif "crush" in dx:
            sheet2.at[index, 'NO1'] = 18
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif "amputation" in dx:
            sheet2.at[index, 'NO1'] = 19
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif (("burn" in dx or "corrosion" in dx) and ("globe" not in dx and "cornea" not in dx and "eye" not in dx and "ocular" not in dx)):
            sheet2.at[index, 'NO1'] = 20
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif "frostbite" in dx:
            sheet2.at[index, 'NO1'] = 21
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif (("bite" in dx and "insect" not in dx) or ("dog" in dx or "squirrel" in dx or "racoon" in dx or "human" in dx) and "medication" not in dx and "complication" not in dx):
            sheet2.at[index, 'NO1'] = 22
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif "electric" in dx:
            sheet2.at[index, 'NO1'] = 23
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif (("corrosion" in dx or "chemical" in dx or "injury" in dx or "burn" in dx or "abrasion" in dx or "trauma" in dx) and ("globe" in dx or "cornea" in dx or "eye" in dx or "ocular" in dx)) or (("eye" in dx or "ocular" in dx) and "pain" in dx):
            sheet2.at[index, 'NO1'] = 24
            sheet2.at[index, 'BP1'] = 135
        elif (("dental" in dx or "tooth" in dx or "teeth" in dx) and ("injury" in dx)) or (("tooth" in dx) and ("fracture" in dx)) or ("dental" in dx and "trauma" in dx) or ("chip" in dx and ("tooth" in dx or "teeth" in dx)) or (("dental" in dx or "tooth" in dx or "teeth" in dx) and "pain" in dx) or ("dental" in dx and ("implant" in dx or "device" in dx)):
            sheet2.at[index, 'NO1'] = 25
            sheet2.at[index, 'BP1'] = 135
        elif (("kidney" in dx) or ("spleen" in dx) or ("splenic" in dx) or ("ear" in dx and "canal" in dx)) and ("injury" in dx or "abrasion" in dx):
            sheet2.at[index, 'NO1'] = 26
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif (("pain" in dx and "sickle" not in dx and "disorder" not in dx) or ("soft" in dx and "tissue" in dx and "cyst" not in dx and "mass" not in dx) or ("swelling" in dx and "eye" not in dx) or ("testicular" in dx and "torsion" in dx)) and ("infection" not in dx and "foreign" not in dx and "fb" not in dx):
            sheet2.at[index, 'NO1'] = 27
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif ("foreign" in dx and ("globe" in dx or "cornea" in dx or "eye" in dx or "ocular" in dx)):
            sheet2.at[index, 'NO1'] = 31
            sheet2.at[index, 'BP1'] = 135
        elif ("foreign" in dx and "ear" in dx and "earlobe" not in dx) or ("fb" in dx and "ear" in dx):
            sheet2.at[index, 'NO1'] = 32
            sheet2.at[index, 'BP1'] = 135
        elif ("foreign" in dx or "fb" in dx) and ("nose" in dx or "nasal" in dx or "nostril" in dx or "sinus" in dx or "nare" in dx):
            sheet2.at[index, 'NO1'] = 33
            sheet2.at[index, 'BP1'] = 135
        elif ("foreign" in dx or "fb" in dx) and ("respira" in dx or "aspiration" in dx or "choking" in dx or "air" in dx) or ("choking" in dx or "gagging" in dx):
            sheet2.at[index, 'NO1'] = 34
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif ("foreign" in dx or "fb" in dx) and ("stomach" in dx or "ingestion" in dx or "colon" in dx or "alimentary" in dx or "esophag" in dx or "swallow" in dx):
            sheet2.at[index, 'NO1'] = 35
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif (("foreign" in dx and "genito-urinary" in dx) or ("foreign" in dx and "bladder" in dx) or ("foreign" in dx and "penis" in dx) or ("foreign" in dx and "urethra" in dx) or ("foreign" in dx and "vagina" in dx)):
            sheet2.at[index, 'NO1'] = 36
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif ("foreign" in dx or "fb" in dx) and ("soft" in dx or "earlobe" in dx or "skin" in dx or (bodyParts(dx) != False)) or ("splinter" in dx):
            sheet2.at[index, 'NO1'] = 37
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif ("minor" in dx and "head" in dx) or ("head" in dx and "injury" in dx) or ("head" in dx and "trauma" in dx):
            sheet2.at[index, 'NO1'] = 41
            sheet2.at[index, 'BP1'] = 135
        elif "concussion" in dx:
            sheet2.at[index, 'NO1'] = 42
            sheet2.at[index, 'BP1'] = 135
        elif ("intracranial" in dx) or ("brain" in dx and ("tumor" not in dx and "tumour" not in dx and "cancer" not in dx)) or ("subarachnoid" in dx) or ("subdural" in dx and "hematoma" in dx):
            sheet2.at[index, 'NO1'] = 43
            sheet2.at[index, 'BP1'] = 135
        elif ("poison" in dx or "toxic" in dx or "overdose" in dx or "ingestion" in dx):
            sheet2.at[index, 'NO1'] = 50
            sheet2.at[index, 'BP1'] = 900
        elif ("drown" in dx or "immersion" in dx):
            sheet2.at[index, 'NO1'] = 51 
            sheet2.at[index, 'BP1'] = 900
        elif "asphyxia" in dx:
            sheet2.at[index, 'NO1'] = 52
            sheet2.at[index, 'BP1'] = 900
        elif ("overexertion" in dx or ("heat" in dx and "stress" in dx) or ("cold" in dx and "stress" in dx)):
            sheet2.at[index, 'NO1'] = 53
            sheet2.at[index, 'BP1'] = 900
        elif ("no" in dx and "injury" in dx and "nose" not in dx):
            sheet2.at[index, 'NO1'] = 70
            sheet2.at[index, 'BP1'] = 900
        elif ("depressi" in dx) or ("aggressi" in dx) or ("tic" in dx and len(dx) == 3) or (("stress" in dx or "anxiety" in dx) and ("fracture" not in dx and "respira" not in dx)) or ("overdose" in dx) or ("anorexia" in dx) or ("poison" in dx) or ("intoxication" in dx) or (("behavi" in dx or "mental" in dx or "disorder" in dx or "social" in dx) and ("bizarre" in dx or "mood" in dx or "food" in dx or "conversion" in dx or "eat" in dx or "depress" in dx or "motor" in dx or "tic" in dx or "compulsive" in dx or "problem" in dx or "change" in dx or "health" in dx or "abnormal" in dx or "aggressive" in dx)) or (("tic" in dx) and ("facial" in dx or "simple" in dx)) or ("suicid" in dx) or ("violent" in dx) or ("ocd" in dx) or ("drug" in dx and "ingestion" in dx) or ("self" in dx and "harm" in dx) or ("panic" in dx) or ("emotional" in dx) or ("disruptive" in dx) or ("temper" in dx) or ("food" in dx and "refusal" in dx) or ("banging" in dx) or ("behavi" in dx and ("change" in dx or "concern" in dx)) and ("neurologic" not in dx) or ("mental" in dx and "disorder" in dx):
            sheet2.at[index, 'NO1'] = 71
            sheet2.at[index, 'BP1'] = 900
        elif ("pulled" in dx and "elbow" in dx) or ("nursemaid" in dx):
            sheet2.at[index, 'NO1'] = 75
            sheet2.at[index, 'BP1'] = 430
        elif "caustic" in dx:
            sheet2.at[index, 'NO1'] = 76
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif (("stab" in dx and "instability" not in dx) or "bullet" in dx or "penetrat" in dx):
            sheet2.at[index, 'NO1'] = 77
            sheet2.at[index, 'BP1'] = bodyParts(dx)
        elif ("injury" in dx or "trauma" in dx):
            sheet2.at[index, 'BP1'] = bodyParts(dx)

        if ("tibia" in dx and "fibula" in dx):
            sheet2.at[index, 'NO2'] = natureOfInjury
            sheet2.at[index, 'BP2'] = bodyParts(dx)

# Saves to a new excel file named "autofilledSheet" in the same location
newFullFileAddress = address+'\\'+"autofilledSheet.xlsx"
newFile = r''+newFullFileAddress
sheet2.to_excel(newFile)
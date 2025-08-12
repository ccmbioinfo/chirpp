from chirpp.inference.config_llama import inference_config
from chirpp.preprocess.config import preprocess_config

post_process={
  "cc_filter": [ 'depression / suicidal / deliberate self harm', 'ingestion', 'chemical', 'burn',
               'concern for patient wellfare', 'overdose ingestion', 'substance misuse / intoxication',
               'vomiting and/or nausea', 'behaviour', 'altered level Of consciousness' ],

  "diag_pl_filter": [ 'ingestion', 'poisoning', 'overdose', 'exposure', 'anxiety', 'substance',
                    'intoxication', 'chemical', 'depression', 'suicidal','depressive', 'crisis',
                    'instability', 'burn', 'self-harm', 'vomitting', 'irritation', 'suicide',
                    'depressed', 'anorexia nervosa', 'caustic', 'corrosive' ],


  "report_header": [ "CSN", "MRN", "ScrMRN", "DOB", "AGE", "SEX", "POSTAL", "ER Time", "ER Date", "ER Day", "INJ DATE", "Hr", "Min", "AM/PM",
                   "I/O", "LOCATION", "AREA", "PLACE", "Diagnosis", "SK Narrative", "PHAC Narrative", "W4P", "NO1", "BP1", "NO2",
                   "BP2", "NO3", "BP3", 'veh', 'veh p',"Notes", 'LOS', "DISP", "IN", "sub", "subID", 'sd1', "sd2", "sd3", "sd4", "sd5", "SPORTS CODE",
                   "E1", "E2", "E3", "E4", "CTAS", "Chief Complaint", "Problem List", "probs", "pre_processed", "Disposition"],

  "note_types": [ 'ED Triage Notes', 'ED Provider Notes', 'PS Initial Consult', 'Consults',
                'Consult Follow Up', 'Admission', 'Discharge Summary', 'Progress Notes',
                'Assessment & Plan Note',  'ED Trauma Note', 'ED Trauma Notes',
                'ED Procedure Note', 'Procedures','Op Note', 'Transfer In / Advice Note' ],

    "pos_complaints": inference_config["pos_complaints"],
    "terms_to_fix": preprocess_config["terms_to_fix"]
}
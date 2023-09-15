device="cuda:0"

# for determining if something is an injury
cases=["injury", "foregin body", "mental health", "other"]
columns=["Diagnosis", "Problem List", "Chief Complaint"]

REPORT_HEADER = ['MRN', 'ScrMRN', 'DOB', 'SEX', 'POSTAL',
       'ER Time', 'ER Date', 'INJ DATE', 'Hr', 'Min', 'AM/PM', 'I/O',
       'LOCATION', 'AREA', 'PLACE', 'Diagnosis', 'SK Narrative', 'PHAC Narrative',
       'W4P', 'NO1', 'BP1', 'NO2', 'BP2', 'NO3', 'BP3', 'Notes',
       'DISP', 'IN', 'LOC2', 'veh', 'veh p', 'sub', 'subID', 'sd1',
       'sd2', 'sd3', 'sd4', 'sd5', 'SPORTS CODE', 'E1', 'E2', 'E3', 'E4',
       'CTAS', 'Chief Complaint', 'probs']

CRYSTAL_CHIRPP_COLUMN_MAP = {'ER Time': 'Arrival Time',
 'CSN': 'CSN',
 'MRN': 'MRN',
 'DOB': 'Date of Birth',
 'SEX': 'Sex',
 'POSTAL': 'Postal Code',
 'ER Date': 'Arrival Date',
 'Diagnosis': 'Diagnosis',
 'Chief Complaint': 'Chief Complaint',
 'CTAS': 'CTAS'}

note_types = ['Transfer In / Advice Note', 'ED Triage Notes', 'ED Trauma Note', 'ED Trauma Notes',
              'ED Provider Notes', 'Assessment & Plan Note','ED Procedure Note', 'Procedures',
              'PS Initial Consult', 'Consults', 'Consult Follow Up', 'Op Note', 'Admission', 'Progress Notes', 'Discharge Summary']
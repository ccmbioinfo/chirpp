# these are some settings the SectionRemover needs

keep_sections=["history_of_present_illness", "observation_and_plan", "chief_complaint", "problem_list", "diagnosis"]
remove_sections=["past_medical_history", "family_history", "patient_instructions", "education",
                "patient_education", "medications", "allergies", "allergy", "imaging", "hospital_course",
                "labs_and_studies", "comments", "social_history",
                "physical_exam", "other"]

section_rules="./section_patterns.json"

lang_model="en_core_web_trf"
gpu=True

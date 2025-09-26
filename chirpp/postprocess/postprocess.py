from chirpp.postprocess.utils import *


class PostProcess:
    def __init__(self, merged_notes, inference_notes, params):
        """
        I am moving a lot of the processing that is done by the database over here because I want to make the
        database instance just for database things, for putting things in and getting things out. This will eventualll
        include a sophisticated form or searching as well
        """
        self.merged_notes = merged_notes
        self.inference_notes = inference_notes
        self.params = params

    def process_merged(self, inference):
        """
        This takes a merged notes dataframe and then splits them into sections, the sections will be passed to the database
        instance to be stored
        :param merged_notes:
        :return: patients, visits, referrals, notes and problems dataframes
        """
        merged_notes= self.merged_notes[~pd.isna(self.merged_notes["Note Text"])]
        patients=get_patients(merged_notes)
        visits=get_visits(merged_notes)
        referrals=get_referrals(merged_notes)
        problems=get_problems(merged_notes)
        notes_df=get_epic_notes(merged_notes)
        chunked_notes=get_chunked_notes(merged_notes, inference)
        return patients, visits, referrals, problems, notes_df, chunked_notes

    def process_inference(self, visits):
        summaries=get_summaries(self.inference_notes)
        processed_notes=get_processed_notes(self.inference_notes)
        cases=get_cases(self.inference_notes, visits)
        return summaries, processed_notes, cases

    def process(self, inference):
        patients, visits, referrals, problems, notes_df, chunked_notes=self.process_merged(inference)
        summaries, processed_notes, cases=self.process_inference(visits)
        return patients, visits, referrals, problems, notes_df, chunked_notes, summaries, processed_notes, cases

    #TODO as part of generate report for legacy support



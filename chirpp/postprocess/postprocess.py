from chirpp.postprocess.utils import *


class PostProcess:
    def __init__(self, raw_notes, processed_notes, params):
        """
        I am moving a lot of the processing that is done by the database over here because I want to make the
        database instance just for database things, for putting things in and getting things out. This will eventualll
        include a sophisticated form or searching as well
        """
        self.raw_notes = raw_notes
        self.processed_notes = processed_notes
        self.params = params

    def process_raw_sections(self, inference):
        """
        This takes a merged notes dataframe and then splits them into sections, the sections will be passed to the database
        instance to be stored
        :param merged_notes:
        :return: patients, visits, referrals, notes and problems dataframes
        """
        patients=get_patients(self.raw_notes)
        visits=get_visits(self.raw_notes, self.processed_notes, self.params["note_types"])
        referrals=get_referrals(self.raw_notes)
        problems=get_problems(self.raw_notes)
        notes_df=get_epic_notes(self.raw_notes)
        chunked_notes=get_chunked_notes(notes_df, inference)
        return patients, visits, referrals, problems, notes_df, chunked_notes

    def process_inference_sections(self, visits):
        summaries=get_summaries(self.processed_notes)
        processed_notes=get_processed_notes(self.processed_notes)
        cases=get_cases(self.processed_notes, visits)
        return summaries, processed_notes, cases

    def process(self, inference):
        patients, visits, referrals, problems, notes_df, chunked_notes=self.process_raw_sections(inference)
        summaries, processed_notes, cases=self.process_inference_sections(visits)
        return patients, visits, referrals, problems, notes_df, chunked_notes, summaries, processed_notes, cases

    #TODO as part of generate report for legacy support



import medspacy


class Autofill:
    """This class holds the necessary methods to fill columns, it will get bigger over time as new
    methods are added"""

    def __init__(self, full_text, clean_text, pl, cc, diag):
        """
        init method
        :param full_text: This is the long text that contains all the relevant notes
        :param clean_text: This is output of section removed
        :param pl: problem list
        :param cc: chief complaint
        :param diag: diagnosis
        """
        self.full_text=full_text
        self.clean_text=clean_text
        self.pl=pl
        self.cc=cc
        self.diag=diag


    def get_no_bp(self, nlp):
        """
        this takes diagnosis, and note text and returns body parts and injuries whenever applicable
        :param nlp: spacy nlp object this needs to have all the context and target rules added.
        :return: tuple bp and no
        """
        diag_doc=nlp(self.diag)
        clean_note_doc=nlp(self.clean_text)

        bps = []
        injs = []
        # first look at diagnosis, if that does not return anything then look at clean text
        for doc in [diag_doc, clean_note_doc]:
            if len(doc.ents)>0: #this means there are body parts
                for ent in doc.ents:
                    if not ent._.is_negated and not ent._.is_historical and not ent._.is_familty and \
                            not ent._.is_hypothetical and not ent._.is_uncertain:
                        bps.append(ent._.literal)
                        if len(ent._.modifiers) > 0:
                            for mod in ent._.modifiers:
                                if mod.category=="INJURY":
                                    injs.append(mod.rule.literal)
            else: #there might not be reconized body parts but there might be recognized injuries
                for item in diag_doc.user_data.values():
                    if type(item) == medspacy.context.context_graph.ConTextGraph:
                        for mod in item:
                            mod.rule.literal

        bps=list(set(bps))
        injs=list(set(injs))


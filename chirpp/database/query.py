from functools import partial
import numpy as np
from sqlalchemy import desc, asc, func, and_, select
import pandas as pd

from chirpp.database.database import DataBase
from chirpp.inference.inference import Inference
from chirpp.database.utils import *


# the query class here will take a dict of all the variables that are needed, there are only a few tables one would want to
# query here, and they could be hard coded.
# the query might look something like this:
#
# query_example={
#     "keywords":{
#         "positive":["accident","playground","injury"],
#         "negative":["abuse","assault"],
#         "detail_level": 1
#     },
#     "semantic":{
#         "description":"find all instances of playground accidents resulting in injury",
#         "detail_level":2,
#         "metric":"cosine",
#         "limit":5000
#     },
#     "filters":{
#         "visits":{
#             "arrival_date":{"gte":"2020-01-01","lte":"2023-12-31"},
#             "ctas":{"in":["2","3","4","5"]}, or "not_in":["1"]
#         },
#         "chirpp_report":{
#             "intent":{"eq":"10"},
#             "am_pm":{"eq":"1"},
#         }
#     }
# }

class Query:
    def __init__(self, query_dict: dict, database: DataBase, inference: Inference,
                 cutoff_method="cum_mass", **kwargs):
        self.database = database
        self.inference = inference
        self.session = self.database.session
        if cutoff_method=="elbow":
            cutoff_fun=knee_threshold
        elif cutoff_method=="cum_mass":
            cutoff_fun=cumulative_mass_threshold

        self.cutoff_method=partial(cutoff_fun, **kwargs)
        self.query_dict=query_dict

    #TODO this only implements or operators for general search, we might want to add and support
    def _keyword_search(self, positive_keywords=None, negative_keywords=None, detail_level=1, normalization=32):
        """
        perform ts vector search from the database, based on the detail level differnet tables and columns will be used
        :param positive_keywords: words to include ts vector search
        :param negative_keywords: words to avoid in ts vector search
        :param detail_level: if 1 search phac_summaries, if 2 search sk narrative column if 3 search the entrire notes
        :param normalization: the kind of normalization that is described here: https://www.postgresql.org/docs/current/textsearch-controls.html#TEXTSEARCH-RANKING
        :return: list of csns
        """
        # Determine table and vector column based on detail_level
        if detail_level == 1:
            table = self.database.tables["summaries"]
            vector_col = table.c.phac_narrative_vector
            csn_col = table.c.csn
        elif detail_level == 2:
            table = self.database.tables["visits"]
            vector_col = table.c.sk_narrative_vector
            csn_col = table.c.csn
        elif detail_level == 3:
            table = self.database.tables["notes"]
            vector_col = table.c.notes_vector
            csn_col = table.c.csn
        else:
            raise ValueError(f"Invalid detail_level: {detail_level}")

        if not positive_keywords and not negative_keywords:
            return []

        parts = []
        if positive_keywords:
            # OR semantics
            parts.append(" OR ".join(positive_keywords))
        if negative_keywords:
            # NOT semantics
            parts.append("NOT (" + " OR ".join(negative_keywords) + ")")

        query_str = " AND ".join(parts)
        ts_query = func.websearch_to_tsquery('english', query_str)
        rank = func.ts_rank(vector_col, ts_query, normalization)
        stmt = (
            select(csn_col)
            .where(vector_col.op('@@')(ts_query))
            .order_by(desc(rank))
        )
        results = self.session.execute(stmt).fetchall()
        return [r[0] for r in results]
    def _semantic_search(self, query, detail_level=1, metric="cosine", limit=5000):
        """
        perfrom semantic search from the database, based on the detail level different tables and columns will be used.
        :param query: natural language query
        :param detail_level: if 1 search phac_summaries, if 2 search processed notes, these are concat of ed triage and provide
        notes, if 3 use chunked notes
        :param metric: L1, L2, cosine, hamming (jaccard is not supported for this kind of search)
        :return: list of csn
        """
        if not self.inference:
            raise ValueError("Inference object is required for semantic search")

        # Embed the query
        # Assuming self.inference.embed returns a list of embeddings
        query_vec = self.inference.embed([query])[0]

        # Determine table and embedding column
        #TODO need to get the max version
        if detail_level == 1:
            table = self.database.tables["summaries"]
            embedding_col = table.c.phac_embeddings
            csn_col = table.c.csn
            get_max=True
            join_needed = False
        elif detail_level == 2:
            table = self.database.tables["processed_notes"]
            embedding_col = table.c.embeddings
            csn_col = table.c.csn
            get_max=False
            join_needed = False
        elif detail_level == 3:
            table = self.database.tables["chunked_notes"]
            embedding_col = table.c.embeddings
            # ChunkedNotes has note_id, need to join Notes then Visits to get CSN
            # Or just Notes if Notes has CSN. Notes table has csn.
            # ChunkedNotes(note_id) -> Notes(id), Notes(csn)
            join_needed = True
            get_max=False
            notes_table = self.database.tables["notes"]
        else:
            raise ValueError(f"Invalid detail_level: {detail_level}")

        # Define distance operator
        # For elbow method, we need the actual scores/distances
        if metric == "cosine":
            dist_op = embedding_col.cosine_distance(query_vec)
            order = asc(dist_op)  # distance: lower is better
            is_distance = False
        elif metric == "L2":
            dist_op = embedding_col.l2_distance(query_vec)
            order = asc(dist_op)
            is_distance = True
        elif metric == "L1":
            dist_op = embedding_col.l1_distance(query_vec)
            order = asc(dist_op)
            is_distance = True
        elif metric == "max_inner_product":
            dist_op = embedding_col.max_inner_product(query_vec)
            order = desc(dist_op)  # inner product: higher is better
            is_distance = False
        else:
            raise ValueError(f"Invalid metric: {metric}")

        # Build query
        # Fetch more results to find elbow, e.g. 5000
        if join_needed and detail_level == 3:
            stmt = select(notes_table.c.csn, dist_op.label("score")).select_from(
                table.join(notes_table, table.c.note_id == notes_table.c.id)
            ).order_by(order).limit(limit)
        else:
            if get_max: #TODO
                stmt = select(csn_col, dist_op.label("score")).order_by(order).limit(limit)
            else:
                stmt = select(csn_col, dist_op.label("score")).order_by(order).limit(limit)

        results = self.session.execute(stmt).fetchall()

        if not results:
            return []

        scores = [r[1] for r in results]
        csns = [r[0] for r in results]

        if len(results) < 300:
            return csns

        elbow_index=self.cutoff_method(scores)
        if is_distance:
            to_ret=csns[(elbow_index + 1):]
        else:
            to_ret=csns[:(elbow_index + 1)]

        # Include the elbow point
        return to_ret

    #TODO this only performs and filter we need to add or support as well, it can be mitigated by keeping intervals wide
    def _process_filter_condition(self, col, value):
        """
        process the filter condition for a single column based on the value dict
        :param col: column name
        :param value: value to compare, this is a dict with keys as operators and values as the values to compare
        :return: a simple sqlalchemy condition, this will get combined with a bunch of other things,
        """

        conditions = []
        for op, val in value.items():
            if op == 'gt':
                conditions.append(col > val)
            elif op == 'lt':
                conditions.append(col < val)
            elif op == 'gte':
                conditions.append(col >= val)
            elif op == 'lte':
                conditions.append(col <= val)
            elif op == 'eq':
                conditions.append(col == val)
            elif op == 'neq':
                conditions.append(col != val)
            elif op == 'in':
                conditions.append(col.in_(val))
            elif op == 'not_in':
                conditions.append(~col.in_(val))
            else:
                continue  # Explicitly ignoring like/ilike as we have tsvectors for that.

        if len(conditions) == 1:
            return conditions[0]
        elif len(conditions) > 1:
            return and_(*conditions)
        else:
            return None

    def _build_query(self, keywords=None, semantic=None, filters=None, is_chirpp=True):
        """
        Orchestrate the search.
        Returns a list of CSNs.
        """
        csns = None

        # Keyword Search
        if keywords:
            pos = keywords.get("positive", [])
            neg = keywords.get("negative", [])
            detail_level = keywords.get("detail_level")
            if pos or neg:
                kw_csns = set(self._keyword_search(pos, neg, detail_level))
                csns = kw_csns

        # Semantic Search
        if semantic:
            sem_csns = set(self._semantic_search(query=semantic["description"],
                                                 detail_level=semantic["detail_level"],
                                                 metric=semantic["metric"], limit=semantic["limit"]))
            if csns is None:
                csns = sem_csns
            else:
                csns = csns.intersection(sem_csns)

        # can have csns if you are not searching for them
        if csns is None and not filters:
            return []  # No criteria

        if filters:
            filter_csns = None

            for table_name, col_dict in filters.items():
                if table_name not in self.database.tables:
                    continue
                table = self.database.tables[table_name]
                if 'csn' not in table.c: #there is one table that does not deal with csns directly that we would care about
                    # that's the chunked notes table, we already accounted for that in semantic search, there is no other
                    # reason to search that table other than semantic search
                    continue

                stmt = select(table.c.csn)
                conditions = []
                for col_name, values in col_dict.items():
                    if hasattr(table.c, col_name):
                        col = getattr(table.c, col_name)
                        condition = self._process_filter_condition(col, values)
                        if condition is not None:
                            conditions.append(condition)

                if conditions:
                    stmt = stmt.where(and_(*conditions))

                if is_chirpp:
                    chirpp_table = self.database.tables["chirpp_report"]
                    stmt = stmt.where(table.c.csn.in_(select(chirpp_table.c.csn)))

            res = self.session.execute(stmt).fetchall()
            current_table_csns = set(r[0] for r in res)

            if filter_csns is None:
                filter_csns = current_table_csns
            else:
                filter_csns = filter_csns.intersection(current_table_csns)

            if filter_csns is not None:
                if csns is None:
                    csns = filter_csns
                else:
                    csns = csns.intersection(filter_csns)

        return list(csns) if csns is not None else []

    #TODO this should not have a hard cutoff but a boolean flag and a sorted list csn, score, bool
    def _rerank(self, csns, query, detail_level=1):
        """
        rerank the results from previous step to get the most relevant notes.
        :param csns: list of csns to get information from
        :param query: natural language query
        :param detail_level: what kind of notes should be used, 1 phac_summaries, 2, processsed notes 3 sk narrative
        :param is_chirpp:
        :return:
        """
        if not csns:
            return []

        #TODO Get max version
        if detail_level == 1: #summaries
            table=self.database.tables["summaries"]
            text = table.c.phac_narrative
            csn_col = table.c.csn
        elif detail_level==2: #
            table = self.database.tables["processed_notes"]
            text = table.c.note_text
            csn_col = table.c.csn
        elif detail_level==3:
            table = self.database.tables["visits"]
            text = table.c.sk_narrative
            csn_col = table.c.csn

        stmt=select(csn_col, text).where(csn_col.in_(csns))
        results = self.session.execute(stmt).fetchall()
        notes=[item[1] for item in results]

        if not notes:
            return []

        results=pd.DataFrame(results,columns=["csn","notes"])
        # inference.rerank returns relevance scores (list of floats)
        scores = self.inference.rerank(query, notes)
        results["score"]=scores
        results=results.sort_values(by="score",ascending=False)
        elbow_index=self.cutoff_method(np.array(results["score"]))
        relevant_csns=results.iloc[:elbow_index,0].tolist()
        return relevant_csns

    def _generate_report(self, csns):
        import pandas as pd
        if not csns:
            return pd.DataFrame(), pd.DataFrame()  # Return empty DFs matching get_report signature

        # We need to fetch data for these CSNs.
        # Reusing logic from database.get_report but filtering by CSN list.

        visit_table = self.database.tables["visits"]
        case_table = self.database.tables["chirpp_report"]
        problems_table = self.database.tables["problems"]
        patients_table = self.database.tables["patients"]

        # Visits
        visits = self.session.execute(select(visit_table).where(visit_table.c.csn.in_(csns))).fetchall()
        visits = pd.DataFrame(visits)
        if visits.empty:
            return pd.DataFrame(), pd.DataFrame()

        # Cases
        cases = self.session.execute(select(case_table).where(case_table.c.csn.in_(csns))).fetchall()
        cases = pd.DataFrame(cases)
        if not cases.empty:
            cases["chirpp"] = True
        else:
            # Create empty cases df with 'chirpp' column if needed for merge
            cases = pd.DataFrame(columns=["csn", "chirpp"])

        # Patients
        mrns = visits["mrn"].unique().tolist()
        patients = self.session.execute(select(patients_table).where(patients_table.c.mrn.in_(mrns))).fetchall()
        patients = pd.DataFrame(patients)

        # Problems
        problems = self.session.execute(select(problems_table).where(problems_table.c.csn.in_(csns))).fetchall()
        problems = pd.DataFrame(problems)

        if not problems.empty:
            problems_merged = []
            problems_grouped = problems.groupby("csn")
            for _, group in problems_grouped:
                problems_merged.append(",".join(group["problem"].to_list()))
            new_problems_df = pd.DataFrame({"csn": problems["csn"].drop_duplicates(), "problem_list": problems_merged})
            problems = new_problems_df
        else:
            problems = pd.DataFrame(columns=["csn", "problem_list"])

        #summaries
        summary_table=self.database.tables["summaries"]
        summaries=self.session.execute(select(summary_table).where(summary_table.c.csn.in_(csns))).fetchall()
        summaries=pd.DataFrame(summaries)
        report=self.database._prepare_report(patients, visits, cases, problems, summaries, get_previous_visits=False)
        return report #This is a tuple first one is non-chirpp second one is chirpp

    def __call__(self, chirpp_only=False):
        """
        Orchestrate the query based on the search_dict. The search_dict might look something like this:
             "keywords":{
                 "positive":["accident","playground","injury"],
                 "negative":["abuse","assault"],
                 "detail_level": 1
             },
             "semantic":{
                 "description":"find all instances of playground accidents resulting in injury",
                 "detail_level":2,
                 "metric":"cosine",
                 "limit":5000
             },
             "filters":{
                 "visits":{
                     "arrival_date":{"gte":"2020-01-01","lte":"2023-12-31"},
                     "ctas":{"in":["2","3","4","5"]}, or "not_in":["1"]
                 },
                 "chirpp_report":{
                     "intent":{"eq":"10"},
                     "am_pm":{"eq":"1"},
                 }
             }
        :param search_dict: dictionary containing search parameters
        :return: pandas dataframes for the report, this is in the same structure as the chirpp reports.
        """
        if "keywords" in self.query_dict.keys():
            keywords = self.query_dict.get("keywords")

        if "filters" in  self.query_dict.get("filters"):
            filters = self.query_dict.get("filters")

        if "semantic" in self.query_dict.keys():
            semantic = self.query_dict.get("semantic")

        do_rerank = self.query_dict.get("rerank", False)
        csns = self._build_query(keywords=keywords, semantic=semantic, filters=filters, is_chirpp=chirpp_only)

        if do_rerank:
            description = semantic["description"]
            csns = self._rerank(csns, description, self.inference)

        # Generate report
        return self._generate_report(csns)




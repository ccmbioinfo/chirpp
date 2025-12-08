import numpy as np
from sqlalchemy import select, desc, asc, func, and_, select

from chirpp.database.database import DataBase
from chirpp.database.utils import find_elbow_index


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
    def __init__(self, database: DataBase, inference=None):
        self.database = database
        self.inference = inference
        self.session = self.database.session

    #TODO this only implements or operators for general search, we might want to add and support
    def _keyword_search(self, positive_keywords, negative_keywords, detail_level=1, normalization=32):
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
            table = self.database.tables["visits"]
            vector_col = table.c.notes_vector
            csn_col = table.c.csn
        else:
            raise ValueError(f"Invalid detail_level: {detail_level}")

        # Construct TS query string
        # Join positive keywords with &
        pos_query = " | ".join(positive_keywords) if positive_keywords else ""

        # Join negative keywords with & !
        neg_query = " | ".join([f"!{k}" for k in negative_keywords]) if negative_keywords else ""

        if pos_query and neg_query:
            query_str = f"({pos_query}) & ({neg_query})"
        elif pos_query:
            query_str = pos_query
        elif neg_query:
            query_str = neg_query
        else:
            return []

        # Build query
        ts_query = func.to_tsquery('english', query_str)

        # Rank with normalization
        rank = func.ts_rank(vector_col, ts_query, normalization)

        stmt = select(csn_col).where(vector_col.op('@@')(ts_query)).order_by(desc(rank))

        # Execute
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
        if detail_level == 1:
            table = self.database.tables["summaries"]
            embedding_col = table.c.phac_embeddings
            csn_col = table.c.csn
            join_needed = False
        elif detail_level == 2:
            table = self.database.tables["processed_notes"]
            embedding_col = table.c.embeddings
            csn_col = table.c.csn
            join_needed = False
        elif detail_level == 3:
            table = self.database.tables["chunked_notes"]
            embedding_col = table.c.embeddings
            # ChunkedNotes has note_id, need to join Notes then Visits to get CSN
            # Or just Notes if Notes has CSN. Notes table has csn.
            # ChunkedNotes(note_id) -> Notes(id), Notes(csn)
            join_needed = True
            notes_table = self.database.tables["notes"]
        else:
            raise ValueError(f"Invalid detail_level: {detail_level}")

        # Define distance operator
        # For elbow method, we need the actual scores/distances
        if metric == "cosine":
            dist_op = embedding_col.cosine_distance(query_vec)
            order = asc(dist_op)  # distance: lower is better
            is_distance = True
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
            stmt = select(csn_col, dist_op.label("score")).order_by(order).limit(limit)

        results = self.session.execute(stmt).fetchall()

        if not results:
            return []

        scores = [r[1] for r in results]
        csns = [r[0] for r in results]

        if len(results) < 300:
            return csns

        elbow_index=find_elbow_index(np.array(scores))
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

    def _add_filters(self, filter_dict):
        """
        Generate a list of SQLAlchemy filter expressions from the dictionary.
        filter_dict format: {"table_name": {"column_name": [values]}}
        """
        filters = []
        for table_name, col_dict in filter_dict.items():
            if table_name not in self.database.tables:
                raise ValueError(f"Unknown table in filters: {table_name}")
            table = self.database.tables[table_name]
            for col_name, values in col_dict.items():
                if hasattr(table.c, col_name):
                    col = getattr(table.c, col_name)
                    condition = self._process_filter_condition(col, values)
                    if condition is not None:
                        filters.append(condition)
                else:
                    raise ValueError(f"Unknown column in filters: {col_name} in table {table_name}")
        return filters

    def _build_query(self, keywords=None, semantic=None, filters=None):
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


    def _rerank(self, csns, query, inference):
        """
        Rerank the CSNs based on the query using the inference object.
        """
        if not csns:
            return []


        visits_table = self.database.tables["visits"]
        stmt = select(visits_table.c.csn, visits_table.c.notes).where(visits_table.c.csn.in_(csns))
        results = self.session.execute(stmt).fetchall()

        # Map csn to note
        csn_note_map = {r[0]: r[1] for r in results if r[1]}
        valid_csns = list(csn_note_map.keys())
        notes = [csn_note_map[csn] for csn in valid_csns]

        if not notes:
            return []

        # inference.rerank returns relevance scores (list of floats)
        scores = inference.rerank(query, notes)

        # Pair csn with score
        csn_scores = list(zip(valid_csns, scores))

        # Sort by score desc
        csn_scores.sort(key=lambda x: x[1], reverse=True)

        return [x[0] for x in csn_scores]

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

        return self.database._prepare_report(patients, visits, cases, problems)

    def __call__(self, search_dict):
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
        keywords = search_dict.get("keywords")
        description = search_dict.get("description")
        filters = search_dict.get("filters")
        detail_level = search_dict.get("detail_level", 1)
        do_rerank = search_dict.get("rerank", False)

        # Build semantic search dict if description is provided AND inference is available
        semantic = None
        if description and self.inference:
            semantic = {
                "description": description,
                "detail_level": detail_level,
                "metric": search_dict.get("metric", "cosine"),
                "limit": search_dict.get("limit", 5000)
            }

        # Build query to get candidate CSNs
        csns = self._build_query(keywords=keywords, semantic=semantic, filters=filters)

        # Rerank if requested and description is present
        if do_rerank and description and self.inference:
            csns = self._rerank(csns, description, self.inference)

        # Generate report
        return self._generate_report(csns)




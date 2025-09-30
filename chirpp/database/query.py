import spacy
from spacy.tokens import Span
from negspacy.negation import Negex

from sqlalchemy import select, func, desc
import torch
from transformers import AutoTokenizer, AutoModel, pipeline


spacy.prefer_gpu()

#TODO I need to define which tables to use, I also need to add additional filters from the cases table
# the intial query needs to return just csns
# TODO negation with negspacy

class Query:
    def __init__(self, query_string, embedding_model, reranker_model, database):
        self.query_string = query_string
        self.embedding_model = embedding_model
        self.reranker_model = reranker_model
        self.database = database
        self.ids=None

    def _extract_keywords(self, model="en_core_web_trf", pos_tags=("NOUN", "PROPN", "ADJ", "VERB")):
        nlp = spacy.load(model)
        negex = Negex(nlp)

        nlp.add_pipe(negex, last=True)
        doc = nlp(self.query_string)

        positive_keywords = []
        negative_keywords = []

        for token in doc:
            if token.pos_ in pos_tags and not token.is_stop and token.is_alpha:
                if token._.negex:
                    negative_keywords.append(token.lemma_.lower())
                else:
                    positive_keywords.append(token.lemma_.lower())


        noun_chunks = [chunk.text.lower() for chunk in doc.noun_chunks]

        # Combine and deduplicate
        pos_keywords = list(set(positive_keywords + noun_chunks))
        neg_keywords = list(set(negative_keywords+ noun_chunks))

        self.keywords = (pos_keywords, neg_keywords)

    def _build_tsquery(self):
        """Build a Postgres tsquery string using AND between keywords."""
        pos_part = " & ".join(self.keywords[0]) # positive keywords
        neg_part = " & ".join(f"!{kw}" for kw in self.keywords[1]) # negative keywords
        if pos_part and neg_part:
            return f"{pos_part} & {neg_part}"
        elif pos_part:
            return pos_part
        elif neg_part:
            return neg_part
        else:
            return ""

    def _embed_query(self):
        embedding_tokenizer = AutoTokenizer.from_pretrained(self.embedding_model)
        embedding_model = AutoModel.from_pretrained(self.embedding_model)
        inputs = embedding_tokenizer(self.query_string, return_tensors="pt")
        with torch.no_grad():
            embeddings = embedding_model(**inputs).last_hidden_state.mean(dim=1)
        self.embeddings=embeddings[0].cpu().numpy()

    def _retrieve_candidates(
            self,
            session,
            w_lexical: float = 0.5,
            w_semantic: float = 0.5,
            keyword_boost: float = 0.1,  # extra boost for chunks containing keywords
    ):
        """
        Hybrid retrieval with normalized scores and keyword boosting.
        """

        stmt = select(
            chunks_table.c.id,
            chunks_table.c.text_id,
            chunks_table.c.chunk,
            func.ts_rank_cd(chunks_table.c.tsv, func.to_tsquery(tsquery)).label("lexical"),
            (1 - func.l2_distance(chunks_table.c.embedding, query_embedding)).label("semantic")
        ).where(
            chunks_table.c.tsv.op("@@")(func.to_tsquery(tsquery))
        )

        candidates = session.execute(stmt).all()
        if not candidates:
            return []

        # Step 2: min-max normalization
        lexical_scores = [c.lexical for c in candidates]
        semantic_scores = [c.semantic for c in candidates]

        min_lex, max_lex = min(lexical_scores), max(lexical_scores)
        min_sem, max_sem = min(semantic_scores), max(semantic_scores)

        # Step 3: compute hybrid score with keyword boosting
        normalized_candidates = []
        for c in candidates:
            lex_norm = self._normalize(c.lexical, min_lex, max_lex)
            sem_norm = self._normalize(c.semantic, min_sem, max_sem)
            hybrid_score = w_lexical * lex_norm + w_semantic * sem_norm

            # Boost if chunk contains any extracted keyword
            chunk_lower = c.chunk.lower()
            if any(kw in chunk_lower for kw in self.keywords):
                hybrid_score += keyword_boost

            normalized_candidates.append((c.id, c.text_id, c.chunk, hybrid_score))

        # Step 4: sort by hybrid score
        normalized_candidates.sort(key=lambda x: x[3], reverse=True)
        return normalized_candidates

    def _rerank(self, session, chunks_table, texts_table):
        candidates = retrieve_candidates_normalized(ses)
        if not candidates:
            return []

        # Prepare input for reranker
        pairs = [{"text": query, "text_pair": c[2]} for c in candidates]
        rerank_scores = reranker(pairs, top_k=None)

        # Aggregate reranker scores by text_id
        agg_scores = {}
        for c, score in zip(candidates, rerank_scores):
            text_id = c[1]
            agg_scores.setdefault(text_id, 0)
            agg_scores[text_id] += score["score"]

        best_ids = sorted(agg_scores, key=agg_scores.get, reverse=True)
        stmt = select(texts_table).where(texts_table.c.id.in_(best_ids))
        return session.execute(stmt).all()

    def _normalize(self, val, min_val, max_val):
        return (val - min_val) / (max_val - min_val) if max_val > min_val else 0.0

    def _add_filters(self, filter_dict):
        pass

    def _run(self):
        pass

    def _report(self):
        pass

    def __str__(self):
        return f"Query: {self.query_string} for {print(self.database)}"

    def __repr__(self):
        return print(self)

    def __add__(self, other):
        pass

    def __sub__(self, other):
        pass

    def __and__(self, other):
        pass

    def __or__(self, other):
        pass


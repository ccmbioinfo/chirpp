import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class QueryType(Enum):
    """Types of queries the system can handle"""
    AGGREGATE = "aggregate"  # Count, average, sum queries
    RETRIEVAL = "retrieval"  # Return specific instances/cases
    DESCRIPTIVE = "descriptive"  # Describe patterns or answer yes/no


@dataclass
class QueryResult:
    """Container for query results"""
    query_type: QueryType
    sql_query: str
    results: Any
    explanation: str
    csn_list: Optional[List[int]] = None


class NaturalLanguageQuerySystem:
    """
    A system that converts natural language queries to SQL and executes them
    against a medical database using open-weights LLMs.
    """

    def __init__(
            self,
            database,
            model_name: str = "defog/sqlcoder-7b-2",
            device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        """
        Initialize the query system.

        Args:
            db_connection_string: PostgreSQL connection string
            model_name: HuggingFace model name for text-to-SQL
                       Recommended: "defog/sqlcoder-7b-2" (~7B params, excellent for SQL)
                       Alternative: "NumbersStation/nsql-llama-2-7B"
            device: Device to run model on
        """
        self.engine = create_engine(db_connection_string)
        self.Session = sessionmaker(bind=self.engine)
        self.device = device

        print(f"Loading model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto",
            trust_remote_code=True
        )

        # Schema context for the model
        self.schema_context = self._build_schema_context()

    def _build_schema_context(self) -> str:
        """Build a comprehensive schema description for the LLM"""
        schema = """
Database Schema for Emergency Department Medical Records:

Tables:

1. patients (Patient Demographics)
   - mrn (INTEGER, PRIMARY KEY): Medical Record Number
   - scr_mrn (INTEGER): Screening MRN
   - dob (DATE): Date of Birth

2. visits (Emergency Department Visits)
   - csn (INTEGER, PRIMARY KEY): Contact Serial Number (unique visit ID)
   - mrn (INTEGER, FOREIGN KEY -> patients.mrn): Patient identifier
   - sex (STRING): Patient sex
   - age (INTEGER): Patient age at visit
   - arrival_date (DATE): Date of ED arrival
   - arrival_time (TIME): Time of ED arrival
   - day_of_week (STRING): Day of week
   - sk_narrative (TEXT): Structured narrative of visit
   - sk_narrative_vector (TSVECTOR): Full-text search index for sk_narrative
   - notes (TEXT): Clinical notes
   - notes_vector (TSVECTOR): Full-text search index for notes
   - postal_code (STRING): Patient postal code
   - address (STRING): Patient address
   - city (STRING): Patient city
   - province (STRING): Patient province
   - chief_complaint (STRING): Main complaint
   - diagnosis (STRING): Final diagnosis
   - disposition (STRING): Patient disposition (admitted, discharged, etc.)
   - ctas (INTEGER): Canadian Triage and Acuity Scale (1-5)
   - los (FLOAT): Length of stay in hours
   - probs (FLOAT): Probability scores

3. summaries (Visit Summaries)
   - id (INTEGER, PRIMARY KEY)
   - csn (INTEGER, FOREIGN KEY -> visits.csn)
   - phac_narrative (STRING): Public Health Agency narrative
   - phac_narrative_vector (TSVECTOR): Full-text search index for phac_narrative
   - phac_embeddings (VECTOR): Embeddings for semantic search
   - version (INTEGER): Version number for updates

4. referrals (Patient Referrals)
   - id (INTEGER, PRIMARY KEY)
   - csn (INTEGER, FOREIGN KEY -> visits.csn)
   - referrals (STRING): Referral information

5. problems (Patient Problems)
   - id (INTEGER, PRIMARY KEY)
   - csn (INTEGER, FOREIGN KEY -> visits.csn)
   - problem (STRING): Problem description

6. notes (Clinical Notes)
   - id (UUID, PRIMARY KEY)
   - csn (INTEGER, FOREIGN KEY -> visits.csn)
   - note_type (STRING): Type of note
   - author_type (STRING): Type of author
   - author_service (STRING): Service of author
   - note_text (TEXT): Full text of note
   - notes_ts_vector (TSVECTOR): Full-text search index for note_text

7. chunked_notes (Semantically Chunked Notes)
   - id (INTEGER, PRIMARY KEY)
   - note_id (UUID, FOREIGN KEY -> notes.id)
   - chunk_number (INTEGER): Chunk sequence number
   - chunk_text (TEXT): Chunked text
   - embeddings (VECTOR): Embeddings for RAG

8. processed_notes (Processed Clinical Notes)
   - id (INTEGER, PRIMARY KEY)
   - csn (INTEGER, FOREIGN KEY -> visits.csn)
   - note_text (TEXT): Processed note text
   - note_text_ts_vector (TSVECTOR): Full-text search index for note_text
   - embeddings (VECTOR): Embeddings

9. chirpp_report (CHIRPP Injury Reports)
   - id (INTEGER, PRIMARY KEY)
   - csn (INTEGER, FOREIGN KEY -> visits.csn)
   - injury_date (INTEGER): Date of injury
   - injury_hour (INTEGER): Hour of injury
   - injury_min (INTEGER): Minute of injury
   - am_pm (STRING): AM/PM indicator
   - i_o (STRING): Indoor/Outdoor
   - location (INTEGER): Location code
   - area (INTEGER): Area code
   - place (STRING): Place description
   - w4p (INTEGER): What for product code
   - no1, bp1, no2, bp2, no3, bp3 (INTEGER): Nature and body part codes
   - disp (INTEGER): Disposition code
   - intent (INTEGER): Intent code
   - veh (INTEGER): Vehicle code
   - veh_p (STRING): Vehicle position
   - sub (INTEGER): Substance code
   - sub_id (STRING): Substance identifier
   - sd1-sd5 (INTEGER): Supplementary data codes
   - sports_code (INTEGER): Sports activity code
   - version (INTEGER): Report version

Key Relationships:
- visits.csn is the main identifier for ED visits
- visits.mrn links to patients.mrn
- All other tables link to visits via csn (except chunked_notes which links via note_id)

IMPORTANT - Full-Text Search Guidelines:
- ALWAYS use tsvector columns for text searching instead of ILIKE or LIKE
- Use the @@ operator with to_tsquery() or plainto_tsquery() for text matching
- Available tsvector columns:
  * visits.sk_narrative_vector for searching visit narratives
  * visits.notes_vector for searching visit notes
  * summaries.phac_narrative_vector for searching PHAC narratives
  * notes.notes_ts_vector for searching clinical notes
  * processed_notes.note_text_ts_vector for searching processed notes

Full-Text Search Examples:
- Search for 'fall' in narratives: WHERE sk_narrative_vector @@ plainto_tsquery('english', 'fall')
- Search for 'fracture' in notes: WHERE notes_vector @@ plainto_tsquery('english', 'fracture')
- Multiple terms: WHERE sk_narrative_vector @@ plainto_tsquery('english', 'fall fracture')
- With ranking: ts_rank(sk_narrative_vector, plainto_tsquery('english', 'fall')) AS rank

Common Query Patterns:
- Use visits.csn to identify specific cases/instances
- Join visits with patients for demographic info
- Join visits with chirpp_report for injury details
- ALWAYS prefer tsvector columns with @@ operator over ILIKE for text searches
- Use plainto_tsquery('english', 'search terms') for natural language queries
- Use to_tsquery('english', 'term1 & term2') for boolean searches
"""
        return schema

    def _classify_query(self, query: str) -> QueryType:
        """Classify the type of query based on keywords"""
        query_lower = query.lower()

        # Check for retrieval keywords
        retrieval_keywords = [
            "show", "list", "return", "get", "find cases", "find instances",
            "which cases", "what cases", "give me cases", "csn"
        ]

        # Check for aggregate keywords
        aggregate_keywords = [
            "how many", "count", "average", "mean", "sum", "total",
            "percentage", "proportion", "distribution"
        ]

        if any(kw in query_lower for kw in retrieval_keywords):
            return QueryType.RETRIEVAL
        elif any(kw in query_lower for kw in aggregate_keywords):
            return QueryType.AGGREGATE
        else:
            return QueryType.DESCRIPTIVE

    def _generate_sql(self, natural_query: str, query_type: QueryType) -> str:
        """Generate SQL from natural language using the LLM"""

        # Add guidance based on query type
        if query_type == QueryType.RETRIEVAL:
            instruction = """
Generate a SQL query that returns the csn (Contact Serial Number) values for cases matching the criteria.
Always include visits.csn in the SELECT clause.
Limit results to 100 rows by default unless specified otherwise.
"""
        else:
            instruction = """
Generate a SQL query that computes aggregates or answers the question.
Use appropriate aggregate functions (COUNT, AVG, SUM, etc.).
"""

        prompt = f"""### Task
Generate a PostgreSQL query to answer the following question.

### Database Schema
{self.schema_context}

### Instructions
{instruction}
- Use proper JOIN syntax when accessing multiple tables
- CRITICAL: For text searches, ALWAYS use tsvector columns with @@ operator
- Example: WHERE sk_narrative_vector @@ plainto_tsquery('english', 'fall fracture')
- NEVER use ILIKE or LIKE for text in notes, narratives, or text fields with tsvector columns
- Use plainto_tsquery() for natural language terms
- Use to_tsquery() for boolean searches (term1 & term2 | term3)
- For date comparisons, use DATE columns appropriately
- Return only the SQL query, no explanations

### Question
{natural_query}

### SQL Query
```sql
"""

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.1,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id
            )

        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract SQL from the generated text
        sql_query = self._extract_sql(generated_text)

        return sql_query

    def _extract_sql(self, generated_text: str) -> str:
        """Extract SQL query from generated text"""
        # Look for SQL between triple backticks or after "```sql"
        sql_pattern = r"```sql\s*(.*?)\s*```"
        match = re.search(sql_pattern, generated_text, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()

        # Look for SQL after the prompt
        if "### SQL Query" in generated_text:
            sql_part = generated_text.split("### SQL Query")[-1]
            sql_part = sql_part.replace("```sql", "").replace("```", "").strip()
            return sql_part

        # If no markers, try to extract SELECT statement
        select_pattern = r"(SELECT\s+.*?;)"
        match = re.search(select_pattern, generated_text, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()

        # Return the last part that looks like SQL
        lines = generated_text.split("\n")
        sql_lines = []
        for line in reversed(lines):
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("--"):
                sql_lines.insert(0, line)
                if "SELECT" in line.upper():
                    break

        return " ".join(sql_lines).strip()

    def _execute_query(self, sql_query: str) -> Tuple[List[Dict], List[int]]:
        """Execute SQL query and return results"""
        session = self.Session()
        try:
            # Clean up the query
            sql_query = sql_query.strip()
            if not sql_query.endswith(";"):
                sql_query += ";"

            result = session.execute(text(sql_query))
            rows = result.fetchall()
            columns = result.keys()

            # Convert to list of dicts
            results = [dict(zip(columns, row)) for row in rows]

            # Extract CSN list if present
            csn_list = []
            if results and 'csn' in results[0]:
                csn_list = [row['csn'] for row in results]

            return results, csn_list

        except Exception as e:
            raise Exception(f"SQL execution error: {str(e)}\nQuery: {sql_query}")
        finally:
            session.close()

    def _generate_explanation(
            self,
            query: str,
            results: List[Dict],
            query_type: QueryType
    ) -> str:
        """Generate a natural language explanation of the results"""

        if not results:
            return "No results found matching the query criteria."

        if query_type == QueryType.RETRIEVAL:
            count = len(results)
            return f"Found {count} case(s) matching the criteria. The CSN values are included in the results."

        elif query_type == QueryType.AGGREGATE:
            # Format the aggregate results
            if len(results) == 1 and len(results[0]) == 1:
                value = list(results[0].values())[0]
                return f"Result: {value}"
            else:
                return f"Found {len(results)} result row(s) with the aggregate data."

        else:
            return f"Query returned {len(results)} result(s)."

    def query(self, natural_language_query: str) -> QueryResult:
        """
        Main method to process a natural language query.

        Args:
            natural_language_query: The question in natural language

        Returns:
            QueryResult object containing SQL, results, and explanation
        """
        print(f"\n{'=' * 60}")
        print(f"Processing query: {natural_language_query}")
        print(f"{'=' * 60}")

        # Step 1: Classify query type
        query_type = self._classify_query(natural_language_query)
        print(f"Query type: {query_type.value}")

        # Step 2: Generate SQL
        print("Generating SQL...")
        sql_query = self._generate_sql(natural_language_query, query_type)
        print(f"Generated SQL:\n{sql_query}")

        # Step 3: Execute query
        print("Executing query...")
        results, csn_list = self._execute_query(sql_query)
        print(f"Retrieved {len(results)} result(s)")

        # Step 4: Generate explanation
        explanation = self._generate_explanation(
            natural_language_query,
            results,
            query_type
        )

        return QueryResult(
            query_type=query_type,
            sql_query=sql_query,
            results=results,
            explanation=explanation,
            csn_list=csn_list if csn_list else None
        )

    def batch_query(self, queries: List[str]) -> List[QueryResult]:
        """Process multiple queries in batch"""
        return [self.query(q) for q in queries]


def main():
    """Example usage"""

    # Initialize the system
    db_connection = "postgresql://user:password@localhost:5432/medical_db"

    system = NaturalLanguageQuerySystem(
        db_connection_string=db_connection,
        model_name="defog/sqlcoder-7b-2"  # ~7B params, fits in 40GB VRAM
    )

    # Example queries
    example_queries = [
        # Retrieval queries (returns CSN values) - using full-text search
        "Show me all cases where the patient had a fall mentioned in their notes",
        "Find all visits with 'fracture' mentioned in the narrative and age under 10",
        "List cases mentioning sports injuries in clinical notes",
        "Find visits where notes mention both 'concussion' and 'bicycle'",

        # Aggregate queries
        "How many patients visited the ED in 2024?",
        "What is the average length of stay for patients with CTAS level 1?",
        "Count cases where narratives mention 'playground' injuries",

        # Complex text searches
        "Show cases with 'burn' or 'scald' in the narrative",
        "Find visits mentioning 'poison' or 'ingestion' in processed notes",
    ]

    # Process queries
    for query in example_queries[:3]:  # Process first 3 as examples
        result = system.query(query)

        print(f"\n{'=' * 60}")
        print(f"Query: {query}")
        print(f"Type: {result.query_type.value}")
        print(f"\nSQL:\n{result.sql_query}")
        print(f"\nExplanation: {result.explanation}")

        if result.csn_list:
            print(f"\nCSN List (first 10): {result.csn_list[:10]}")

        print(f"\nResults (first 3 rows):")
        for row in result.results[:3]:
            print(row)
        print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
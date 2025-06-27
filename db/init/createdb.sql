
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';

SET default_tablespace = '';

SET default_table_access_method = heap;

CREATE TABLE public.chirpp_report (
    id integer NOT NULL,
    csn integer,
    injury_date date,
    injury_hour integer,
    injury_min integer,
    am_pm character varying,
    i_o character varying,
    location integer,
    area integer,
    place character varying,
    w4p integer,
    no1 integer,
    bp1 integer,
    no2 integer,
    bp2 integer,
    no3 integer,
    bp3 integer,
    notes text,
    disp integer,
    intent integer,
    veh integer,
    veh_p character varying,
    sub integer,
    sub_id character varying,
    sd1 integer,
    sd2 integer,
    sd3 integer,
    sd4 integer,
    sd5 integer,
    sports_code integer
);

CREATE SEQUENCE public.chirpp_report_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE public.chunked_notes (
    id integer NOT NULL,
    note_id integer,
    chunk_number integer,
    chunk_text text,
    embeddings public.vector(1024),
    chunk_ts_vector tsvector GENERATED ALWAYS AS (to_tsvector('english'::regconfig, chunk_text)) STORED
);

CREATE SEQUENCE public.chunked_notes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE public.custom_label_visits (
    id integer NOT NULL,
    label_id integer,
    csn integer
);

CREATE SEQUENCE public.custom_label_visits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE public.custom_labels (
    id integer NOT NULL,
    label_name character varying,
    label_description text,
    key_words character varying,
    context_aware boolean,
    context_rules json,
    active boolean
);

CREATE SEQUENCE public.custom_labels_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE public.logs (
    id integer NOT NULL,
    "user" integer,
    "timestamp" timestamp without time zone,
    command character varying
);

CREATE SEQUENCE public.logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE public.managers (
    id integer NOT NULL,
    user_id integer,
    manages integer
);

CREATE SEQUENCE public.managers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE public.notes (
    id integer NOT NULL,
    csn integer,
    note_type character varying,
    author_type character varying,
    author_service character varying,
    note_text text,
    notes_ts_vector tsvector GENERATED ALWAYS AS (to_tsvector('english'::regconfig, note_text)) STORED
);

CREATE SEQUENCE public.notes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


CREATE TABLE public.patients (
    mrn integer NOT NULL,
    dob date
);

CREATE SEQUENCE public.patients_mrn_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


CREATE TABLE public.problems (
    id integer NOT NULL,
    csn integer,
    problem character varying
);

CREATE SEQUENCE public.problems_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE public.processed_notes (
    id integer NOT NULL,
    csn integer,
    note_text text,
    note_text_ts_vector tsvector GENERATED ALWAYS AS (to_tsvector('english'::regconfig, note_text)) STORED,
    embeddings public.vector(1024)
);

CREATE SEQUENCE public.processed_notes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


CREATE TABLE public.referrals (
    id integer NOT NULL,
    csn integer,
    referrals character varying
);


CREATE SEQUENCE public.referrals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE public.users (
    id integer NOT NULL,
    first_name character varying,
    last_name character varying,
    email character varying,
    password character varying,
    active boolean,
    uuid uuid
);

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE public.visits (
    csn integer NOT NULL,
    sex character varying,
    age integer,
    mrn integer,
    arrival_date date,
    arrival_time time without time zone,
    day_of_week character varying,
    sk_narrative text,
    phac_narrative text,
    postal_code character varying,
    chief_complaint character varying,
    diagnosis character varying,
    disposition character varying,
    ctas integer,
    los double precision,
    processed boolean,
    address character varying,
    city character varying,
    province character varying,
    sk_narrative_vector tsvector GENERATED ALWAYS AS (to_tsvector('english'::regconfig, sk_narrative)) STORED,
    phac_narrative_vector tsvector GENERATED ALWAYS AS (to_tsvector('english'::regconfig, phac_narrative)) STORED,
    probs double precision
);

CREATE SEQUENCE public.visits_csn_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE ONLY public.chirpp_report ALTER COLUMN id SET DEFAULT nextval('public.chirpp_report_id_seq'::regclass);

ALTER TABLE ONLY public.chunked_notes ALTER COLUMN id SET DEFAULT nextval('public.chunked_notes_id_seq'::regclass);

ALTER TABLE ONLY public.custom_label_visits ALTER COLUMN id SET DEFAULT nextval('public.custom_label_visits_id_seq'::regclass);

ALTER TABLE ONLY public.custom_labels ALTER COLUMN id SET DEFAULT nextval('public.custom_labels_id_seq'::regclass);

ALTER TABLE ONLY public.logs ALTER COLUMN id SET DEFAULT nextval('public.logs_id_seq'::regclass);

ALTER TABLE ONLY public.managers ALTER COLUMN id SET DEFAULT nextval('public.managers_id_seq'::regclass);

ALTER TABLE ONLY public.notes ALTER COLUMN id SET DEFAULT nextval('public.notes_id_seq'::regclass);

ALTER TABLE ONLY public.patients ALTER COLUMN mrn SET DEFAULT nextval('public.patients_mrn_seq'::regclass);

ALTER TABLE ONLY public.problems ALTER COLUMN id SET DEFAULT nextval('public.problems_id_seq'::regclass);

ALTER TABLE ONLY public.processed_notes ALTER COLUMN id SET DEFAULT nextval('public.processed_notes_id_seq'::regclass);

ALTER TABLE ONLY public.referrals ALTER COLUMN id SET DEFAULT nextval('public.referrals_id_seq'::regclass);

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);

ALTER TABLE ONLY public.visits ALTER COLUMN csn SET DEFAULT nextval('public.visits_csn_seq'::regclass);

ALTER TABLE ONLY public.chirpp_report
    ADD CONSTRAINT chirpp_report_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.chunked_notes
    ADD CONSTRAINT chunked_notes_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.custom_label_visits
    ADD CONSTRAINT custom_label_visits_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.custom_labels
    ADD CONSTRAINT custom_labels_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.managers
    ADD CONSTRAINT managers_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.notes
    ADD CONSTRAINT notes_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_pkey PRIMARY KEY (mrn);

ALTER TABLE ONLY public.problems
    ADD CONSTRAINT problems_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.processed_notes
    ADD CONSTRAINT processed_notes_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.referrals
    ADD CONSTRAINT referrals_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.visits
    ADD CONSTRAINT visits_pkey PRIMARY KEY (csn);

CREATE INDEX ix_chirpp_report_csn ON public.chirpp_report USING btree (csn);

CREATE INDEX ix_chirpp_report_id ON public.chirpp_report USING btree (id);

CREATE INDEX ix_chirpp_report_inj_date ON public.chirpp_report USING btree (injury_date);

CREATE INDEX ix_chirpp_report_intent ON public.chirpp_report USING btree (intent);

CREATE INDEX ix_chunked_notes_id ON public.chunked_notes USING btree (id);

CREATE INDEX ix_chunked_notes_note_id ON public.chunked_notes USING btree (note_id);

CREATE INDEX ix_custom_label_visits_id ON public.custom_label_visits USING btree (id);

CREATE INDEX ix_custom_labels_id ON public.custom_labels USING btree (id);

CREATE INDEX ix_custom_labels_label_name ON public.custom_labels USING btree (label_name);

CREATE INDEX ix_managers_id ON public.managers USING btree (id);

CREATE INDEX ix_note_text_ts_vector ON public.processed_notes USING gin (note_text_ts_vector);

CREATE INDEX ix_notes_author_service ON public.notes USING btree (author_service);

CREATE INDEX ix_notes_author_type ON public.notes USING btree (author_type);

CREATE INDEX ix_notes_csn ON public.notes USING btree (csn);

CREATE INDEX ix_notes_id ON public.notes USING btree (id);

CREATE INDEX ix_notes_note_type ON public.notes USING btree (note_type);

CREATE INDEX ix_patients_mrn ON public.patients USING btree (mrn);

CREATE INDEX ix_phac_narrative_ts_vector ON public.visits USING gin (phac_narrative_vector);

CREATE INDEX ix_problems_id ON public.problems USING btree (id);

CREATE INDEX ix_processed_notes_csn ON public.processed_notes USING btree (csn);

CREATE INDEX ix_processed_notes_id ON public.processed_notes USING btree (id);

CREATE INDEX ix_raw_notes_ts_vector ON public.notes USING gin (notes_ts_vector);

CREATE INDEX ix_referrals_csn ON public.referrals USING btree (csn);

CREATE INDEX ix_referrals_id ON public.referrals USING btree (id);

CREATE INDEX ix_referrals_problems ON public.problems USING btree (csn);

CREATE INDEX ix_sk_narrative_ts_vector ON public.visits USING gin (sk_narrative_vector);

CREATE INDEX ix_users_id ON public.users USING btree (id);

CREATE INDEX ix_visits_arrival_date ON public.visits USING btree (arrival_date);

CREATE INDEX ix_visits_arrival_time ON public.visits USING btree (arrival_time);

CREATE INDEX ix_visits_chief_complaint ON public.visits USING btree (chief_complaint);

CREATE INDEX ix_visits_csn ON public.visits USING btree (csn);

CREATE INDEX ix_visits_diagnosis ON public.visits USING btree (diagnosis);

CREATE INDEX ix_visits_mrn ON public.visits USING btree (mrn);

ALTER TABLE ONLY public.chirpp_report
    ADD CONSTRAINT chirpp_report_csn_fkey FOREIGN KEY (csn) REFERENCES public.visits(csn);


ALTER TABLE ONLY public.chunked_notes
    ADD CONSTRAINT chunked_notes_note_id_fkey FOREIGN KEY (note_id) REFERENCES public.notes(id);

ALTER TABLE ONLY public.custom_label_visits
    ADD CONSTRAINT custom_label_visits_csn_fkey FOREIGN KEY (csn) REFERENCES public.visits(csn);

ALTER TABLE ONLY public.custom_label_visits
    ADD CONSTRAINT custom_label_visits_label_id_fkey FOREIGN KEY (label_id) REFERENCES public.custom_labels(id);

ALTER TABLE ONLY public.logs
    ADD CONSTRAINT logs_user_fkey FOREIGN KEY ("user") REFERENCES public.users(id);

ALTER TABLE ONLY public.managers
    ADD CONSTRAINT managers_manages_fkey FOREIGN KEY (manages) REFERENCES public.users(id);

ALTER TABLE ONLY public.managers
    ADD CONSTRAINT managers_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);

ALTER TABLE ONLY public.notes
    ADD CONSTRAINT notes_csn_fkey FOREIGN KEY (csn) REFERENCES public.visits(csn);

ALTER TABLE ONLY public.problems
    ADD CONSTRAINT problems_csn_fkey FOREIGN KEY (csn) REFERENCES public.visits(csn);

ALTER TABLE ONLY public.processed_notes
    ADD CONSTRAINT processed_notes_csn_fkey FOREIGN KEY (csn) REFERENCES public.visits(csn);

ALTER TABLE ONLY public.referrals
    ADD CONSTRAINT referrals_csn_fkey FOREIGN KEY (csn) REFERENCES public.visits(csn);

ALTER TABLE ONLY public.visits
    ADD CONSTRAINT visits_mrn_fkey FOREIGN KEY (mrn) REFERENCES public.patients(mrn);

from datetime import datetime
from math import floor

from sqlalchemy import (
    Column, ForeignKey, Integer, String, DateTime, 
    Date, Text, Float, Time, types, Computed, Index, Boolean,
    JSON
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import declarative_base

from pgvector.sqlalchemy import Vector


class TSVector(types.TypeDecorator):
    impl = TSVECTOR


Base = declarative_base()


class Patients(Base):
    __tablename__ = "patients"
    mrn = Column(Integer, index=True, primary_key=True)  # this is mrn
    dob = Column(Date)


class Visits(Base):
    __tablename__ = "visits"
    csn = Column(Integer, index=True, primary_key=True)
    sex = Column(String)
    age = Column(Integer)
    mrn = Column(Integer, ForeignKey("patients.mrn"), index=True)
    arrival_date = Column(Date)
    arrival_time = Column(Time)
    postal_code = Column(String)
    chief_complaint = Column(String, index=True)
    diagnosis = Column(String)
    disposition = Column(String)
    ctas = Column(Integer, nullable=True)
    los = Column(Float)
    #human reviews are in the visits sections because we need review for both + and - cases
    processed = Column(Boolean)
    address=Column(String)
    city = Column(String)
    province = Column(String)


class Referrals(Base):
    __tablename__ = "referrals"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    csn = Column(Integer, ForeignKey("visits.csn"))
    referrals = Column(String)


class Problems(Base):
    __tablename__ = "problems"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    csn = Column(Integer, ForeignKey("visits.csn"))
    problem = Column(String)


class Notes(Base):
    __tablename__ = "notes"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    csn = Column(Integer, ForeignKey("visits.csn"))
    note_type = Column(String, index=True)
    author_type = Column(String)
    author_service = Column(String)
    note_text = Column(Text)
    # this is the postgres ts vector column, it is a computed column
    notes_ts_vector = Column(TSVector(), Computed(
        "to_tsvector('english', note_text)",
        persisted=True))

    __table_args__ = (Index('ix_raw_notes_ts_vector',
                            notes_ts_vector, postgresql_using='gin'), )

class ProcessedNotes(Base):
    __tablename__="processed_notes"
    id=Column(Integer, autoincrement=True, primary_key=True, index=True)
    csn = Column(Integer, ForeignKey("visits.csn"))
    note_text=Column(Text)
    note_text_ts_vector=Column(TSVector(), Computed("to_tsvector('english', note_text)",
                               persisted=True))
    jina_query_embed=Column(Vector(1024))
    jina_pass_embed = Column(Vector(1024))
    jina_sep_embed=Column(Vector(1024))
    jina_class_embed=Column(Vector(1024))
    jina_match_embed=Column(Vector(1024))
    __table_args__ = (Index('ix_note_text_ts_vector',
                            note_text_ts_vector, postgresql_using='gin'), )


class Cases(Base):
    __tablename__ = "chirpp_report"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    csn = Column(Integer, ForeignKey("visits.csn"))
    injury_date = Column(Date)
    injury_hour = Column(Integer)
    injury_min = Column(Integer)
    am_pm = Column(Integer)
    i_o = Column(Integer)
    location = Column(Integer)
    area = Column(Integer)
    place = Column(String)
    sk_narratvie=Column(Text)
    phac_narrative = Column(Text)
    w4p = Column(Integer)
    no1 = Column(Integer)
    bp1 = Column(Integer)
    no2 = Column(Integer)
    bp2 = Column(Integer)
    no3 = Column(Integer)
    bp3 = Column(Integer)
    notes = Column(Text) #I do not need this, this will be generated from raw notes do not need them in the excel
    # files
    disp = Column(Integer)
    intent = Column(Integer)
    veh = Column(Integer)
    veh_p = Column(String)
    sub = Column(Integer)
    sub_id = Column(String)
    sd1 = Column(Integer)
    sd2 = Column(Integer)
    sd3 = Column(Integer)
    sd4 = Column(Integer)
    sd5 = Column(Integer)
    sports_code = Column(Integer)
    # this is the sections removed notes these are used for inference for the most part
    phac_ts_vector = Column(TSVector(), Computed(
        "to_tsvector('english', phac_narrative)",
        persisted=True))
 
    notes_ts_vector = Column(TSVector(), Computed(
        "to_tsvector('english', notes)",
        persisted=True))
    sk_ts_vector = Column(TSVector(), Computed(
        "to_tsvector('english', sk_narrative)",
        persisted=True))

    __table_args__ = (
        Index('ix_phac_ts_vector',
              phac_ts_vector, postgresql_using='gin'),
        Index('ix_notes_ts_vector',
              notes_ts_vector, postgresql_using='gin'),
    )


# these are the custom labels that are created for different research purposes
class CustomLabels(Base):
    __tablename__ = "custom_labels"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    label_name = Column(String, index=True)
    label_description = Column(String)
    key_words = Column(String)  # this might be more than just comma seprarted key words
    context_aware = Column(Boolean)  # this will generate new section rules on the fly and search
    context_rules = Column(JSON)  # this will need a schema verification system
    active = Column(Boolean)


# these are the visits that correspond to different custom labels
class CustomLabelVisits(Base):
    __tablename__ = "custom_label_visits"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    label_id = Column(Integer, ForeignKey("custom_labels.id"))
    csn = Column(Integer, ForeignKey("visits.csn"))

class Users(Base):
    __tablename__="users"
    id=Column(Integer, autoincrement=True, primary_key=True, index=True)
    first_name=Column(String)
    last_name=Column(String)
    email=Column(String)
    password=Column(String)
    active=Column(Boolean)


class Managers(Base):
    __tablename__="managers"
    id=Column(Integer, autoincrement=True, primary_key=True, index=True)
    user_id=Column(Integer, ForeignKey("users.id"))
    manages=Column(Integer, ForeignKey("users.id"))

# this will keep track of all the activities in the database
class Logs(Base):
    __tablename__="logs"
    id=Column(Integer, autoincrement=True, primary_key=True)
    user=Column(Integer, ForeignKey("users.id"))
    timestamp=Column(DateTime)
    command=Column(String)



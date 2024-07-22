from datetime import datetime
from math import floor

from sqlalchemy import (
    Column, ForeignKey, Integer, String,
    Date, Text, Float, DateTime, types, Computed, Index, Boolean,
    JSON
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import declarative_base


class TSVector(types.TypeDecorator):
    impl = TSVECTOR


Base = declarative_base()


class Patients(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    mrn = Column(Integer, primary_key=True, index=True)  # this is mrn
    dob = Column(Date)
    # TODO there might be some edge cases due to leap years might need to use dateutil
    age = Column(Integer, Computed(floor(
        (datetime.today().date() - datetime.date(dob).days() / 365))
    ))


class Visits(Base):
    __tablename__ = "visits"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    csn = Column(Integer, index=True)
    sex = Column(String)
    mrn = Column(Integer, ForeignKey("patients.id"), index=True)
    arrival_date = Column(Date)
    arrival_time = Column(DateTime)
    postal_code = Column(String)
    chief_complaint = Column(String, index=True)
    diagnosis = Column(String)
    disposition = Column(String)
    ctas = Column(Integer, nullable=True)
    los = Column(Float)
    #human reviews are in the visits sections because we need review for both + and - cases
    human_review = Column(Boolean)


class Referrals(Base):
    __tablename__ = "referrals"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    visit_id = Column(Integer, ForeignKey("visits.id"))
    referrals = Column(String)


class Problems(Base):
    __tablename__ = "problems"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    visit_id = Column(Integer, ForeignKey("visits.id"))
    problem = Column(String)


class Notes(Base):
    __tablename__ = "notes"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    visit_id = Column(Integer, ForeignKey("visits.id"))
    note_type = Column(String, index=True)
    author_type = Column(String)
    author_service = Column(String)
    note_text = Column(Text)
    # this is the postgres ts vector column, it is a computed column
    notes_ts_vector = Column(TSVector(), Computed(
        "to_tsvector('english', note_text)",
        persisted=True))

    __table_args__ = (Index('ix_notes_ts_vector',
                            notes_ts_vector, postgresql_using='gin'),)


class Cases(Base):
    __tablename__ = "chirpp_report"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    visit_id = Column(Integer, ForeignKey("visits.id"))
    injury_date = Column(Date)
    injury_hour = Column(Integer)
    injury_min = Column(Integer)
    am_pm = Column(Integer)
    i_o = Column(Integer)
    location = Column(Integer)
    area = Column(Integer)
    place = Column(String)
    phac_narrative = Column(String)
    sk_narrative = Column(String)
    w4p = Column(Integer)
    no1 = Column(Integer)
    bp1 = Column(Integer)
    no2 = Column(Integer)
    bp2 = Column(Integer)
    no3 = Column(Integer)
    bp3 = Column(Integer)
    notes = Column(Integer)
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
    processed_notes = Column(String)
    phac_ts_vector = Column(TSVector(), Computed(
        "to_tsvector('english', phac_narrative)",
        persisted=True))
    sk_ts_vector = Column(TSVector(), Computed(
        "to_tsvector('english', sk_narrative)",
        persisted=True))
    processed_ts_vector = Column(TSVector(), Computed(
        "to_tsvector('english', sk_narrative)",
        persisted=True))

    __table_args__ = (
        Index('ix_phac_ts_vector',
              phac_ts_vector, postgresql_using='gin'),
        Index('ix_sk_ts_vector',
              sk_ts_vector, postgresql_using='gin'),
        Index('ix_processed_ts_vector',
              sk_ts_vector, postgresql_using='gin'),
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


# these are the visits that correspond to different custom labels
class CustomLabelVisits(Base):
    __tablename__ = "custom_label_visits"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    label_id = Column(Integer, ForeignKey("custom_labels.id"))
    visit_id = Column(Integer, ForeignKey("visits.id"))

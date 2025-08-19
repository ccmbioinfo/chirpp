import uuid

from sqlalchemy import (
    Column, ForeignKey, Integer, String, DateTime, 
    Date, Text, Float, Time, types, Computed, Index, Boolean,
    JSON
)
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import declarative_base

from pgvector.sqlalchemy import Vector


class TSVector(types.TypeDecorator):
    impl = TSVECTOR


Base = declarative_base()


class Patients(Base):
    __tablename__ = "patients"
    mrn = Column(Integer, index=True, primary_key=True)  # this is mrn
    dob = Column(Date)

#TODO add phac_embeddings to the database and calculate phac embeddings during generate report
class Visits(Base):
    __tablename__ = "visits"
    csn = Column(Integer, index=True, primary_key=True)
    sex = Column(String)
    age = Column(Integer)
    mrn = Column(Integer, ForeignKey("patients.mrn"), index=True)
    arrival_date = Column(Date, index=True)
    arrival_time = Column(Time)
    day_of_week = Column(String)
    sk_narrative=Column(Text)
    phac_narrative = Column(Text)
    postal_code = Column(String)
    chief_complaint = Column(String, index=True)
    diagnosis = Column(String, index=True)
    disposition = Column(String)
    ctas = Column(Integer, nullable=True)
    los = Column(Float)
    #human reviews are in the visits sections because we need review for both + and - cases
    processed = Column(Boolean)
    address=Column(String)
    city = Column(String)
    province = Column(String)
    probs=Column(Float)
    phac_embeddings = Column(Vector(1024))
    sk_narrative_vector = Column(TSVector(), Computed(
        "to_tsvector('english', sk_narrative)",
        persisted=True))
    phac_narrative_vector = Column(TSVector(), Computed(
        "to_tsvector('english', phac_narrative)",
        persisted=True))

    __table_args__ = (Index('ix_sk_narrative_ts_vector',
                            sk_narrative_vector, postgresql_using='gin'),
                      Index('ix_phac_narrative_ts_vector',
                            phac_narrative_vector, postgresql_using='gin'),
                      )


class Referrals(Base):
    __tablename__ = "referrals"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    csn = Column(Integer, ForeignKey("visits.csn"), index=True)
    referrals = Column(String)


class Problems(Base):
    __tablename__ = "problems"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    csn = Column(Integer, ForeignKey("visits.csn"), index=True)
    problem = Column(String)


class Notes(Base):
    __tablename__ = "notes"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    csn = Column(Integer, ForeignKey("visits.csn"), index=True)
    note_type = Column(String, index=True)
    author_type = Column(String, index=True)
    author_service = Column(String, index=True)
    note_text = Column(Text)
    # this is the postgres ts vector column, it is a computed column
    notes_ts_vector = Column(TSVector(), Computed(
        "to_tsvector('english', note_text)",
        persisted=True))

    __table_args__ = (Index('ix_raw_notes_ts_vector',
                            notes_ts_vector, postgresql_using='gin'), )

class ChunkedNotes(Base):
    __tablename__ = "chunked_notes"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id"), index=True)
    chunk_number = Column(Integer)
    chunk_text = Column(Text)
    embeddings=Column(Vector(1024))


class ProcessedNotes(Base):
    __tablename__="processed_notes"
    id=Column(Integer, autoincrement=True, primary_key=True, index=True)
    csn = Column(Integer, ForeignKey("visits.csn"), index=True)
    note_text=Column(Text)
    note_text_ts_vector=Column(TSVector(), Computed("to_tsvector('english', note_text)",
                               persisted=True))
    embeddings=Column(Vector(1024))
    __table_args__ = (Index('ix_note_text_ts_vector',
                            note_text_ts_vector, postgresql_using='gin'), )

class Cases(Base):
    __tablename__ = "chirpp_report"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    csn = Column(Integer, ForeignKey("visits.csn"), index=True)
    injury_date = Column(Date, index=True)
    injury_hour = Column(Integer)
    injury_min = Column(Integer)
    am_pm = Column(String)
    i_o = Column(String)
    location = Column(Integer)
    area = Column(Integer)
    place = Column(String)
    w4p = Column(Integer)
    no1 = Column(Integer)
    bp1 = Column(Integer)
    no2 = Column(Integer)
    bp2 = Column(Integer)
    no3 = Column(Integer)
    bp3 = Column(Integer)
    notes = Column(Text)
    disp = Column(Integer)
    intent = Column(Integer, index=True)
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

# these are the custom labels that are created for different research purposes
class CustomLabels(Base):
    __tablename__ = "custom_labels"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    label_name = Column(String, index=True)
    label_description = Column(Text)
    key_words = Column(String)  # this might be more than just comma seprarted key words
    context_aware = Column(Boolean)  # this will generate new section rules on the fly and search
    context_rules = Column(JSON)  # this will need a schema verification system
    active = Column(Boolean)


# these are the visits that correspond to different custom labels
class CustomLabelVisits(Base):
    __tablename__ = "custom_label_visits"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    label_id = Column(Integer, ForeignKey("custom_labels.id"), index=True)
    csn = Column(Integer, ForeignKey("visits.csn"), index=True)

class Users(Base):
    __tablename__="users"
    id=Column(Integer, autoincrement=True, primary_key=True, index=True)
    uuid=Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
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
    user=Column(Integer, ForeignKey("users.id"), index=True)
    timestamp=Column(DateTime, index=True)
    command=Column(String)



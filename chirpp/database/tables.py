import uuid

from sqlalchemy import (
    Column, ForeignKey, Integer, String,
    Date, Text, Float, Time, types, Computed, Index
)
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import declarative_base

from pgvector.sqlalchemy import Vector


class TSVector(types.TypeDecorator):
    impl = TSVECTOR


Base = declarative_base()

# sex is not included here because I've seen some notes change even though it should not. there is no gender field
class Patients(Base):
    __tablename__ = "patients"
    mrn = Column(Integer, index=True, primary_key=True)
    scr_mrn=Column(Integer, index=True)
    dob = Column(Date)


# the columns here are from epic they will not change
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
    notes=Column(Text)
    postal_code = Column(String)
    chief_complaint = Column(String, index=True)
    diagnosis = Column(String, index=True)
    disposition = Column(String)
    ctas = Column(Integer, nullable=True)
    los = Column(Float)
    address=Column(String)
    city = Column(String)
    province = Column(String)
    probs=Column(Float)
    sk_narrative_vector = Column(TSVector(), Computed(
        "to_tsvector('english', sk_narrative)",
        persisted=True))
    notes_vector = Column(TSVector(), Computed(
        "to_tsvector('english', notes)",
        persisted=True))

    __table_args__ = (Index('ix_sk_narrative_ts_vector',
                            sk_narrative_vector, postgresql_using='gin'),
                      Index('ix_visits_notes_ts_vector',
                            notes_vector, postgresql_using='gin'),
                      )


# these are summaries of a visits, not all the summaries are used in chirpp but they are all summarized in case
# a presentation is missed by the classifier model and we want to add it later.
# of the chirpp cases some summaries might get updated so we will need a version column, when the summary is updated
# we will need to update the embeddings as well.
class Summaries(Base):
    __tablename__ = "summaries"
    id = Column(Integer, primary_key=True)
    csn = Column(Integer, ForeignKey("visits.csn"), index=True)
    phac_narrative = Column(String)
    phac_embeddings = Column(Vector(4096))
    version = Column(Integer, nullable=False)
    phac_narrative_vector = Column(TSVector(), Computed(
        "to_tsvector('english', phac_narrative)",
        persisted=True))

    __table_args__ = (
        Index('ix_phac_narrative_ts_vector',
              phac_narrative_vector, postgresql_using='gin'),
        )


# same as above
class Referrals(Base):
    __tablename__ = "referrals"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    csn = Column(Integer, ForeignKey("visits.csn"), index=True)
    referrals = Column(String)

# same as above
class Problems(Base):
    __tablename__ = "problems"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    csn = Column(Integer, ForeignKey("visits.csn"), index=True)
    problem = Column(String)

# this is the only table that uses uuid because it is the only table that has another table that foreign keys to it
# I can use .returning to get the ids but that is an extra step and not needed, we do not care about orders and we will
# only be using the id to pull things from the chunked notes table
class Notes(Base):
    __tablename__ = "notes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

# these are just semantically chunked notes for rag applications, I am still adding them to the databse but
# they are not really needed for v0 or v1, the notes are from epic the embeeding model may change but again unlikely
class ChunkedNotes(Base):
    __tablename__ = "chunked_notes"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    note_id = Column(UUID(as_uuid=True), ForeignKey("notes.id"), index=True)
    chunk_number = Column(Integer)
    chunk_text = Column(Text)
    embeddings=Column(Vector(4096))

# this may change but unlikely, the "processed notes" are just the regular notes where we remove things that we do not care
# about such as vitals and vaccinations etc. while they are used extensively by all the models the chirpp team do not use
# them directly, so they will stay as is most likely
class ProcessedNotes(Base):
    __tablename__="processed_notes"
    id=Column(Integer, autoincrement=True, primary_key=True, index=True)
    csn = Column(Integer, ForeignKey("visits.csn"), index=True)
    note_text=Column(Text)
    embeddings=Column(Vector(4096))
    note_text_ts_vector = Column(TSVector(), Computed("to_tsvector('english', note_text)",
                                                      persisted=True))
    __table_args__ = (Index('ix_note_text_ts_vector',
                            note_text_ts_vector, postgresql_using='gin'), )

# this is the main report that is filled by the chirpp team, I will be attaching some file under documents to
# give an idea about the possible files this is the one that will need versioning
# there is one column that sets the version that is autoincremented if the csn is already there
class Cases(Base):
    __tablename__ = "chirpp_report"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    csn = Column(Integer, ForeignKey("visits.csn"), index=True)
    injury_date = Column(Integer, index=True)
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
    version = Column(Integer, nullable=False, default=1)


# Authentication table for UI access
class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    password_changed = Column(Integer, nullable=False, default=0)  # 0 = not changed, 1 = changed
    is_active = Column(Integer, nullable=False, default=1)  # 1 = active, 0 = inactive
    created_at = Column(Date, nullable=False)
    last_login = Column(Date, nullable=True)


# Manager table for role-based access control
class Manager(Base):
    __tablename__ = "manager"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)


# ManagedUsers junction table - tracks which users each manager manages
class ManagedUsers(Base):
    __tablename__ = "managed_users"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    manager_id = Column(Integer, ForeignKey("manager.id"), nullable=False, index=True)
    managed_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)


# Logs table for tracking user actions
class Logs(Base):
    __tablename__ = "logs"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String, nullable=False, index=True)  # login, raw_report, chirpp_report, query, upload_raw, upload_report
    parameters = Column(Text, nullable=True)  # JSON string of parameters
    timestamp = Column(Date, nullable=False, index=True)


# Query Reports table for tracking saved query report files
class QueryReports(Base):
    __tablename__ = "query_reports"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    file_path = Column(String, nullable=False)  # Absolute path to the saved report file
    query_parameters = Column(Text, nullable=True)  # JSON string of query parameters
    created_at = Column(Date, nullable=False, index=True)
    result_count = Column(Integer, nullable=True)  # Number of results in the report

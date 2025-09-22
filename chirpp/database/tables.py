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

# sex is not included here because I've seem some notes change even though it should not. there is no gender field
class Patients(Base):
    __tablename__ = "patients"
    mrn = Column(Integer, index=True, primary_key=True)  # this is mrn
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

    __table_args__ = (Index('ix_sk_narrative_ts_vector',
                            sk_narrative_vector, postgresql_using='gin'),

                      )

# these are the visit summaries, all cases will be summarized by AI and some
# some (the ones that are actual cases (see chirrp_report table) might have their summaries
# updated
class Summaries(Base):
    __tablename__ = "summaries"
    id = Column(Integer, primary_key=True)
    csn = Column(Integer, ForeignKey("visits.csn"), index=True)
    phac_narrative = Column(String)
    phac_embeddings = Column(Vector(1024))
    version = Column(Integer, nullable=False, default=1)
    phac_narrative_vector = Column(TSVector(), Computed(
        "to_tsvector('english', phac_narrative)",
        persisted=True))

    __table_args__ = (
        Index('ix_phac_narrative_ts_vector',
              phac_narrative_vector, postgresql_using='gin'),
        )

    __mapper_args__ = {
        "version_id_col": version,
        "version_id_generator": lambda version: version + 1
    }


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

# same as above
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

# these are just semantically chunked notes for rag applications, I am still adding them to the databse but
# they are not really needed for v0 or v1, the notes are from epic the embeeding model may change but again unlikely
class ChunkedNotes(Base):
    __tablename__ = "chunked_notes"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id"), index=True)
    chunk_number = Column(Integer)
    chunk_text = Column(Text)
    embeddings=Column(Vector(1024))

# this may change but unlikely, the "processed notes are just the regular notes where we remove things that we do not care
# about such as vitals and vaccinations etc.
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

# this is the main report that is filled by the chirpp team, I will be attaching some file under documents to
# give an idea about the possible files this is the one that will need versioning
# there is one column that sets the version that is autoincremented if the csn is already there
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
    version = Column(Integer, nullable=False, default=1)
    __mapper_args__ = {
        "version_id_col": version,
        "version_id_generator": lambda version: version + 1
    }



    # this is the sections removed notes these are used for inference for the most part

# If you look at the other branches you will see that there were more tables that were reserved for auth because
# I was planning on writing the whole ui myself. So I have removed those tables and leave it up to you
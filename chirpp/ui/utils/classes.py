
import hashlib
import uuid
from datetime import datetime
from dataclasses import dataclass
from functools import wraps, cached_property
import json

import bcrypt

from sqlalchemy import create_engine, select

from chirpp.database.database import DataBase
from chirpp.database.query import Query
from chirpp.ui.utils.errors import *

@dataclass(frozen=True)
class Database:
    user:str
    pwd:str
    port:str
    host: str
    db_name:str

    @property
    def conn_str(self):
        conn_str=f'postgresql+psycopg2://{self.user}:{self.pwd}@{self.host}:{self.port}/{self.db_name}'
        return conn_str

    @cached_property
    def engine(self):
        engine=create_engine(self.conn_str)
        return engine

    @cached_property
    def connection(self):
        db=DataBase(self.engine)
        return db

@dataclass
class User:
    id: int
    email: str
    first_name: str
    last_name: str
    password_hash: str #this is the hash
    created_at: datetime
    is_manager: bool
    is_active: bool
    password_changed: bool

    #This is becoming a property because we do not need to call it unless the user clicks on the admin page
    # then we will generate it on the spot
    @property
    def manages(self):
        manages_table=st.session_state.database.metadata.tables['managed_users']
        users_table = st.session_state.database.metadata.tables['users']
        stmt = (
            select(
                users_table.c.id,
                users_table.c.first_name,
                users_table.c.last_name,
                users_table.c.email,
                users_table.c.is_active
            )
            .join(manages_table, users_table.c.id == manages_table.c.managed_user_id)
            .where(manages_table.c.manager_id == self.id)
        )
        # 3. Execute
        result = st.session_state.database.session.execute(stmt).fetchall()

        if len(result)==0:
            return None
        else:
            return result


    @staticmethod
    def _check_credentials(email: str, password: str, database):
        users_table=database.metadata.tables['users']
        stmt=users_table.select().where(users_table.c.email==email)
        user_info=database.session.execute(stmt).fetchall()

        if len(user_info)==0:
            return None

        if len(user_info)>1:
            raise TooManyUsersError()

        pw_hash=user_info[0].password_hash
        correct_pw=bcrypt.checkpw(password.encode(), pw_hash.encode())

        if correct_pw:
            return user_info[0]
        else:
            return None

    @classmethod
    def from_db(cls, email, password, database):
        info=cls._check_credentials(email, password, database)
        if info is None:
            return None
        elif not info.is_active:
            return None
        else:
            return cls(id=info.id, email=info.email, first_name=info.first_name, last_name=info.last_name,
                       password_hash=info.password_hash, created_at=info.created_at, password_changed=info.password_changed,
                       is_manager=info.is_manager, is_active=info.is_active)

    def change_password(self, new_password, database):
        users_table = database.metadata.tables['users']
        new_hash=bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        if new_hash==self.password_hash:
            new_hash=bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

        if not self.password_changed:
            update_pw = users_table.update().where(users_table.c.id == self.id).values(password_hash=new_hash,
                                                                                       password_changed=True)
        else:
            update_pw=users_table.update().where(users_table.c.id == self.id).values(password=new_hash)

        database.session.execute(update_pw)
        database.session.commit()
        self.password_hash=new_hash
        if not self.password_changed:
            self.password_changed = True

    def change_email(self, new_email, database):
        users_table = database.metadata.tables['users']
        update_email = users_table.update().where(users_table.c.id == self.id).values(email=new_email)
        database.session.execute(update_email)
        database.session.commit()
        self.email=new_email

    def add_user(self, first, last, email, database):
        if self.is_manager:
            user_id=uuid.uuid4().hex
            users_table = database.metadata.tables['users']
            managers_table = database.metadata.tables['managed_users']

            pwd=hashlib.md5(first.encode()).hexdigest()
            pwd_hashed=bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
            user_stms=users_table.insert().values(id=user_id, first_name=first, last_name=last, email=email,
                                        password_hash=pwd_hashed, is_active=True,
                                        password_changed=False, created_at=datetime.now(),
                                        is_manager=False)
            manager_stmt=managers_table.insert().values(manager_id=self.id, managed_user_id=user_id)
            database.session.execute(user_stms)
            database.session.execute(manager_stmt)
            database.session.commit()
            return pwd
        else:
            raise RoleError(f"User {self.id} is not a manager")

    def deactivate_user(self, user_id, database):
        users_table = database.metadata.tables['users']

        managed_ids = [item["user_id"] for item in self.manages]
        if user_id in managed_ids:
            users_table.update().where(users_table.c.id == self.id).values(is_active=False)
        else:
            raise RoleError(f"User {id} is not one of the subordinates")

    def promote(self, manager_id, managed_ids, database):
        users_table = database.metadata.tables['users']
        managers_table=database.metadata.tables['managed_users']

        managed_ids = [id for id in  managed_ids if id in self.manages["id"]]
        if manager_id in managed_ids:
            user_stmt=users_table.update().where(users_table.c.id == self.id).values(is_manager=True)
            database.session.execute(user_stmt)
            database.session.commit()
            for user in managed_ids:
                if user in managed_ids:
                    sub_stmt=managers_table.insert().values(manager_id=manager_id, managed_user_id=user)
                    database.session.execute(sub_stmt)
                    database.session.commit()
                else:
                    raise RoleError(f"User {user} is not one of the subordinates")
        else:
            raise RoleError(f"User {id} is not one of the subordinates")

    def demote(self, user_id, database):
        users_table = database.metadata.tables['users']
        managers_table = database.metadata.tables['managed_users']
        user_stmt = users_table.update().where(users_table.c.id == user_id).values(is_manager=False)
        database.session.execute(user_stmt)
        database.session.commit()

        managers_table.delete().where(managers_table.c.manager_id == user_id)
        database.session.execute(managers_table)
        database.session.commit()


    def reset_password(self, user_id, database):
        pass


@dataclass
class Query:
    user_id: str
    type: str
    parameters: dict | None
    timestamp: datetime


    @classmethod
    def generate_report(cls):
        pass

    @classmethod
    def search_db(cls):
        pass



def track_activity(action, user_id, database):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            log = Log(
                user_id=user_id,
                action=action,
                timestamp=datetime.utcnow(),
                parameters={
                    "args": [str(a) for a in args],
                    "kwargs": {k: str(v) for k, v in kwargs.items()},
                },
            )
            log.to_db(database)
            return result
        return wrapper
    return decorator

# using uuids here so I don't have to worry about running returning
@dataclass
class Log:
    user_id: str
    action: str
    timestamp: datetime
    parameters: dict | None = None
    def to_db(self, database):
        logs_table = database.metadata.tables["logs"]
        stmt = logs_table.insert().values(
            id=str(uuid.uuid4()),
            user_id=self.user_id,
            action=self.action,
            parameters=json.dumps(self.parameters) if self.parameters else None,
            timestamp=self.timestamp,
        )
        with database.engine.begin() as conn:
            conn.execute(stmt)


@dataclass
class UserLogs:
    user_id: str
    logs: list[Log]

    @classmethod
    def from_db(cls, user_id, database):
        logs_table = database.metadata.tables["logs"]

        stmt = logs_table.select().where(
            logs_table.c.user_id == user_id
        ).order_by(logs_table.c.timestamp.desc())

        with database.engine.begin() as conn:
            rows = conn.execute(stmt).fetchall()

        logs = [
            Log(
                user_id=row.user_id,
                action=row.action,
                timestamp=row.timestamp,
                parameters=json.loads(row.parameters) if row.parameters else None,
            )
            for row in rows
        ]

        return cls(user_id=user_id, logs=logs)


@dataclass
class ManagerLogs:
    manager_id: str
    logs: list[Log]

    @classmethod
    def from_db(cls, manager_id, database):

        logs_table = database.metadata.tables["logs"]
        users_table = database.metadata.tables["users"]
        managed_users_table = database.metadata.tables["managed_users"]

        managed_users_stmt=managed_users_table.select(managed_users_table.c.managed_user_id).\
            where(managed_users_table.c.user_id == manager_id).subquery()

        stmt=logs_table.select().where(users_table.c.id.in_(managed_users_stmt.c.managed_user_id))
        rows=database.session.execute(stmt).fetchall()

        logs = [
            Log(
                user_id=row.user_id,
                action=row.action,
                timestamp=row.timestamp,
                parameters=json.loads(row.parameters) if row.parameters else None,
            )
            for row in rows
        ]

        return cls(manager_id=manager_id, logs=logs)
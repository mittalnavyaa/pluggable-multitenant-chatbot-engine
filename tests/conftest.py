import os
import sys
import pytest
import sqlite3
import uuid
import datetime
import re
from sqlalchemy import event
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

# 1. Register UUID adapter for sqlite3 so that raw SQL inserts with UUIDs work
sqlite3.register_adapter(uuid.UUID, lambda u: u.hex)

# Patch SQLAlchemy's UUID bind_processor to gracefully accept string inputs during tests
from sqlalchemy.types import UUID
original_bind_processor = UUID.bind_processor

def patched_bind_processor(self, dialect):
    proc = original_bind_processor(self, dialect)
    if proc is not None:
        def process(value):
            if isinstance(value, str):
                try:
                    value = uuid.UUID(value)
                except ValueError:
                    pass
            return proc(value)
        return process
    return proc

UUID.bind_processor = patched_bind_processor

# 2. Enforce environment variables for testing BEFORE importing any backend source code
os.environ["DATABASE_URL"] = "sqlite:///test_db.sqlite"
os.environ["EMBEDDING_PROVIDER"] = "mock"
os.environ["EMBEDDING_MODEL"] = "mock-1536"
os.environ["EMBEDDING_DIMENSION"] = "1536"

# 3. Custom type compiler to compile PostgreSQL JSONB to JSON on SQLite
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"

# 4. Resolve the backend path to allow importing 'src'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, "apps", "central-hub-backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Import engine to register events
from src.database.database import engine

def date_trunc(format, ts_val):
    if not ts_val:
        return None
    if isinstance(ts_val, datetime.datetime):
        ts_str = ts_val.strftime("%Y-%m-%d %H:%M:%S")
    else:
        ts_str = str(ts_val).replace("T", " ")
    if format == 'hour':
        return ts_str[:13] + ":00:00"
    elif format == 'day':
        return ts_str[:10] + " 00:00:00"
    return ts_str

@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    try:
        dbapi_connection.create_function("uuid_generate_v4", 0, lambda: uuid.uuid4().hex)
        dbapi_connection.create_function("date_trunc", 2, date_trunc)
        dbapi_connection.create_function("now", 0, lambda: datetime.datetime.utcnow().isoformat())
        dbapi_connection.create_function("timezone", 2, lambda tz, val: val)
    except Exception:
        pass

def rewrite_sql_for_sqlite(sql):
    # Remove ::int, ::float, ::timestamp
    sql = sql.replace("::int", "")
    sql = sql.replace("::float", "")
    sql = sql.replace("::timestamp", "")
    # Remove INTERVAL modifier
    sql = re.sub(r"-\s*INTERVAL\s*'[^']+'", "", sql)
    return sql

@event.listens_for(engine, "before_cursor_execute", retval=True)
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    statement = rewrite_sql_for_sqlite(statement)
    return statement, parameters

# Mock classes for MinIO and Redis to avoid real connection attempts during tests
class MockRedis:
    def __init__(self, *args, **kwargs):
        pass
    @classmethod
    def from_url(cls, *args, **kwargs):
        return cls()
    def publish(self, *args, **kwargs):
        pass
    def get(self, *args, **kwargs):
        return None
    def set(self, *args, **kwargs):
        return True
    def delete(self, *args, **kwargs):
        return True

class MockMinio:
    _store = {}

    def __init__(self, *args, **kwargs):
        pass

    def bucket_exists(self, bucket_name):
        return True

    def make_bucket(self, bucket_name):
        pass

    def put_object(self, bucket_name, object_name, data, length, part_size=None, content_type=None):
        # Handle file-like objects or bytes
        if hasattr(data, "read"):
            content = data.read()
        else:
            content = data
        self._store[object_name] = content
        return object_name

    def get_object(self, bucket_name, object_name):
        if object_name not in self._store:
            from minio.error import S3Error
            from urllib3.response import HTTPResponse
            mock_resp = HTTPResponse(status=404, body=b"")
            raise S3Error(
                code="NoSuchKey",
                message="The specified key does not exist.",
                resource=object_name,
                request_id="mock_id",
                host_id="mock_host",
                response=mock_resp
            )
        content = self._store[object_name]
        
        class MockResponse:
            def __init__(self, content):
                self.content = content
            def read(self):
                if isinstance(self.content, str):
                    return self.content.encode("utf-8")
                return self.content
            def stream(self, chunk_size=32*1024):
                yield self.read()
            def close(self):
                pass
            def release_conn(self):
                pass
        return MockResponse(content)

    def remove_object(self, bucket_name, object_name):
        if object_name in self._store:
            del self._store[object_name]

# 5. Patch minio, redis, and qdrant at module-level import time
import minio
minio.Minio = MockMinio

import redis
redis.Redis = MockRedis

from qdrant_client import QdrantClient as OriginalQdrantClient
class MockedQdrantClient(OriginalQdrantClient):
    def __init__(self, *args, **kwargs):
        super().__init__(location=":memory:")

import qdrant_client
qdrant_client.QdrantClient = MockedQdrantClient

@pytest.fixture(autouse=True)
def mock_minio_and_redis(monkeypatch):
    monkeypatch.setattr(minio, "Minio", MockMinio)
    monkeypatch.setattr(redis, "Redis", MockRedis)
    monkeypatch.setattr(qdrant_client, "QdrantClient", MockedQdrantClient)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    db_file = "test_db.sqlite"
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass
            
    # Import and run create_all to initialize SQLite schema
    from src.database.base import Base
    from src.database.database import engine
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Clean up database file after session finishes
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass

# 6. Intercept result sets returned by SQLAlchemy to convert SQLite datetime strings to datetime objects
class PatchedRow:
    def __init__(self, original_row):
        self._row = original_row
        
    def __getattr__(self, name):
        val = getattr(self._row, name)
        return self._convert_val(val)
        
    def __getitem__(self, index):
        val = self._row[index]
        return self._convert_val(val)
        
    def _convert_val(self, val):
        if isinstance(val, str):
            # Matches formats like "2026-07-16 00:00:00" or "2026-07-16 00:00:00.000000"
            if len(val) >= 19 and val[4] == '-' and val[7] == '-' and val[10] == ' ' and val[13] == ':':
                try:
                    return datetime.datetime.strptime(val[:19], "%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass
            # Matches formats with T like "2026-07-16T00:00:00"
            elif len(val) >= 19 and val[4] == '-' and val[7] == '-' and val[10] == 'T' and val[13] == ':':
                try:
                    return datetime.datetime.strptime(val[:19], "%Y-%m-%dT%H:%M:%S")
                except Exception:
                    pass
        return val
        
    def __repr__(self):
        return repr(self._row)

class PatchedResult:
    def __init__(self, original_result):
        self._res = original_result
        
    def __getattr__(self, name):
        return getattr(self._res, name)
        
    def __iter__(self):
        for row in self._res:
            yield PatchedRow(row)
            
    def all(self):
        return [PatchedRow(row) for row in self._res.all()]
        
    def first(self):
        row = self._res.first()
        return PatchedRow(row) if row is not None else None
        
    def one(self):
        return PatchedRow(self._res.one())
        
    def scalar(self):
        return self._res.scalar()

from sqlalchemy.engine import Connection
original_execute = Connection.execute

def patched_execute(self, statement, parameters=None, **kw):
    res = original_execute(self, statement, parameters, **kw)
    return PatchedResult(res)

Connection.execute = patched_execute

# 7. Configure Celery to run tasks eagerly (synchronously) during testing
from src.celery_app import celery_app
celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = False

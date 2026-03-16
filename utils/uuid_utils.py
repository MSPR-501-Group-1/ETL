"""
Deterministic UUID Generation Utilities
Uses UUID v5 (name-based) for consistent, reproducible IDs
"""
import uuid
from pyspark.sql.types import StringType
from pyspark.sql.functions import udf

# Define namespaces for different entity types
# These are fixed UUIDs that serve as namespaces for generating deterministic UUIDs
NAMESPACE_USER = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
NAMESPACE_EXERCISE = uuid.UUID('6ba7b811-9dad-11d1-80b4-00c04fd430c8')
NAMESPACE_FOOD = uuid.UUID('6ba7b812-9dad-11d1-80b4-00c04fd430c8')
NAMESPACE_ACTIVITY = uuid.UUID('6ba7b813-9dad-11d1-80b4-00c04fd430c8')
NAMESPACE_SESSION = uuid.UUID('6ba7b814-9dad-11d1-80b4-00c04fd430c8')
NAMESPACE_DETAIL = uuid.UUID('6ba7b815-9dad-11d1-80b4-00c04fd430c8')
NAMESPACE_PROFILE = uuid.UUID('6ba7b816-9dad-11d1-80b4-00c04fd430c8')
NAMESPACE_METRIC  = uuid.UUID('6ba7b817-9dad-11d1-80b4-00c04fd430c8')
NAMESPACE_ROLE    = uuid.UUID('6ba7b818-9dad-11d1-80b4-00c04fd430c8')

# Python functions for UUID generation
def generate_user_uuid(email: str) -> str:
    """Generate deterministic user UUID from email"""
    if not email:
        return None
    return str(uuid.uuid5(NAMESPACE_USER, email))

def generate_exercise_uuid(name: str) -> str:
    """Generate deterministic exercise UUID from exercise name"""
    if not name:
        return None
    return str(uuid.uuid5(NAMESPACE_EXERCISE, name))

def generate_food_uuid(name: str, brand: str = None) -> str:
    """Generate deterministic food UUID from name and optional brand"""
    if not name:
        return None
    key = f"{name}|{brand or 'no_brand'}"
    return str(uuid.uuid5(NAMESPACE_FOOD, key))

def generate_activity_uuid(name: str) -> str:
    """Generate deterministic activity UUID from activity name"""
    if not name:
        return None
    return str(uuid.uuid5(NAMESPACE_ACTIVITY, name))

def generate_session_uuid(user_id: str, timestamp: str, activity_id: str = None, source: str = None) -> str:
    """Generate deterministic session UUID from user_id, timestamp, optional activity_id, and source"""
    if not user_id or not timestamp:
        return None
    key = f"{user_id}|{timestamp}|{activity_id or 'no_activity'}|{source or 'default'}"
    return str(uuid.uuid5(NAMESPACE_SESSION, key))

def generate_detail_uuid(session_id: str, exercise_id: str, sequence: int) -> str:
    """Generate deterministic detail UUID from session_id, exercise_id, and sequence number"""
    if not session_id or not exercise_id:
        return None
    key = f"{session_id}|{exercise_id}|{sequence}"
    return str(uuid.uuid5(NAMESPACE_DETAIL, key))

def generate_profile_uuid(user_id: str) -> str:
    """Generate deterministic profile UUID from user_id"""
    if not user_id:
        return None
    return str(uuid.uuid5(NAMESPACE_PROFILE, user_id))

def generate_metric_uuid(user_id: str, date: str) -> str:
    """Generate deterministic metric UUID from user_id and date"""
    if not user_id or not date:
        return None
    key = f"{user_id}|{date}"
    return str(uuid.uuid5(NAMESPACE_METRIC, key))

def generate_role_uuid(role_name: str) -> str:
    """Generate deterministic role UUID from role name (e.g. 'FREEMIUM')."""
    if not role_name:
        return None
    return str(uuid.uuid5(NAMESPACE_ROLE, role_name))

# Pre-computed default role IDs — used in pipelines and seed SQL (Step 10)
DEFAULT_FREEMIUM_ROLE_ID = generate_role_uuid("FREEMIUM")

# PySpark UDFs for use in transformations
user_uuid_udf = udf(generate_user_uuid, StringType())
role_uuid_udf = udf(generate_role_uuid, StringType())
exercise_uuid_udf = udf(generate_exercise_uuid, StringType())
food_uuid_udf = udf(generate_food_uuid, StringType())
activity_uuid_udf = udf(generate_activity_uuid, StringType())

# Session UUID UDF with optional source parameter (4 arguments)
def _session_uuid_wrapper(user_id, timestamp, activity_id, source=None):
    return generate_session_uuid(user_id, timestamp, activity_id, source)

session_uuid_udf = udf(_session_uuid_wrapper, StringType())
detail_uuid_udf = udf(generate_detail_uuid, StringType())
profile_uuid_udf = udf(generate_profile_uuid, StringType())
metric_uuid_udf = udf(generate_metric_uuid, StringType())

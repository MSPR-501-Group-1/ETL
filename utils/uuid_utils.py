import uuid
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType

NAMESPACE_EXERCISE = uuid.UUID('6ba7b811-9dad-11d1-80b4-00c04fd430c8')
NAMESPACE_FOOD     = uuid.UUID('6ba7b812-9dad-11d1-80b4-00c04fd430c8')

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


exercise_uuid_udf = udf(generate_exercise_uuid, StringType())
food_uuid_udf = udf(generate_food_uuid, StringType())

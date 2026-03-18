"""
Reference data seeding for HealthAI Coach database.

Inserts the minimum required rows before any pipeline data is loaded:
  - data_source  (FK target for etl_execution)
  - role         (FK target for user_)
  - health_goal  (FK target for user_profile)

Uses ON CONFLICT DO NOTHING — safe to re-run at every ETL start.
"""
import uuid
from datetime import datetime
from typing import Optional

import psycopg2

from utils.db_utils import get_db_config
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Namespace UUIDs (fixed — never change) ──────────────────────────────────
_NS_SOURCE = uuid.UUID('6ba7b820-9dad-11d1-80b4-00c04fd430c8')
_NS_HG     = uuid.UUID('6ba7b819-9dad-11d1-80b4-00c04fd430c8')

def _source_id(key: str) -> str:
    return str(uuid.uuid5(_NS_SOURCE, key))

def _goal_id(label: str) -> str:
    return str(uuid.uuid5(_NS_HG, label))


# ── Static seed data ─────────────────────────────────────────────────────────

DATA_SOURCES = [
    (
        _source_id("kaggle:adilshamim8/daily-food-and-nutrition-dataset"),
        "Nutrition Dataset",
        "KAGGLE", "CSV",
        "adilshamim8/daily-food-and-nutrition",
        None, True,
    ),
    (
        _source_id("kaggle:trolukovich/nutritional-values-for-common-foods-and-products"),
        "Nutrition Values Dataset",
        "KAGGLE", "CSV",
        "trolukovich/nutritional-values",
        None, True,
    ),
]

HEALTH_GOALS = [
    (_goal_id("LOSE_WEIGHT"),     "LOSE_WEIGHT",     "Reduce body fat"),
    (_goal_id("GAIN_MUSCLE"),     "GAIN_MUSCLE",     "Increase muscle mass"),
    (_goal_id("MAINTAIN_WEIGHT"), "MAINTAIN_WEIGHT", "Maintain current weight"),
    (_goal_id("IMPROVE_STAMINA"), "IMPROVE_STAMINA", "Improve cardiovascular endurance"),
]


# ── Public function ───────────────────────────────────────────────────────────

def seed_reference_data() -> bool:
    """
    Insert required reference rows before any pipeline data is loaded.

    Insert order: data_source → role → health_goal
    (data_source must exist before etl_execution can reference it.)
    """
    from utils.uuid_utils import generate_role_uuid

    roles = [
        (generate_role_uuid("FREEMIUM"),     "FREEMIUM",     True),
        (generate_role_uuid("PREMIUM"),      "PREMIUM",      True),
        (generate_role_uuid("PREMIUM_PLUS"), "PREMIUM_PLUS", True),
        (generate_role_uuid("B2B"),          "B2B",          True),
        (generate_role_uuid("ADMIN"),        "ADMIN",        True),
    ]

    config = get_db_config()
    try:
        conn = psycopg2.connect(
            host=config["host"], port=int(config["port"]),
            dbname=config["database"], user=config["user"], password=config["password"],
        )
        now = datetime.utcnow()
        with conn:
            with conn.cursor() as cur:
                for src_id, name, src_type, fmt, url, expected, is_active in DATA_SOURCES:
                    cur.execute(
                        'INSERT INTO data_source '
                        '(source_id, source_name, source_type, format, source_url, '
                        'expected_records, last_updates, is_active) '
                        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING',
                        (src_id, name, src_type, fmt, url, expected, now, is_active),
                    )
                for role_id, role_type, is_system in roles:
                    cur.execute(
                        'INSERT INTO "role" (role_id, role_type, is_system) '
                        'VALUES (%s, %s::role_type_enum, %s) ON CONFLICT DO NOTHING',
                        (role_id, role_type, is_system),
                    )
                for goal_id, label, description in HEALTH_GOALS:
                    cur.execute(
                        'INSERT INTO health_goal (goal_id, label, description) '
                        'VALUES (%s, %s, %s) ON CONFLICT DO NOTHING',
                        (goal_id, label, description),
                    )
        conn.close()
        logger.info(
            f"✅ Reference data seeded: {len(DATA_SOURCES)} sources, "
            f"{len(roles)} roles, {len(HEALTH_GOALS)} health goals"
        )
        return True
    except Exception as e:
        logger.error(f"seed_reference_data failed: {e}")
        return False

# ETL Adaptation — New DB Schema (`01_initdb.sql`)

## Step 1 — Update `database/init.sql` reference
- [x] Replace (or symlink) `database/init.sql` with `database/01_initdb.sql` so `init_db_schema()` in `utils/load.py` points to the correct file

---

## Step 2 — Update `utils/uuid_utils.py` → VARCHAR(50) keys
- [x] PKs are now `VARCHAR(50)`, not UUID columns with `DEFAULT uuid_generate_v4()` — UUID v5 strings (36 chars) still fit, no change needed to generation logic, but verify nothing truncates them

---

## Step 3 — Update `utils/db_utils.py` → `DB_TABLE_SCHEMAS`
- [x] Rename `user` → `user_`
- [x] Rename `food` → `ingredients` and remap column names (`calories_100g` → `calories_g`, `protein_100g` → `protein_g`, `carbs_100g` → `carbs_g`, `fat_100g` → `fat_g`, drop `nutriscore`/`category_ref` → use ENUMs `nutriscore_enum`/`category_enum`)
- [x] Update `user_profile`: remove `profile_id` PK, `user_id` is now both PK and FK; add `goal_id`, `allergies` (enum), `diet_type` (enum); remove `health_goal_id`, `preferences_json`
- [x] Update `user_metrics`: remove `user_id` column (now linked via `gets` junction table); rename `body_fat_percentage` → `body_fat_pourcentage`
- [x] Update `exercise`: `difficulty_level` → `exercise_difficulty_enum`, `category` → `exercise_category_enum`, `body_part_target` → `body_part_enum`; `description VARCHAR(50)` (truncate long values); remove `created_at`/`updated_at`
- [x] Update `workout_session`: remove `activity_id`, rename `duration_minutes` → `duration_time SMALLINT`, remove `distance_km`
- [x] Rename `session_detail` → `exercice_details`; remove `weight_kg`
- [x] Remove `activity_type` (table no longer exists)
- [x] Add `gets` schema (junction: `goal_id`, `metric_id`)

---

## Step 4 — Update `utils/load.py`
- [x] Update `init_db_schema()` SQL path to point to `01_initdb.sql`
- [x] Update `load_order` in `main.py` Stage 7:
  - New FK-safe order: `health_goal` → `role` → `user_profile` → `user_` → `user_metrics` → `gets` → `exercise` → `workout_session` → `exercice_details` → `ingredients`
  - Remove `activity_type`, `user` (old name)

---

## Step 5 — Update `processors/gym_members/`
- [x] `transform.py`: remove `profile_uuid_udf`; `gender_code` → INT (1/2/0); `role_code` → `FREEMIUM`; add `role_id` (lit `DEFAULT_FREEMIUM_ROLE_ID`); add `user_id_1` (alias of `user_id`)
- [x] `transform.py`: `user_profile` — no separate `profile_id`; `allergies=NONE`, `diet_type=NONE`, `goal_id=NULL`, `updated_at`
- [x] `transform.py`: `user_metrics` — remove `user_id`; `body_fat_pourcentage`; `sleep_hours` INT; remove `metrics_created_at`
- [x] `pipeline.py`: `table_column_map` rewritten — key `"user"` → `"user_"`, all column names updated
- [x] `utils/uuid_utils.py`: added `NAMESPACE_ROLE`, `generate_role_uuid`, `role_uuid_udf`, `DEFAULT_FREEMIUM_ROLE_ID`

---

## Step 6 — Update `processors/body_performance/`
- [x] `transform.py`: fixed missing `md5`/`concat_ws` imports; `gender_code` → INT; `role_code` → `FREEMIUM`; add `role_id`, `user_id_1`; `allergies=NONE`, `diet_type=NONE`, `goal_id=NULL`, `updated_at`; `body_fat_pourcentage`; `sleep_hours` INT; remove `profile_id`, `metrics_created_at`
- [x] `pipeline.py`: `table_column_map` rewritten — `"user"` → `"user_"`, all column names updated to match new schema

---

## Step 7 — Update `processors/exercises/`
- [x] `transform.py`: added `upper`, `substring` imports; rewrote `map_to_mcd_schema` — `body_part_target` mapped to `body_part_enum` (ARMS/LEGS/BACK/CHEST/SHOULDERS/CORE/FULL_BODY); `difficulty_level` mapped to `exercise_difficulty_enum` (BEGINNER/INTERMEDIATE/ADVANCED, "expert"→ADVANCED); `category` mapped to `exercise_category_enum` (STRENGTH/CARDIO/FLEXIBILITY/BALANCE/OTHER); `description` truncated to 50 chars
- [x] `transform.py`: rewrote `clean_and_validate` — removed `lower()` calls (enums must stay uppercase); pipeline.py had no changes needed

---

## Step 8 — Update `processors/fitness_tracker/`
- [x] `transform.py`: removed `create_activity_types` function and `activity_uuid_udf` import
- [x] `transform.py`: `transform_to_workout_session` — removed `df_activities` param, `activity_id`, `distance_km`; renamed `duration_minutes` → `duration_time` (integer/SMALLINT); updated `session_id` UDF call (passes `None` for activity_id)
- [x] `transform.py`: updated final `.select()` to `session_id, start_time, duration_time, calories_burned, notes, user_id`
- [x] `transform.py`: `clean_and_validate` simplified to single-DF form; removed `activity_id` null check
- [x] `transform.py`: user CSV path `GM_PROCESSED_DIR / "user"` → `GM_PROCESSED_DIR / "user_"`
- [x] `transform.py`: `transform_fitness_tracker` returns only `df_sessions` (no `df_activities`)
- [x] `pipeline.py`: updated to unpack single return value, removed `activity_type` CSV save, updated counts/log

---

## Step 9 — Update `processors/nutrition/` and `processors/nutrition_values/`
- [x] Both `transform.py`: added `_map_category_udf` (maps raw strings → `category_enum`: VEGETABLE/FRUIT/MEAT/DAIRY/GRAIN/BEVERAGE/SNACK/OTHER)
- [x] Both `transform.py`: `food_id` → `ingredients_id`; removed `brand`; `calories_100g`→`calories_g`, `protein_100g`→`protein_g`, `carbs_100g`→`carbs_g`, `fat_100g`→`fat_g`; `category_ref`→`category` (enum); `nutriscore` stays NULL
- [x] Both `transform.py`: `clean_and_validate`/`clean_data` updated to use `calories_g`, `protein_g`, `carbs_g`, `fat_g` column names
- [x] Both `pipeline.py`: output folder `"food"` → `"ingredients"`

---

## Step 10 — Pre-seed required reference data
- [x] `utils/load.py`: added `seed_reference_data()` — inserts all 5 `role_type_enum` rows and 4 `health_goal` rows; role UUIDs computed via `generate_role_uuid()` at runtime (same function as pipelines — no UUID duplication); `ON CONFLICT DO NOTHING` for idempotency
- [x] `main.py`: `seed_reference_data` imported; called in Stage 7 immediately after `init_db_schema()` and before CSV loads; failure is fatal (cannot load `user_` without FREEMIUM role row)

---

## Step 11 — End-to-end test
- [ ] `docker-compose down -v` → `docker-compose up --build`
- [ ] Verify all 6 pipelines pass
- [ ] Verify Stage 7 loads all tables without FK or type errors
- [ ] Spot-check ENUMs: run `SELECT DISTINCT difficulty_level FROM exercise` etc. in psql

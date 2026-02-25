-- ============================================================
-- HealthAI Coach - Database Schema
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- EXERCISE TABLE (from MCD)
-- ============================================================
CREATE TABLE IF NOT EXISTS exercise (
    exercise_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    body_part_target VARCHAR(100),
    video_url TEXT,
    description TEXT,
    difficulty_level VARCHAR(50),
    equipment_required VARCHAR(100),
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_exercise_difficulty ON exercise(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_exercise_equipment ON exercise(equipment_required);
CREATE INDEX IF NOT EXISTS idx_exercise_category ON exercise(category);
CREATE INDEX IF NOT EXISTS idx_exercise_body_part ON exercise(body_part_target);

-- ============================================================
-- FOOD TABLE (from MCD)
-- ============================================================
CREATE TABLE IF NOT EXISTS food (
    food_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(255),
    calories_100g DECIMAL(8,2),
    protein_100g DECIMAL(8,2),
    carbs_100g DECIMAL(8,2),
    fat_100g DECIMAL(8,2),
    nutriscore VARCHAR(1),
    category_ref VARCHAR(100),
    fiber_g DECIMAL(8,2),
    sugar_g DECIMAL(8,2),
    sodium_mg DECIMAL(8,2),
    cholesterol_mg DECIMAL(8,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_food_category ON food(category_ref);
CREATE INDEX IF NOT EXISTS idx_food_nutriscore ON food(nutriscore);
CREATE INDEX IF NOT EXISTS idx_food_name ON food(name);

-- ============================================================
-- USER TABLES (from MCD)
-- ============================================================
CREATE TABLE IF NOT EXISTS "user" (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    birth_date DATE,
    gender_code VARCHAR(1) CHECK (gender_code IN ('M', 'F', 'O')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    role_code VARCHAR(20) DEFAULT 'USER' CHECK (role_code IN ('ADMIN', 'USER', 'COACH'))
);

CREATE TABLE IF NOT EXISTS user_profile (
    profile_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    height_cm INTEGER,
    current_weight_kg DECIMAL(5,2),
    activity_level_ref VARCHAR(50),
    health_goal_id UUID,
    allergies_json TEXT,
    preferences_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_metrics (
    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    recorded_date DATE NOT NULL,
    weight_kg DECIMAL(5,2),
    body_fat_percentage DECIMAL(4,2),
    steps INTEGER,
    calories_burned DECIMAL(7,2),
    heart_rate_avg INTEGER,
    heart_rate_max INTEGER,
    sleep_hours DECIMAL(4,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for user tables
CREATE INDEX IF NOT EXISTS idx_user_email ON "user"(email);
CREATE INDEX IF NOT EXISTS idx_user_profile_user_id ON user_profile(user_id);
CREATE INDEX IF NOT EXISTS idx_user_metrics_user_id ON user_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_user_metrics_date ON user_metrics(recorded_date);

-- ============================================================
-- ACTIVITY & WORKOUT TABLES (from MCD)
-- ============================================================
CREATE TABLE IF NOT EXISTS activity_type (
    activity_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    met_value DECIMAL(5,2),
    icon_url TEXT
);

CREATE TABLE IF NOT EXISTS workout_session (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES "user"(user_id) ON DELETE CASCADE,
    activity_id UUID REFERENCES activity_type(activity_id) ON DELETE SET NULL,
    start_time TIMESTAMP,
    duration_minutes INTEGER,
    calories_burned DECIMAL(8,2),
    distance_km DECIMAL(8,2),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS session_detail (
    detail_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES workout_session(session_id) ON DELETE CASCADE,
    exercise_id UUID REFERENCES exercise(exercise_id) ON DELETE SET NULL,
    sets INTEGER,
    reps INTEGER,
    weight_kg DECIMAL(6,2)
);

-- Indexes for activity tables
CREATE INDEX IF NOT EXISTS idx_workout_session_user_id ON workout_session(user_id);
CREATE INDEX IF NOT EXISTS idx_workout_session_activity_id ON workout_session(activity_id);
CREATE INDEX IF NOT EXISTS idx_workout_session_start_time ON workout_session(start_time);
CREATE INDEX IF NOT EXISTS idx_session_detail_session_id ON session_detail(session_id);
CREATE INDEX IF NOT EXISTS idx_session_detail_exercise_id ON session_detail(exercise_id);

-- ============================================================
-- ETL METADATA TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS data_source (
    source_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(255) NOT NULL,
    source_type VARCHAR(100),
    source_url TEXT,
    format VARCHAR(50),
    expected_records INTEGER,
    last_updated TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS etl_execution (
    execution_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES data_source(source_id),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    status VARCHAR(50),
    records_extracted INTEGER,
    records_loaded INTEGER,
    records_rejected INTEGER,
    error_message TEXT,
    triggered_by VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS data_quality_check (
    check_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID REFERENCES etl_execution(execution_id),
    target_table VARCHAR(100),
    check_type VARCHAR(100),
    check_rule TEXT,
    records_checked INTEGER,
    records_failed INTEGER,
    failure_rate DECIMAL(5,2),
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50)
);

-- ============================================================
-- Insert initial data sources
-- ============================================================
INSERT INTO data_source (source_name, source_type, source_url, format, is_active)
VALUES 
    ('ExerciseDB', 'GitHub', 'https://github.com/yuhonas/free-exercise-db', 'JSON', TRUE),
    ('NutritionDB', 'Kaggle', 'https://www.kaggle.com/datasets/adilshamim8/daily-food-and-nutrition-dataset', 'CSV', TRUE),
    ('NutritionValuesDB', 'Kaggle', 'https://www.kaggle.com/datasets/trolukovich/nutritional-values-for-common-foods-and-products', 'CSV', TRUE)
ON CONFLICT DO NOTHING;

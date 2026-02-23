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

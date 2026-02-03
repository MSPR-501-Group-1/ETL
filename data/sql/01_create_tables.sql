-- =========================================================
-- HealthAI Coach - Database Schema
-- Version: 1.0
-- Date: 2026-02-03
-- Description: Création des tables principales
-- =========================================================

-- Enable UUID extension for PostgreSQL
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. CORE & AUTHENTICATION
CREATE TABLE health_goals (
    goal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    birth_date DATE,
    gender_code CHAR(1) CHECK (gender_code IN ('M', 'F', 'O')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    role_code VARCHAR(10) CHECK (role_code IN ('ADMIN', 'USER', 'COACH')) DEFAULT 'USER'
);

CREATE TABLE user_profiles (
    profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    height_cm INTEGER CHECK (height_cm BETWEEN 50 AND 300),
    current_weight_kg DECIMAL(5,2) CHECK (current_weight_kg BETWEEN 20 AND 500),
    activity_level_ref VARCHAR(20),
    health_goal_id UUID REFERENCES health_goals(goal_id),
    allergies_json JSONB,
    preferences_json JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. SUBSCRIPTION & BILLING
CREATE TABLE subscription_plans (
    plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL,
    monthly_price DECIMAL(10,2) NOT NULL CHECK (monthly_price >= 0),
    duration_months INTEGER DEFAULT 1,
    features_json JSONB,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES subscription_plans(plan_id),
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(20) CHECK (status IN ('ACTIVE', 'EXPIRED', 'CANCELLED')) DEFAULT 'ACTIVE',
    auto_renew BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE invoices (
    invoice_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    subscription_id UUID NOT NULL REFERENCES subscriptions(subscription_id),
    issued_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) CHECK (status IN ('PAID', 'PENDING')) DEFAULT 'PENDING',
    pdf_url VARCHAR(500)
);

CREATE TABLE payment_transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(invoice_id),
    processed_at TIMESTAMP,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(20) CHECK (payment_method IN ('CARD', 'PAYPAL')),
    transaction_ref_ext VARCHAR(100),
    status VARCHAR(20) CHECK (status IN ('SUCCESS', 'FAILED', 'PENDING')) DEFAULT 'PENDING'
);

-- 3. NUTRITION
CREATE TABLE foods (
    food_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    brand VARCHAR(100),
    calories_100g DECIMAL(8,2),
    protein_100g DECIMAL(6,2),
    carbs_100g DECIMAL(6,2),
    fat_100g DECIMAL(6,2),
    nutriscore CHAR(1) CHECK (nutriscore IN ('A', 'B', 'C', 'D', 'E')),
    category_ref VARCHAR(50),
    fiber_g DECIMAL(6,2),
    sugar_g DECIMAL(6,2),
    sodium_mg DECIMAL(8,2),
    cholesterol_mg DECIMAL(8,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE recipes (
    recipe_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    instructions TEXT,
    prep_time_min INTEGER,
    difficulty VARCHAR(10) CHECK (difficulty IN ('EASY', 'MEDIUM', 'HARD')),
    created_by_user_id UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE recipe_ingredients (
    link_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID NOT NULL REFERENCES recipes(recipe_id) ON DELETE CASCADE,
    food_id UUID NOT NULL REFERENCES foods(food_id),
    quantity_grams DECIMAL(8,2) NOT NULL
);

CREATE TABLE food_diary_entries (
    entry_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    food_id UUID NOT NULL REFERENCES foods(food_id),
    consumed_at TIMESTAMP NOT NULL,
    quantity_grams DECIMAL(8,2) NOT NULL,
    meal_type VARCHAR(20) CHECK (meal_type IN ('BREAKFAST', 'LUNCH', 'DINNER', 'SNACK')),
    calories_consumed DECIMAL(8,2)
);

-- 4. PHYSICAL ACTIVITY
CREATE TABLE activity_types (
    activity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    met_value DECIMAL(4,2),
    icon_url VARCHAR(500)
);

CREATE TABLE exercises (
    exercise_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    body_part_target VARCHAR(100),
    video_url VARCHAR(500),
    description TEXT,
    difficulty_level VARCHAR(20),
    equipment_required VARCHAR(100),
    category VARCHAR(50),
    -- ETL enriched columns from ExerciseDB
    level VARCHAR(20),
    difficulty_score INTEGER CHECK (difficulty_score BETWEEN 1 AND 5),
    complexity_score DECIMAL(4,2),
    muscle_count INTEGER,
    exercise_type VARCHAR(20),
    movement_type VARCHAR(20),
    requires_equipment BOOLEAN,
    all_muscles JSONB,
    primary_muscles JSONB,
    secondary_muscles JSONB,
    instructions JSONB,
    images JSONB,
    -- Metadata
    data_source VARCHAR(50),
    scraped_at TIMESTAMP,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workout_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    activity_id UUID REFERENCES activity_types(activity_id),
    start_time TIMESTAMP NOT NULL,
    duration_minutes INTEGER CHECK (duration_minutes > 0),
    calories_burned DECIMAL(8,2),
    distance_km DECIMAL(8,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE session_details (
    detail_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES workout_sessions(session_id) ON DELETE CASCADE,
    exercise_id UUID NOT NULL REFERENCES exercises(exercise_id),
    sets INTEGER,
    reps INTEGER,
    weight_kg DECIMAL(6,2)
);

-- 5. HEALTH IOT & TRACKING
CREATE TABLE connected_devices (
    device_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    device_name VARCHAR(100) NOT NULL,
    device_type VARCHAR(20) CHECK (device_type IN ('WATCH', 'SCALE', 'APP')),
    last_sync TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE biometric_measures (
    measure_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    type VARCHAR(20) CHECK (type IN ('HEART_RATE', 'WEIGHT', 'SLEEP', 'STEPS')) NOT NULL,
    value DECIMAL(10,2) NOT NULL,
    measured_at TIMESTAMP NOT NULL,
    source_device_id UUID REFERENCES connected_devices(device_id)
);

CREATE TABLE recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    category VARCHAR(20) CHECK (category IN ('NUTRITION', 'SPORT', 'WELLNESS')) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content_text TEXT,
    confidence_score DECIMAL(3,2) CHECK (confidence_score BETWEEN 0 AND 1),
    is_viewed BOOLEAN DEFAULT FALSE,
    feedback_rating VARCHAR(20) CHECK (feedback_rating IN ('THUMBS_UP', 'THUMBS_DOWN'))
);

-- 6. PROGRESS TRACKING
CREATE TABLE progress_trackers (
    progress_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    tracking_date DATE NOT NULL,
    weight_kg DECIMAL(5,2),
    body_fat_percentage DECIMAL(4,2),
    weekly_workouts_count INTEGER,
    weekly_calories_avg DECIMAL(8,2),
    goal_achievement_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    recorded_date DATE NOT NULL,
    weight_kg DECIMAL(5,2),
    body_fat_percentage DECIMAL(4,2),
    steps INTEGER,
    calories_burned DECIMAL(8,2),
    heart_rate_avg INTEGER,
    heart_rate_max INTEGER,
    sleep_hours DECIMAL(4,2),
    -- ETL enriched columns from Gym Members dataset
    age INTEGER,
    gender CHAR(1),
    height_m DECIMAL(3,2),
    bmi DECIMAL(4,2),
    bmi_category VARCHAR(20),
    experience_level VARCHAR(20),
    fitness_score DECIMAL(6,2),
    age_group VARCHAR(10),
    max_bpm INTEGER,
    avg_bpm INTEGER,
    workout_frequency_days_week INTEGER,
    session_duration_hours DECIMAL(4,2),
    calorie_burn_rate DECIMAL(6,2),
    heart_rate_reserve INTEGER,
    body_fat_category VARCHAR(20),
    experience_score INTEGER,
    -- Metadata
    data_source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE diet_recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    meal_type VARCHAR(20),
    recommended_foods JSONB,
    total_calories DECIMAL(8,2),
    protein_g DECIMAL(6,2),
    carbs_g DECIMAL(6,2),
    fat_g DECIMAL(6,2),
    diet_type VARCHAR(30),
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_followed BOOLEAN DEFAULT FALSE
);

-- 7. ETL METADATA
CREATE TABLE data_sources (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name VARCHAR(100) NOT NULL,
    source_type VARCHAR(20) NOT NULL,
    source_url TEXT,
    format VARCHAR(10),
    expected_records INTEGER,
    last_updated TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE etl_executions (
    execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES data_sources(source_id),
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    records_extracted INTEGER,
    records_loaded INTEGER,
    records_rejected INTEGER,
    error_message TEXT,
    triggered_by VARCHAR(50)
);

CREATE TABLE data_quality_checks (
    check_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES etl_executions(execution_id),
    target_table VARCHAR(50) NOT NULL,
    check_type VARCHAR(30) NOT NULL,
    check_rule TEXT,
    records_checked INTEGER,
    records_failed INTEGER,
    failure_rate DECIMAL(5,4),
    checked_at TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL
);

CREATE TABLE data_anomalies (
    anomaly_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES etl_executions(execution_id),
    check_id UUID REFERENCES data_quality_checks(check_id),
    source_table VARCHAR(50) NOT NULL,
    anomaly_type VARCHAR(30) NOT NULL,
    field_name VARCHAR(50),
    record_identifier VARCHAR(100),
    original_value TEXT,
    detected_at TIMESTAMP NOT NULL,
    severity VARCHAR(20),
    is_resolved BOOLEAN DEFAULT FALSE,
    resolution_action TEXT
);
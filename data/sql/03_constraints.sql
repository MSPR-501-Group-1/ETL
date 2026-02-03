-- =========================================================
-- Additional Constraints and Business Rules
-- HealthAI Coach Database
-- =========================================================

-- User Profile Constraints
ALTER TABLE user_profiles 
ADD CONSTRAINT check_height_weight_ratio 
CHECK (
    (height_cm IS NULL OR current_weight_kg IS NULL) OR 
    (current_weight_kg / POWER(height_cm / 100.0, 2) BETWEEN 10 AND 50)
);

-- Subscription Business Rules
ALTER TABLE subscriptions 
ADD CONSTRAINT check_subscription_dates 
CHECK (end_date IS NULL OR end_date >= start_date);

-- Payment Transaction Constraints
ALTER TABLE payment_transactions 
ADD CONSTRAINT check_payment_amount_positive 
CHECK (amount > 0);

-- Food Nutrition Constraints
ALTER TABLE foods 
ADD CONSTRAINT check_nutrition_values_positive 
CHECK (
    calories_100g >= 0 AND 
    protein_100g >= 0 AND 
    carbs_100g >= 0 AND 
    fat_100g >= 0
);

-- Exercise Constraints
ALTER TABLE exercises 
ADD CONSTRAINT check_difficulty_score_valid 
CHECK (difficulty_score IS NULL OR difficulty_score BETWEEN 1 AND 5);

ALTER TABLE exercises 
ADD CONSTRAINT check_muscle_count_positive 
CHECK (muscle_count IS NULL OR muscle_count > 0);

-- Workout Session Constraints
ALTER TABLE workout_sessions 
ADD CONSTRAINT check_duration_positive 
CHECK (duration_minutes > 0);

ALTER TABLE workout_sessions 
ADD CONSTRAINT check_calories_positive 
CHECK (calories_burned IS NULL OR calories_burned > 0);

ALTER TABLE workout_sessions 
ADD CONSTRAINT check_distance_positive 
CHECK (distance_km IS NULL OR distance_km > 0);

-- Session Details Constraints
ALTER TABLE session_details 
ADD CONSTRAINT check_sets_positive 
CHECK (sets IS NULL OR sets > 0);

ALTER TABLE session_details 
ADD CONSTRAINT check_reps_positive 
CHECK (reps IS NULL OR reps > 0);

ALTER TABLE session_details 
ADD CONSTRAINT check_weight_positive 
CHECK (weight_kg IS NULL OR weight_kg > 0);

-- Biometric Measures Constraints
ALTER TABLE biometric_measures 
ADD CONSTRAINT check_heart_rate_realistic 
CHECK (
    type != 'HEART_RATE' OR 
    (value BETWEEN 30 AND 250)
);

ALTER TABLE biometric_measures 
ADD CONSTRAINT check_weight_realistic 
CHECK (
    type != 'WEIGHT' OR 
    (value BETWEEN 20 AND 500)
);

ALTER TABLE biometric_measures 
ADD CONSTRAINT check_steps_positive 
CHECK (
    type != 'STEPS' OR 
    (value >= 0 AND value <= 100000)
);

ALTER TABLE biometric_measures 
ADD CONSTRAINT check_sleep_realistic 
CHECK (
    type != 'SLEEP' OR 
    (value BETWEEN 0 AND 24)
);

-- User Metrics Constraints (from ETL data)
ALTER TABLE user_metrics 
ADD CONSTRAINT check_age_realistic 
CHECK (age IS NULL OR age BETWEEN 15 AND 120);

ALTER TABLE user_metrics 
ADD CONSTRAINT check_bmi_realistic 
CHECK (bmi IS NULL OR bmi BETWEEN 10 AND 60);

ALTER TABLE user_metrics 
ADD CONSTRAINT check_body_fat_realistic 
CHECK (body_fat_percentage IS NULL OR body_fat_percentage BETWEEN 3 AND 60);

ALTER TABLE user_metrics 
ADD CONSTRAINT check_heart_rates_order 
CHECK (
    (max_bpm IS NULL OR avg_bpm IS NULL) OR 
    max_bmp >= avg_bpm
);

-- Recipe Constraints
ALTER TABLE recipe_ingredients 
ADD CONSTRAINT check_quantity_positive 
CHECK (quantity_grams > 0);

-- Food Diary Constraints
ALTER TABLE food_diary_entries 
ADD CONSTRAINT check_quantity_consumed_positive 
CHECK (quantity_grams > 0);

ALTER TABLE food_diary_entries 
ADD CONSTRAINT check_calories_consumed_positive 
CHECK (calories_consumed IS NULL OR calories_consumed > 0);

-- ETL Execution Constraints
ALTER TABLE etl_executions 
ADD CONSTRAINT check_execution_dates 
CHECK (ended_at IS NULL OR ended_at >= started_at);

ALTER TABLE etl_executions 
ADD CONSTRAINT check_records_positive 
CHECK (
    (records_extracted IS NULL OR records_extracted >= 0) AND
    (records_loaded IS NULL OR records_loaded >= 0) AND
    (records_rejected IS NULL OR records_rejected >= 0)
);

-- Data Quality Check Constraints
ALTER TABLE data_quality_checks 
ADD CONSTRAINT check_records_checked_positive 
CHECK (records_checked >= 0);

ALTER TABLE data_quality_checks 
ADD CONSTRAINT check_failure_rate_valid 
CHECK (failure_rate IS NULL OR failure_rate BETWEEN 0 AND 1);

-- Unique Constraints for Business Logic
ALTER TABLE user_profiles 
ADD CONSTRAINT unique_user_profile_per_user 
UNIQUE (user_id);

ALTER TABLE connected_devices 
ADD CONSTRAINT unique_device_name_per_user 
UNIQUE (user_id, device_name);

-- Ensure one active subscription per user at a time
CREATE UNIQUE INDEX unique_active_subscription_per_user 
ON subscriptions (user_id) 
WHERE status = 'ACTIVE';
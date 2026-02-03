-- =========================================================
-- Database Indexes for Performance Optimization
-- HealthAI Coach - ETL Pipeline
-- =========================================================

-- Users and Authentication
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);

-- User Profiles
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_health_goal ON user_profiles(health_goal_id);

-- Subscriptions
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_dates ON subscriptions(start_date, end_date);

-- Nutrition
CREATE INDEX idx_foods_name ON foods(name);
CREATE INDEX idx_foods_category ON foods(category_ref);
CREATE INDEX idx_foods_nutriscore ON foods(nutriscore);

CREATE INDEX idx_food_diary_user_date ON food_diary_entries(user_id, consumed_at);
CREATE INDEX idx_food_diary_meal_type ON food_diary_entries(meal_type);

CREATE INDEX idx_recipes_difficulty ON recipes(difficulty);
CREATE INDEX idx_recipes_created_by ON recipes(created_by_user_id);

-- Physical Activity
CREATE INDEX idx_exercises_name ON exercises(name);
CREATE INDEX idx_exercises_category ON exercises(category);
CREATE INDEX idx_exercises_difficulty ON exercises(difficulty_level);
CREATE INDEX idx_exercises_equipment ON exercises(equipment_required);
CREATE INDEX idx_exercises_body_part ON exercises(body_part_target);
CREATE INDEX idx_exercises_data_source ON exercises(data_source);

CREATE INDEX idx_workout_sessions_user_date ON workout_sessions(user_id, start_time);
CREATE INDEX idx_workout_sessions_activity ON workout_sessions(activity_id);

CREATE INDEX idx_session_details_session_id ON session_details(session_id);
CREATE INDEX idx_session_details_exercise_id ON session_details(exercise_id);

-- Health Tracking
CREATE INDEX idx_biometric_measures_user_type ON biometric_measures(user_id, type);
CREATE INDEX idx_biometric_measures_measured_at ON biometric_measures(measured_at);

CREATE INDEX idx_user_metrics_user_date ON user_metrics(user_id, recorded_date);
CREATE INDEX idx_user_metrics_bmi ON user_metrics(bmi_category);
CREATE INDEX idx_user_metrics_age_group ON user_metrics(age_group);
CREATE INDEX idx_user_metrics_data_source ON user_metrics(data_source);

CREATE INDEX idx_connected_devices_user_id ON connected_devices(user_id);
CREATE INDEX idx_connected_devices_type ON connected_devices(device_type);
CREATE INDEX idx_connected_devices_active ON connected_devices(is_active);

-- Recommendations
CREATE INDEX idx_recommendations_user_id ON recommendations(user_id);
CREATE INDEX idx_recommendations_category ON recommendations(category);
CREATE INDEX idx_recommendations_generated_at ON recommendations(generated_at);
CREATE INDEX idx_recommendations_viewed ON recommendations(is_viewed);

-- Progress Tracking
CREATE INDEX idx_progress_trackers_user_date ON progress_trackers(user_id, tracking_date);
CREATE INDEX idx_diet_recommendations_user_id ON diet_recommendations(user_id);
CREATE INDEX idx_diet_recommendations_meal_type ON diet_recommendations(meal_type);

-- ETL Metadata
CREATE INDEX idx_etl_executions_source_id ON etl_executions(source_id);
CREATE INDEX idx_etl_executions_status ON etl_executions(status);
CREATE INDEX idx_etl_executions_started_at ON etl_executions(started_at);

CREATE INDEX idx_data_quality_checks_execution_id ON data_quality_checks(execution_id);
CREATE INDEX idx_data_quality_checks_target_table ON data_quality_checks(target_table);

CREATE INDEX idx_data_anomalies_execution_id ON data_anomalies(execution_id);
CREATE INDEX idx_data_anomalies_severity ON data_anomalies(severity);
CREATE INDEX idx_data_anomalies_resolved ON data_anomalies(is_resolved);

-- Composite indexes for common queries
CREATE INDEX idx_exercises_category_equipment ON exercises(category, equipment_required);
CREATE INDEX idx_exercises_difficulty_body_part ON exercises(difficulty_level, body_part_target);
CREATE INDEX idx_user_metrics_age_gender ON user_metrics(age_group, gender);
CREATE INDEX idx_biometric_user_type_date ON biometric_measures(user_id, type, measured_at DESC);
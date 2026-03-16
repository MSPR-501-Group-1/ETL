-- SCRIPT PostreSQL pour la DB

-- Pour le hachage ---------------------------------------
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ENUMS ------------------------------------------------

CREATE TYPE role_type_enum AS ENUM (
    'FREEMIUM', 'PREMIUM', 'PREMIUM_PLUS', 'B2B', 'ADMIN'
);

CREATE TYPE org_type_enum AS ENUM (
    'COMPANY', 'GYM', 'MUTUAL', 'NGO', 'OTHER'
);

CREATE TYPE nutriscore_enum AS ENUM (
    'A', 'B', 'C', 'D', 'E'
);

CREATE TYPE category_enum AS ENUM (
    'VEGETABLE', 'FRUIT', 'MEAT', 'DAIRY', 'GRAIN', 'BEVERAGE', 'SNACK', 'OTHER'
);

CREATE TYPE recipe_difficulty_enum AS ENUM (
    'EASY', 'MEDIUM', 'HARD'
);

CREATE TYPE exercise_difficulty_enum AS ENUM (
    'BEGINNER', 'INTERMEDIATE', 'ADVANCED'
);

CREATE TYPE exercise_category_enum AS ENUM (
    'CARDIO', 'STRENGTH', 'FLEXIBILITY', 'BALANCE', 'OTHER'
);

CREATE TYPE allergies_enum AS ENUM (
    'NONE', 'MILK', 'GLUTEN', 'SEAFOOD', 'SOY', 'EGGS', 'NUTS', 'OTHER'
);

CREATE TYPE diet_type_enum AS ENUM (
    'NONE', 'VEGETARIAN', 'VEGAN', 'PESCATARIAN', 'KETO', 'PALEO', 'OTHER'
);

CREATE TYPE body_part_enum AS ENUM (
    'ARMS', 'LEGS', 'BACK', 'CHEST', 'SHOULDERS', 'CORE', 'FULL_BODY'
);

-- TABLES ------------------------------------------------

CREATE TABLE health_goal(
   goal_id VARCHAR(50),
   label VARCHAR(50),
   description VARCHAR(200),
   PRIMARY KEY(goal_id)
);

CREATE TABLE ingredients(
   ingredients_id VARCHAR(50),
   name VARCHAR(50),
   calories_g DECIMAL(4,1),
   fat_g DECIMAL(4,1),
   nutriscore nutriscore_enum,
   category category_enum,
   fiber_g DECIMAL(4,1),
   sugar_g DECIMAL(4,1),
   sodium_mg DECIMAL(4,1),
   cholesterol_mg DECIMAL(4,1),
   protein_g DECIMAL(4,1),
   carbs_g DECIMAL(4,1),
   PRIMARY KEY(ingredients_id)
);

CREATE TABLE recipe(
   recipe_id VARCHAR(50),
   title VARCHAR(50),
   instructions VARCHAR(500),
   prep_time_min SMALLINT,
   difficulty recipe_difficulty_enum,
   PRIMARY KEY(recipe_id)
);

CREATE TABLE exercise(
   exercise_id VARCHAR(50),
   name VARCHAR(50),
   body_part_target body_part_enum,
   video_url VARCHAR(50),
   description VARCHAR(50),
   difficulty_level exercise_difficulty_enum,
   equipment_required VARCHAR(50),
   category exercise_category_enum,
   PRIMARY KEY(exercise_id)
);

CREATE TABLE connected_device(
   device_id VARCHAR(50),
   device_name VARCHAR(50),
   device_type VARCHAR(50),
   last_synch TIMESTAMP,
   is_active BOOLEAN,
   PRIMARY KEY(device_id)
);

CREATE TABLE data_source(
   source_id VARCHAR(50),
   source_name VARCHAR(50),
   source_type VARCHAR(50),
   format VARCHAR(50),
   source_url VARCHAR(50),
   expected_records VARCHAR(50),
   last_updates TIMESTAMP,
   is_active BOOLEAN,
   PRIMARY KEY(source_id)
);

CREATE TABLE etl_execution(
   execution_id VARCHAR(50),
   started_at TIMESTAMP,
   ended_at TIMESTAMP,
   status BOOLEAN,
   records_extracted BOOLEAN,
   records_loaded BOOLEAN,
   records_rejected BOOLEAN,
   error_message VARCHAR(50),
   triggered_by VARCHAR(50),
   source_id VARCHAR(50) NOT NULL,
   PRIMARY KEY(execution_id),
   FOREIGN KEY(source_id) REFERENCES data_source(source_id)
);

CREATE TABLE data_quality_check_(
   check_id VARCHAR(50),
   target_table VARCHAR(50),
   check_type VARCHAR(50),
   check_rule VARCHAR(50),
   records_checked VARCHAR(50),
   records_failed VARCHAR(50),
   checked_at TIMESTAMP,
   status BOOLEAN,
   execution_id VARCHAR(50) NOT NULL,
   PRIMARY KEY(check_id),
   FOREIGN KEY(execution_id) REFERENCES etl_execution(execution_id)
);

CREATE TABLE data_anomaly(
   anomaly_id VARCHAR(50),
   source_table VARCHAR(50),
   anomaly_table VARCHAR(50),
   field_name VARCHAR(50),
   record_identifier VARCHAR(50),
   original_value VARCHAR(50),
   detected_at TIMESTAMP,
   severity VARCHAR(50),
   is_resolved BOOLEAN,
   resolution_action VARCHAR(50),
   check_id VARCHAR(50),
   execution_id VARCHAR(50) NOT NULL,
   PRIMARY KEY(anomaly_id),
   FOREIGN KEY(check_id) REFERENCES data_quality_check_(check_id),
   FOREIGN KEY(execution_id) REFERENCES etl_execution(execution_id)
);

CREATE TABLE feature(
   feature_id VARCHAR(50),
   name VARCHAR(50),
   description VARCHAR(200),
   category VARCHAR(50),
   PRIMARY KEY(feature_id)
);

CREATE TABLE role(
   role_id VARCHAR(50),
   role_type role_type_enum,
   is_system BOOLEAN,
   PRIMARY KEY(role_id)
);

CREATE TABLE organization(
   organization_id VARCHAR(50),
   name VARCHAR(50),
   org_type org_type_enum,
   domain VARCHAR(50),
   PRIMARY KEY(organization_id)
);

CREATE TABLE subscription_plan(
   plan_id VARCHAR(50),
   name VARCHAR(50),
   description VARCHAR(50),
   billing_cycle VARCHAR(50),
   price_ht DECIMAL(15,2),
   is_public BOOLEAN,
   created_at TIMESTAMP,
   updated_at TIMESTAMP,
   role_id VARCHAR(50) NOT NULL,
   PRIMARY KEY(plan_id),
   FOREIGN KEY(role_id) REFERENCES role(role_id)
);

CREATE TABLE user_(
   user_id VARCHAR(50),
   email VARCHAR(50),
   password_hash VARCHAR(200),
   first_name VARCHAR(50),
   last_name VARCHAR(50),
   birth_date TIMESTAMP,
   gender_code INT,
   created_at TIMESTAMP,
   is_active BOOLEAN,
   role_code role_type_enum,
   role_id VARCHAR(50) NOT NULL,
   PRIMARY KEY(user_id),
   FOREIGN KEY(role_id) REFERENCES role(role_id)
);

CREATE TABLE user_profile(
   user_id VARCHAR(50),
   height_cm DECIMAL(3,2),
   current_weight_kg DECIMAL(5,2),
   activity_level_ref VARCHAR(50),
   allergies allergies_enum,
   diet_type diet_type_enum,
   updated_at TIMESTAMP,
   goal_id VARCHAR(50),
   PRIMARY KEY(user_id),
   FOREIGN KEY(goal_id) REFERENCES health_goal(goal_id),
   FOREIGN KEY(user_id) REFERENCES user_(user_id)
);

CREATE TABLE user_metrics(
   metric_id VARCHAR(50),
   recorded_date TIMESTAMP,
   weight_kg DECIMAL(5,2),
   body_fat_pourcentage DECIMAL(4,1),
   steps INT,
   calories_burned DECIMAL(5,1),
   heart_rate_avg INT,
   heart_rate_max INT,
   sleep_hours INT,
   PRIMARY KEY(metric_id)
);

CREATE TABLE subscription(
   subscription_id VARCHAR(50),
   start_date TIMESTAMP,
   end_date TIMESTAMP,
   status BOOLEAN,
   cancelled_at TIMESTAMP,
   cancellation_reason VARCHAR(50),
   created_at TIMESTAMP,
   updated_at TIMESTAMP,
   user_id VARCHAR(50) NOT NULL,
   plan_id VARCHAR(50) NOT NULL,
   PRIMARY KEY(subscription_id),
   FOREIGN KEY(user_id) REFERENCES user_(user_id),
   FOREIGN KEY(plan_id) REFERENCES subscription_plan(plan_id)
);

CREATE TABLE payment_transaction(
   transaction_id VARCHAR(50),
   processed_at TIMESTAMP,
   amount_ht NUMERIC(15,2),
   status BOOLEAN,
   created_at TIMESTAMP,
   subscription_id VARCHAR(50) NOT NULL,
   PRIMARY KEY(transaction_id),
   FOREIGN KEY(subscription_id) REFERENCES subscription(subscription_id)
);

CREATE TABLE meal(
   meal_id VARCHAR(50),
   consumed_at TIMESTAMP,
   quantity_grams INT,
   diet_type diet_type_enum,
   calories_consumed INT,
   ingredients VARCHAR(50),
   user_id VARCHAR(50) NOT NULL,
   PRIMARY KEY(meal_id),
   FOREIGN KEY(user_id) REFERENCES user_(user_id)
);

CREATE TABLE workout_session(
   session_id VARCHAR(50),
   start_time TIMESTAMP,
   duration_time SMALLINT,
   calories_burned SMALLINT,
   notes VARCHAR(50),
   user_id VARCHAR(50) NOT NULL,
   PRIMARY KEY(session_id),
   FOREIGN KEY(user_id) REFERENCES user_(user_id)
);

CREATE TABLE exercice_details(
   exercice_details_id VARCHAR(50),
   sets INT,
   reps INT,
   exercise_id VARCHAR(50) NOT NULL,
   session_id VARCHAR(50) NOT NULL,
   PRIMARY KEY(exercice_details_id),
   FOREIGN KEY(exercise_id) REFERENCES exercise(exercise_id),
   FOREIGN KEY(session_id) REFERENCES workout_session(session_id)
);

CREATE TABLE biometric_measure(
   measure_id VARCHAR(50),
   type VARCHAR(50),
   value_ INT,
   measured_at TIMESTAMP,
   user_id VARCHAR(50) NOT NULL,
   PRIMARY KEY(measure_id),
   FOREIGN KEY(user_id) REFERENCES user_(user_id)
);

CREATE TABLE ai_recommendation(
   recommendation_id VARCHAR(50),
   generated_at TIMESTAMP,
   category VARCHAR(50),
   title VARCHAR(50),
   content_text VARCHAR(200),
   confidence_score DECIMAL(15,2),
   is_viewed BOOLEAN,
   feedback_rating DECIMAL(15,2),
   user_id VARCHAR(50) NOT NULL,
   PRIMARY KEY(recommendation_id),
   FOREIGN KEY(user_id) REFERENCES user_(user_id)
);

CREATE TABLE diet_recommendation(
   recommendation_id VARCHAR(50),
   recommended_foods VARCHAR(200),
   total_calories INT,
   protein_g DECIMAL(4,1),
   carbs_g DECIMAL(4,1),
   fat_g DECIMAL(4,1),
   diet_type diet_type_enum,
   generated_at TIMESTAMP,
   is_followed BOOLEAN,
   user_id VARCHAR(50) NOT NULL,
   PRIMARY KEY(recommendation_id),
   FOREIGN KEY(user_id) REFERENCES user_(user_id)
);

CREATE TABLE subscription_history(
   history_id VARCHAR(50),
   status_event VARCHAR(50),
   previous_role VARCHAR(50),
   new_role VARCHAR(50),
   occurred_at_ TIMESTAMP,
   plan_id VARCHAR(50) NOT NULL,
   plan_id_1 VARCHAR(50) NOT NULL,
   user_id VARCHAR(50) NOT NULL,
   subscription_id VARCHAR(50) NOT NULL,
   PRIMARY KEY(history_id),
   FOREIGN KEY(plan_id) REFERENCES subscription_plan(plan_id),
   FOREIGN KEY(plan_id_1) REFERENCES subscription_plan(plan_id),
   FOREIGN KEY(user_id) REFERENCES user_(user_id),
   FOREIGN KEY(subscription_id) REFERENCES subscription(subscription_id)
);

CREATE TABLE consumes(
   ingredients_id VARCHAR(50),
   meal_id VARCHAR(50),
   quantity INT,
   PRIMARY KEY(ingredients_id, meal_id),
   FOREIGN KEY(ingredients_id) REFERENCES ingredients(ingredients_id),
   FOREIGN KEY(meal_id) REFERENCES meal(meal_id)
);

CREATE TABLE recipe_ingredients(
   ingredients_id VARCHAR(50),
   recipe_id VARCHAR(50),
   quantity INT,
   PRIMARY KEY(ingredients_id, recipe_id),
   FOREIGN KEY(ingredients_id) REFERENCES ingredients(ingredients_id),
   FOREIGN KEY(recipe_id) REFERENCES recipe(recipe_id)
);

CREATE TABLE pairs(
   user_id VARCHAR(50),
   device_id VARCHAR(50),
   PRIMARY KEY(user_id, device_id),
   FOREIGN KEY(user_id) REFERENCES user_(user_id),
   FOREIGN KEY(device_id) REFERENCES connected_device(device_id)
);

CREATE TABLE records(
   device_id VARCHAR(50),
   measure_id VARCHAR(50),
   PRIMARY KEY(device_id, measure_id),
   FOREIGN KEY(device_id) REFERENCES connected_device(device_id),
   FOREIGN KEY(measure_id) REFERENCES biometric_measure(measure_id)
);

CREATE TABLE links(
   user_id VARCHAR(50),
   source_id VARCHAR(50),
   PRIMARY KEY(user_id, source_id),
   FOREIGN KEY(user_id) REFERENCES user_(user_id),
   FOREIGN KEY(source_id) REFERENCES data_source(source_id)
);

CREATE TABLE gets(
   goal_id VARCHAR(50),
   metric_id VARCHAR(50),
   PRIMARY KEY(goal_id, metric_id),
   FOREIGN KEY(goal_id) REFERENCES health_goal(goal_id),
   FOREIGN KEY(metric_id) REFERENCES user_metrics(metric_id)
);

CREATE TABLE has_feature(
   plan_id VARCHAR(50),
   feature_id VARCHAR(50),
   PRIMARY KEY(plan_id, feature_id),
   FOREIGN KEY(plan_id) REFERENCES subscription_plan(plan_id),
   FOREIGN KEY(feature_id) REFERENCES feature(feature_id)
);

CREATE TABLE has_access(
   subscription_id VARCHAR(50),
   organization_id VARCHAR(50),
   PRIMARY KEY(subscription_id, organization_id),
   FOREIGN KEY(subscription_id) REFERENCES subscription(subscription_id),
   FOREIGN KEY(organization_id) REFERENCES organization(organization_id)
);

CREATE TABLE Parts_of(
   user_id VARCHAR(50),
   organization_id VARCHAR(50),
   PRIMARY KEY(user_id, organization_id),
   FOREIGN KEY(user_id) REFERENCES user_(user_id),
   FOREIGN KEY(organization_id) REFERENCES organization(organization_id)
);
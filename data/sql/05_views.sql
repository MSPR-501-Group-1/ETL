-- =========================================================
-- Useful Views for HealthAI Coach API
-- Simplified access to complex data relationships
-- =========================================================

-- User Profile Summary (combines user + profile + subscription)
CREATE OR REPLACE VIEW v_user_profiles AS
SELECT 
    u.user_id,
    u.email,
    u.first_name,
    u.last_name,
    u.gender_code,
    u.birth_date,
    EXTRACT(YEAR FROM AGE(u.birth_date)) as age,
    u.created_at as user_created_at,
    u.is_active,
    up.profile_id,
    up.height_cm,
    up.current_weight_kg,
    up.activity_level_ref,
    hg.label as health_goal,
    up.updated_at as profile_updated_at,
    sp.name as subscription_plan,
    s.status as subscription_status,
    s.end_date as subscription_end_date
FROM users u
LEFT JOIN user_profiles up ON u.user_id = up.user_id
LEFT JOIN health_goals hg ON up.health_goal_id = hg.goal_id
LEFT JOIN subscriptions s ON u.user_id = s.user_id AND s.status = 'ACTIVE'
LEFT JOIN subscription_plans sp ON s.plan_id = sp.plan_id;

-- Exercise Catalog with Enriched Data
CREATE OR REPLACE VIEW v_exercise_catalog AS
SELECT 
    exercise_id,
    name,
    category,
    body_part_target,
    equipment_required,
    difficulty_level,
    level,
    difficulty_score,
    complexity_score,
    muscle_count,
    exercise_type,
    movement_type,
    requires_equipment,
    COALESCE(primary_muscles->>'0', '') as primary_muscle_1,
    COALESCE(primary_muscles->>'1', '') as primary_muscle_2,
    COALESCE(secondary_muscles->>'0', '') as secondary_muscle_1,
    array_length(ARRAY(SELECT jsonb_array_elements_text(instructions)), 1) as instruction_steps,
    data_source,
    processed_at
FROM exercises
WHERE name IS NOT NULL
ORDER BY name;

-- User Fitness Dashboard
CREATE OR REPLACE VIEW v_user_fitness_dashboard AS
SELECT 
    um.user_id,
    u.first_name,
    u.last_name,
    um.recorded_date,
    um.weight_kg,
    um.bmi,
    um.bmi_category,
    um.age,
    um.age_group,
    um.fitness_score,
    um.experience_level,
    um.workout_frequency_days_week,
    um.max_bmp as max_bpm,
    um.avg_bpm,
    um.heart_rate_reserve,
    um.body_fat_percentage,
    um.body_fat_category,
    -- Recent activity summary
    (SELECT COUNT(*) 
     FROM workout_sessions ws 
     WHERE ws.user_id = um.user_id 
     AND ws.start_time >= CURRENT_DATE - INTERVAL '7 days') as workouts_last_week,
    (SELECT AVG(calories_burned) 
     FROM workout_sessions ws 
     WHERE ws.user_id = um.user_id 
     AND ws.start_time >= CURRENT_DATE - INTERVAL '30 days') as avg_calories_last_month
FROM user_metrics um
JOIN users u ON um.user_id = u.user_id
WHERE um.recorded_date = (
    SELECT MAX(recorded_date) 
    FROM user_metrics um2 
    WHERE um2.user_id = um.user_id
);

-- Nutrition Summary by User
CREATE OR REPLACE VIEW v_user_nutrition_summary AS
SELECT 
    fde.user_id,
    DATE(fde.consumed_at) as consumption_date,
    COUNT(*) as total_entries,
    SUM(fde.calories_consumed) as total_calories,
    SUM(f.protein_100g * fde.quantity_grams / 100) as total_protein_g,
    SUM(f.carbs_100g * fde.quantity_grams / 100) as total_carbs_g,
    SUM(f.fat_100g * fde.quantity_grams / 100) as total_fat_g,
    COUNT(CASE WHEN fde.meal_type = 'BREAKFAST' THEN 1 END) as breakfast_entries,
    COUNT(CASE WHEN fde.meal_type = 'LUNCH' THEN 1 END) as lunch_entries,
    COUNT(CASE WHEN fde.meal_type = 'DINNER' THEN 1 END) as dinner_entries,
    COUNT(CASE WHEN fde.meal_type = 'SNACK' THEN 1 END) as snack_entries
FROM food_diary_entries fde
JOIN foods f ON fde.food_id = f.food_id
GROUP BY fde.user_id, DATE(fde.consumed_at)
ORDER BY fde.user_id, consumption_date DESC;

-- Exercise Performance by User
CREATE OR REPLACE VIEW v_user_exercise_performance AS
SELECT 
    ws.user_id,
    e.name as exercise_name,
    e.category,
    e.body_part_target,
    COUNT(sd.detail_id) as total_sessions,
    AVG(sd.sets) as avg_sets,
    AVG(sd.reps) as avg_reps,
    AVG(sd.weight_kg) as avg_weight_kg,
    MAX(sd.weight_kg) as max_weight_kg,
    MIN(ws.start_time) as first_performed,
    MAX(ws.start_time) as last_performed
FROM workout_sessions ws
JOIN session_details sd ON ws.session_id = sd.session_id
JOIN exercises e ON sd.exercise_id = e.exercise_id
GROUP BY ws.user_id, e.exercise_id, e.name, e.category, e.body_part_target
HAVING COUNT(sd.detail_id) >= 3  -- Only exercises performed at least 3 times
ORDER BY ws.user_id, total_sessions DESC;

-- ETL Pipeline Status Dashboard
CREATE OR REPLACE VIEW v_etl_status_dashboard AS
SELECT 
    ds.source_name,
    ds.source_type,
    ds.expected_records,
    ds.is_active,
    ee.execution_id,
    ee.started_at as last_execution_start,
    ee.ended_at as last_execution_end,
    ee.status as last_execution_status,
    ee.records_extracted,
    ee.records_loaded,
    ee.records_rejected,
    CASE 
        WHEN ee.records_extracted > 0 
        THEN ROUND((ee.records_loaded::decimal / ee.records_extracted * 100), 2)
        ELSE 0 
    END as success_rate_percentage,
    ee.error_message,
    -- Quality metrics
    (SELECT COUNT(*) 
     FROM data_quality_checks dqc 
     WHERE dqc.execution_id = ee.execution_id 
     AND dqc.status = 'PASSED') as quality_checks_passed,
    (SELECT COUNT(*) 
     FROM data_quality_checks dqc 
     WHERE dqc.execution_id = ee.execution_id 
     AND dqc.status = 'FAILED') as quality_checks_failed,
    (SELECT COUNT(*) 
     FROM data_anomalies da 
     WHERE da.execution_id = ee.execution_id 
     AND da.is_resolved = false) as unresolved_anomalies
FROM data_sources ds
LEFT JOIN LATERAL (
    SELECT * FROM etl_executions ee2 
    WHERE ee2.source_id = ds.source_id 
    ORDER BY ee2.started_at DESC 
    LIMIT 1
) ee ON true
ORDER BY ds.source_name;

-- Popular Exercises by Category
CREATE OR REPLACE VIEW v_popular_exercises AS
SELECT 
    e.category,
    e.name,
    e.body_part_target,
    e.equipment_required,
    e.difficulty_level,
    COUNT(sd.detail_id) as usage_count,
    COUNT(DISTINCT ws.user_id) as unique_users,
    AVG(sd.sets * sd.reps) as avg_volume
FROM exercises e
JOIN session_details sd ON e.exercise_id = sd.exercise_id
JOIN workout_sessions ws ON sd.session_id = ws.session_id
WHERE ws.start_time >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY e.exercise_id, e.category, e.name, e.body_part_target, e.equipment_required, e.difficulty_level
HAVING COUNT(sd.detail_id) >= 5
ORDER BY e.category, usage_count DESC;

-- User Engagement Metrics
CREATE OR REPLACE VIEW v_user_engagement AS
SELECT 
    u.user_id,
    u.email,
    u.created_at as registration_date,
    EXTRACT(DAYS FROM (CURRENT_DATE - u.created_at::date)) as days_since_registration,
    
    -- Workout engagement
    (SELECT COUNT(*) FROM workout_sessions ws WHERE ws.user_id = u.user_id) as total_workouts,
    (SELECT COUNT(*) FROM workout_sessions ws WHERE ws.user_id = u.user_id 
     AND ws.start_time >= CURRENT_DATE - INTERVAL '7 days') as workouts_last_7_days,
    (SELECT COUNT(*) FROM workout_sessions ws WHERE ws.user_id = u.user_id 
     AND ws.start_time >= CURRENT_DATE - INTERVAL '30 days') as workouts_last_30_days,
    
    -- Nutrition engagement
    (SELECT COUNT(*) FROM food_diary_entries fde WHERE fde.user_id = u.user_id) as total_food_entries,
    (SELECT COUNT(DISTINCT DATE(consumed_at)) FROM food_diary_entries fde 
     WHERE fde.user_id = u.user_id 
     AND fde.consumed_at >= CURRENT_DATE - INTERVAL '7 days') as nutrition_days_last_7,
    
    -- Last activity
    GREATEST(
        (SELECT MAX(start_time) FROM workout_sessions ws WHERE ws.user_id = u.user_id),
        (SELECT MAX(consumed_at) FROM food_diary_entries fde WHERE fde.user_id = u.user_id)
    ) as last_activity_date,
    
    -- Subscription status
    s.status as subscription_status,
    sp.name as subscription_plan
FROM users u
LEFT JOIN subscriptions s ON u.user_id = s.user_id AND s.status = 'ACTIVE'
LEFT JOIN subscription_plans sp ON s.plan_id = sp.plan_id
WHERE u.is_active = true
ORDER BY last_activity_date DESC NULLS LAST;
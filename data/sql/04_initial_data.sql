-- =========================================================
-- Initial Data for HealthAI Coach Database
-- Reference tables and configuration data
-- =========================================================

-- Health Goals
INSERT INTO health_goals (goal_id, label, description) VALUES
    (gen_random_uuid(), 'Perte de poids', 'Objectif de réduction du poids corporel'),
    (gen_random_uuid(), 'Prise de masse', 'Objectif de gain musculaire'),
    (gen_random_uuid(), 'Maintien forme', 'Maintenir la condition physique actuelle'),
    (gen_random_uuid(), 'Amélioration endurance', 'Développer les capacités cardio-vasculaires'),
    (gen_random_uuid(), 'Renforcement musculaire', 'Tonifier et renforcer les muscles'),
    (gen_random_uuid(), 'Amélioration souplesse', 'Développer la flexibilité et mobilité');

-- Subscription Plans
INSERT INTO subscription_plans (plan_id, name, monthly_price, duration_months, features_json, is_active) VALUES
    (gen_random_uuid(), 'Freemium', 0.00, 12, 
     '{"features": ["basic_tracking", "limited_recipes", "simple_dashboard"]}', true),
    (gen_random_uuid(), 'Premium', 9.99, 1, 
     '{"features": ["advanced_recommendations", "detailed_nutrition_plans", "workout_programs", "progress_analytics"]}', true),
    (gen_random_uuid(), 'Premium+', 19.99, 1, 
     '{"features": ["biometric_sync", "coach_consultations", "personalized_coaching", "priority_support", "advanced_analytics"]}', true);

-- Activity Types (for workout sessions)
INSERT INTO activity_types (activity_id, name, met_value, icon_url) VALUES
    (gen_random_uuid(), 'Course à pied', 8.0, '/icons/running.svg'),
    (gen_random_uuid(), 'Vélo', 6.0, '/icons/cycling.svg'),
    (gen_random_uuid(), 'Musculation', 4.5, '/icons/weightlifting.svg'),
    (gen_random_uuid(), 'Natation', 8.5, '/icons/swimming.svg'),
    (gen_random_uuid(), 'Yoga', 3.0, '/icons/yoga.svg'),
    (gen_random_uuid(), 'Marche', 3.5, '/icons/walking.svg'),
    (gen_random_uuid(), 'Tennis', 7.0, '/icons/tennis.svg'),
    (gen_random_uuid(), 'Football', 7.5, '/icons/football.svg'),
    (gen_random_uuid(), 'Escalade', 11.0, '/icons/climbing.svg'),
    (gen_random_uuid(), 'Danse', 4.8, '/icons/dance.svg');

-- Data Sources for ETL tracking
INSERT INTO data_sources (source_id, source_name, source_type, source_url, format, expected_records, last_updated, is_active) VALUES
    (gen_random_uuid(), 'ExerciseDB', 'API', 
     'https://github.com/yuhonas/free-exercise-db', 'JSON', 1000, CURRENT_TIMESTAMP, true),
    (gen_random_uuid(), 'Kaggle Gym Members', 'DATASET', 
     'https://www.kaggle.com/datasets/valakhorasani/gym-members-exercise-dataset', 'CSV', 900, CURRENT_TIMESTAMP, true),
    (gen_random_uuid(), 'Kaggle Nutrition', 'DATASET', 
     'https://www.kaggle.com/datasets/adilshamim8/daily-food-and-nutrition-dataset', 'CSV', 500, CURRENT_TIMESTAMP, true),
    (gen_random_uuid(), 'Kaggle Diet Recommendations', 'DATASET',
     'https://www.kaggle.com/datasets/ziya07/diet-recommendations-dataset', 'CSV', 300, CURRENT_TIMESTAMP, true),
    (gen_random_uuid(), 'Kaggle Fitness Tracker', 'DATASET',
     'https://www.kaggle.com/datasets/nadeemajeedch/fitness-tracker-dataset', 'CSV', 1000, CURRENT_TIMESTAMP, true);

-- Sample Food Categories (for nutrition module)
INSERT INTO foods (food_id, name, brand, calories_100g, protein_100g, carbs_100g, fat_100g, nutriscore, category_ref) VALUES
    (gen_random_uuid(), 'Pomme', NULL, 52, 0.3, 14, 0.2, 'A', 'fruits'),
    (gen_random_uuid(), 'Banane', NULL, 89, 1.1, 23, 0.3, 'A', 'fruits'),
    (gen_random_uuid(), 'Riz basmati', NULL, 365, 7.1, 78, 0.9, 'B', 'cereales'),
    (gen_random_uuid(), 'Blanc de poulet', NULL, 165, 31, 0, 3.6, 'A', 'viandes'),
    (gen_random_uuid(), 'Saumon', NULL, 208, 25, 0, 12, 'A', 'poissons'),
    (gen_random_uuid(), 'Brocolis', NULL, 34, 2.8, 7, 0.4, 'A', 'legumes'),
    (gen_random_uuid(), 'Œuf entier', NULL, 155, 13, 1.1, 11, 'B', 'produits_laitiers');

-- Sample Admin User (for testing - password should be hashed in real environment)
INSERT INTO users (user_id, email, password_hash, first_name, last_name, birth_date, gender_code, created_at, is_active, role_code) VALUES
    (gen_random_uuid(), 'admin@healthai.coach', 'hashed_password_here', 'Admin', 'System', '1990-01-01', 'O', CURRENT_TIMESTAMP, true, 'ADMIN');

-- Sample Recipes
DO $$
DECLARE
    recipe_uuid UUID;
    apple_id UUID;
    banana_id UUID;
    chicken_id UUID;
BEGIN
    -- Get food IDs
    SELECT food_id INTO apple_id FROM foods WHERE name = 'Pomme' LIMIT 1;
    SELECT food_id INTO banana_id FROM foods WHERE name = 'Banane' LIMIT 1; 
    SELECT food_id INTO chicken_id FROM foods WHERE name = 'Blanc de poulet' LIMIT 1;

    -- Create sample recipe
    recipe_uuid := gen_random_uuid();
    INSERT INTO recipes (recipe_id, title, instructions, prep_time_min, difficulty) VALUES
        (recipe_uuid, 'Salade de fruits énergétique', 
         'Couper les fruits en morceaux. Mélanger dans un bol. Servir frais.', 
         10, 'EASY');

    -- Add ingredients
    INSERT INTO recipe_ingredients (link_id, recipe_id, food_id, quantity_grams) VALUES
        (gen_random_uuid(), recipe_uuid, apple_id, 150),
        (gen_random_uuid(), recipe_uuid, banana_id, 120);

    -- Create another recipe
    recipe_uuid := gen_random_uuid();
    INSERT INTO recipes (recipe_id, title, instructions, prep_time_min, difficulty) VALUES
        (recipe_uuid, 'Blanc de poulet grillé', 
         'Assaisonner le poulet. Cuire à la poêle 6-8 min de chaque côté.', 
         20, 'MEDIUM');

    INSERT INTO recipe_ingredients (link_id, recipe_id, food_id, quantity_grams) VALUES
        (gen_random_uuid(), recipe_uuid, chicken_id, 200);
END $$;
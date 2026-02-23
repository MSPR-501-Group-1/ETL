erDiagram
    %% =========================================================
    %% 1. CORE & AUTHENTICATION
    %% =========================================================
    USER {
        UUID user_id PK
        STRING email
        STRING password_hash
        STRING first_name
        STRING last_name
        DATE birth_date
        STRING gender_code "M/F/O"
        DATE created_at
        BOOLEAN is_active
        STRING role_code "ADMIN/USER/COACH"
    }

    USER_PROFILE {
        UUID profile_id PK
        UUID user_id FK
        INTEGER height_cm
        DECIMAL current_weight_kg
        STRING activity_level_ref
        UUID health_goal_id FK
        JSON allergies_json
        JSON preferences_json
        DATETIME updated_at
    }

    HEALTH_GOAL {
        UUID goal_id PK
        STRING label "Perte de poids, Prise de masse..."
        STRING description
    }

    %% Relationships Core
    USER ||--|| USER_PROFILE : "has_profile"
    USER_PROFILE }o--|| HEALTH_GOAL : "aims_for"

    %% =========================================================
    %% 2. SUBSCRIPTION & BILLING (MVP)
    %% =========================================================
    SUBSCRIPTION_PLAN {
        UUID plan_id PK
        STRING name "Gold, Silver, Free"
        DECIMAL monthly_price
        INTEGER duration_months
        JSON features_json
        BOOLEAN is_active
    }

    SUBSCRIPTION {
        UUID subscription_id PK
        UUID user_id FK
        UUID plan_id FK
        DATE start_date
        DATE end_date
        STRING status "ACTIVE, EXPIRED, CANCELLED"
        BOOLEAN auto_renew
    }

    INVOICE {
        UUID invoice_id PK
        UUID user_id FK
        UUID subscription_id FK
        DATETIME issued_at
        DECIMAL total_amount
        STRING status "PAID, PENDING"
        STRING pdf_url
    }

    PAYMENT_TRANSACTION {
        UUID transaction_id PK
        UUID invoice_id FK
        DATETIME processed_at
        DECIMAL amount
        STRING payment_method "CARD, PAYPAL"
        STRING transaction_ref_ext
        STRING status "SUCCESS, FAILED"
    }

    %% Relationships Billing
    USER ||--o{ SUBSCRIPTION : "purchases"
    SUBSCRIPTION_PLAN ||--o{ SUBSCRIPTION : "defines"
    USER ||--o{ INVOICE : "billed_to"
    SUBSCRIPTION ||--o{ INVOICE : "generates"
    INVOICE ||--o{ PAYMENT_TRANSACTION : "paid_via"

    %% =========================================================
    %% 3. NUTRITION DOMAIN
    %% =========================================================
    FOOD {
        UUID food_id PK
        STRING name
        STRING brand
        DECIMAL calories_100g
        DECIMAL protein_100g
        DECIMAL carbs_100g
        DECIMAL fat_100g
        STRING nutriscore "A, B, C, D, E"
        STRING category_ref
        DECIMAL fiber_g
        DECIMAL sugar_g
        DECIMAL sodium_mg
        DECIMAL cholesterol_mg
    }

    RECIPE {
        UUID recipe_id PK
        STRING title
        STRING instructions
        INTEGER prep_time_min
        STRING difficulty "EASY, MEDIUM, HARD"
        UUID created_by_user_id FK "Nullable (System or User)"
    }

    RECIPE_INGREDIENT {
        UUID link_id PK
        UUID recipe_id FK
        UUID food_id FK
        DECIMAL quantity_grams
    }

    FOOD_DIARY_ENTRY {
        UUID entry_id PK
        UUID user_id FK
        UUID food_id FK
        DATETIME consumed_at
        DECIMAL quantity_grams
        STRING meal_type "BREAKFAST, LUNCH, DINNER, SNACK"
        DECIMAL calories_consumed
    }

    %% Relationships Nutrition
    RECIPE ||--o{ RECIPE_INGREDIENT : "composed_of"
    RECIPE_INGREDIENT }o--|| FOOD : "uses"
    USER ||--o{ FOOD_DIARY_ENTRY : "logs"
    FOOD_DIARY_ENTRY }o--|| FOOD : "consumes"

    %% =========================================================
    %% 4. PHYSICAL ACTIVITY DOMAIN
    %% =========================================================
    ACTIVITY_TYPE {
        UUID activity_id PK
        STRING name "Running, Cycling, Gym"
        DECIMAL met_value "Metabolic Equivalent"
        STRING icon_url
    }

    WORKOUT_SESSION {
        UUID session_id PK
        UUID user_id FK
        UUID activity_id FK
        DATETIME start_time
        INTEGER duration_minutes
        DECIMAL calories_burned
        DECIMAL distance_km
        STRING notes
    }

    EXERCISE {
        UUID exercise_id PK
        STRING name
        STRING body_part_target
        STRING video_url
        STRING description
        STRING difficulty_level
        STRING equipment_required
        STRING category
    }

    SESSION_DETAIL {
        UUID detail_id PK
        UUID session_id FK
        UUID exercise_id FK
        INTEGER sets
        INTEGER reps
        DECIMAL weight_kg
    }

    %% Relationships Activity
    USER ||--o{ WORKOUT_SESSION : "performs"
    WORKOUT_SESSION }o--|| ACTIVITY_TYPE : "is_type"
    WORKOUT_SESSION ||--o{ SESSION_DETAIL : "includes"
    SESSION_DETAIL }o--|| EXERCISE : "practices"

    %% =========================================================
    %% 5. HEALTH IOT & AI
    %% =========================================================
    CONNECTED_DEVICE {
        UUID device_id PK
        UUID user_id FK
        STRING device_name
        STRING device_type "WATCH, SCALE, APP"
        DATETIME last_sync
        BOOLEAN is_active
    }

    BIOMETRIC_MEASURE {
        UUID measure_id PK
        UUID user_id FK
        STRING type "HEART_RATE, WEIGHT, SLEEP, STEPS"
        DECIMAL value
        DATETIME measured_at
        UUID source_device_id FK
    }

    AI_RECOMMENDATION {
        UUID recommendation_id PK
        UUID user_id FK
        DATETIME generated_at
        STRING category "NUTRITION, SPORT, WELLNESS"
        STRING title
        STRING content_text
        DECIMAL confidence_score
        BOOLEAN is_viewed
        STRING feedback_rating "THUMBS_UP, THUMBS_DOWN"
    }

    %% Relationships IoT/AI
    USER ||--o{ CONNECTED_DEVICE : "pairs"
    USER ||--o{ BIOMETRIC_MEASURE : "tracks"
    CONNECTED_DEVICE |o--|| BIOMETRIC_MEASURE : "records"
    USER ||--o{ AI_RECOMMENDATION : "receives"

    %% =========================================================
    %% 6. PROGRESS TRACKING
    %% =========================================================
    PROGRESS_TRACKER {
        UUID progress_id PK
        UUID user_id FK
        DATE tracking_date
        DECIMAL weight_kg
        DECIMAL body_fat_percentage
        INTEGER weekly_workouts_count
        DECIMAL weekly_calories_avg
        JSON goal_achievement_json
        DATE created_at
    }

    USER_METRICS {
        UUID metric_id PK
        UUID user_id FK
        DATE recorded_date
        DECIMAL weight_kg
        DECIMAL body_fat_percentage
        INTEGER steps
        DECIMAL calories_burned
        INTEGER heart_rate_avg
        INTEGER heart_rate_max
        DECIMAL sleep_hours
        DATETIME created_at
    }

    DIET_RECOMMENDATION {
        UUID recommendation_id PK
        UUID user_id FK
        STRING meal_type
        JSON recommended_foods
        DECIMAL total_calories
        DECIMAL protein_g
        DECIMAL carbs_g
        DECIMAL fat_g
        STRING diet_type
        DATETIME generated_at
        BOOLEAN is_followed
    }

    %% Relationships Progress
    USER ||--o{ PROGRESS_TRACKER : "tracks_progress"
    USER ||--o{ USER_METRICS : "has_metrics"
    USER ||--o{ DIET_RECOMMENDATION : "receives"

    %% =========================================================
    %% 7. ETL METADATA
    %% =========================================================
    DATA_SOURCE {
        UUID source_id PK
        STRING source_name
        STRING source_type
        STRING source_url
        STRING format
        INTEGER expected_records
        DATETIME last_updated
        BOOLEAN is_active
    }

    ETL_EXECUTION {
        UUID execution_id PK
        UUID source_id FK
        DATETIME started_at
        DATETIME ended_at
        STRING status
        INTEGER records_extracted
        INTEGER records_loaded
        INTEGER records_rejected
        STRING error_message
        STRING triggered_by
    }

    DATA_QUALITY_CHECK {
        UUID check_id PK
        UUID execution_id FK
        STRING target_table
        STRING check_type
        STRING check_rule
        INTEGER records_checked
        INTEGER records_failed
        DECIMAL failure_rate
        DATETIME checked_at
        STRING status
    }

    DATA_ANOMALY {
        UUID anomaly_id PK
        UUID execution_id FK
        UUID check_id FK
        STRING source_table
        STRING anomaly_type
        STRING field_name
        STRING record_identifier
        STRING original_value
        DATETIME detected_at
        STRING severity
        BOOLEAN is_resolved
        STRING resolution_action
    }

    %% Relationships ETL
    DATA_SOURCE ||--o{ ETL_EXECUTION : "executes"
    ETL_EXECUTION ||--o{ DATA_QUALITY_CHECK : "validates"
    ETL_EXECUTION ||--o{ DATA_ANOMALY : "detects"
    DATA_QUALITY_CHECK ||--o{ DATA_ANOMALY : "identifies"
# ETL Pipeline Usage Guide

## Pipeline Dependencies

The ETL pipelines have the following dependencies:

```
gym_members (users) 
    ├─→ fitness_tracker (activity_types)
    │       └─→ body_performance (workout_sessions)
    └─→ body_performance (workout_sessions)

exercises (independent)
nutrition (independent)
nutrition_values (independent)
```

## Running Pipelines

### Option 1: Run All Pipelines in Correct Order (Recommended)

The orchestrator automatically runs all pipelines in dependency order:

```bash
# Clean start
docker-compose down -v

# Run all pipelines with orchestrator
docker-compose up etl-all

# Or just
docker-compose up
```

**Execution Order:**
1. Gym Members → creates users
2. Exercises → creates exercise catalog
3. Fitness Tracker → creates activity types (needs users)
4. Body Performance → creates workout sessions (needs users + activities)
5. Nutrition pipelines → creates food data

### Option 2: Run Individual Pipelines

For testing or incremental loads:

```bash
# Run a single pipeline
docker-compose up etl-exercises
docker-compose up etl-gym-members
docker-compose up etl-nutrition

# Run multiple specific pipelines
docker-compose up etl-gym-members etl-exercises
```

⚠️ **Warning:** When running individual pipelines, respect dependencies:
- Run `etl-gym-members` BEFORE `etl-fitness-tracker` or `etl-body-performance`
- Run `etl-fitness-tracker` BEFORE `etl-body-performance`

### Option 3: Run with Python Directly

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows

# Run orchestrator
python orchestrator.py

# Or run single pipeline
python main.py --pipeline exercises
python main.py --pipeline gym-members
```

## Available Services

| Service | Description | Dependencies |
|---------|-------------|--------------|
| `etl-all` | Orchestrator - runs all pipelines in order | None - handles all internally |
| `etl-exercises` | Exercise catalog | None |
| `etl-gym-members` | User data | None |
| `etl-fitness-tracker` | Activity types + workouts | Requires `etl-gym-members` |
| `etl-body-performance` | Workout sessions | Requires `etl-gym-members` + `etl-fitness-tracker` |
| `etl-nutrition` | Daily food nutrition | None |
| `etl-nutrition-values` | Common foods nutrition | None |

## Troubleshooting

### Foreign Key Constraint Errors

If you see errors like:
```
ERROR: insert or update on table "workout_session" violates foreign key constraint
```

**Solution:** You ran pipelines out of order. Clean the database and use the orchestrator:
```bash
docker-compose down -v
docker-compose up etl-all
```

### Duplicate Key Errors

If you see:
```
ERROR: duplicate key value violates unique constraint
```

**Solution:** Data already exists. Clean the database:
```bash
docker-compose down -v
docker-compose up etl-all
```

## Logs

View logs for a specific service:
```bash
docker-compose logs etl-all
docker-compose logs etl-gym-members
docker-compose logs postgres
```

## Database Access

Connect to the PostgreSQL database:
```bash
docker exec -it healthai_postgres psql -U healthai -d healthai_db
```

Check loaded data:
```sql
SELECT COUNT(*) FROM "user";
SELECT COUNT(*) FROM exercise;
SELECT COUNT(*) FROM workout_session;
SELECT COUNT(*) FROM activity_type;
```

#!/bin/bash
# Verify ETL pipeline execution

echo "🔍 Verifying ETL Pipeline Results"
echo "=================================="

# Check if PostgreSQL is running
echo -e "\n1. Checking PostgreSQL connection..."
docker exec healthai_postgres psql -U healthai -d healthai_db -c "SELECT version();" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ PostgreSQL is running"
else
    echo "   ❌ PostgreSQL is not accessible"
    exit 1
fi

# Check exercise table
echo -e "\n2. Checking exercise table..."
COUNT=$(docker exec healthai_postgres psql -U healthai -d healthai_db -t -c "SELECT COUNT(*) FROM exercise;" 2>/dev/null | xargs)
if [ -n "$COUNT" ] && [ "$COUNT" -gt 0 ]; then
    echo "   ✅ Exercise table has $COUNT rows"
else
    echo "   ❌ Exercise table is empty or doesn't exist"
    exit 1
fi

# Check data files
echo -e "\n3. Checking data files..."
if [ -d "data/processed/exercises.parquet" ]; then
    echo "   ✅ Parquet file exists"
else
    echo "   ⚠️  Parquet file not found"
fi

if [ -d "data/processed/exercises_csv" ]; then
    echo "   ✅ CSV export exists"
else
    echo "   ⚠️  CSV export not found"
fi

# Show sample data
echo -e "\n4. Sample data from PostgreSQL:"
docker exec healthai_postgres psql -U healthai -d healthai_db -c "SELECT name, difficulty_level, equipment_required FROM exercise LIMIT 5;"

echo -e "\n=================================="
echo "✅ Verification completed!"

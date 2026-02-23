# Verify ETL pipeline execution
Write-Host "🔍 Verifying ETL Pipeline Results" -ForegroundColor Cyan
Write-Host ("=" * 50)

# Check if PostgreSQL is running
Write-Host "`n1. Checking PostgreSQL connection..."
try {
    docker exec healthai_postgres psql -U healthai -d healthai_db -c "SELECT version();" 2>&1 | Out-Null
    Write-Host "   ✅ PostgreSQL is running" -ForegroundColor Green
} catch {
    Write-Host "   ❌ PostgreSQL is not accessible" -ForegroundColor Red
    exit 1
}

# Check exercise table
Write-Host "`n2. Checking exercise table..."
try {
    $count = docker exec healthai_postgres psql -U healthai -d healthai_db -t -c "SELECT COUNT(*) FROM exercise;" 2>$null
    $count = $count.Trim()
    if ($count -gt 0) {
        Write-Host "   ✅ Exercise table has $count rows" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Exercise table is empty" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ❌ Exercise table doesn't exist" -ForegroundColor Red
    exit 1
}

# Check data files
Write-Host "`n3. Checking data files..."
if (Test-Path "data/processed/exercises.parquet") {
    Write-Host "   ✅ Parquet file exists" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Parquet file not found" -ForegroundColor Yellow
}

if (Test-Path "data/processed/exercises_csv") {
    Write-Host "   ✅ CSV export exists" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  CSV export not found" -ForegroundColor Yellow
}

# Show sample data
Write-Host "`n4. Sample data from PostgreSQL:" -ForegroundColor Cyan
docker exec healthai_postgres psql -U healthai -d healthai_db -c "SELECT name, difficulty_level, equipment_required FROM exercise LIMIT 5;"

Write-Host "`n$("=" * 50)"
Write-Host "✅ Verification completed!" -ForegroundColor Green

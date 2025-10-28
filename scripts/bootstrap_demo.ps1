<#
Bootstrap demo environment (PowerShell)

Steps:
  1. Start docker-compose.dev.yml
  2. Wait for Postgres to be ready
  3. Load storage/init_db.sql into Postgres
  4. Create Kafka topic 'credit_behavior'

Run from repo root:
  .\scripts\bootstrap_demo.ps1
#>

$composeFile = "docker-compose.dev.yml"

Write-Host "Starting docker-compose..."
docker-compose -f $composeFile up -d

Write-Host "Waiting for Postgres to be ready..."
$maxTries = 30
$tries = 0
while ($tries -lt $maxTries) {
    try {
        docker exec postgres pg_isready -U kruth
        if ($LASTEXITCODE -eq 0) { break }
    } catch {
        # ignore
    }
    Start-Sleep -Seconds 2
    $tries += 1
}
if ($tries -ge $maxTries) { Write-Error "Postgres not ready after waiting"; exit 1 }

Write-Host "Loading DB schema..."
docker cp .\storage\init_db.sql postgres:/tmp/init_db.sql
docker exec -i postgres psql -U kruth -d credit_risk -f /tmp/init_db.sql

Write-Host "Creating Kafka topic 'credit_behavior' (if not exists)..."
docker exec kafka kafka-topics --create --if-not-exists --topic credit_behavior --bootstrap-server kafka:9092 --partitions 3 --replication-factor 1

Write-Host "Bootstrap complete. Sample commands:"
Write-Host "  python -m ingestion.kafka_producer  # start producer"
Write-Host "  python -m ingestion.stream_processor  # start consumer"
Write-Host "  python models/train_logistic.py  # train baseline model"
Write-Host "  streamlit run dashboard\app.py  # open dashboard"

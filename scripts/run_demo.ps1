<#
Run a quick demo: start infra, bootstrap, train model, run consumer in background, emit 100 events, and start Streamlit.

Usage: .\scripts\run_demo.ps1
#>

Write-Host "Starting demo (this will run services and a short streaming demo)"

docker-compose -f docker-compose.dev.yml up -d

.
\scripts\bootstrap_demo.ps1

Write-Host "Training logistic model..."
python models/train_logistic.py

Write-Host "Starting stream processor in background..."
Start-Process -FilePath python -ArgumentList 'ingestion/stream_processor.py' -NoNewWindow

Start-Sleep -Seconds 3

Write-Host "Producing 100 demo events..."
python ingestion/kafka_producer.py --count 100 --rate 50

Start-Sleep -Seconds 2

Write-Host "Starting Streamlit dashboard..."
Start-Process -FilePath streamlit -ArgumentList 'run','dashboard/app.py' -NoNewWindow

Write-Host "Demo started. Streamlit should be available; producer sent 100 events." 

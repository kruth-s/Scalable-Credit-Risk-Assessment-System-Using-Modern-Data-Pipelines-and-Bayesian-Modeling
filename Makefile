.PHONY: up bootstrap train produce consume demo

COMPOSE_FILE := docker-compose.dev.yml

up:
	docker-compose -f $(COMPOSE_FILE) up -d

bootstrap:
	sh scripts/bootstrap_demo.sh

train:
	python models/train_logistic.py

produce:
	python ingestion/kafka_producer.py --count 100 --rate 50

consume:
	python ingestion/stream_processor.py

demo: up bootstrap train
	@echo "Producing 100 events and starting consumer and dashboard..."
	python ingestion/kafka_producer.py --count 100 --rate 50 &
	python ingestion/stream_processor.py &
	streamlit run dashboard/app.py

# Real-time CDC Pipeline with PostgreSQL, Kafka, and HDFS

## Overview
This pipeline captures changes from PostgreSQL using Debezium, streams them through Kafka, and stores them in HDFS.        
  
## Components     
1. **PostgreSQL** - Source database with logical decoding enabled
2. **Kafka** - Message broker for change events          
3. **Kafka Connect** - With Debezium source and HDFS sink connectors
4. **Hadoop HDFS** - Distributed file system for storage   
5. **Airflow** - Orchestration of the pipeline
 
## Setup
### 1. Setup and Infrastructure
```bash

cd C:\Users\raoua\Desktop\DataVisualisation\Assigns\assign2\pipeline
docker-compose -f docker/docker-compose-postgres.yml up -d

docker-compose -f docker/docker-compose-kafka.yml up -d

docker-compose -f docker/docker-compose-hadoop.yml up -d

#docker exec -it docker-namenode-1 hdfs dfs -mkdir -p /data/lake
#docker exec -it docker-namenode-1 hdfs dfs -chmod -R 777 /data/lake

docker-compose -f docker/docker-compose-connect.yml up -d

docker-compose -f docker/docker-compose-airflow.yml up -d
docker-compose -f docker/docker-compose-airflow.yml run --rm airflow-webserver airflow db migrate
docker-compose -f docker/docker-compose-airflow.yml run --rm airflow-webserver airflow users create  --username admin --password admin  --firstname Admin --lastname User  --role Admin  --email admin@example.com
docker-compose -f docker/docker-compose-airflow.yml exec airflow-webserver airflow users list
docker exec -it docker-postgres-airflow-1 psql -U airflow -c "\dt" airflow

docker ps -a  
```
### 2. Data Ingestion and Test Generator 
```bash
# Build and run the crypto data ingestor
#docker build -t crypto-ingestor -f docker/Dockerfile-crypto .
#docker run -d --network=pipeline_default --name crypto-ingestor crypto-ingestor

docker exec -it docker-connect-1 python /app/scripts/crypto_ingest.py
docker exec -it docker-connect-1 python /app/scripts/test_generator.py --duration 300

# Check PostgreSQL for data
docker exec -it docker-postgres-1 psql -U postgres -d mydb -c "SELECT * FROM crypto_prices LIMIT 5;"


```
### 3. Debezium and Kafka Setup
```bash
# create & check connectors
curl -X POST -H "Content-Type: application/json" --data @"C:\Users\raoua\Desktop\DataVisualisation\Assigns\assign2\pipeline\connectors\debezium-pg-source.json" http://localhost:8083/connectors
curl -X POST -H "Content-Type: application/json" --data @"C:\Users\raoua\Desktop\DataVisualisation\Assigns\assign2\pipeline\connectors\hdfs-sink.json" http://localhost:8083/connectors
curl http://localhost:8083/connectors
curl http://localhost:8083/connectors/debezium-pg-source/status
curl http://localhost:8083/connectors/hdfs-sink/status

# Check Kafka topics 
docker exec -it docker-kafka-1 kafka-topics --list --bootstrap-server kafka:9092

docker exec -it docker-kafka-1 kafka-console-consumer --bootstrap-server kafka:9092 --topic dbz_.public.crypto_prices --from-beginning --max-messages 5
```
### 4. HDFS Sink and Data Lake
```bash
# Check HDFS files
docker exec -it docker-namenode-1 hdfs dfs -ls /data/lake

# View the content of the sink file
docker exec -it docker-namenode-1 hdfs dfs -cat /data/lake/dbz_public_crypto_prices/partition=0/*.json | head -n 5

# Show that all records are appended to single files per partition
docker exec -it docker-namenode-1 hdfs dfs -du -h /data/lake
```
### 5. Airflow DAG
```bash
http://localhost:8080 #(login: admin/admin)
# Trigger the DAG
docker exec -it docker-airflow-webserver-1 airflow dags trigger data_pipeline
```
### 6. End-to-End Demonstration
```bash
# Run the test generator through Airflow
# Show in UI by clicking "Run" on the DAG and then trigger the DAG

# Open multiple terminal windows to show:
# 1. PostgreSQL data changes
docker exec -it docker-postgres-1 psql -U postgres -d mydb -c "SELECT COUNT(*) FROM crypto_prices;"

# 2. Kafka message flow
docker exec -it docker-kafka-1 kafka-console-consumer --bootstrap-server kafka:9092 --topic dbz_.public.crypto_prices --from-beginning --max-messages 5

# 3. HDFS file growth
docker exec -it docker-namenode-1 hdfs dfs -ls /data/lake
```

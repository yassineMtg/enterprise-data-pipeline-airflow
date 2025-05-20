from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
import requests

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def create_debezium_connector():
    connector_config = {
        "name": "debezium-pg-source",
        "config": {
            "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
            "database.hostname": "postgres",
            "database.port": "5432",
            "database.user": "postgres",
            "database.password": "postgres",
            "database.dbname": "mydb",
            "database.server.name": "pg-server",
            "table.include.list": "public.crypto_prices",
            "plugin.name": "pgoutput",
            "slot.name": "debezium_slot",
            "publication.name": "debezium_pub",
            "database.history.kafka.bootstrap.servers": "kafka:9092",
            "database.history.kafka.topic": "schema-changes.public",
            "topic.prefix": "dbz_"
        }
    }
    response = requests.post(
        "http://connect:8083/connectors",
        headers={"Content-Type": "application/json"},
        json=connector_config
    )
    response.raise_for_status()

def create_hdfs_sink_connector():
    connector_config = {
        "name": "hdfs-sink",
        "config": {
            "connector.class": "io.confluent.connect.hdfs.HdfsSinkConnector",
            "tasks.max": "1",
            "topics": "dbz_public_crypto_prices",
            "hdfs.url": "hdfs://namenode:8020/data/lake",
            "hadoop.conf.dir": "/etc/hadoop/conf",
            "flush.size": "1000",
            "rotate.interval.ms": "86400000",
            "logs.dir": "/data/lake/logs",
            "format.class": "io.confluent.connect.hdfs.json.JsonFormat",
            "storage.class": "io.confluent.connect.hdfs.storage.HdfsStorage",
            "schema.compatibility": "NONE",
            "value.converter": "org.apache.kafka.connect.json.JsonConverter",
            "value.converter.schemas.enable": "false",
            "key.converter": "org.apache.kafka.connect.json.JsonConverter",
            "key.converter.schemas.enable": "false"
        }
    }
    response = requests.post(
        "http://connect:8083/connectors",
        headers={"Content-Type": "application/json"},
        json=connector_config
    )
    response.raise_for_status()

def create_hive_table():
    from pyhive import hive
    conn = hive.Connection(
        host='hive-server',
        port=10000,
        username='hive',
        database='default'
    )
    cursor = conn.cursor()
    cursor.execute("""
        CREATE EXTERNAL TABLE IF NOT EXISTS crypto_prices (
            id INT,
            timestamp TIMESTAMP,
            currency STRING,
            price_usd DECIMAL(18,2)
        STORED AS PARQUET
        LOCATION '/data/lake/crypto_prices'
    """)
    cursor.close()
    conn.close()

with DAG(
    'data_pipeline',
    default_args=default_args,
    description='CDC Pipeline from PostgreSQL to HDFS',
    schedule_interval=timedelta(days=1),
    catchup=False,
) as dag:

    start_services = BashOperator(
        task_id='start_services',
        bash_command='echo "Starting services..."',
    )

    create_debezium = PythonOperator(
        task_id='create_debezium_connector',
        python_callable=create_debezium_connector,
    )

    create_hdfs = PythonOperator(
        task_id='create_hdfs_sink_connector',
        python_callable=create_hdfs_sink_connector,
    )

    create_hive = PythonOperator(
    task_id='create_hive_table',
    python_callable=create_hive_table,
)

    run_test_generator = BashOperator(
        task_id='run_test_generator',
        bash_command='python /app/scripts/test_generator.py --duration 300',
    )

    start_services >> [create_debezium, create_hdfs, create_hive] >> run_test_generator
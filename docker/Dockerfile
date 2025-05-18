FROM confluentinc/cp-kafka-connect:7.0.1

# Download and install Debezium PostgreSQL Connector
RUN curl -k -L -o /tmp/debezium-postgres.tar.gz \
    https://repo1.maven.org/maven2/io/debezium/debezium-connector-postgres/2.1.1.Final/debezium-connector-postgres-2.1.1.Final-plugin.tar.gz \
    && mkdir -p /usr/share/confluent-hub-components/debezium-postgres \
    && tar -xzf /tmp/debezium-postgres.tar.gz -C /usr/share/confluent-hub-components/debezium-postgres --strip-components 1 \
    && rm /tmp/debezium-postgres.tar.gz

# Install HDFS Sink Connector
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-hdfs:10.1.8

# Copy scripts
COPY ../scripts /app/scripts
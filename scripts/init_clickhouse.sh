#!/bin/bash
# ClickHouse init: create DB, tables and seed data
# Usage: bash scripts/init_clickhouse.sh [container_name]

CONTAINER=${1:-architecture-bionicpro-clickhouse-1}

ch() {
    echo "$1" | docker exec -i "$CONTAINER" clickhouse-client
}

echo "==> Creating database bionicpro..."
ch "CREATE DATABASE IF NOT EXISTS bionicpro"

echo "==> Creating table report_mart..."
ch "
CREATE TABLE IF NOT EXISTS bionicpro.report_mart (
    user_id               String,
    report_date           Date,
    username              String,
    email                 String,
    prosthesis_id         String,
    avg_reaction_time_ms  Float64,
    total_movements       UInt64,
    avg_battery_level     Float64,
    signal_quality_avg    Float64,
    active_hours          Float64,
    anomaly_count         UInt32,
    last_calibration_date DateTime,
    etl_processed_at      DateTime
) ENGINE = MergeTree()
ORDER BY (user_id, report_date)
"

echo "==> Creating table etl_metadata..."
ch "
CREATE TABLE IF NOT EXISTS bionicpro.etl_metadata (
    dag_id              String,
    last_processed_date Date,
    processed_at        DateTime
) ENGINE = MergeTree()
ORDER BY dag_id
"

echo "==> Seeding etl_metadata..."
ch "
INSERT INTO bionicpro.etl_metadata
SELECT 'etl_reports', toDate('2026-04-25'), toDateTime('2026-04-25 12:00:00')
WHERE NOT EXISTS (
    SELECT 1 FROM bionicpro.etl_metadata WHERE dag_id = 'etl_reports'
)
"

echo "==> Seeding report_mart (2 rows for prothetic1)..."
echo "    NOTE: replace 'prothetic-user-1-uuid' with real UUID from Keycloak"
echo "    http://localhost:8080/admin -> Users -> prothetic1 -> ID"

ch "
INSERT INTO bionicpro.report_mart
SELECT
    'prothetic-user-1-uuid', toDate('2026-04-25'), 'prothetic1', 'prothetic1@example.com',
    'PROS-001', 87.4, 1240, 78.3, 0.91, 6.5, 2,
    toDateTime('2026-03-01 10:00:00'), toDateTime('2026-04-25 12:00:00')
WHERE NOT EXISTS (
    SELECT 1 FROM bionicpro.report_mart WHERE prosthesis_id = 'PROS-001' AND report_date = '2026-04-25'
)
"

ch "
INSERT INTO bionicpro.report_mart
SELECT
    'prothetic-user-1-uuid', toDate('2026-04-24'), 'prothetic1', 'prothetic1@example.com',
    'PROS-001', 92.1, 1105, 65.0, 0.88, 5.8, 1,
    toDateTime('2026-03-01 10:00:00'), toDateTime('2026-04-24 12:00:00')
WHERE NOT EXISTS (
    SELECT 1 FROM bionicpro.report_mart WHERE prosthesis_id = 'PROS-001' AND report_date = '2026-04-24'
)
"

echo ""
echo "==> Verification:"
echo "SELECT count() AS report_rows FROM bionicpro.report_mart" | docker exec -i "$CONTAINER" clickhouse-client
echo "SELECT dag_id, last_processed_date FROM bionicpro.etl_metadata" | docker exec -i "$CONTAINER" clickhouse-client
echo ""
echo "Done!"

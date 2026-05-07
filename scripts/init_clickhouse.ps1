# ClickHouse init: create DB, tables and seed data
# Usage: .\scripts\init_clickhouse.ps1 [-Container <container_name>]

param(
    [string]$Container = "architecture-bionicpro-clickhouse-1"
)

function Invoke-CH {
    param([string]$Sql)
    $Sql | docker exec -i $Container clickhouse-client
}

Write-Host "==> Creating database bionicpro..."
Invoke-CH @"
CREATE DATABASE IF NOT EXISTS bionicpro
"@

Write-Host "==> Creating table report_mart..."
Invoke-CH @"
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
"@

Write-Host "==> Creating table etl_metadata..."
Invoke-CH @"
CREATE TABLE IF NOT EXISTS bionicpro.etl_metadata (
    dag_id              String,
    last_processed_date Date,
    processed_at        DateTime
) ENGINE = MergeTree()
ORDER BY dag_id
"@

Write-Host "==> Seeding etl_metadata..."
Invoke-CH @"
INSERT INTO bionicpro.etl_metadata
SELECT 'etl_reports', toDate('2026-04-25'), toDateTime('2026-04-25 12:00:00')
WHERE NOT EXISTS (
    SELECT 1 FROM bionicpro.etl_metadata WHERE dag_id = 'etl_reports'
)
"@

Write-Host "==> Seeding report_mart (2 rows for prothetic1)..."
Write-Host "    NOTE: replace 'prothetic-user-1-uuid' with real UUID from Keycloak"
Write-Host "    http://localhost:8080/admin -> Users -> prothetic1 -> ID"

Invoke-CH @"
INSERT INTO bionicpro.report_mart
SELECT
    'prothetic-user-1-uuid', toDate('2026-04-25'), 'prothetic1', 'prothetic1@example.com',
    'PROS-001', 87.4, 1240, 78.3, 0.91, 6.5, 2,
    toDateTime('2026-03-01 10:00:00'), toDateTime('2026-04-25 12:00:00')
WHERE NOT EXISTS (
    SELECT 1 FROM bionicpro.report_mart WHERE prosthesis_id = 'PROS-001' AND report_date = '2026-04-25'
)
"@

Invoke-CH @"
INSERT INTO bionicpro.report_mart
SELECT
    'prothetic-user-1-uuid', toDate('2026-04-24'), 'prothetic1', 'prothetic1@example.com',
    'PROS-001', 92.1, 1105, 65.0, 0.88, 5.8, 1,
    toDateTime('2026-03-01 10:00:00'), toDateTime('2026-04-24 12:00:00')
WHERE NOT EXISTS (
    SELECT 1 FROM bionicpro.report_mart WHERE prosthesis_id = 'PROS-001' AND report_date = '2026-04-24'
)
"@

Write-Host ""
Write-Host "==> Verification:"
"SELECT count() AS report_rows FROM bionicpro.report_mart" | docker exec -i $Container clickhouse-client
"SELECT dag_id, last_processed_date FROM bionicpro.etl_metadata" | docker exec -i $Container clickhouse-client
Write-Host ""
Write-Host "Done!"

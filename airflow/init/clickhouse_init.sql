-- ClickHouse initialization

CREATE DATABASE IF NOT EXISTS bionicpro;

CREATE TABLE IF NOT EXISTS bionicpro.report_mart (
    user_id String,
    report_date Date,
    username String,
    email String,
    prosthesis_id String,
    avg_reaction_time_ms Float64,
    total_movements UInt64,
    avg_battery_level Float64,
    signal_quality_avg Float64,
    active_hours Float64,
    anomaly_count UInt32,
    last_calibration_date DateTime,
    etl_processed_at DateTime
) ENGINE = ReplacingMergeTree(etl_processed_at)
ORDER BY (user_id, report_date, prosthesis_id);

CREATE TABLE IF NOT EXISTS bionicpro.etl_metadata (
    dag_id String,
    last_processed_date Date,
    processed_at DateTime
) ENGINE = ReplacingMergeTree(processed_at)
ORDER BY (dag_id);

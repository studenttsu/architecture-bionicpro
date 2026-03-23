"""
BionicPRO ETL DAG: Извлечение данных из CRM и Telemetry DB,
трансформация и загрузка витрины report_mart в ClickHouse.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.http.hooks.http import HttpHook

import json
import logging

logger = logging.getLogger(__name__)

default_args = {
    "owner": "bionicpro",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def extract_crm_data(**context):
    """Извлечение данных клиентов из CRM (PostgreSQL)."""
    pg_hook = PostgresHook(postgres_conn_id="crm_postgres")
    sql = """
        SELECT
            c.user_id,
            c.username,
            c.email,
            p.prosthesis_id,
            p.model,
            p.installation_date,
            p.last_calibration_date
        FROM customers c
        JOIN prostheses p ON c.user_id = p.user_id
    """
    records = pg_hook.get_records(sql)
    columns = [
        "user_id", "username", "email", "prosthesis_id",
        "model", "installation_date", "last_calibration_date"
    ]
    result = [dict(zip(columns, row)) for row in records]
    logger.info(f"Extracted {len(result)} CRM records")
    context["ti"].xcom_push(key="crm_data", value=result)


def extract_telemetry_data(**context):
    """Извлечение данных телеметрии из Telemetry DB (PostgreSQL)."""
    pg_hook = PostgresHook(postgres_conn_id="telemetry_postgres")

    execution_date = context["ds"]
    sql = f"""
        SELECT
            prosthesis_id,
            AVG(reaction_time_ms) AS avg_reaction_time_ms,
            COUNT(*) AS total_movements,
            AVG(battery_level) AS avg_battery_level,
            AVG(signal_quality) AS signal_quality_avg,
            SUM(active_minutes) / 60.0 AS active_hours,
            SUM(CASE WHEN is_anomaly THEN 1 ELSE 0 END) AS anomaly_count
        FROM telemetry
        WHERE DATE(recorded_at) = '{execution_date}'
        GROUP BY prosthesis_id
    """
    records = pg_hook.get_records(sql)
    columns = [
        "prosthesis_id", "avg_reaction_time_ms", "total_movements",
        "avg_battery_level", "signal_quality_avg", "active_hours",
        "anomaly_count"
    ]
    result = [dict(zip(columns, row)) for row in records]
    logger.info(f"Extracted {len(result)} telemetry records for {execution_date}")
    context["ti"].xcom_push(key="telemetry_data", value=result)


def transform_data(**context):
    """Объединение данных CRM и телеметрии по prosthesis_id."""
    crm_data = context["ti"].xcom_pull(key="crm_data", task_ids="extract_crm")
    telemetry_data = context["ti"].xcom_pull(
        key="telemetry_data", task_ids="extract_telemetry"
    )
    execution_date = context["ds"]

    telemetry_map = {row["prosthesis_id"]: row for row in telemetry_data}

    merged = []
    for crm_row in crm_data:
        prosthesis_id = crm_row["prosthesis_id"]
        tel = telemetry_map.get(prosthesis_id, {})

        merged.append({
            "user_id": crm_row["user_id"],
            "report_date": execution_date,
            "username": crm_row["username"],
            "email": crm_row["email"],
            "prosthesis_id": prosthesis_id,
            "avg_reaction_time_ms": tel.get("avg_reaction_time_ms", 0.0),
            "total_movements": tel.get("total_movements", 0),
            "avg_battery_level": tel.get("avg_battery_level", 0.0),
            "signal_quality_avg": tel.get("signal_quality_avg", 0.0),
            "active_hours": tel.get("active_hours", 0.0),
            "anomaly_count": tel.get("anomaly_count", 0),
            "last_calibration_date": crm_row.get("last_calibration_date", ""),
            "etl_processed_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        })

    logger.info(f"Transformed {len(merged)} records")
    context["ti"].xcom_push(key="merged_data", value=merged)


def load_to_clickhouse(**context):
    """Загрузка витрины report_mart в ClickHouse."""
    merged_data = context["ti"].xcom_pull(
        key="merged_data", task_ids="transform"
    )
    execution_date = context["ds"]

    if not merged_data:
        logger.warning("No data to load into ClickHouse")
        return

    http_hook = HttpHook(method="POST", http_conn_id="clickhouse_http")

    delete_sql = (
        f"ALTER TABLE bionicpro.report_mart "
        f"DELETE WHERE report_date = '{execution_date}'"
    )
    http_hook.run(endpoint="/", data=delete_sql)
    logger.info(f"Deleted existing records for {execution_date}")

    values_parts = []
    for row in merged_data:
        last_cal = row["last_calibration_date"] or "1970-01-01 00:00:00"
        values_parts.append(
            f"('{row['user_id']}', '{row['report_date']}', "
            f"'{row['username']}', '{row['email']}', "
            f"'{row['prosthesis_id']}', "
            f"{row['avg_reaction_time_ms']}, {row['total_movements']}, "
            f"{row['avg_battery_level']}, {row['signal_quality_avg']}, "
            f"{row['active_hours']}, {row['anomaly_count']}, "
            f"'{last_cal}', '{row['etl_processed_at']}')"
        )

    insert_sql = (
        "INSERT INTO bionicpro.report_mart "
        "(user_id, report_date, username, email, prosthesis_id, "
        "avg_reaction_time_ms, total_movements, avg_battery_level, "
        "signal_quality_avg, active_hours, anomaly_count, "
        "last_calibration_date, etl_processed_at) VALUES "
        + ", ".join(values_parts)
    )
    http_hook.run(endpoint="/", data=insert_sql)
    logger.info(f"Loaded {len(merged_data)} records into report_mart")

    meta_sql = (
        "INSERT INTO bionicpro.etl_metadata "
        "(dag_id, last_processed_date, processed_at) VALUES "
        f"('etl_reports', '{execution_date}', "
        f"'{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}')"
    )
    http_hook.run(endpoint="/", data=meta_sql)
    logger.info(f"Updated etl_metadata: last_processed_date={execution_date}")


with DAG(
    dag_id="bionicpro_etl_reports",
    default_args=default_args,
    description="ETL: CRM + Telemetry -> ClickHouse report_mart",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["bionicpro", "etl", "reports"],
) as dag:

    extract_crm = PythonOperator(
        task_id="extract_crm",
        python_callable=extract_crm_data,
    )

    extract_telemetry = PythonOperator(
        task_id="extract_telemetry",
        python_callable=extract_telemetry_data,
    )

    transform = PythonOperator(
        task_id="transform",
        python_callable=transform_data,
    )

    load = PythonOperator(
        task_id="load_to_clickhouse",
        python_callable=load_to_clickhouse,
    )

    [extract_crm, extract_telemetry] >> transform >> load

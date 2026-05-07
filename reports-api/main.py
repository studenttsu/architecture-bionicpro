"""
BionicPRO Reports API.
Provides GET /reports endpoint that returns prosthesis usage report
from ClickHouse OLAP database. Access is restricted to authenticated
users who can only view their own reports (user_id from JWT sub claim).
"""

from datetime import date, datetime
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
import clickhouse_connect
import logging

from config import settings
from auth import get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="BionicPRO Reports API",
    description="API for generating prosthesis usage reports",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_clickhouse_client():
    """Create ClickHouse client connection."""
    return clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_database,
    )


def get_last_processed_date(ch_client) -> Optional[date]:
    """Get the last date processed by Airflow ETL."""
    try:
        result = ch_client.query(
            "SELECT max(last_processed_date) FROM bionicpro.etl_metadata "
            "WHERE dag_id = 'etl_reports'"
        )
        if result.result_rows and result.result_rows[0][0]:
            value = result.result_rows[0][0]
            if isinstance(value, (date, datetime)):
                return value if isinstance(value, date) else value.date()
            return datetime.strptime(str(value), "%Y-%m-%d").date()
    except Exception as e:
        logger.warning(f"Could not fetch last_processed_date: {e}")
    return None


@app.get("/reports")
async def get_report(
    date_from: Optional[str] = Query(
        None, description="Start date (YYYY-MM-DD)"
    ),
    date_to: Optional[str] = Query(
        None, description="End date (YYYY-MM-DD)"
    ),
    current_user: dict = Depends(get_current_user),
):
    """
    Get prosthesis usage report for the authenticated user.
    
    Access control: user_id is taken from the JWT 'sub' claim,
    ensuring users can only access their own reports.
    Reports are only generated for periods already processed by Airflow.
    """
    user_id = current_user["username"]
    logger.info(
        f"Report requested by username={user_id} "
        f"(sub={current_user['user_id']})"
    )

    try:
        ch_client = get_clickhouse_client()
    except Exception as e:
        logger.error(f"ClickHouse connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Report database is unavailable",
        )

    # Check last processed date
    last_processed = get_last_processed_date(ch_client)
    if last_processed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reports available yet. Data has not been processed by ETL.",
        )

    # Parse and validate date range
    try:
        if date_from:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
        else:
            from_date = date(2020, 1, 1)

        if date_to:
            to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
        else:
            to_date = last_processed
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD.",
        )

    # Ensure requested range does not exceed processed data
    if to_date > last_processed:
        to_date = last_processed
        logger.info(
            f"Adjusted to_date to last_processed={last_processed}"
        )

    # Query report_mart for this user only
    query = (
        "SELECT "
        "  user_id, report_date, username, email, prosthesis_id, "
        "  avg_reaction_time_ms, total_movements, avg_battery_level, "
        "  signal_quality_avg, active_hours, anomaly_count, "
        "  last_calibration_date, etl_processed_at "
        "FROM bionicpro.report_mart "
        "WHERE user_id = %(user_id)s "
        "  AND report_date >= %(from_date)s "
        "  AND report_date <= %(to_date)s "
        "ORDER BY report_date DESC, prosthesis_id"
    )

    try:
        result = ch_client.query(
            query,
            parameters={
                "user_id": user_id,
                "from_date": from_date.strftime("%Y-%m-%d"),
                "to_date": to_date.strftime("%Y-%m-%d"),
            },
        )
    except Exception as e:
        logger.error(f"ClickHouse query error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate report",
        )

    columns = [
        "user_id", "report_date", "username", "email", "prosthesis_id",
        "avg_reaction_time_ms", "total_movements", "avg_battery_level",
        "signal_quality_avg", "active_hours", "anomaly_count",
        "last_calibration_date", "etl_processed_at",
    ]
    reports = []
    for row in result.result_rows:
        record = dict(zip(columns, row))
        # Convert date/datetime to string for JSON serialization
        for key in ("report_date", "last_calibration_date", "etl_processed_at"):
            if isinstance(record[key], (date, datetime)):
                record[key] = record[key].isoformat()
        reports.append(record)

    return {
        "user_id": user_id,
        "username": current_user["username"],
        "date_from": from_date.isoformat(),
        "date_to": to_date.isoformat(),
        "last_processed_date": last_processed.isoformat(),
        "total_records": len(reports),
        "reports": reports,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

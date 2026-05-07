-- Telemetry Database initialization
CREATE TABLE IF NOT EXISTS telemetry (
    id SERIAL PRIMARY KEY,
    prosthesis_id VARCHAR(255) NOT NULL,
    reaction_time_ms FLOAT NOT NULL,
    battery_level FLOAT NOT NULL,
    signal_quality FLOAT NOT NULL,
    active_minutes FLOAT NOT NULL DEFAULT 0,
    is_anomaly BOOLEAN DEFAULT FALSE,
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_telemetry_prosthesis_date
    ON telemetry (prosthesis_id, DATE(recorded_at));

-- Sample telemetry data
INSERT INTO telemetry (prosthesis_id, reaction_time_ms, battery_level, signal_quality, active_minutes, is_anomaly, recorded_at) VALUES
    ('PROS-001', 85.2, 92.5, 0.95, 30, FALSE, NOW() - INTERVAL '1 hour'),
    ('PROS-001', 78.1, 90.0, 0.93, 25, FALSE, NOW() - INTERVAL '2 hours'),
    ('PROS-001', 120.5, 88.0, 0.70, 15, TRUE, NOW() - INTERVAL '3 hours'),
    ('PROS-001', 82.0, 85.5, 0.92, 35, FALSE, NOW() - INTERVAL '4 hours'),
    ('PROS-002', 90.3, 95.0, 0.97, 40, FALSE, NOW() - INTERVAL '1 hour'),
    ('PROS-002', 88.7, 93.0, 0.96, 35, FALSE, NOW() - INTERVAL '2 hours'),
    ('PROS-002', 95.1, 91.0, 0.94, 20, FALSE, NOW() - INTERVAL '3 hours'),
    ('PROS-003', 105.0, 80.0, 0.85, 20, FALSE, NOW() - INTERVAL '1 hour'),
    ('PROS-003', 110.2, 78.0, 0.80, 15, TRUE, NOW() - INTERVAL '2 hours'),
    ('PROS-003', 98.5, 82.0, 0.88, 25, FALSE, NOW() - INTERVAL '3 hours');

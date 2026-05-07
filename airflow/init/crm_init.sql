-- CRM Database initialization
CREATE TABLE IF NOT EXISTS customers (
    user_id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prostheses (
    prosthesis_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES customers(user_id),
    model VARCHAR(255) NOT NULL,
    installation_date DATE,
    last_calibration_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active'
);

-- Sample data
INSERT INTO customers (user_id, username, email, first_name, last_name) VALUES
    ('prothetic1', 'prothetic1', 'prothetic1@example.com', 'Prothetic', 'One'),
    ('prothetic2', 'prothetic2', 'prothetic2@example.com', 'Prothetic', 'Two'),
    ('prothetic3', 'prothetic3', 'prothetic3@example.com', 'Prothetic', 'Three')
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO prostheses (prosthesis_id, user_id, model, installation_date, last_calibration_date) VALUES
    ('PROS-001', 'prothetic1', 'BionicHand-V3', '2025-06-15', '2026-02-20 10:00:00'),
    ('PROS-002', 'prothetic2', 'BionicHand-V3', '2025-08-20', '2026-03-01 14:30:00'),
    ('PROS-003', 'prothetic3', 'BionicArm-V2', '2025-10-01', '2026-03-10 09:00:00')
ON CONFLICT (prosthesis_id) DO NOTHING;

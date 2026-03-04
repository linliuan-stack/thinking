CREATE TABLE IF NOT EXISTS experiments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_by INTEGER REFERENCES users(id),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plates (
    id SERIAL PRIMARY KEY,
    experiment_id INTEGER NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    rows INTEGER NOT NULL DEFAULT 8,
    cols INTEGER NOT NULL DEFAULT 12,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plate_wells (
    id SERIAL PRIMARY KEY,
    plate_id INTEGER NOT NULL REFERENCES plates(id) ON DELETE CASCADE,
    row_index INTEGER NOT NULL,
    col_index INTEGER NOT NULL,
    compound_name VARCHAR(100),
    concentration DECIMAL(20,6),
    concentration_unit VARCHAR(20) DEFAULT 'μM',
    batch VARCHAR(50),
    value DECIMAL(20,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(plate_id, row_index, col_index)
);

INSERT INTO modules (name, description, icon, status, service_type) VALUES
    ('实验管理', '药物实验孔板管理与剂量-反应分析', 'Histogram', 'active', 'python')
ON CONFLICT DO NOTHING;

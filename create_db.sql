CREATE TABLE Directions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200)
);
CREATE TABLE Sources (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL CHECK (type IN ('ФГОС', 'Профстандарт', 'Вакансия')),
    name VARCHAR(100),
    description TEXT
);
CREATE TABLE Competencies (
    id SERIAL PRIMARY KEY,
    direction_id INTEGER REFERENCES Directions(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200),
    description TEXT,
    category VARCHAR(50),
    UNIQUE(direction_id, code)
);
CREATE TABLE Competency_Source (
    competency_id INTEGER REFERENCES Competencies(id) ON DELETE CASCADE,
    source_id INTEGER REFERENCES Sources(id) ON DELETE CASCADE,
    frequency DECIMAL(5,2),
    level VARCHAR(50),
    PRIMARY KEY (competency_id, source_id)
);

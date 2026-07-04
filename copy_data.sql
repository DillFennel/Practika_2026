COPY Competency(name, category, description) 
FROM 'competencies.csv' DELIMITER ',' CSV HEADER;

COPY Source(type, name, description) 
FROM 'sources.csv' DELIMITER ',' CSV HEADER;

COPY Competency_Source(competency_id, source_id, frequency, level) 
FROM 'competency_source.csv' DELIMITER ',' CSV HEADER;
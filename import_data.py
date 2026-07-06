import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

DB_PARAMS = {
    'dbname': 'competencies_db',
    'user': 'postgres',
    'password': '12345',
    'host': 'localhost',
    'port': 5432
}

df = pd.read_csv('all_competencies_3.csv')

conn = psycopg2.connect(**DB_PARAMS)
cur = conn.cursor()

# --- Удаляем старые таблицы (если есть) ---
cur.execute("DROP TABLE IF EXISTS Competency_Source CASCADE;")
cur.execute("DROP TABLE IF EXISTS Competencies CASCADE;")
cur.execute("DROP TABLE IF EXISTS Sources CASCADE;")
conn.commit()
print("Старые таблицы удалены")

# --- Создаём таблицы заново ---
cur.execute("""
CREATE TABLE Sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('ФГОС', 'Профстандарт', 'Вакансия')),
    description TEXT
);
""")

cur.execute("""
CREATE TABLE Competencies (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200),
    description TEXT,
    category VARCHAR(50)
);
""")

cur.execute("""
CREATE TABLE Competency_Source (
    competency_id INTEGER REFERENCES Competencies(id) ON DELETE CASCADE,
    source_id INTEGER REFERENCES Sources(id) ON DELETE CASCADE,
    direction VARCHAR(100),
    count INTEGER DEFAULT 1,
    level VARCHAR(50),
    PRIMARY KEY (competency_id, source_id, direction)
);
""")
conn.commit()
print("Таблицы созданы")

# --- Заполнение Sources (справочник) ---
sources = {
    'ФГОС': ('ФГОС ВО', 'ФГОС', 'Федеральный государственный образовательный стандарт высшего образования'),
    'Профстандарт': ('Профессиональные стандарты', 'Профстандарт', 'Профессиональные стандарты ИТ-сферы'),
    'Вакансия': ('SuperJob', 'Вакансия', 'Вакансии с SuperJob')
}

for source_type, (name, type_, desc) in sources.items():
    cur.execute("""
        INSERT INTO Sources (name, type, description)
        VALUES (%s, %s, %s)
        ON CONFLICT (name) DO NOTHING;
    """, (name, type_, desc))
conn.commit()

cur.execute("SELECT id, type FROM Sources;")
source_map = {row[1]: row[0] for row in cur.fetchall()}
print("Sources:", source_map)

# --- Загрузка Competencies (уникальные по code) ---
unique_comp = df[['code', 'category_group', 'description']].drop_duplicates(subset=['code'])
unique_comp = unique_comp[unique_comp['code'].notna() & (unique_comp['code'] != '')]

insert_comp = []
for _, row in unique_comp.iterrows():
    code = row['code']
    category = row['category_group'] if pd.notna(row['category_group']) else ''
    description = row['description'] if pd.notna(row['description']) else ''
    insert_comp.append((code, code, description, category))

execute_values(cur, """
    INSERT INTO Competencies (code, name, description, category)
    VALUES %s
    ON CONFLICT (code) DO NOTHING;
""", insert_comp)
conn.commit()

cur.execute("SELECT id, code FROM Competencies;")
comp_map = {row[1]: row[0] for row in cur.fetchall()}
print(f"Загружено {len(comp_map)} компетенций")

# --- Загрузка связей (Competency_Source) ---
# ФГОС
fgos_df = df[df['source'] == 'ФГОС']
for _, row in fgos_df.iterrows():
    comp_id = comp_map.get(row['code'])
    if comp_id is None:
        continue
    direction = row['direction'] if pd.notna(row['direction']) else ''
    count = int(row.get('count', 1))
    cur.execute("""
        INSERT INTO Competency_Source (competency_id, source_id, direction, count)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (competency_id, source_id, direction) DO UPDATE
        SET count = Competency_Source.count + EXCLUDED.count;
    """, (comp_id, source_map['ФГОС'], direction, count))
conn.commit()
print("ФГОС загружены")

# Профстандарты
prof_df = df[df['source'] == 'Профстандарт']
for _, row in prof_df.iterrows():
    comp_id = comp_map.get(row['code'])
    if comp_id is None:
        continue
    direction = row['direction'] if pd.notna(row['direction']) else ''
    count = int(row.get('count', 1))
    cur.execute("""
        INSERT INTO Competency_Source (competency_id, source_id, direction, count)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (competency_id, source_id, direction) DO UPDATE
        SET count = Competency_Source.count + EXCLUDED.count;
    """, (comp_id, source_map['Профстандарт'], direction, count))
conn.commit()
print("Профстандарты загружены")

# Вакансии
vac_df = df[df['source'] == 'Вакансия']
for _, row in vac_df.iterrows():
    skill_code = row['normalized_code'] if pd.notna(row.get('normalized_code')) else row['code']
    comp_id = comp_map.get(skill_code)
    if comp_id is None:
        cur.execute("""
            INSERT INTO Competencies (code, name, description, category)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (code) DO NOTHING;
        """, (skill_code, skill_code, '', 'skill'))
        conn.commit()
        cur.execute("SELECT id FROM Competencies WHERE code = %s;", (skill_code,))
        res = cur.fetchone()
        if res:
            comp_id = res[0]
            comp_map[skill_code] = comp_id
        else:
            continue
    direction = row['direction'] if pd.notna(row['direction']) else ''
    count = int(row.get('count', 1))
    cur.execute("""
        INSERT INTO Competency_Source (competency_id, source_id, direction, count)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (competency_id, source_id, direction) DO UPDATE
        SET count = Competency_Source.count + EXCLUDED.count;
    """, (comp_id, source_map['Вакансия'], direction, count))
conn.commit()
print("Вакансии загружены")

cur.close()
conn.close()
print("ВСЕ ДАННЫЕ УСПЕШНО ЗАГРУЖЕНЫ!")
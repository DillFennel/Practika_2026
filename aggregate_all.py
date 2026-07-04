import pandas as pd
import re

# 1. Загружаем ФГОС
fgos = pd.read_csv('competencies_extracted.csv')
fgos['source'] = 'ФГОС'
fgos['count'] = 1

def extract_category(code):
    if pd.isna(code):
        return ''
    if code.startswith('УК'):
        return 'УК'
    elif code.startswith('ОПК'):
        return 'ОПК'
    elif code.startswith('ПК'):
        return 'ПК'
    return ''

fgos['category'] = fgos['code'].apply(extract_category)

fgos = fgos[['source', 'direction', 'category', 'code', 'description', 'count']]

# 2. Загружаем профстандарты
prof = pd.read_csv('profstandarts.csv')
prof['source'] = 'Профстандарт'
prof['count'] = 1
prof['category'] = prof['otf'].apply(lambda x: x.replace('«', '').replace('»', '').strip() if pd.notna(x) else '')
prof['code'] = prof['standard_code']
prof['description'] = prof['tf'] + ': ' + prof['td'].str[:200]
prof['direction'] = prof['standard_name']

prof = prof[['source', 'direction', 'category', 'code', 'description', 'count']]

# 3. Загружаем вакансии
vac = pd.read_csv('superjob_roles.csv')
vac['source'] = 'Вакансия'

def expand_skills(row):
    skills_str = row['skills']
    if pd.isna(skills_str) or skills_str == '':
        return []
    skills = [s.strip() for s in skills_str.split(',') if s.strip()]
    return [{'skill': s, 'role': row['role'], 'count': 1} for s in skills]

expanded = []
for _, row in vac.iterrows():
    for skill_data in expand_skills(row):
        expanded.append({
            'source': 'Вакансия',
            'direction': row['role'],
            'category': 'skill',
            'code': skill_data['skill'],
            'description': '',
            'count': 1
        })

vac_expanded = pd.DataFrame(expanded)

vac_agg = vac_expanded.groupby(['source', 'direction', 'category', 'code'], as_index=False).agg({
    'count': 'sum',
    'description': lambda x: ''
})

# 4. Объединяем всё
all_data = pd.concat([
    fgos,
    prof,
    vac_agg
], ignore_index=True)

# 5. Нормализация названий навыков для сравнения
skill_mapping = {
    'Python': 'Python',
    'Java': 'Java',
    'JavaScript': 'JavaScript',
    'TypeScript': 'TypeScript',
    'C++': 'C++',
    'C#': 'C#',
    'Go': 'Go',
    'PHP': 'PHP',
    'Swift': 'Swift',
    'Kotlin': 'Kotlin',
    '1С': '1С',
    'SQL': 'SQL',
    'PostgreSQL': 'PostgreSQL',
    'MySQL': 'MySQL',
    'MongoDB': 'MongoDB',
    'Redis': 'Redis',
    'Docker': 'Docker',
    'Kubernetes': 'Kubernetes',
    'Linux': 'Linux',
    'Git': 'Git',
    'CI/CD': 'CI/CD',
    'AWS': 'AWS',
    'Azure': 'Azure',
    'React': 'React',
    'Vue.js': 'Vue.js',
    'Angular': 'Angular',
    'Django': 'Django',
    'Flask': 'Flask',
    'Spring': 'Spring',
    'Node.js': 'Node.js',
    'Elasticsearch': 'Elasticsearch',
    'Kafka': 'Kafka',
    'Jenkins': 'Jenkins',
    'Ansible': 'Ansible',
    'Terraform': 'Terraform',
    'Prometheus': 'Prometheus',
    'Grafana': 'Grafana',
}

# Создаём колонку с нормализованным названием
all_data['normalized_code'] = all_data['code']
vac_mask = all_data['source'] == 'Вакансия'
all_data.loc[vac_mask, 'normalized_code'] = all_data.loc[vac_mask, 'code'].map(lambda x: skill_mapping.get(x, x))

# 6. Сохраняем
all_data.to_csv('all_competencies.csv', index=False, encoding='utf-8')
print(f"Агрегировано {len(all_data)} записей")
print(f"Источники: {all_data['source'].unique().tolist()}")
print("\nПример данных:")
print(all_data.head(10))
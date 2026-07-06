import pandas as pd
import re

df = pd.read_csv('all_competencies_2.csv', encoding='utf-8')

# ----- Вспомогательные функции -----

# Сокращение описания для ФГОС (до 5-6 слов)
def shorten_desc(desc):
    cleaned = re.sub(r'^(способностью|умением|владением|готовностью|знанием|пониманием)\s*', '', desc)
    words = cleaned.split()
    short = ' '.join(words[:6])
    if len(short) > 60:
        short = short[:57] + '...'
    return short

# Определение группы для ФГОС (ОПК и ПК)
def fgos_group(code, desc):
    if code.startswith('ОПК'):
        return 'Общие компетенции'
    desc_lower = desc.lower()
    if 'проектировани' in desc_lower or 'архитектур' in desc_lower:
        return 'Архитектура и проектирование'
    if 'управлени' in desc_lower or 'организаци' in desc_lower or 'планирован' in desc_lower or 'переговор' in desc_lower:
        return 'Управление проектами'
    if 'документирован' in desc_lower or 'отчет' in desc_lower:
        return 'Документация и стандартизация'
    if 'анализ' in desc_lower or 'данн' in desc_lower or 'моделирован' in desc_lower or 'статистик' in desc_lower or 'оптимизаци' in desc_lower:
        return 'Анализ данных и моделирование'
    if 'безопасн' in desc_lower:
        return 'Информационная безопасность'
    if 'администрирован' in desc_lower or 'эксплуатаци' in desc_lower or 'сеть' in desc_lower:
        return 'Инфраструктура и администрирование'
    if 'программирован' in desc_lower or 'код' in desc_lower or 'алгоритм' in desc_lower or 'разработк' in desc_lower:
        return 'Программирование и разработка ПО'
    if 'требован' in desc_lower or 'спецификаци' in desc_lower:
        return 'Системный анализ и требования'
    return 'Программирование и разработка ПО'  # по умолчанию

# Определение группы для профстандартов по названию трудовой функции
def prof_group(category):
    cat_lower = category.lower()
    if 'архитектур' in cat_lower or 'проектирован' in cat_lower:
        return 'Архитектура и проектирование'
    if 'требован' in cat_lower or 'аналитик' in cat_lower or 'сопровожд' in cat_lower:
        return 'Системный анализ и требования'
    if 'документирован' in cat_lower:
        return 'Документация и стандартизация'
    if 'управлен' in cat_lower or 'организац' in cat_lower or 'планирован' in cat_lower:
        return 'Управление проектами'
    if 'безопасн' in cat_lower:
        return 'Информационная безопасность'
    if 'драйвер' in cat_lower or 'компилятор' in cat_lower or 'утилит' in cat_lower or 'системн' in cat_lower:
        return 'Программирование и разработка ПО'
    if 'баз' in cat_lower and 'данн' in cat_lower:
        return 'Базы данных'
    if 'отладк' in cat_lower or 'тестирован' in cat_lower or 'рефакторинг' in cat_lower:
        return 'Программирование и разработка ПО'
    if 'сеть' in cat_lower or 'администрирован' in cat_lower or 'эксплуатаци' in cat_lower:
        return 'Инфраструктура и администрирование'
    return 'Программирование и разработка ПО'

# Определение группы для навыков из вакансий
def skill_group(skill):
    skill_lower = skill.lower()
    # Языки программирования
    langs = {'c++', 'go', 'python', 'java', 'c#', 'javascript', 'kotlin', 'php', 'swift', 'typescript', '1с'}
    if skill_lower in langs:
        return 'Программирование и разработка ПО'
    # DevOps инструменты
    devops = {'ci/cd', 'docker', 'kubernetes', 'ansible', 'terraform', 'linux', 'grafana', 'prometheus'}
    if skill_lower in devops:
        return 'Инфраструктура и администрирование'
    # Базы данных
    db = {'sql', 'postgresql', 'redis'}
    if skill_lower in db:
        return 'Базы данных'
    # Потоковая обработка
    if skill_lower == 'kafka':
        return 'Анализ данных и моделирование'
    # Git и подобное
    if skill_lower == 'git':
        return 'Программирование и разработка ПО'
    # React и другие веб-фреймворки
    if skill_lower in {'react', 'angular', 'vue'}:
        return 'Программирование и разработка ПО'
    # Всё остальное – по умолчанию
    return 'Программирование и разработка ПО'

# ----- Основное преобразование -----

for idx, row in df.iterrows():
    src = row['source']
    if src == 'ФГОС':
        # Сокращаем описание в category
        df.at[idx, 'category'] = shorten_desc(row['description'])
        # Назначаем группу
        df.at[idx, 'category_group'] = fgos_group(row['code'], row['description'])
    elif src == 'Профстандарт':
        # category оставляем как есть (название трудовой функции)
        # Назначаем группу по названию
        df.at[idx, 'category_group'] = prof_group(row['category'])
    elif src == 'Вакансия':
        # category оставляем как есть (навык)
        # Назначаем группу по навыку
        df.at[idx, 'category_group'] = skill_group(row['category'])
    # иные источники (если есть) пропускаем без изменений

# Сохраняем результат
df.to_csv('all_competencies_3.csv', index=False, encoding='utf-8')
print("Готово! Результат в all_competencies_2_unified.csv")
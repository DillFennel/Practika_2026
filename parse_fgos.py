import os
import re
import csv
import pdfplumber

def clean_description(desc):
    # Удаляем начальные и конечные мусорные символы
    desc = re.sub(r'^[\s"\'\(\);]+', '', desc)
    desc = re.sub(r'[\s"\'\(\);]+$', '', desc)
    
    # Если есть двоеточие и после него начинается с ключевого слова,
    # удаляем часть до двоеточия (заголовок вида "проектная деятельность:")
    match = re.match(r'^([^:]+деятельность:|[^:]+деятельности:)\s*(.+)', desc)
    if match:
        after = match.group(2).strip()
        # Проверяем, что после двоеточия идёт слово, типичное для начала компетенции
        if re.match(r'^(способностью|владением|готовностью|умением|знанием|пониманием|применением|навыками|культурой)', after, re.IGNORECASE):
            desc = after
        else:
            # Если после двоеточия не ключевое слово, оставляем как есть
            pass
    
    # Убираем множественные пробелы
    desc = re.sub(r'\s+', ' ', desc)
    return desc

def extract_competencies_from_text(text):
    competencies = []
    code_pattern = re.compile(r'(УК-\d+|ОПК-\d+|ПК-\d+(?:\.\d+)?)')
    matches = list(code_pattern.finditer(text))
    
    for i, match in enumerate(matches):
        code = match.group(1)
        start = match.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        
        raw_desc = text[start:end].strip()
        raw_desc = re.sub(r'\s+', ' ', raw_desc)
        
        # Пропускаем, если raw_desc содержит явный мусор (номера разделов, таблицы, ссылки)
        if re.search(r'(5\.\d+\.|6\.\d+\.|7\.\d+\.|Таблица|КонсультантПлюс|www\.consultant\.ru)', raw_desc):
            continue
        
        clean_desc = clean_description(raw_desc)
        if clean_desc and len(clean_desc) > 10:  # отсекаем слишком короткие
            competencies.append({'code': code, 'description': clean_desc})
    
    return competencies

def extract_from_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ''
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + '\n'
            return full_text
    except Exception as e:
        print(f"Ошибка при чтении {pdf_path}: {e}")
        return ''

# --------------------------------------------------------
pdf_dir = 'pdfs'
output_csv = 'competencies_extracted.csv'
all_data = []

for filename in os.listdir(pdf_dir):
    if not filename.endswith('.pdf'):
        continue
    pdf_path = os.path.join(pdf_dir, filename)
    
    code_match = re.search(r'(\d{6})', filename)
    if code_match:
        raw = code_match.group(1)
        direction_code = f"{raw[:2]}.{raw[2:4]}.{raw[4:6]}"
    else:
        direction_code = filename.replace('.pdf', '')
    
    print(f"\nОбработка {direction_code} из {filename}...")
    full_text = extract_from_pdf(pdf_path)
    
    # Проверка, что текст извлечён
    if len(full_text.strip()) < 100:
        print(f"  ВНИМАНИЕ: текст очень короткий ({len(full_text)} символов), возможно, PDF является скан-копией.")
    
    comps = extract_competencies_from_text(full_text)
    print(f"  Найдено {len(comps)} компетенций")
    
    for comp in comps:
        if isinstance(comp, dict) and 'code' in comp and 'description' in comp:
            all_data.append({
                'direction': direction_code,
                'code': comp['code'],
                'description': comp['description']
            })

with open(output_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['direction', 'code', 'description'])
    writer.writeheader()
    writer.writerows(all_data)

print(f"\nГотово! Извлечено {len(all_data)} записей. Результат в {output_csv}")
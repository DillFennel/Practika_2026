import os
import re
import csv
import pdfplumber

def extract_competencies_from_text(text):
    """Извлекает компетенции из текста, возвращает список словарей {'code': ..., 'description': ...}."""
    competencies = []
    
    # 1. Паттерн: код в начале строки (УК-1, ОПК-2, ПК-1.1)
    pattern1 = re.compile(r'(УК-\d+|ОПК-\d+|ПК-\d+(?:\.\d+)?)\s+(.+?)(?=\s+(?:УК-\d+|ОПК-\d+|ПК-\d+(?:\.\d+)?)|\Z)', re.DOTALL)
    for code, desc in pattern1.findall(text):
        desc = ' '.join(desc.split())
        if code and desc:
            competencies.append({'code': code.strip(), 'description': desc.strip()})
    
    # 2. Паттерн: код в скобках после описания (например, "... (ОК-1)")
    pattern2 = re.compile(r'(.+?)\s*\(\s*(УК-\d+|ОПК-\d+|ПК-\d+(?:\.\d+)?)\s*\)[;,.]?', re.UNICODE)
    for desc, code in pattern2.findall(text):
        desc = ' '.join(desc.split())
        if code and desc:
            competencies.append({'code': code.strip(), 'description': desc.strip()})
    
    # 3. Если ничего не нашли, пробуем построчный перебор (оба варианта)
    if not competencies:
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # а) код в начале
            m = re.match(r'(УК-\d+|ОПК-\d+|ПК-\d+(?:\.\d+)?)\s+(.+)', line)
            if m:
                competencies.append({'code': m.group(1).strip(), 'description': m.group(2).strip()})
                continue
            # б) код в скобках в конце
            m2 = re.search(r'\((\s*УК-\d+\s*|\s*ОПК-\d+\s*|\s*ПК-\d+(?:\.\d+)?\s*)\)\s*[;,.]?$', line)
            if m2:
                code = m2.group(1).strip()
                desc = line[:m2.start()].strip()
                if desc:
                    competencies.append({'code': code, 'description': desc})
    
    # Удаляем возможные дубликаты (по коду)
    seen = set()
    unique = []
    for comp in competencies:
        if comp['code'] not in seen:
            seen.add(comp['code'])
            unique.append(comp)
    return unique

def extract_from_pdf(pdf_path):
    """Извлекает полный текст из PDF, возвращает строку."""
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
    
    # Извлекаем код направления из имени файла (6 цифр)
    code_match = re.search(r'(\d{6})', filename)
    if code_match:
        raw = code_match.group(1)
        direction_code = f"{raw[:2]}.{raw[2:4]}.{raw[4:6]}"
    else:
        direction_code = filename.replace('.pdf', '')
    
    print(f"\nОбработка {direction_code} из {filename}...")
    full_text = extract_from_pdf(pdf_path)
    
    # Отладочный вывод первых 500 символов для первого файла (по желанию)
    if filename == os.listdir(pdf_dir)[0]:
        print("--- Отладочный текст (первые 500 символов) ---")
        print(full_text[:500])
        print("--- Конец отладки ---")
    
    comps = extract_competencies_from_text(full_text)
    print(f"  Найдено {len(comps)} компетенций")
    
    for comp in comps:
        # Проверяем, что comp — словарь с нужными ключами
        if isinstance(comp, dict) and 'code' in comp and 'description' in comp:
            all_data.append({
                'direction': direction_code,
                'code': comp['code'],
                'description': comp['description']
            })
        else:
            print(f"  ВНИМАНИЕ: неверный формат компетенции: {comp} (тип {type(comp)})")

# Сохраняем результат
with open(output_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['direction', 'code', 'description'])
    writer.writeheader()
    writer.writerows(all_data)

print(f"\nГотово! Извлечено {len(all_data)} записей. Результат в {output_csv}")
import os
import re
import csv
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import io

def extract_standard_name_and_code(text):
    """
    Извлекает название и код профессионального стандарта.
    Возвращает кортеж (name, code).
    """
    name = None
    code = None
    
    # 1. Ищем код стандарта
    code_patterns = [
        r'(Профессиональный стандарт\s*)?(\d{2}\.\d{3})',
        r'Код\s*(\d{2}\.\d{3})',
        r'(\d{2}\.\d{3})\s*–\s*[А-Я]',
    ]
    for pattern in code_patterns:
        match = re.search(pattern, text)
        if match:
            # Если две группы, берём вторую, иначе всю
            if len(match.groups()) > 1:
                code = match.group(2).strip()
            else:
                code = match.group(0).strip()
            break
    
    # 2. Ищем название стандарта
    # Ищем строки, содержащие "Профессиональный стандарт" и следующие за ними
    # Часто название в кавычках или после тире
    name_patterns = [
        r'Профессиональный стандарт\s*[–-]?\s*["«]?([^"«»\n]+)["»]?',
        r'Наименование\s*вида\s*профессиональной\s*деятельности\s*[–-]?\s*["«]?([^"«»\n]+)["»]?',
        r'Профессиональный\s*стандарт\s*["«]?([^"«»\n]+)["»]?',
        r'([А-Я][а-я]+\s+[А-Я][а-я]+)\s*–\s*[^–]+',  # попытка угадать
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Если название длинное (> 50 символов), скорее всего, это не название, а описание
            if len(name) > 80:
                name = None
                continue
            break
    
    # Если название не найдено, попробуем взять первую строку, содержащую слово "стандарт"
    if not name:
        lines = text.split('\n')
        for line in lines:
            if 'стандарт' in line.lower() and len(line) < 100:
                line = re.sub(r'^(Профессиональный|Федеральный|Государственный)\s+', '', line)
                name = line.strip()
                break
    
    return name, code

def extract_text_from_pdf(pdf_path, use_ocr_if_needed=True):
    """Извлекает текст из PDF, при необходимости использует OCR."""
    text = ''
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
    except Exception as e:
        print(f"pdfplumber ошибка для {pdf_path}: {e}")

    if use_ocr_if_needed and len(text.strip()) < 200:
        print(f"  Текст не извлечён (длина {len(text)}), запускаем OCR...")
        try:
            images = convert_from_path(pdf_path, dpi=300)
            ocr_text = ''
            for img in images:
                page_text = pytesseract.image_to_string(img, lang='rus')
                ocr_text += page_text + '\n'
            text = ocr_text
        except Exception as e:
            print(f"  Ошибка OCR: {e}")
    return text

def extract_standard_code(text):
    """Ищет код профессионального стандарта (например, 06.001)"""
    patterns = [
        r'(Профессиональный стандарт\s*)?(\d{2}\.\d{3})',
        r'Код\s*(\d{2}\.\d{3})',
        r'(\d{2}\.\d{3})\s*–\s*[А-Я]',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1) if len(match.groups()) > 1 else match.group(0)
    return 'unknown'

def extract_otf_tf_td(text):
    """
    Извлекает из текста профессионального стандарта:
    - обобщённые трудовые функции (ОТФ)
    - трудовые функции (ТФ)
    - трудовые действия (ТД)
    Возвращает список словарей.
    """
    results = []
    # 1. Разбиваем текст по маркерам ОТФ
    otf_blocks = re.split(r'(3\.\d+\.\s*Обобщенная\s*трудовая\s*функция[^\n]*)', text, flags=re.IGNORECASE)
    
    if len(otf_blocks) < 2:
        otf_blocks = re.split(r'(Обобщенная\s*трудовая\s*функция[^\n]*)', text, flags=re.IGNORECASE)
    
    current_otf = None
    for i, block in enumerate(otf_blocks):
        if re.search(r'Обобщенная\s*трудовая\s*функция', block, re.IGNORECASE):
            match = re.search(r'Обобщенная\s*трудовая\s*функция\s*[–-]?\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
            if match:
                current_otf = match.group(1).strip()
            else:
                current_otf = block.strip()
            continue
        elif current_otf and block.strip():
            tf_blocks = re.split(r'(Трудовая\s*функция[^\n]*)', block, flags=re.IGNORECASE)
            current_tf = None
            for j, tf_block in enumerate(tf_blocks):
                if re.search(r'Трудовая\s*функция', tf_block, re.IGNORECASE):
                    tf_match = re.search(r'Трудовая\s*функция\s*[–-]?\s*(.+?)(?:\n|$)', tf_block, re.IGNORECASE)
                    if tf_match:
                        current_tf = tf_match.group(1).strip()
                    else:
                        current_tf = tf_block.strip()
                    continue
                elif current_tf and tf_block.strip():
                    td_text = ''
                    td_lines = []
                    for line in tf_block.split('\n'):
                        line = line.strip()
                        if re.match(r'^[•\-–]\s*', line):
                            td_lines.append(re.sub(r'^[•\-–]\s*', '', line))
                        elif line and not re.search(r'Необходимые\s*умения|Необходимые\s*знания', line, re.IGNORECASE):
                            td_lines.append(line)
                    td_text = '; '.join(td_lines)
                    if td_text:
                        results.append({
                            'otf': current_otf,
                            'tf': current_tf,
                            'td': td_text
                        })
                    current_tf = None

    if not results:
        lines = text.split('\n')
        current_otf = None
        current_tf = None
        for i, line in enumerate(lines):
            line = line.strip()
            if re.search(r'Обобщенная\s*трудовая\s*функция', line, re.IGNORECASE):
                parts = line.split('–')
                current_otf = parts[-1].strip() if len(parts) > 1 else line
                current_tf = None
            elif re.search(r'Трудовая\s*функция', line, re.IGNORECASE) and not re.search(r'Обобщенная', line, re.IGNORECASE):
                parts = line.split('–')
                current_tf = parts[-1].strip() if len(parts) > 1 else line
            elif re.match(r'^[•\-–]\s*', line) and current_tf:
                td = re.sub(r'^[•\-–]\s*', '', line)
                results.append({
                    'otf': current_otf or 'Не указано',
                    'tf': current_tf or 'Не указано',
                    'td': td
                })
            elif line and current_tf and not re.search(r'Необходимые|умения|знания', line, re.IGNORECASE):
                pass
    return results

# --- Основной процесс ---
standarts_dir = 'standarts'
output_csv = 'profstandarts.csv'

all_data = []
for filename in os.listdir(standarts_dir):
    if not filename.lower().endswith('.pdf'):
        continue
    pdf_path = os.path.join(standarts_dir, filename)
    print(f"\nОбработка {filename}...")
    
    text = extract_text_from_pdf(pdf_path, use_ocr_if_needed=True)
    if not text.strip():
        print(f"  Не удалось извлечь текст из {filename}")
        continue
    
    standard_name, standard_code = extract_standard_name_and_code(text)
    print(f"  Название: {standard_name}")
    print(f"  Код: {standard_code}")
    
    data = extract_otf_tf_td(text)
    for item in data:
        all_data.append({
            'filename': filename,
            'standard_name': standard_name or 'Не указано',
            'standard_code': standard_code or 'Не указано',
            'otf': item['otf'],
            'tf': item['tf'],
            'td': item['td']
        })
    print(f"  Извлечено {len(data)} записей")

with open(output_csv, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['filename', 'standard_name', 'standard_code', 'otf', 'tf', 'td']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(all_data)

print(f"\nВсего извлечено {len(all_data)} записей. Сохранено в {output_csv}")
import requests
from bs4 import BeautifulSoup
import time
import re
import os
from urllib.parse import urljoin, unquote, urlparse, parse_qs

def parse_fgos_ugsn(ugsn_url):
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })

    response = session.get(ugsn_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    results = []

    # Ищем все ссылки на PDF на странице УГСН
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/fgosvo/downloads' in href:
            pdf_link = urljoin('https://fgosvo.ru', href)
            parsed = urlparse(pdf_link)
            params = parse_qs(parsed.query)
            f_value = params.get('f', [''])[0]
            decoded = unquote(f_value)
            filename = decoded.split('/')[-1]
            code_match = re.search(r'(\d{6})', filename)
            code = code_match.group(1)
            formatted_code = f"{code[:2]}.{code[2:4]}.{code[4:6]}"
        
            results.append((formatted_code, pdf_link))

            time.sleep(0.5)

    return results

def download_pdf(pdf_url, output_dir='pdfs'):
    """Скачивает PDF по ссылке и сохраняет в указанную папку"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Извлекаем имя файла из URL
    filename = pdf_url.split('f=')[-1].split('&')[0]
    from urllib.parse import unquote
    filename = unquote(filename).split('/')[-1]
    
    filepath = os.path.join(output_dir, filename)
    
    if os.path.exists(filepath):
        print(f"  Файл уже существует: {filepath}")
        return filepath
    
    print(f"  Скачиваем: {filename}")
    response = requests.get(pdf_url)
    response.raise_for_status()
    
    with open(filepath, 'wb') as f:
        f.write(response.content)
    return filepath

if __name__ == '__main__':
    main_url = "https://fgosvo.ru/fgosvo/index/5"
    response = requests.get(main_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    items = soup.select('#w0 .item .item-link')
    target_codes = ['31', '81']
    target_urls = []

    for item in items:
        href = item.get('href')
        name = item.text.strip()
        try:
            ugsn_code = href.split('/')[-1]
        except ValueError:
            continue
        if ugsn_code not in target_codes:
            continue
        full_url = "https://fgosvo.ru" + href
        print(f"Парсим УГСН: {name} -> {full_url}")
        target_urls.append(full_url)
        time.sleep(1)

    # Целевые коды направлений (магистратура)
    target_direction_codes = ['02.04.03', '09.04.01', '09.04.02', '09.04.03', '09.04.04']

    all_competencies = {}
    for url in target_urls:
        print(f"\n=== Обрабатываем УГСН: {url} ===")
        result = parse_fgos_ugsn(url)
        for code, pdf_link in result:
            if not code in target_direction_codes:
                continue
            pdf_file = download_pdf(pdf_link)
            print(f"  Направление {code}: {pdf_file}")
        
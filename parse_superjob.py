import requests
import time
import csv
from typing import List, Dict, Optional, Set
from collections import defaultdict

from keys.superjob import API_KEY


class SuperJobParser:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.superjob.ru/2.0/vacancies/"
        self.headers = {"X-Api-App-Id": self.api_key}
        
        # Словарь навыков для извлечения (без изменений)
        self.skill_keywords = {
            "python": "Python",
            "java": "Java",
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "c++": "C++",
            "c#": "C#",
            "go": "Go",
            "ruby": "Ruby",
            "php": "PHP",
            "swift": "Swift",
            "kotlin": "Kotlin",
            "1с": "1С",
            "sql": "SQL",
            "postgresql": "PostgreSQL",
            "mysql": "MySQL",
            "mongodb": "MongoDB",
            "docker": "Docker",
            "kubernetes": "Kubernetes",
            "linux": "Linux",
            "git": "Git",
            "ci/cd": "CI/CD",
            "aws": "AWS",
            "azure": "Azure",
            "react": "React",
            "vue": "Vue.js",
            "angular": "Angular",
            "django": "Django",
            "flask": "Flask",
            "spring": "Spring",
            "node.js": "Node.js",
            "redis": "Redis",
            "elasticsearch": "Elasticsearch",
            "kafka": "Kafka",
            "jenkins": "Jenkins",
            "ansible": "Ansible",
            "terraform": "Terraform",
            "prometheus": "Prometheus",
            "grafana": "Grafana",
        }

    def get_vacancies(self, keyword: str, count: int = 100, town: Optional[int] = None, page: int = 0) -> Dict:
        """Один запрос к API с увеличенным count (до 100)."""
        params = {"keyword": keyword, "count": count, "page": page}
        if town:
            params["town"] = town
        try:
            resp = requests.get(self.base_url, headers=self.headers, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"  Ошибка запроса для '{keyword}' (город {town}): {e}")
            return {}

    def get_vacancies_batch(self, keyword: str, total: int = 500, town: Optional[int] = None) -> List[Dict]:
        """
        Собирает все вакансии по одному ключевому слову и городу.
        Использует пагинацию с учётом поля total из ответа.
        """
        all_vacancies = []
        page = 0
        per_page = min(100, total)  # максимум 100 на страницу
        while len(all_vacancies) < total:
            data = self.get_vacancies(keyword, per_page, town, page)
            if not data or "objects" not in data:
                break
            objects = data["objects"]
            if not objects:
                break
            all_vacancies.extend(objects)
            
            total_api = data.get("total", 0)
            if total_api and len(all_vacancies) >= total_api:
                break
            
            page += 1
            time.sleep(0.3)
        return all_vacancies[:total]

    def extract_competencies(self, vacancy: Dict) -> List[str]:
        """Извлекает навыки из текста вакансии (без изменений)."""
        full_text = ""
        for field in ['vacancyRichText', 'description', 'work', 'requirements', 'candidat']:
            field_value = vacancy.get(field)
            if field_value:
                if isinstance(field_value, str):
                    full_text += " " + field_value.lower()
                elif isinstance(field_value, dict):
                    full_text += " " + str(field_value).lower()
        profession = vacancy.get('profession', '')
        if profession:
            full_text += " " + profession.lower()
        
        found = []
        for key, normalized in self.skill_keywords.items():
            if key in full_text:
                found.append(normalized)
        return found

    def collect_for_role(
        self,
        role_name: str,
        keywords: List[str],
        towns: List[int],
        total_per_role: int = 500,
    ) -> List[Dict]:
        """
        Собирает вакансии для одной профессии (роли) по всем синонимам и городам.
        Возвращает список уникальных вакансий (удаляет дубли по id).
        """
        seen_ids: Set[int] = set()
        all_vacancies = []
        
        for town in towns:
            for kw in keywords:
                print(f"  → Поиск по '{kw}' в городе {town}...")
                vacancies = self.get_vacancies_batch(keyword=kw, total=total_per_role, town=town)
                print(f"    Найдено {len(vacancies)} вакансий")
                
                for vac in vacancies:
                    vac_id = vac.get('id')
                    if vac_id and vac_id not in seen_ids:
                        seen_ids.add(vac_id)
                        # Добавляем мета-информацию
                        vac['_role'] = role_name
                        vac['_town'] = town
                        vac['_town_title'] = vac.get('town', {}).get('title') if isinstance(vac.get('town'), dict) else None
                        all_vacancies.append(vac)
        
        print(f"  Итого уникальных вакансий для '{role_name}': {len(all_vacancies)}")
        return all_vacancies

    def collect_multiple_roles(
        self,
        roles: Dict[str, List[str]],
        towns: List[int],
        total_per_role: int = 500,
        output_file: str = "all_vacancies.csv"
    ):
        """
        Главный метод сбора для нескольких ролей.
        Сохраняет результаты в один CSV и отдельную статистику по навыкам.
        """
        all_data = []
        all_skills_summary = defaultdict(int)
        
        for role_name, keywords in roles.items():
            print(f"\nСобираем вакансии для '{role_name}' (синонимы: {keywords})...")
            role_vacancies = self.collect_for_role(role_name, keywords, towns, total_per_role)
            
            for vac in role_vacancies:
                skills = self.extract_competencies(vac)
                for s in skills:
                    all_skills_summary[s] += 1
                
                all_data.append({
                    'role': vac.get('_role', role_name),
                    'town': vac.get('_town_title') or vac.get('town'),
                    'id': vac.get('id'),
                    'profession': vac.get('profession', ''),
                    'firm_name': vac.get('firm_name', ''),
                    'payment_from': vac.get('payment_from'),
                    'payment_to': vac.get('payment_to'),
                    'currency': vac.get('currency'),
                    'experience': vac.get('experience', {}).get('title') if isinstance(vac.get('experience'), dict) else vac.get('experience'),
                    'education': vac.get('education', {}).get('title') if isinstance(vac.get('education'), dict) else vac.get('education'),
                    'date_published': vac.get('date_published'),
                    'link': vac.get('link'),
                    'skills': ', '.join(skills)
                })
        
        # Сохраняем все вакансии
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['role', 'town', 'id', 'profession', 'firm_name', 'payment_from', 'payment_to',
                          'currency', 'experience', 'education', 'date_published', 'link', 'skills']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_data)
        
        # Сохраняем статистику навыков
        stats_file = output_file.replace('.csv', '_skills_stats.csv')
        with open(stats_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['skill', 'count'])
            for skill, count in sorted(all_skills_summary.items(), key=lambda x: x[1], reverse=True):
                writer.writerow([skill, count])
        
        print(f"\nВсего собрано {len(all_data)} уникальных вакансий")
        print(f"Результаты сохранены в {output_file} и {stats_file}")
        return all_data, all_skills_summary


if __name__ == "__main__":
    parser = SuperJobParser(API_KEY)  # если ключ в keys.superjob
    
    roles = {
        "программист": ["программист", "разработчик", "developer", "инженер-программист", "программист-разработчик"],
        "системный аналитик": ["системный аналитик", "бизнес-аналитик", "аналитик требований", "системный аналитик"],
        "архитектор ПО": ["архитектор программного обеспечения", "архитектор", "solution architect", "архитектор решений"]
    }
    
    towns = [1, 4, 3, 8]
    
    vacancies, skills = parser.collect_multiple_roles(
        roles=roles,
        towns=towns,
        total_per_role=200,
        output_file="superjob_roles.csv"
    )
    
    # Выводим топ-10 самых частых навыков
    print("\nТоп-10 самых востребованных навыков (по всем ролям):")
    for i, (skill, count) in enumerate(sorted(skills.items(), key=lambda x: x[1], reverse=True)[:10], 1):
        print(f"  {i}. {skill}: {count} упоминаний")
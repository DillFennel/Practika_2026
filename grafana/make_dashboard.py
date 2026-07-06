#!/usr/bin/env python3
import json
import sys
import requests
import os

# ---------- НАСТРОЙКИ ----------
GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASSWORD = "12345"
DASHBOARD_FILE = "dashboard-1783298192238.json"

def import_dashboard_v2(dashboard_path, grafana_url, user, password):
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        dashboard = json.load(f)

    # Проверяем формат
    if dashboard.get('apiVersion') != 'dashboard.grafana.app/v2':
        print("Ожидается apiVersion: dashboard.grafana.app/v2")
        sys.exit(1)

    # Очищаем metadata от полей, которые нельзя передавать при создании/обновлении
    metadata = dashboard.get('metadata', {})
    metadata.pop('resourceVersion', None)
    metadata.pop('generation', None)
    metadata.pop('creationTimestamp', None)
    metadata.pop('annotations', None)
    # Убеждаемся, что есть namespace
    if 'namespace' not in metadata:
        metadata['namespace'] = 'default'

    # Определяем метод и URL
    uid = metadata.get('name')
    if uid:
        url = f"{grafana_url}/apis/dashboard.grafana.app/v2/namespaces/default/dashboards/{uid}"
        method = 'PUT'   # обновление
    else:
        url = f"{grafana_url}/apis/dashboard.grafana.app/v2/namespaces/default/dashboards"
        method = 'POST'  # создание

    headers = {'Content-Type': 'application/json'}
    auth = (user, password)

    try:
        if method == 'PUT':
            resp = requests.put(url, json=dashboard, headers=headers, auth=auth)
        else:
            resp = requests.post(url, json=dashboard, headers=headers, auth=auth)

        if resp.status_code in (200, 201):
            data = resp.json()
            new_uid = data.get('metadata', {}).get('name', uid)
            print(f"Дашборд успешно импортирован, uid: {new_uid}")
            print(f"Ссылка: {grafana_url}/d/{new_uid}")
        else:
            print(f"Ошибка {resp.status_code}: {resp.text}")
            sys.exit(1)
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Можно использовать переменные окружения
    url = os.getenv("GRAFANA_URL", GRAFANA_URL)
    user = os.getenv("GRAFANA_USER", GRAFANA_USER)
    password = os.getenv("GRAFANA_PASSWORD", GRAFANA_PASSWORD)
    file = os.getenv("DASHBOARD_FILE", DASHBOARD_FILE)

    import_dashboard_v2(file, url, user, password)
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 1. Загружаем обновлённые данные (после первого скрипта)
df = pd.read_csv('all_competencies_2_updated.csv', encoding='utf-8')

# 2. Группируем по категории и источнику, считаем количество
grouped = df.groupby(['category_group', 'source']).size().reset_index(name='count')

# 3. Преобразуем в таблицу (pivot) для удобства построения
pivot = grouped.pivot(index='category_group', columns='source', values='count').fillna(0)

# Убедимся, что колонки идут в нужном порядке (ФГОС, Вакансия, Профстандарт)
# и что все три присутствуют (если нет, добавим с нулями)
desired_order = ['ФГОС', 'Вакансия', 'Профстандарт']
for col in desired_order:
    if col not in pivot.columns:
        pivot[col] = 0
pivot = pivot[desired_order]

# Сортируем по сумме (опционально) для лучшей читаемости
pivot['total'] = pivot.sum(axis=1)
pivot = pivot.sort_values('total', ascending=False).drop('total', axis=1)

# 4. Построение сгруппированной столбчатой диаграммы
categories = pivot.index
x = np.arange(len(categories))  # позиции для групп
width = 0.25  # ширина каждого столбца

fig, ax = plt.subplots(figsize=(12, 7))

# Рисуем столбцы для каждого источника
colors = {'ФГОС': '#4C72B0', 'Вакансия': '#55A868', 'Профстандарт': '#C44E52'}
for i, source in enumerate(desired_order):
    values = pivot[source].values
    ax.bar(x + i*width, values, width, label=source, color=colors[source])

# Оформление
ax.set_xlabel('Категория компетенций', fontsize=12)
ax.set_ylabel('Количество компетенций', fontsize=12)
ax.set_title('Распределение компетенций по категориям и источникам', fontsize=14)
ax.set_xticks(x + width)  # центр группы
ax.set_xticklabels(categories, rotation=45, ha='right', fontsize=10)
ax.legend(title='Источник')

# Добавляем значения на столбцы (опционально)
for i, source in enumerate(desired_order):
    values = pivot[source].values
    for j, val in enumerate(values):
        if val > 0:
            ax.text(j + i*width, val + 0.3, str(int(val)), ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig('competencies_by_source.png', dpi=300)
plt.show()
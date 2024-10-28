import sqlite3
import re
import time
import requests
import pandas as pd

from swarm import Swarm, Agent
from tabulate import tabulate

# 初始化 Swarm 客户端
client = Swarm()

# 创建内存数据库连接
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# 从csv中读取数据
cursor.execute('''
CREATE TABLE cardatas (
    car_id INTEGER PRIMARY KEY,
    brand TEXT,
    model TEXT,
    year INTEGER,
    color TEXT,
    mileage REAL,
    price REAL,
    location TEXT
)
''')

file_path = 'Car Data.csv'
car_data = pd.read_csv(file_path)

for _, row in car_data.iterrows():
    cursor.execute('INSERT INTO cardatas VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                   [row['CarID'], row['Brand'], row['Model'], row['Year'], row['Color'],
                    row['Mileage'], row['Price'], row['Location']])
conn.commit()


def instructions(context_variables):
    return """你是一个能够将中文自然语言查询转换为SQL查询的AI助手。
    数据库有一个名为'cardatas'的表，包含以下列：car_id, brand, model, year, color, mileage,
    price, location。只返回SQL查询，不要包含任何其他文本或解释。支持复杂查询，如比较、排序和聚合函数。"""


def clean_sql_query(sql_query):
    """清理SQL查询，移除可能的Markdown格式和多余空白"""
    cleaned = re.sub(r'```sql\s*|\s*```', '', sql_query).strip()
    return cleaned


def execute_sql(sql_query):
    """执行SQL查询并返回结果"""
    try:
        cursor.execute(sql_query)
        results = cursor.fetchall()
        return results
    except sqlite3.Error as e:
        return f"SQL错误: {e}"


def explain_query(sql_query):
    """提供更具体的SQL查询解释"""
    parts = sql_query.upper().split()
    explanation = "这个查询"

    if 'SELECT' in parts:
        select_index = parts.index('SELECT')
        from_index = parts.index('FROM')
        fields = ', '.join(parts[select_index + 1:from_index]).lower()
        table = parts[from_index + 1].lower()
        explanation += f"从{table}表中获取{fields}"

    if 'WHERE' in parts:
        where_index = parts.index('WHERE')
        condition = ' '.join(parts[where_index + 1:]).lower()
        explanation += f"，条件是{condition}"

    if 'ORDER BY' in parts:
        order_index = parts.index('ORDER')
        order = ' '.join(parts[order_index + 2:]).lower()
        explanation += f"，结果按{order}排序"

    if 'LIMIT' in parts:
        limit_index = parts.index('LIMIT')
        limit = parts[limit_index + 1]
        explanation += f"，只显示前{limit}条结果"

    return explanation + "。"


def format_results(results, sql_query):
    """格式化查询结果，添加上下文和单位"""
    if not results or len(results) == 0:
        return "没有找到匹配的结果。"

    if isinstance(results, str):  # 错误消息
        return results

    headers = [description[0] for description in cursor.description]

    # 添加单位
    # if 'price' in headers:
    #     price_index = headers.index('price')
    #     results = [list(row) for row in results]
    #     for row in results:
    #         row[price_index] = f"{row[price_index]}元"

    formatted_results = tabulate(results, headers=headers, tablefmt="grid")

    # 添加结果上下文
    # if len(results) == 1 and 'car_id' in headers and 'price' in headers:
    #     carid_index = headers.index('car_id')
    #     price_index = headers.index('price')
    #     context = f"{results[0][carid_index]}的薪水是{results[0][price_index]}"
    #     return f"{context}\n\n{formatted_results}"

    return formatted_results


agent = Agent(
    name="SQLAgent",
    instructions=instructions,
)


def process_query(natural_language_query):
    """处理自然语言查询，转换为SQL，执行并返回结果"""
    # 使用 Swarm 将自然语言转换为 SQL
    try:
        response = client.run(
            messages=[{"role": "user", "content": natural_language_query}],
            agent=agent,
        )

    except requests.exceptions.Timeout:
        time.sleep(10)
        print("Swarm API请求超时，请稍后再试。")

    sql_query = clean_sql_query(response.messages[-1]["content"])

    # 执行 SQL 查询
    results = execute_sql(sql_query)

    # 获取查询解释
    explanation = explain_query(sql_query)

    # 格式化结果
    formatted_results = format_results(results, sql_query)

    return f"SQL查询: {sql_query}\n解释: {explanation}\n结果:\n{formatted_results}"


# 主程序循环
if __name__ == "__main__":
    print("欢迎使用text to SQL系统！")
    print("输入 'exit' 或 'quit' 退出程序。")
    print("本系统支持复杂查询，如比较、排序和聚合函数。")

    while True:
        user_input = input("\n请输入您的查询 (或 'exit' 退出): ")
        if user_input.lower() in ['exit', 'quit']:
            print("谢谢使用，再见！")
            break

        print(process_query(user_input))

# 关闭数据库连接
conn.close()

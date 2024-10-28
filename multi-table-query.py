import sqlite3
import re
from swarm import Swarm, Agent
from tabulate import tabulate

# 初始化 Swarm 客户端
client = Swarm()

# 创建内存数据库连接
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# 创建员工表
cursor.execute('''
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name TEXT,
    department_id INTEGER,
    salary REAL
)
''')

# 创建部门表
cursor.execute('''
CREATE TABLE departments (
    id INTEGER PRIMARY KEY,
    name TEXT,
    location TEXT
)
''')

# 插入员工数据
employees = [
    (1, '张伟', 1, 75000),
    (2, '王芳', 2, 65000),
    (3, '李斯', 3, 80000),
    (4, '赵静', 4, 70000),
    (5, '陈明', 1, 72000),
    (6, '杨丽', 2, 68000),
    (7, '周浩', 3, 82000),
    (8, '吴娜', 4, 71000),
    (9, '刘洋', 1, 76000),
    (10, '孙琳', 2, 67000)
]
cursor.executemany('INSERT INTO employees VALUES (?,?,?,?)', employees)

# 插入部门数据
departments = [
    (1, 'IT', '北京'),
    (2, 'HR', '上海'),
    (3, '销售', '广州'),
    (4, '市场', '深圳')
]
cursor.executemany('INSERT INTO departments VALUES (?,?,?)', departments)

conn.commit()


def instructions(context_variables):
    return """你是一个能够将中文自然语言查询转换为SQL查询的AI助手。
    数据库有两个表：
    1. 'employees'表，包含以下列：id, name, department_id, salary
    2. 'departments'表，包含以下列：id, name, location
    只返回SQL查询，不要包含任何其他文本或解释。支持复杂查询，包括多表连接、比较、排序和聚合函数。"""


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
    """提供更具体的SQL查询解释，包括多表查询"""
    parts = sql_query.upper().split()
    explanation = "这个查询"

    if 'SELECT' in parts:
        select_index = parts.index('SELECT')
        from_index = parts.index('FROM')
        fields = ', '.join(parts[select_index + 1:from_index]).lower()
        tables = []
        for i in range(from_index + 1, len(parts)):
            if parts[i] in ['WHERE', 'GROUP', 'ORDER', 'LIMIT']:
                break
            if parts[i] not in ['JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'ON', 'AND']:
                tables.append(parts[i].lower())
        tables = ', '.join(tables)
        explanation += f"从{tables}表中获取{fields}"

    if 'JOIN' in parts:
        explanation += "，进行了表连接"

    if 'WHERE' in parts:
        where_index = parts.index('WHERE')
        condition = ' '.join(parts[where_index + 1:]).lower()
        explanation += f"，条件是{condition}"

    if 'GROUP BY' in parts:
        group_index = parts.index('GROUP')
        group = ' '.join(parts[group_index + 2:]).lower()
        explanation += f"，按{group}进行分组"

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

    # 为薪水添加单位
    if 'salary' in headers:
        salary_index = headers.index('salary')
        results = [list(row) for row in results]
        for row in results:
            row[salary_index] = f"{row[salary_index]}元"

    formatted_results = tabulate(results, headers=headers, tablefmt="grid")

    return formatted_results


agent = Agent(
    name="SQLAgent",
    instructions=instructions,
)


def process_query(natural_language_query):
    """处理自然语言查询，转换为SQL，执行并返回结果"""
    # 使用 Swarm 将自然语言转换为 SQL
    response = client.run(
        messages=[{"role": "user", "content": natural_language_query}],
        agent=agent,
    )
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
    print("欢迎使用支持多表查询的中文自然语言到SQL转换系统！")
    print("输入 'exit' 或 'quit' 退出程序。")
    print("本系统支持复杂查询，包括多表连接、比较、排序和聚合函数。")

    while True:
        user_input = input("\n请输入您的查询 (或 'exit' 退出): ")
        if user_input.lower() in ['exit', 'quit']:
            print("谢谢使用，再见！")
            break

        print(process_query(user_input))

# 关闭数据库连接
conn.close()

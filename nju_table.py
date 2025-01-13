from seatable_api import Base, context
from config import config
import json
import re
import os
from collections import defaultdict


server_url = 'https://table.nju.edu.cn'
api_token = config['api_token']

def fetch_data():
    base = Base(api_token, server_url)
    try:
        base.auth()
    except:
        print("Failed to authenticate")
        return
    
    # 获取所有子表的元数据
    row_names = {
        '2024':['课程','授课老师'],
        '2022':['课程','老师'],
        '2021':['课程名','任课老师'],
        '2020':['课程','老师']
    }
    metadata = base.get_metadata()
    tables = metadata['tables']
    
    result = []
    
    # 遍历所有子表
    for table in tables:
        table_name:str = table['name']
        
        # 检查子表名称是否以年份开头
        if re.match(r'^\d{4}', table_name):
            if table_name.startswith('2023'): continue
            rows = base.list_rows(table_name)
            # 检查子表是否包含“课程名称”和“授课老师”这两列
            course_row_name = row_names[table_name[:4]][0]
            teacher_row_name = row_names[table_name[:4]][1]
            if course_row_name in rows[0] and teacher_row_name in rows[0]:
                for row in rows:
                    if not row[course_row_name] and not row[teacher_row_name]:
                        continue
                    if '额外标签' in row and row['额外标签'] == '允许额外补充标签': 
                        continue
                    entry = {
                        "课程名称": row[course_row_name],
                        "教师": row[teacher_row_name]
                    }
                    # 添加评价列
                    cnt = 0
                    for i, key in enumerate(row):
                        if key.startswith('评价'):
                            if row[key]:
                                entry[f"评价_{cnt}"] = row[key]
                                cnt += 1
                    result.append(entry)
    
    # 将结果保存为 JSON 文件
    with open('data/seatable.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

def merge_json_files():
    data_folder = 'data'
    merged_data = defaultdict(lambda: defaultdict(list))

    # 读取所有 .json 文件
    for filename in os.listdir(data_folder):
        if filename.endswith('.json') and not filename.startswith('merged_data'):
            filepath = os.path.join(data_folder, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for entry in data:
                    course_name = entry.get('课程名称')
                    teacher = entry.get('教师')
                    if course_name or teacher:
                        key = (course_name, teacher)
                        for k, v in entry.items():
                            if k.startswith('评价'):
                                #if teacher == '蒋天婵':print(filename, v)
                                merged_data[key][k].append(v) 
    # 合并评价
    result = []
    for (course_name, teacher), evaluations in merged_data.items():
        merged_entry = {
            '课程名称': course_name,
            '教师': teacher
        }
        cnt = 0
        evals = set()
        for tmp in evaluations.values():
            for eval in tmp:
                if type(eval) == list:
                    for element in eval: evals.add(element.strip())
                else:
                    evals.add(eval.strip())
        for eval in evals:
            merged_entry[f'评价_{cnt}'] = eval
            cnt += 1
        if len(merged_entry) > 2:
            result.append(merged_entry)

    # 保存合并后的数据
    with open('data/merged_data.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    fetch_data()
    merge_json_files()

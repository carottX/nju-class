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
        '2025':['课程','授课老师'],
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
                        "教师": row[teacher_row_name],
                        "来源": f"NJU Table - {table_name}"
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
    all_reviews = []  # 存储所有的评价条目

    # 读取所有 .json 文件
    for filename in os.listdir(data_folder):
        if filename.endswith('.json') and not filename.startswith('merged_data'):
            filepath = os.path.join(data_folder, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for entry in data:
                    course_name = entry.get('课程名称')
                    teacher = entry.get('教师')
                    source = entry.get('来源', filename)  # 获取来源信息，如果没有则使用文件名
                    
                    if course_name or teacher:
                        # 为每个评价创建单独的条目
                        reviews = []
                        for k, v in entry.items():
                            if k.startswith('评价') and v:
                                reviews.append(v.strip() if isinstance(v, str) else str(v).strip())
                        
                        # 如果有评价，为每个评价创建条目；如果没有评价，创建一个基本条目
                        if reviews:
                            for review in reviews:
                                review_entry = {
                                    '课程名称': course_name,
                                    '教师': teacher,
                                    '来源': [source],
                                    '评价_0': review
                                }
                                all_reviews.append(review_entry)
                        else:
                            basic_entry = {
                                '课程名称': course_name,
                                '教师': teacher,
                                '来源': [source]
                            }
                            all_reviews.append(basic_entry)

    # 去重：合并相同课程、教师、评价内容的条目，合并来源信息
    unique_reviews = {}
    for review in all_reviews:
        key = (review['课程名称'], review['教师'], review.get('评价_0', ''))
        if key in unique_reviews:
            # 合并来源信息
            existing_sources = set(unique_reviews[key]['来源'])
            new_sources = set(review['来源'])
            unique_reviews[key]['来源'] = list(existing_sources | new_sources)
        else:
            unique_reviews[key] = review.copy()

    # 保存合并后的数据
    result = list(unique_reviews.values())
    with open('data/merged_data.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    fetch_data()
    merge_json_files()

from flask import Flask, request, jsonify, render_template
import pandas as pd
import glob
import logging
import re
import threading
import time
from pypinyin import lazy_pinyin, Style
from nju_table import fetch_data, merge_json_files
from config import config

app = Flask(__name__)

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# 全局变量和锁
data = None
data_lock = threading.Lock()

def load_data():
    all_files = glob.glob("data/merged_data.json")
    df_list = []
    logging.info("Loading data from JSON files")
    for file in all_files:
        df = pd.read_json(file)
        df_list.append(df)
    combined_df = pd.concat(df_list, ignore_index=True)
    return combined_df

def update_data():
    global data
    while True:
        fetch_data()
        merge_json_files()
        with data_lock:
            data = load_data()
        time.sleep(3600)  # 每小时运行一次

# 启动定时任务线程
update_thread = threading.Thread(target=update_data)
update_thread.daemon = True
update_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search/teacher', methods=['GET'])
def search_teacher():
    teacher_name = request.args.get('name')
    if not teacher_name:
        return jsonify({'error': 'Teacher name is required'}), 400
    
    with data_lock:
        # 精准匹配
        exact_match = data[data['教师'] == teacher_name]
        
        # 构建正则表达式模式，允许在字符之间有任意字符
        pattern = '.*'.join(teacher_name)
        regex = re.compile(pattern, re.IGNORECASE)
        
        # 模糊匹配
        partial_match = data[data['教师'].str.contains(regex, na=False) & (data['教师'] != teacher_name)]
        
        # 拼音首字母匹配
        def match_pinyin_initials(name, initials):
            if pd.isna(name):
                return False
            pinyin_initials = ''.join([p[0] for p in lazy_pinyin(name, style=Style.FIRST_LETTER)])
            return pinyin_initials.startswith(initials.lower())
        
        pinyin_match = data[data['教师'].apply(lambda x: match_pinyin_initials(x, teacher_name))]
        
        # 合并结果，精准匹配的结果在前
        result = pd.concat([exact_match, partial_match, pinyin_match]).drop_duplicates()
        result = result.apply(lambda x: x.dropna(), axis=1)
    
    if result.empty:
        return jsonify({'message': 'No courses found for this teacher'}), 404
    
    return result.to_json(orient='records', force_ascii=False)

@app.route('/search/course', methods=['GET'])
def search_course():
    course_name = request.args.get('name')
    if not course_name:
        return jsonify({'error': 'Course name is required'}), 400
    
    with data_lock:
        # 精准匹配
        exact_match = data[data['课程名称'] == course_name]
        
        # 构建正则表达式模式，允许在字符之间有任意字符
        pattern = '.*'.join(course_name)
        regex = re.compile(pattern, re.IGNORECASE)
        
        # 模糊匹配
        partial_match = data[data['课程名称'].str.contains(regex, na=False) & (data['课程名称'] != course_name)]
        
        # 合并结果，精准匹配的结果在前
        result = pd.concat([exact_match, partial_match]).drop_duplicates()
        result = result.apply(lambda x: x.dropna(), axis=1)
    
    if result.empty:
        return jsonify({'message': 'No reviews found for this course'}), 404
    
    return result.to_json(orient='records', force_ascii=False)

if __name__ == '__main__':
    with data_lock:
        data = load_data()
    app.run(debug=True)
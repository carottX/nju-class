from flask import Flask, request, jsonify, render_template
import pandas as pd
import glob
import re
import logging

app = Flask(__name__)

# 读取所有xlsx文件并合并数据
def load_data():
    all_files = glob.glob("data/*.xlsx")
    df_list = []
    for file in all_files:
        xls = pd.ExcelFile(file)
        for sheet_name in xls.sheet_names:
            print(f'Reading {file} - {sheet_name}')
            df = pd.read_excel(xls, sheet_name=sheet_name)
            df_list.append(df)
    combined_df = pd.concat(df_list, ignore_index=True)
    return combined_df

data = load_data()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search/teacher', methods=['GET'])
def search_teacher():
    teacher_name = request.args.get('name')
    if not teacher_name:
        return jsonify({'error': 'Teacher name is required'}), 400
    
    exact_match = data[data['教师'] == teacher_name]

    # 根据老师名字查询课程
    # 构建正则表达式模式，允许在字符之间有任意字符
    pattern = '.*'.join(teacher_name)
    regex = re.compile(pattern)
    
    # 模糊匹配
    partial_match = data[data['教师'].str.contains(regex, na=False) & (data['教师'] != teacher_name)]
    
    # 合并结果，精准匹配的结果在前
    result = pd.concat([exact_match, partial_match])
    result = result.apply(lambda x: x.dropna(), axis=1)

    result = result.apply(lambda x: x.dropna(), axis=1)
    if result.empty:
        return jsonify({'message': 'No courses found for this teacher'}), 404
    return result.to_json(orient='records',force_ascii=False)

@app.route('/search/course', methods=['GET'])
def search_course():
    course_name = request.args.get('name')
    if not course_name:
        return jsonify({'error': 'Course name is required'}), 400
    
    # 精准匹配
    exact_match = data[data['课程名称'] == course_name]
    
    # 构建正则表达式模式，允许在字符之间有任意字符
    pattern = '.*'.join(course_name)
    regex = re.compile(pattern)
    
    # 模糊匹配
    partial_match = data[data['课程名称'].str.contains(regex, na=False) & (data['课程名称'] != course_name)]
    
    # 合并结果，精准匹配的结果在前
    result = pd.concat([exact_match, partial_match])
    result = result.apply(lambda x: x.dropna(), axis=1)
    
    if result.empty:
        return jsonify({'message': 'No reviews found for this course'}), 404
    
    return result.to_json(orient='records', force_ascii=False)

if __name__ == '__main__':
    app.run(debug=True)
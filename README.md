# NJU选课助手
## 支持功能：
搜索老师/课程，支持模糊搜索、首字母搜索

## data数据来源要求：
是 json 文件

xlsx 文件可以通过 `convert.py` 转换为 json 文件

使用“教师”“课程名称”“评价”来分别表示授课教师、课程名、评价。

评价可以写在多栏里，但表头必须都以评价命名

## TODO：
排序有关评价

## DEMO SITE
http://nju.ys.al

## 如何在本地部署
以 linux 系统为例：
```bash
python3 -m venv ./.venv
source ./.venv/bin/activate
pip install -r requirements.txt
python3 ./app.py
```

import glob
import os
import json
import openpyxl

for xlsx_file in glob.glob("data/*.xlsx"):
    wb = openpyxl.load_workbook(xlsx_file)
    all_data = []
    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        rows = list(sheet.values)
        if not rows:
            continue
        headers = []
        seen = {}
        for h in rows[0]:
            h = h or "Unnamed"
            if h in seen:
                seen[h] += 1
                h = f"{h}_{seen[h]}"
            else:
                seen[h] = 0
                if "评价" in h:
                    h += "_0"
            if "课程" in h:
                h = "课程名称"
            headers.append(h)
        data_rows = [row for row in rows[1:] if any(cell for cell in row)]
        sheet_data = []
        has_kecheng = "课程名称" in headers
        for row in data_rows:
            filtered = {}
            for k, v in zip(headers, row):
                if k.startswith("Unnamed"):
                    continue
                if k == "课程名称" and (v is None or v == ""):
                    v = sheet_name
                if v is not None:
                    filtered[k] = str(v)
            if not has_kecheng:
                filtered["课程名称"] = sheet_name
            if filtered:
                sheet_data.append(filtered)
        all_data.extend(sheet_data)
    json_file = os.path.splitext(xlsx_file)[0] + ".json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
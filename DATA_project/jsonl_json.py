import json

jsonl_file = 'sft_data.jsonl'
json_file = 'sft_data.jsonl'

data = []
with open(jsonl_file, 'r', encoding='utf-8') as f:
    for line in f:
        # 逐行读取并转换为字典
        data.append(json.loads(line))

# 将整个列表保存为带缩进的标准 JSON
with open(json_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print("转换完成！现在你可以清晰地查看 data.json 了。")
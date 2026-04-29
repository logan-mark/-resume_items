import argilla as rg
from datasets import load_dataset

# 1. 初始化客户端 (Argilla 2.x 的新写法)
# 请务必替换为你自己的 API_KEY
client = rg.Argilla(api_url="http://127.0.0.1:6900", api_key="你刚刚复制的API_KEY")

print("✅ 成功连接到本地 Argilla 服务！")

# 2. 定义数据集的配置 (Settings)
settings = rg.Settings(
    fields=[
        rg.TextField(name="instruction", title="指令"),
        rg.TextField(name="response", title="AI 生成的回答")
    ],
    questions=[
        rg.RatingQuestion(name="quality", title="回答质量评分", values=[1, 2, 3, 4, 5]),
        rg.TextQuestion(name="correction", title="如果回答有误，请在此修正", required=False)
    ]
)

# 3. 在服务器上创建这个数据集
dataset_name = "my_first_sft_dataset"
print(f"正在创建打标数据集: {dataset_name}...")

# 检查是否已经存在同名数据集，如果存在就删掉重建（方便你反复测试）
if client.datasets(name=dataset_name):
    client.datasets(name=dataset_name).delete()

dataset = rg.Dataset(
    name=dataset_name,
    settings=settings,
    client=client,
)
dataset.create()

# 4. 加载本地数据
print("正在加载本地 sft_data.jsonl 文件...")
local_data = load_dataset("json", data_files="sft_data.jsonl", split="train")

# 5. 打包成 Record 并上传
print("正在将数据推送到网页端，请稍候...")
records = [
    rg.Record(fields={"instruction": item["instruction"], "response": item["output"]})
    for item in local_data
]

# Argilla 2.x 的最新上传语法
dataset.records.log(records)

print("🎉 大功告成！数据已推送。快去 http://127.0.0.1:6900 刷新网页看看吧！")
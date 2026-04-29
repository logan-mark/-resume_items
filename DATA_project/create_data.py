import json
import random
from openai import OpenAI

# 初始化你的 API 客户端 (假设使用支持 OpenAI 格式的接口，如 DeepSeek, 通义千问或本地 vLLM)
client = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")
model_name = "qwen2.5:7b"

# 1. 准备种子指令 (Seed Instructions)
seed_tasks = [
    "用 Python 写一个快速排序算法。",
    "解释一下什么是黑洞的事件视界。",
    "帮我写一封给老板的病假邮件，语气要委婉。"
]


def generate_new_instructions(seeds, num_new=3):
    """第一步：让老师模型根据种子，头脑风暴出新的指令"""
    prompt = f"""你是一个数据生成专家。请阅读以下几条【种子指令】，并模仿它们的风格、难度和多样性，提出 {num_new} 条全新的、完全不同的指令。
    不要重复种子指令。请直接输出这 {num_new} 条指令，每行一条，不要带任何前缀或序号。

    【种子指令】：
    {chr(10).join(seeds)}
    """

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8  # 稍微调高温度，增加多样性
    )
    # 按行分割返回的结果
    return [line.strip() for line in response.choices[0].message.content.split('\n') if line.strip()]


def generate_response(instruction):
    """第二步：让老师模型回答这个新指令"""
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": instruction}],
        temperature=0.3  # 回答需要严谨，温度调低
    )
    return response.choices[0].message.content


# --- 开始自动化流水线 ---
if __name__ == "__main__":
    generated_dataset = []
    print("🚀 开始 Self-Instruct 数据裂变...")

    # 随机抽取 2 个种子给模型作为参考
    sampled_seeds = random.sample(seed_tasks, 2)

    # 1. 生成新指令
    new_instructions = generate_new_instructions(sampled_seeds, num_new=2)
    print(f"\n✨ 成功生成新指令:\n" + "\n".join(new_instructions))

    # 2. 为新指令生成高质量回答，并打包成 JSON
    for inst in new_instructions:
        print(f"正在为指令生成回答: {inst[:15]}...")
        answer = generate_response(inst)

        # 组装成标准 SFT 格式
        data_pair = {
            "instruction": inst,
            "input": "",  # 如果有额外的上下文可以在这里填
            "output": answer
        }
        generated_dataset.append(data_pair)

    # 3. 保存为 JSONL 文件 (大模型微调的标准格式)
    with open('sft_data.jsonl', 'w', encoding='utf-8') as f:
        for item in generated_dataset:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print("\n✅ 成功保存至 sft_data.jsonl！")
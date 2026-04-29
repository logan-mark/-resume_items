import re
from collections import Counter

def clean_text_pipeline(text):
    # 规则 1：长度过滤 (比如少于30个字符直接丢弃)
    if len(text) < 30:
        return False, "拦截原因：文本太短"

    # 规则 2：高频停用词检测 (检查是否具备自然语言的特征)
    stop_words = ["的", "了", "是", "在", "和"]
    if not any(word in text for word in stop_words):
        return False, "拦截原因：缺乏自然语言特征（无停用词）"

    # 规则 3：有效字符比例 (汉字、英文字母、数字)
    # 匹配所有的汉字、字母和数字
    valid_chars = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]', text)
    if len(valid_chars) / len(text) < 0.6:
        return False, "拦截原因：特殊符号过多（疑似乱码或代码）"

    # 规则 4：字符级重复度 (找出出现次数最多的那个字，计算它的占比)
    most_common_char, count = Counter(text).most_common(1)[0]
    if count / len(text) > 0.15:
        return False, "拦截原因：单一字符重复度过高（复读机）"

    return True, "✅ 通过测试，保留为高质量数据"

# --- 测试我们的清洗流水线 ---
test_data = [
    "这是一段非常正常的新闻报道。今天天气晴朗，气温适宜，适合大家出门游玩。大语言模型的数据清洗非常重要。",
    "商品1 价格99 商品2 价格199 商品3 价格299", # 像列表，没有连词
    "系统加载中...加载中...加载中...加载中...加载中...加载中...加载中...", # 重复度极高
    "function test() { console.log('hello') } @@@###!!!$$$", # 代码和特殊符号混杂
    "今天天气好。" # 太短
]

print("--- 开始清洗数据 ---\n")
for i, doc in enumerate(test_data):
    passed, reason = clean_text_pipeline(doc)
    print(f"【文档 {i+1}】: {doc[:20]}... \n结果: {reason}\n")
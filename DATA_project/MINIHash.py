from datasketch import MinHash, MinHashLSH
import jieba # 用于中文分词或切片

# --- 准备测试数据 ---
docA = "今天苹果公司发布了最新的M4芯片，性能大幅提升，功耗显著降低。"
docB = "今日苹果公司发布了最新的M4芯片，性能大幅提升！功耗显著下降。" # 与 A 高度相似
docC = "大语言模型的数据清洗是目前AI工程师最核心的工作之一。" # 完全无关

# --- 第一步：切片 (Shingling) ---
# 为了演示方便，我们使用简单的 2-gram (连续2个字) 进行切片
def get_shingles(text, n=2):
    return set([text[i:i+n] for i in range(len(text)-n+1)])

setA = get_shingles(docA)
setB = get_shingles(docB)
setC = get_shingles(docC)

print(f"文档A的切片示例: {list(setA)[:5]}...")

# --- 第二步：降维 (提取 MinHash 指纹) ---
# num_perm = 128 意味着我们提取 128 个数字作为这篇文章的“数字指纹”
m1 = MinHash(num_perm=128)
m2 = MinHash(num_perm=128)
m3 = MinHash(num_perm=128)

# 将切片数据更新到 MinHash 对象中（必须编码为 utf-8）
for d in setA: m1.update(d.encode('utf8'))
for d in setB: m2.update(d.encode('utf8'))
for d in setC: m3.update(d.encode('utf8'))

print(f"文档A的MinHash指纹(前5个数字): {m1.hashvalues[:5]}...")

# --- 第三步：分桶 (构建 LSH 索引) ---
# threshold=0.8 表示我们只想找出 Jaccard 相似度大于 80% 的文章
# num_perm 必须与上面保持一致
lsh = MinHashLSH(threshold=0.8, num_perm=128)

# 将所有的文档指纹“插入”到 LSH 系统的桶里
lsh.insert("doc_A", m1)
lsh.insert("doc_B", m2)
lsh.insert("doc_C", m3)

# --- 见证奇迹的时刻：查询 ---
# 我们向 LSH 系统提问：谁和 doc_A 最像？
# LSH 不会去跟 doc_B 和 doc_C 挨个做文本对比，而是直接去 doc_A 所在的“桶”里拿数据
result = lsh.query(m1)

print("\n--- 查询结果 ---")
print(f"与文档 A 相似度 > 0.8 的文档有: {result}")
# 预期输出: ['doc_A', 'doc_B'] (doc_C 被成功忽略了)
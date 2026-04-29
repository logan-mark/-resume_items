from fpdf import FPDF

# 自定义 PDF 类（支持中文字体）
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'RAG 测试文档', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'第 {self.page_no()} 页', 0, 0, 'C')

# 创建 PDF 对象
pdf = PDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)

# 设置中文字体（需提前下载支持中文的 .ttf 文件，如 "msyh.ttc" 或使用内置字体）
# 这里使用内置字体，仅支持拉丁字符。如需中文，请取消注释并替换字体路径。
# pdf.add_font('SimHei', '', 'simhei.ttf', uni=True)
# pdf.set_font('SimHei', '', 11)

# 为简便，先使用 Arial 写英文示例内容（也完全可用作 RAG 测试）
pdf.set_font('Arial', '', 11)

# 正文内容
content = """
1. 什么是 RAG？

检索增强生成 (Retrieval-Augmented Generation, RAG) 是一种结合信息检索与大语言模型的技术架构。它先从知识库中检索相关文档片段，再将这些片段作为上下文提示给 LLM，从而生成更准确、更符合事实的回答。

2. RAG 的核心流程

- 索引（Indexing）：将文档分割成块（Chunks），计算嵌入向量并存储到向量数据库。
- 检索（Retrieval）：根据用户问题，通过相似度搜索召回最相关的 top-k 个块。
- 生成（Generation）：将检索到的块与问题组合成提示，交由 LLM 生成最终答案。

3. 关键参数示例

- 分块大小（chunk_size）：256 / 512 / 1024
- 重叠长度（overlap）：20 ~ 50
- top-k：3 或 5
- 相似度阈值：0.7

4. 用于测试的问答对（可模拟评估）

问：RAG 如何减少大模型的幻觉？
答：通过检索真实的外部知识作为参考，约束模型生成范围。

问：什么是向量数据库？
答：专门用于存储和检索高维向量的数据库，如 Chroma、FAISS、Pinecone。

5. 一段重复字段（用于测试去重/合并）

RAG 是检索增强生成。
RAG 是检索增强生成。
RAG 可以提升回答准确性。

6. 长段落测试分块效果

该段落用于测试分块策略是否按句子边界或固定长度分割。包含多个句子。也包含一些无意义的填充词，例如：Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
"""

# 写入多行文本
for line in content.strip().split('\n'):
    if line.strip():
        pdf.multi_cell(0, 8, line.strip())
    else:
        pdf.ln(4)

# 保存 PDF
pdf.output('rag_test_document.pdf')
print("PDF 已生成：rag_test_document.pdf")
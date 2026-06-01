import pdfplumber
import pandas as pd
import re


class FinancialReportParser:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def clean_noise(self, text: str) -> str:
        """
        清洗页眉页脚、页码等噪声数据（你需要根据你的 PDF 实际情况调整正则）
        """
        if not text:
            return ""
        # 剔除纯数字页码（以及带前后空格的数字）
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        # 清除大段连续的空白字符
        text = re.sub(r' {4,}','',text)
        # 把句尾不在段落末尾的单换行符替换为空格
        #如果换行符前面不是句号问号感叹号，且后面跟着小写字母，说明是句中的物理换行
        text = re.sub(r'(?<=[^\.!\?])\n\s*(?=[A-Za-z0-z9])', '', text)
        return text.strip()

    def extract_table_to_markdown(self, page) -> str:
        """
        核心难点：将 PDF 表格精准抽取，并转换为 LLM 最友好的 Markdown 格式
        """
        tables = page.extract_tables()
        if not tables:
            return ""

        md_tables = []
        for table in tables:
            # 清理表格中的 None 值和换行符
            cleaned_table = []
            for row in table:
                cleaned_row = [str(cell).replace('\n', ' ') if cell else "" for cell in row]
                cleaned_table.append(cleaned_row)

            # 使用 pandas 转换为 Markdown
            if len(cleaned_table) > 1:
                df = pd.DataFrame(cleaned_table[1:], columns=cleaned_table[0])
                #替换空字符串为NaN，并删除全空的列
                df.replace("",pd.NA,inplace=True)
                df.dropna(axis=1,how='all',inplace=True)
                md_tables.append(df.to_markdown(index=False))

        return "\n\n".join(md_tables)

    def extract_text_with_layout(self, page) -> str:
        """
        提取文本，尽量保持原本的阅读顺序（如果是双栏，需要更高级的 bounding box 逻辑，这里先做基础处理）
        """
        # pdfplumber 的 extract_text 默认会做一定程度的布局推断
        text = page.extract_text(layout=True)
        return self.clean_noise(text)

    def parse(self, output_path: str):
        """
        执行全流程解析
        """
        print(f"开始解析文档: {self.pdf_path}")
        full_content = []

        with pdfplumber.open(self.pdf_path) as pdf:
            total_pages = len(pdf.pages)

            start_index=40
            end_index=60

            # 建议测试时先切片，比如 pdf.pages[10:15]，别一上来就跑几百页
            for i, page in enumerate(pdf.pages[start_index:end_index]):
                real_page_num = start_index + i + 1
                print(f"正在处理第 {real_page_num}/{total_pages} 页...")

                # 1. 提取文字
                page_text = self.extract_text_with_layout(page)

                # 2. 提取表格并转为 Markdown
                page_tables_md = self.extract_table_to_markdown(page)

                # 3. 组合（在实际工业界，我们会记录表格在文本中的精准锚点，这里为了快速 MVP，我们把表格追加在当页文本后）
                combined_content = f"## 第 {i + 1} 页\n\n"
                if page_text:
                    combined_content += f"{page_text}\n\n"
                if page_tables_md:
                    combined_content += f"### 本页数据表\n\n{page_tables_md}\n\n"

                full_content.append(combined_content)

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(full_content))

        print(f"解析完成！输出已保存至: {output_path}")


# ==========================================
# 测试运行
# ==========================================
if __name__ == "__main__":
    # pip install pdfplumber pandas tabulate
    parser = FinancialReportParser("TSLA_2024.pdf")
    # 强烈建议先用 5-10 页的内容做测试，把正则和表格清洗调优
    parser.parse("parsed_report_2.md")
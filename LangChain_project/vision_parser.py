import fitz  # PyMuPDF
import base64
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
# 🌟 必须导入 Document 类
from langchain_core.documents import Document

# 1. 召唤轻量级视觉翻译官 Moondream
vlm = ChatOllama(model="moondream", temperature=0, base_url="http://127.0.0.1:11434")


def extract_and_describe_images(pdf_path: str) -> list[Document]:
    print(f"📄 开始解析文档: {pdf_path}")
    doc = fitz.open(pdf_path)

    # 🚨 修复点：在这里正确初始化空列表
    image_documents = []

    # 遍历 PDF 的每一页
    for page_num in range(len(doc)):
        page = doc[page_num]

        # 获取当前页的所有图片
        image_list = page.get_images(full=True)
        if image_list:
            print(f"🔍 在第 {page_num + 1} 页发现 {len(image_list)} 张图片，开始召唤 VLM 解析...")

        for img_index, img in enumerate(image_list):
            xref = img[0]
            # 提取图片二进制数据
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            # 将图片转为 Base64 编码
            img_base64 = base64.b64encode(image_bytes).decode('utf-8')

            # 构造多模态 Prompt
            message = HumanMessage(
                content=[
                    {"type": "text",
                     "text": "请像一位专业的数据分析师一样，极其详细地描述这张图片中的所有核心内容、数据趋势或文字信息。"},
                    {"type": "image_url", "image_url": {"url": f"data:image/{image_ext};base64,{img_base64}"}}
                ]
            )

            # 执行看图说话
            response = vlm.invoke([message])

            # 🌟 核心：封装为带有 Metadata 的 Document 对象
            doc_obj = Document(
                page_content=f"图片详细描述：\n{response.content}",
                metadata={
                    "source": pdf_path,
                    "page": page_num + 1,
                    "type": "visual_chart",  # 打上图表标签
                    "image_index": img_index + 1
                }
            )

            # 追加到列表中
            image_documents.append(doc_obj)
            print(f"✅ 第 {page_num + 1} 页的图 {img_index + 1} 解析完成，已封装为 Document！")

    return image_documents


# ==========================================
# 本地测试执行
# ==========================================
if __name__ == "__main__":
    # 确保目录下有这个测试 PDF
    test_pdf = "textpdf.pdf"

    try:
        results = extract_and_describe_images(test_pdf)
        print("\n🎉 全文图片特征提取完毕！")
        print(f"总共生成了 {len(results)} 个高质量的多模态 Document 对象。")

        if results:
            print("\n【示例元数据 (Metadata)】：")
            print(results[0].metadata)
            print("\n【示例内容 (Page Content)】：")
            print(results[0].page_content[:150] + "...")

    except Exception as e:
        print(f"发生错误: {e}")
import fitz  # PyMuPDF
import json
import statistics
from typing import List, Dict, Any


class PdfToDotsFormat:
    def __init__(self, pdf_path: str):
        self.doc = fitz.open(pdf_path)

    def _get_font_histogram(self) -> List[tuple]:
        """统计全文档的字体大小分布，用于推断标题"""
        font_sizes = []
        for page in self.doc:
            blocks = page.get_text("dict")["blocks"]
            for b in blocks:
                if "lines" in b:
                    for l in b["lines"]:
                        for s in l["spans"]:
                            # Round to 1 decimal place to group similar sizes
                            font_sizes.append(round(s["size"], 1))

        # 统计频率
        if not font_sizes:
            return []
        return sorted(list(set(font_sizes)), reverse=True)

    def parse(self) -> List[Dict[str, Any]]:
        """解析PDF并返回符合Dots OCR格式的JSON"""
        json_doc = []

        # 获取字体大小的唯一值，从大到小排序
        # 假设：最大的1-2个字号是标题，中间是正文，最小可能是注脚
        sorted_sizes = self._get_font_histogram()
        if not sorted_sizes:
            return []

        # 简单的启发式规则：
        # 最大字号 -> Title
        # 第二/三字号 -> Section-header (Level 1/2)
        # 其他 -> Text
        title_size = sorted_sizes[0] if sorted_sizes else 0
        h1_size = sorted_sizes[1] if len(sorted_sizes) > 1 else 0
        h2_size = sorted_sizes[2] if len(sorted_sizes) > 2 else 0

        for page_num, page in enumerate(self.doc):
            page_data = {
                "page_no": page_num + 1,
                "full_layout_info": []
            }

            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                # 忽略图片块，只处理文本块 (type 0 is text)
                if block["type"] != 0:
                    continue

                # 合并同一block中的所有行文本
                block_text = ""
                block_bbox = None
                
                # 初始化block的边界框
                min_x0, min_y0, max_x1, max_y1 = float('inf'), float('inf'), float('-inf'), float('-inf')

                for line_idx, line in enumerate(block["lines"]):
                    line_text = ""
                    line_min_x0, line_min_y0, line_max_x1, line_max_y1 = float('inf'), float('inf'), float('-inf'), float('-inf')
                    
                    for span in line["spans"]:
                        text = span["text"]
                        if not text.strip() and not block_text:
                            continue
                        
                        # 更新行的边界框
                        bbox = span["bbox"]
                        line_min_x0 = min(line_min_x0, bbox[0])
                        line_min_y0 = min(line_min_y0, bbox[1])
                        line_max_x1 = max(line_max_x1, bbox[2])
                        line_max_y1 = max(line_max_y1, bbox[3])
                        
                        line_text += text
                    
                    # 添加行文本到块文本中
                    if line_text.strip():
                        # 如果不是第一行，添加换行符
                        if block_text:
                            block_text += "\n"
                        block_text += line_text.strip()
                    
                    # 更新整个块的边界框
                    if line_min_x0 != float('inf'):
                        min_x0 = min(min_x0, line_min_x0)
                        min_y0 = min(min_y0, line_min_y0)
                        max_x1 = max(max_x1, line_max_x1)
                        max_y1 = max(max_y1, line_max_y1)

                # 如果有文本内容，则创建一个box
                if block_text.strip():
                    # 计算平均字体大小用于分类
                    avg_size = 0
                    size_count = 0
                    for line in block["lines"]:
                        for span in line["spans"]:
                            if span["text"].strip():
                                avg_size += span["size"]
                                size_count += 1
                    if size_count > 0:
                        avg_size = round(avg_size / size_count, 1)

                    # 默认类别
                    category = "Text"
                    processed_text = block_text.strip()

                    # 根据字号推断类别和层级（这是为了适配你的Chunker逻辑）
                    if avg_size >= title_size:
                        category = "Title"
                    elif avg_size >= h1_size:
                        category = "Section-header"
                        # 你的Chunker逻辑依赖 '#' 来判断层级，这里我们模拟添加
                        processed_text = f"# {block_text.strip()}"
                    elif avg_size >= h2_size:
                        category = "Section-header"
                        processed_text = f"## {block_text.strip()}"

                    # 构造最终的边界框
                    if min_x0 != float('inf'):
                        final_bbox = [min_x0, min_y0, max_x1, max_y1]
                    else:
                        # fallback to first span's bbox if no valid bbox found
                        final_bbox = [0, 0, 0, 0]

                    # 模拟构造 Dots OCR 的 box 结构
                    box = {
                        "text": processed_text,
                        "category": category,
                        "bbox": final_bbox,
                        "page_no": page_num + 1
                        # 这里可以扩展 logic 识别表格或图片
                    }

                    page_data["full_layout_info"].append(box)

            json_doc.append(page_data)

        return json_doc


def scan_pdf_to_json(pdf_path: str, output_json_path: str):
    scanner = PdfToDotsFormat(pdf_path)
    data = scanner.parse()

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"扫描完成，JSON已保存至: {output_json_path}")


if __name__ == "__main__":
    scan_pdf_to_json("sample.pdf", "dots_ocr_result.json")
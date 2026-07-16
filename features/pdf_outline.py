# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import fitz
from PyPDF2 import PdfReader, PdfWriter
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QSpinBox, 
    QCheckBox, QPushButton, QFileDialog, QMessageBox, QComboBox, QSizePolicy
)


class OutlinePanel(QWidget):
    changed = Signal()
    detect_bookmark_signal = Signal()
    clear_bookmark_signal = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("操作模式："))
        self.output_mode = QComboBox()
        self.output_mode.addItems(["插入书签", "生成目录（基于已有书签）", "插入书签 + 生成目录"])
        self.output_mode.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        output_row.addWidget(self.output_mode)
        layout.addLayout(output_row)

        self.scope_widget = QWidget()
        scope_layout = QHBoxLayout(self.scope_widget)
        scope_layout.setContentsMargins(0, 0, 0, 0)
        scope_layout.addWidget(QLabel("编号范围："))
        self.number_scope = QComboBox()
        self.number_scope.addItems(["无编号", "仅一级标题", "多级标题"])
        self.number_scope.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        scope_layout.addWidget(self.number_scope)
        self.scope_widget.setVisible(False)
        layout.addWidget(self.scope_widget)

        self.style_widget = QWidget()
        self.style_widget.setVisible(False)
        style_layout = QHBoxLayout(self.style_widget)
        style_layout.setContentsMargins(0, 0, 0, 0)
        style_layout.addWidget(QLabel("编号样式："))
        self.number_style = QComboBox()
        self.number_style.addItems(["1 / 1.1 / 1.1.1", "一 / （一）/ 1.", "第一章 / 第一节 / 第一条"])
        self.number_style.setVisible(False)
        self.number_style.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        style_layout.addWidget(self.number_style)
        layout.addWidget(self.style_widget)

        def update_visibility():
            is_toc_mode = self.output_mode.currentIndex() != 0
            self.scope_widget.setVisible(is_toc_mode)
            if is_toc_mode:
                is_numbered = self.number_scope.currentIndex() != 0
                self.style_widget.setVisible(is_numbered)
                self.number_style.setVisible(is_numbered)
            else:
                self.style_widget.setVisible(False)
                self.number_style.setVisible(False)

        self.output_mode.currentIndexChanged.connect(update_visibility)
        self.number_scope.currentIndexChanged.connect(update_visibility)

        row = QHBoxLayout()
        row.setSpacing(8)

        left_widget = QWidget()
        left_layout = QHBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.addWidget(QLabel("页码偏移量："))
        self.offset_spin = QSpinBox()
        self.offset_spin.setRange(-99, 99)
        self.offset_spin.setValue(0)
        self.offset_spin.setFixedWidth(120)
        self.offset_spin.setToolTip("当正文从第 N 页开始时，填入 N-1")
        left_layout.addWidget(self.offset_spin)

        row.addWidget(left_widget)
        row.addStretch() 
        self.overwrite_check = QCheckBox("覆盖已有书签")
        self.overwrite_check.setChecked(True)
        row.addWidget(self.overwrite_check) 

        layout.addLayout(row)

        title_row = QHBoxLayout()
        lbl_bookmarks = QLabel("全局书签列表")
        lbl_bookmarks.setStyleSheet("font-weight: 600; margin-top: 4px;")
        title_row.addWidget(lbl_bookmarks)
        title_row.addStretch()
        self.btn_import = QPushButton("从文本文件导入")
        self.btn_import.setStyleSheet("font-size: 11px; padding: 4px 12px; min-height: 24px;")
        self.btn_import.clicked.connect(self.import_from_file)
        title_row.addWidget(self.btn_import)
        layout.addLayout(title_row)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText(
            "用 Tab 或空格分隔（层级 标题 页码）\n\n"
            "示例：\n\n"
            "1   第一章   1\n"
            "2   1.1节    3\n"
            "3   1.1.1节  5\n\n"
        )
        self.text_edit.setFixedHeight(140)
        layout.addWidget(self.text_edit)

        btn_row = QHBoxLayout()
        self.btn_detect = QPushButton("检测页码与书签")
        self.btn_detect.clicked.connect(self.detect_bookmark_signal.emit)
        btn_row.addWidget(self.btn_detect, 1)

        self.btn_clear = QPushButton("清除书签")
        self.btn_clear.setStyleSheet("background-color: #f44336; color: white;")
        self.btn_clear.clicked.connect(self.clear_bookmark_signal.emit)
        btn_row.addWidget(self.btn_clear, 1)

        layout.addLayout(btn_row)
        layout.addStretch()

        self.text_edit.textChanged.connect(self.changed)
        self.offset_spin.valueChanged.connect(self.changed)
        self.overwrite_check.stateChanged.connect(self.changed)
        self.output_mode.currentIndexChanged.connect(self.changed)
        self.number_scope.currentIndexChanged.connect(self.changed)
        self.number_style.currentIndexChanged.connect(self.changed)

        update_visibility()

    def import_from_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择书签数据文件", "", "文本文件 (*.txt);;CSV文件 (*.csv);;所有文件 (*.*)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_edit.setPlainText(content)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"读取文件失败：{e}")


def build_panel() -> QWidget:
    return OutlinePanel()


def collect_settings(panel: OutlinePanel) -> dict:
    return {
        "text": panel.text_edit.toPlainText(),
        "offset": panel.offset_spin.value(),
        "overwrite": panel.overwrite_check.isChecked(),
        "output_mode": panel.output_mode.currentIndex(),
        "number_scope": panel.number_scope.currentIndex(),
        "number_style": panel.number_style.currentIndex(),
    }


def prepare_preview(items, settings):
    offset = settings.get("offset", 0)
    output_mode = settings.get("output_mode", 0)
    scope_idx = settings.get("number_scope", 0)
    style_idx = settings.get("number_style", 0)

    scope_names = ["无编号", "仅一级", "多级"]
    style_names = ["1/1.1/1.1.1", "一/（一）/1.", "第一章/第一节/第一条"]
    mode_names = ["插入书签", "生成目录（基于已有书签）", "插入书签 + 生成目录"]

    if scope_idx == 0:
        number_text = "无编号"
    else:
        number_text = f"{scope_names[scope_idx]} / {style_names[scope_idx]}"

    global_text = settings.get("text", "").strip()

    for it in items:
        custom_text = getattr(it, "custom_outlines", "")
        text_to_use = custom_text if custom_text.strip() else global_text

        count = 0
        if text_to_use:
            for line in text_to_use.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    count += 1

        it.preview_extra = {"A": f"书签: {count} 条，偏移: {offset}，模式: {mode_names[output_mode]}，编号: {number_text}"}


def parse_outlines(text: str, offset: int = 0) -> list:
    outlines = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if '\t' in line:
            parts = line.split('\t')
        else:
            parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        try:
            level = int(parts[0].strip())
            title = parts[1].strip()
            page = int(parts[2].strip()) + offset - 1
            if page < 0:
                page = 0
            outlines.append((level, title, page))
        except ValueError:
            continue
    return outlines


def extract_outlines_from_pdf(pdf_path: str, offset: int = 0) -> list:
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    doc.close()
    outlines = []
    for level, title, page in toc:
        page_num = page - 1 + offset
        if page_num < 0:
            page_num = 0
        outlines.append((level, title, page_num))
    return outlines


def number_to_chinese(num):
    chinese_nums = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    if num <= 10:
        return chinese_nums[num]
    elif num < 20:
        return "十" + (chinese_nums[num - 10] if num - 10 > 0 else "")
    elif num < 100:
        return chinese_nums[num // 10] + "十" + (chinese_nums[num % 10] if num % 10 > 0 else "")
    return str(num)


def get_number_string(level, counters, scope_idx, style_idx):
    if scope_idx == 0:
        return ""

    if scope_idx == 1:
        if level != 1:
            return ""
        num = counters[0]
        if style_idx == 0:
            return f"{num}."
        elif style_idx == 1:
            return number_to_chinese(num) + "、"
        else:
            if num == 1:
                return "第一章"
            elif num == 2:
                return "第二章"
            elif num == 3:
                return "第三章"
            elif num == 4:
                return "第四章"
            elif num == 5:
                return "第五章"
            elif num == 6:
                return "第六章"
            elif num == 7:
                return "第七章"
            elif num == 8:
                return "第八章"
            elif num == 9:
                return "第九章"
            else:
                return f"第{number_to_chinese(num)}章"

    if scope_idx == 2:
        if style_idx == 0:
            if level == 1:
                return f"{counters[0]}."
            elif level == 2:
                return f"{counters[0]}.{counters[1]}."
            else:
                return f"{counters[0]}.{counters[1]}.{counters[2]}."
        elif style_idx == 1:
            if level == 1:
                return number_to_chinese(counters[0]) + "、"
            elif level == 2:
                return "（" + number_to_chinese(counters[1]) + "）"
            else:
                return f"{counters[2]}."
        else:
            if level == 1:
                num = counters[0]
                if num == 1:
                    return "第一章"
                elif num == 2:
                    return "第二章"
                elif num == 3:
                    return "第三章"
                elif num == 4:
                    return "第四章"
                elif num == 5:
                    return "第五章"
                elif num == 6:
                    return "第六章"
                elif num == 7:
                    return "第七章"
                elif num == 8:
                    return "第八章"
                elif num == 9:
                    return "第九章"
                else:
                    return f"第{number_to_chinese(num)}章"
            elif level == 2:
                num = counters[1]
                if num == 1:
                    return "第一节"
                elif num == 2:
                    return "第二节"
                elif num == 3:
                    return "第三节"
                elif num == 4:
                    return "第四节"
                elif num == 5:
                    return "第五节"
                elif num == 6:
                    return "第六节"
                elif num == 7:
                    return "第七节"
                elif num == 8:
                    return "第八节"
                elif num == 9:
                    return "第九节"
                else:
                    return f"第{number_to_chinese(num)}节"
            else:
                num = counters[2]
                if num == 1:
                    return "第一条"
                elif num == 2:
                    return "第二条"
                elif num == 3:
                    return "第三条"
                elif num == 4:
                    return "第四条"
                elif num == 5:
                    return "第五条"
                elif num == 6:
                    return "第六条"
                elif num == 7:
                    return "第七条"
                elif num == 8:
                    return "第八条"
                elif num == 9:
                    return "第九条"
                else:
                    return f"第{number_to_chinese(num)}条"

    return ""


def generate_toc_pdf(outlines, output_path, scope_idx=0, style_idx=0):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    try:
        pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
        font_name = 'SimHei'
    except:
        font_name = 'Helvetica'

    c = canvas.Canvas(output_path, pagesize=A4)
    w, h = A4

    c.setFont(font_name, 22)
    c.drawCentredString(w/2, h - 3*cm, "目 录")

    c.setFont(font_name, 14)
    y = h - 5*cm
    left_margin = 3*cm
    right_margin = 3*cm
    max_width = w - left_margin - right_margin

    counters = [0, 0, 0]

    for level, title, page in outlines:
        if level == 1:
            counters[0] += 1
            counters[1] = 0
            counters[2] = 0
        elif level == 2:
            counters[1] += 1
            counters[2] = 0
        elif level == 3:
            counters[2] += 1

        if y < 2*cm:
            c.showPage()
            y = h - 2*cm
            c.setFont(font_name, 14)

        indent = (level - 1) * 1.2 * cm
        x = left_margin + indent

        number_str = get_number_string(level, counters, scope_idx, style_idx)

        if number_str:
            if style_idx == 0:
                display_title = number_str + " " + title
            elif style_idx == 1:
                display_title = number_str + " " + title
            else:
                display_title = number_str + " " + title
        else:
            display_title = title

        title_width = c.stringWidth(display_title, font_name, 14)
        page_str = str(page + 1)
        page_width = c.stringWidth(page_str, font_name, 14)
        dot_width = max_width - indent - title_width - page_width

        c.drawString(x, y, display_title)

        if dot_width > 10:
            c.setDash(1, 2)
            c.setStrokeColorRGB(0.5, 0.5, 0.5)
            c.line(x + title_width + 2, y + 4, w - right_margin - page_width - 2, y + 4)
            c.setDash()
            c.setStrokeColorRGB(0, 0, 0)

        c.drawRightString(w - right_margin, y, page_str)

        y -= 1*cm

    c.save()


def insert_toc_to_pdf(original_pdf, toc_pdf, output_pdf):
    doc_toc = fitz.open(toc_pdf)
    doc_orig = fitz.open(original_pdf)
    
    toc = doc_orig.get_toc()
    toc_pages = doc_toc.page_count
    
    doc_toc.insert_pdf(doc_orig)
    
    if toc:
        adjusted_toc = []
        for level, title, page in toc:
            adjusted_toc.append((level, title, page + toc_pages))
        doc_toc.set_toc(adjusted_toc)
    
    doc_toc.save(output_pdf)
    doc_toc.close()
    doc_orig.close()


def run_task(file_item, settings: dict):
    src = file_item.input_path
    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)

    base_name = os.path.splitext(file_item.output_name)[0] if file_item.output_name else os.path.splitext(os.path.basename(src))[0]
    out_name = base_name + ".pdf"
    out_path = os.path.join(out_dir, out_name)
    file_item.output_name = out_name

    offset = settings.get("offset", 0)
    output_mode = settings.get("output_mode", 0)
    scope_idx = settings.get("number_scope", 0)
    style_idx = settings.get("number_style", 0)

    if output_mode == 0:
        text = getattr(file_item, "custom_outlines", "") if getattr(file_item, "custom_outlines", "") else settings.get("text", "").strip()
        if not text:
            raise ValueError("书签列表为空")
        outlines = parse_outlines(text, offset)
        reader = PdfReader(src)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        parent_stack = {}
        for level, title, page_num in outlines:
            if page_num < 0:
                page_num = 0
            if page_num >= len(reader.pages):
                page_num = len(reader.pages) - 1
            parent = None
            if level > 1:
                parent = parent_stack.get(level - 1)
            bookmark = writer.add_outline_item(title, page_num, parent=parent)
            parent_stack[level] = bookmark
        with open(out_path, 'wb') as f:
            writer.write(f)

    elif output_mode == 1:
        outlines = extract_outlines_from_pdf(src, offset)
        if not outlines:
            raise ValueError("PDF 中未找到任何书签")
        toc_path = os.path.join(out_dir, "_temp_toc.pdf")
        generate_toc_pdf(outlines, toc_path, scope_idx, style_idx)
        insert_toc_to_pdf(src, toc_path, out_path)
        if os.path.exists(toc_path):
            os.remove(toc_path)

    elif output_mode == 2:
        text = getattr(file_item, "custom_outlines", "") if getattr(file_item, "custom_outlines", "") else settings.get("text", "").strip()
        if not text:
            raise ValueError("书签列表为空")

        outlines_raw = parse_outlines(text, 0)

        offset = settings.get("offset", 0)
        outlines_display = []
        outlines_bookmark = []

        for level, title, page_0based in outlines_raw:
            page_1based = page_0based + 1
            expected_page_1based = page_1based + offset

            outlines_display.append((level, title, expected_page_1based - 1))
            outlines_bookmark.append((level, title, page_0based))

        toc_path = os.path.join(out_dir, "_temp_toc.pdf")
        generate_toc_pdf(outlines_display, toc_path, scope_idx, style_idx)

        reader = PdfReader(src)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        parent_stack = {}
        for level, title, page_0based in outlines_bookmark:
            bookmark_page = page_0based
            if bookmark_page < 0:
                bookmark_page = 0
            if bookmark_page >= len(reader.pages):
                bookmark_page = len(reader.pages) - 1
            parent = None
            if level > 1:
                parent = parent_stack.get(level - 1)
            bookmark = writer.add_outline_item(title, bookmark_page, parent=parent)
            parent_stack[level] = bookmark

        temp_with_bookmark = os.path.join(out_dir, "_temp_with_bookmark.pdf")
        with open(temp_with_bookmark, 'wb') as f:
            writer.write(f)

        insert_toc_to_pdf(temp_with_bookmark, toc_path, out_path)

        if os.path.exists(toc_path):
            os.remove(toc_path)
        if os.path.exists(temp_with_bookmark):
            os.remove(temp_with_bookmark)

    file_item.status = "完成"
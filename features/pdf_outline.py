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
        """初始化设置面板"""
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        row_mode = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["插入书签", "生成目录（基于已有书签）", "插入书签 + 生成目录"])
        self.mode_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_mode.addWidget(QLabel("操作模式:"))
        row_mode.addWidget(self.mode_combo, 1)
        layout.addLayout(row_mode)

        self.scope_widget = QWidget()
        row_scope = QHBoxLayout(self.scope_widget)
        row_scope.setContentsMargins(0, 0, 0, 0)        
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["无编号", "仅一级标题", "多级标题"])
        self.scope_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_scope.addWidget(QLabel("编号范围:"))
        row_scope.addWidget(self.scope_combo, 1)  
        layout.addWidget(self.scope_widget)

        self.number_widget = QWidget()
        row_number = QHBoxLayout(self.number_widget)
        row_number.setContentsMargins(0, 0, 0, 0)
        self.number_combo = QComboBox()
        self.number_combo.addItems(["1 / 1.1 / 1.1.1", "一 / （一）/ 1.", "第一章 / 第一节 / 第一条"])
        self.number_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_number.addWidget(QLabel("编号样式:"))
        row_number.addWidget(self.number_combo, 1)
        layout.addWidget(self.number_widget)

        row_offset = QHBoxLayout()
        self.offset_spin = QSpinBox()
        self.offset_spin.setRange(-99, 99)
        self.offset_spin.setValue(0)
        self.offset_spin.setToolTip("当正文从第 N 页开始时，填入 N-1")
        self.offset_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.overwrite_check = QCheckBox("覆盖已有书签")
        self.overwrite_check.setChecked(True)        
        self.overwrite_check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row_offset.addWidget(QLabel("页码偏移量:"))
        row_offset.addWidget(self.offset_spin, 1)
        row_offset.addWidget(self.overwrite_check)
        layout.addLayout(row_offset)

        row_bookmark = QHBoxLayout()
        bookmark_label = QLabel("全局书签列表")
        bookmark_label.setStyleSheet("font-weight: 600; margin-top: 4px; margin-left: -3px")
        bookmark_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.import_btn = QPushButton("从文本文件导入")
        self.import_btn.setStyleSheet("font-size: 11px; padding: 4px 12px; min-height: 24px;")
        self.import_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row_bookmark.addWidget(bookmark_label)
        row_bookmark.addStretch()
        row_bookmark.addWidget(self.import_btn)
        layout.addLayout(row_bookmark)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText(
            "用 Tab 或空格分隔（层级 标题 页码）\n\n"
            "示例：\n"
            "1   第一章   1\n"
            "2   1.1节    3\n"
            "3   1.1.1节  5\n\n"
        )
        self.text_edit.setFixedHeight(130)
        self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.text_edit, 1)

        row_btn = QHBoxLayout()
        self.detect_btn = QPushButton("检测页码与书签")
        self.detect_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.clear_btn = QPushButton("清除书签")
        self.clear_btn.setStyleSheet("background-color: #f44336; color: white;")
        self.clear_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_btn.addWidget(self.detect_btn, 1)
        row_btn.addWidget(self.clear_btn, 1)
        layout.addLayout(row_btn)

        layout.addStretch()

        self.mode_combo.currentIndexChanged.connect(self._update_visibility)
        self.mode_combo.currentIndexChanged.connect(self.changed)
        self.scope_combo.currentIndexChanged.connect(self._update_visibility)
        self.scope_combo.currentIndexChanged.connect(self.changed)
        self.number_combo.currentIndexChanged.connect(self.changed)
        self.text_edit.textChanged.connect(self.changed)
        self.offset_spin.valueChanged.connect(self.changed)
        self.overwrite_check.stateChanged.connect(self.changed)
        self.import_btn.clicked.connect(self.import_from_file)
        self.detect_btn.clicked.connect(self.detect_bookmark_signal.emit)
        self.clear_btn.clicked.connect(self.clear_bookmark_signal.emit)

        self._update_visibility()
        
    def _update_visibility(self):
        """操作模式切换"""
        is_toc_mode = self.mode_combo.currentIndex() != 0
        self.scope_widget.setVisible(is_toc_mode)
        if is_toc_mode:
            is_numbered = self.scope_combo.currentIndex() != 0
            self.number_widget.setVisible(is_numbered)
            self.number_combo.setVisible(is_numbered)
        else:
            self.number_widget.setVisible(False)
            self.number_combo.setVisible(False)

    def import_from_file(self):
        """从文本文件导入书签数据"""
        path, _ = QFileDialog.getOpenFileName(self, "选择书签数据文件", "", "文本文件 (*.txt);;CSV文件 (*.csv);;所有文件 (*.*)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_edit.setPlainText(content)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"读取文件失败：{e}")


def build_panel() -> QWidget:
    """构建面板实例"""
    return OutlinePanel()


def collect_settings(panel: OutlinePanel) -> dict:
    """收集面板设置"""
    return {
        "text": panel.text_edit.toPlainText(),
        "offset": panel.offset_spin.value(),
        "overwrite": panel.overwrite_check.isChecked(),
        "mode": panel.mode_combo.currentIndex(),
        "scope": panel.scope_combo.currentIndex(),
        "number": panel.number_combo.currentIndex(),
    }


def prepare_preview(items, settings):
    """生成预览信息"""
    offset = settings.get("offset", 0)
    mode = settings.get("mode", 0)
    scope_idx = settings.get("scope", 0)
    style_idx = settings.get("number", 0)
    mode_names = ["插入书签", "生成目录（基于已有书签）", "插入书签 + 生成目录"]
    scope_names = ["无编号", "仅一级", "多级"]
    style_names = ["1/1.1/1.1.1", "一/（一）/1.", "第一章/第一节/第一条"]
    number_text = "无编号" if scope_idx == 0 else f"{scope_names[scope_idx]} / {style_names[style_idx]}"
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
        it.preview_extra = {
            "A": f"书签：{count}条，偏移{offset}，模式{mode_names[mode]}，编号{number_text}"
        }


def parse_outlines(text: str, offset: int = 0) -> list:
    """解析用户输入的书签文本"""
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
    """从 PDF 中提取现有书签"""
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
    """将数字转换为中文数字"""
    chinese_nums = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    if num <= 10:
        return chinese_nums[num]
    elif num < 20:
        return "十" + (chinese_nums[num - 10] if num - 10 > 0 else "")
    elif num < 100:
        return chinese_nums[num // 10] + "十" + (chinese_nums[num % 10] if num % 10 > 0 else "")
    return str(num)


def get_number_string(level, counters, scope_idx, style_idx):
    """根据编号范围、样式和计数器生成编号字符串"""
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
    """生成目录 PDF"""
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
    """将目录 PDF 插入到原 PDF 前面，并调整书签页码偏移"""
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
    """执行单个 PDF 书签操作"""
    src = file_item.input_path
    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, file_item.output_name)
    offset = settings.get("offset", 0)
    mode = settings.get("mode", 0)
    scope_idx = settings.get("scope", 0)
    style_idx = settings.get("number", 0)
    if mode == 0:
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
    elif mode == 1:
        outlines = extract_outlines_from_pdf(src, offset)
        if not outlines:
            raise ValueError("PDF 中未找到任何书签")
        toc_path = os.path.join(out_dir, "_temp_toc.pdf")
        generate_toc_pdf(outlines, toc_path, scope_idx, style_idx)
        insert_toc_to_pdf(src, toc_path, out_path)
        if os.path.exists(toc_path):
            os.remove(toc_path)
    elif mode == 2:
        text = getattr(file_item, "custom_outlines", "") if getattr(file_item, "custom_outlines", "") else settings.get("text", "").strip()
        if not text:
            raise ValueError("书签列表为空")
        outlines_raw = parse_outlines(text, 0)
        offset = settings.get("offset", 0)
        outlines_display = []
        for level, title, page_0based in outlines_raw:
            page_1based = page_0based + 1
            expected_page_1based = page_1based + offset
            outlines_display.append((level, title, expected_page_1based - 1))
        toc_path = os.path.join(out_dir, "_temp_toc.pdf")
        generate_toc_pdf(outlines_display, toc_path, scope_idx, style_idx)
        doc = fitz.open(src)
        toc = []
        for level, title, page_0based in outlines_raw:
            page_num = page_0based
            if page_num < 0:
                page_num = 0
            if page_num >= len(doc):
                page_num = len(doc) - 1
            toc.append([level, title, page_num + 1])
        doc.set_toc(toc)
        temp_with_bookmark = os.path.join(out_dir, "_temp_with_bookmark.pdf")
        doc.save(temp_with_bookmark)
        doc.close()
        insert_toc_to_pdf(temp_with_bookmark, toc_path, out_path)
        if os.path.exists(toc_path):
            os.remove(toc_path)
        if os.path.exists(temp_with_bookmark):
            os.remove(temp_with_bookmark)
    file_item.status = "完成"
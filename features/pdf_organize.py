# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
from PyPDF2 import PdfReader, PdfWriter
from PySide6.QtCore import Signal
from PySide6.QtGui import QIntValidator, QAction, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit,
    QSpinBox, QPushButton, QFileDialog, QCheckBox, QSizePolicy
)
from core.utils import parse_page_range, resource_path, sanitize_base_name


class OrganizePanel(QWidget):
    changed = Signal()
    detect_page_signal = Signal()

    def __init__(self):
        """初始化设置面板"""
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        self.action_combo = QComboBox()
        self.action_combo.addItems(["提取页面", "插入页面", "替换页面", "拆分页面", "重排页面", "删除页面"])
        self.action_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.insert_check = QCheckBox("按序插入")
        self.insert_check.setChecked(False)
        self.insert_check.setToolTip("将源文件的第N页插入到列表中第N个文件的指定位置")
        self.insert_check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.delete_check = QCheckBox("提取后删除页面")
        self.delete_check.setChecked(False)
        self.delete_check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        row_param1 = QHBoxLayout()
        row_param1.addWidget(QLabel("操作模式:"))
        row_param1.addWidget(self.action_combo, 1)
        row_param1.addWidget(self.insert_check)
        row_param1.addWidget(self.delete_check)
        layout.addLayout(row_param1)

        self.extract_widget = QWidget()
        self.extract_range_edit = QLineEdit()
        self.extract_range_edit.setPlaceholderText("1-3,5,8-10（留空=全部）")
        self.extract_range_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        row_extract = QHBoxLayout()
        row_extract.addWidget(QLabel("页面范围:"))
        row_extract.addWidget(self.extract_range_edit, 1)
        extract_layout = QVBoxLayout(self.extract_widget)
        extract_layout.setContentsMargins(0, 0, 0, 0)
        extract_layout.addLayout(row_extract)
        layout.addWidget(self.extract_widget)

        self.insert_widget = QWidget()
        self.insert_file_edit = QLineEdit()
        self.insert_file_edit.setPlaceholderText("点击右侧图标选择PDF文件")
        self.insert_file_edit.setReadOnly(True)
        self.insert_file_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        insert_file_action = QAction(self)
        insert_file_action.setIcon(QIcon(resource_path("assets/folder.png")))
        insert_file_action.setToolTip("选择要插入的PDF文件")
        insert_file_action.triggered.connect(self._select_insert_file)
        self.insert_file_edit.addAction(insert_file_action, QLineEdit.TrailingPosition)
        self.insert_position_combo = QComboBox()
        self.insert_position_combo.addItems(["自定义", "最后一页"])
        self.insert_position_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.insert_page_edit = QLineEdit()
        self.insert_page_edit.setPlaceholderText("1")
        self.insert_page_edit.setValidator(QIntValidator(1, 99999))
        self.insert_page_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.insert_dir_combo = QComboBox()
        self.insert_dir_combo.addItems(["之前", "之后"])
        self.insert_dir_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.insert_position_widget = QWidget()

        row_insert1 = QHBoxLayout()
        row_insert1.addWidget(QLabel("插入文件:"))
        row_insert1.addWidget(self.insert_file_edit, 1)
        row_insert2 = QHBoxLayout()
        row_insert2.addWidget(QLabel("插入位置:"))
        row_insert2.addWidget(self.insert_position_combo)
        row_insert2.addWidget(self.insert_position_widget)
        row_insert2.addWidget(self.insert_dir_combo)
        insert_page_layout = QHBoxLayout(self.insert_position_widget)
        insert_page_layout.setContentsMargins(0, 0, 0, 0)
        insert_page_layout.addWidget(QLabel("第"))
        insert_page_layout.addWidget(self.insert_page_edit)
        insert_page_layout.addWidget(QLabel("页"))         
        insert_layout = QVBoxLayout(self.insert_widget)
        insert_layout.setContentsMargins(0, 0, 0, 0)
        insert_layout.addLayout(row_insert1)
        insert_layout.addLayout(row_insert2)
        layout.addWidget(self.insert_widget)

        self.replace_widget = QWidget()
        self.replace_range_edit = QLineEdit()
        self.replace_range_edit.setPlaceholderText("1-3,5,8-10")
        self.replace_range_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.replace_file_edit = QLineEdit()
        self.replace_file_edit.setPlaceholderText("点击右侧图标选择PDF文件")
        self.replace_file_edit.setReadOnly(True)
        self.replace_file_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        replace_file_action = QAction(self)
        replace_file_action.setIcon(QIcon(resource_path("assets/folder.png")))
        replace_file_action.setToolTip("选择来源PDF文件")
        replace_file_action.triggered.connect(self._select_replace_file)
        self.replace_file_edit.addAction(replace_file_action, QLineEdit.TrailingPosition)
        self.replace_source_edit = QLineEdit()
        self.replace_source_edit.setPlaceholderText("1-3,5（留空=全部）")
        self.replace_source_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        row_replace1 = QHBoxLayout()
        row_replace1.addWidget(QLabel("替换页面:"))
        row_replace1.addWidget(self.replace_range_edit, 1)
        row_replace2 = QHBoxLayout()
        row_replace2.addWidget(QLabel("替换文件:"))
        row_replace2.addWidget(self.replace_file_edit, 1)
        row_replace3 = QHBoxLayout()
        row_replace3.addWidget(QLabel("使用页面:"))
        row_replace3.addWidget(self.replace_source_edit, 1)
        replace_layout = QVBoxLayout(self.replace_widget)
        replace_layout.setContentsMargins(0, 0, 0, 0)    
        replace_layout.addLayout(row_replace1)
        replace_layout.addLayout(row_replace2)
        replace_layout.addLayout(row_replace3)
        layout.addWidget(self.replace_widget)

        self.split_widget = QWidget()
        self.split_combo = QComboBox()
        self.split_combo.addItems(["按固定页数", "按指定页面范围"])
        self.split_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.split_count_widget = QWidget()
        self.split_count_spin = QSpinBox()
        self.split_count_spin.setRange(1, 9999)
        self.split_count_spin.setValue(5)
        self.split_count_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)      
        self.split_range_widget = QWidget()
        self.split_range_edit = QLineEdit()
        self.split_range_edit.setPlaceholderText("1-3,4-6,7-9")
        self.split_range_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)       

        row_split = QHBoxLayout()
        row_split.addWidget(QLabel("拆分方式:"))
        row_split.addWidget(self.split_combo, 1)
        split_count_layout = QHBoxLayout(self.split_count_widget)
        split_count_layout.setContentsMargins(0, 0, 0, 0)
        split_count_layout.addWidget(QLabel("每份页数:"))
        split_count_layout.addWidget(self.split_count_spin, 1)       
        split_range_layout = QHBoxLayout(self.split_range_widget)
        split_range_layout.setContentsMargins(0, 0, 0, 0)
        split_range_layout.addWidget(QLabel("页面范围:"))
        split_range_layout.addWidget(self.split_range_edit, 1)         
        split_layout = QVBoxLayout(self.split_widget)
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.addLayout(row_split)
        split_layout.addWidget(self.split_count_widget)        
        split_layout.addWidget(self.split_range_widget)
        layout.addWidget(self.split_widget)

        self.reorder_widget = QWidget()
        self.reorder_range_edit = QLineEdit()
        self.reorder_range_edit.setPlaceholderText("3-5")
        self.reorder_range_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.reorder_position_combo = QComboBox()
        self.reorder_position_combo.addItems(["自定义", "最后一页"])
        self.reorder_position_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.reorder_page_edit = QLineEdit()
        self.reorder_page_edit.setPlaceholderText("1")
        self.reorder_page_edit.setValidator(QIntValidator(1, 99999))
        self.reorder_page_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.reorder_dir_combo = QComboBox()
        self.reorder_dir_combo.addItems(["之前", "之后"])
        self.reorder_dir_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.reorder_position_widget = QWidget()    
            
        row_reorder1 = QHBoxLayout()
        row_reorder1.addWidget(QLabel("页面范围:"))
        row_reorder1.addWidget(self.reorder_range_edit, 1)        
        row_reorder2 = QHBoxLayout()
        row_reorder2.addWidget(QLabel("插入位置:"))
        row_reorder2.addWidget(self.reorder_position_combo)
        row_reorder2.addWidget(self.reorder_position_widget)
        row_reorder2.addWidget(self.reorder_dir_combo)          
        reorder_page_layout = QHBoxLayout(self.reorder_position_widget)
        reorder_page_layout.setContentsMargins(0, 0, 0, 0)
        reorder_page_layout.addWidget(QLabel("第"))
        reorder_page_layout.addWidget(self.reorder_page_edit)
        reorder_page_layout.addWidget(QLabel("页"))            
        reorder_layout = QVBoxLayout(self.reorder_widget)
        reorder_layout.setContentsMargins(0, 0, 0, 0)    
        reorder_layout.addLayout(row_reorder1)
        reorder_layout.addLayout(row_reorder2)
        layout.addWidget(self.reorder_widget)

        self.delete_widget = QWidget()
        self.delete_range_edit = QLineEdit()
        self.delete_range_edit.setPlaceholderText("1-3,5,8-10")
        self.delete_range_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        row_delete = QHBoxLayout()
        row_delete.addWidget(QLabel("页面范围:"))
        row_delete.addWidget(self.delete_range_edit, 1)
        delete_layout = QVBoxLayout(self.delete_widget)
        delete_layout.setContentsMargins(0, 0, 0, 0)  
        delete_layout.addLayout(row_delete)            
        layout.addWidget(self.delete_widget)

        self.detect_btn = QPushButton("检测页码")
        self.detect_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        layout.addWidget(self.detect_btn, 1)

        layout.addStretch()

        self.action_combo.currentIndexChanged.connect(self._on_mode_changed)
        self.action_combo.currentIndexChanged.connect(self.changed)
        self.extract_range_edit.textChanged.connect(self.changed)
        self.delete_check.stateChanged.connect(self.changed)
        self.insert_file_edit.textChanged.connect(self.changed)
        self.insert_position_combo.currentIndexChanged.connect(self._on_insert_position_mode_changed)
        self.insert_position_combo.currentIndexChanged.connect(self.changed)
        self.insert_page_edit.textChanged.connect(self.changed)
        self.insert_dir_combo.currentIndexChanged.connect(self.changed)
        self.replace_range_edit.textChanged.connect(self.changed)
        self.replace_file_edit.textChanged.connect(self.changed)
        self.replace_source_edit.textChanged.connect(self.changed)
        self.split_combo.currentIndexChanged.connect(self._on_split_mode_changed)
        self.split_combo.currentIndexChanged.connect(self.changed)
        self.split_count_spin.valueChanged.connect(self.changed)
        self.split_range_edit.textChanged.connect(self.changed)
        self.reorder_range_edit.textChanged.connect(self.changed)
        self.reorder_position_combo.currentIndexChanged.connect(self._on_reorder_position_mode_changed)
        self.reorder_position_combo.currentIndexChanged.connect(self.changed)
        self.reorder_page_edit.textChanged.connect(self.changed)
        self.reorder_dir_combo.currentIndexChanged.connect(self.changed)
        self.delete_range_edit.textChanged.connect(self.changed)
        self.insert_check.stateChanged.connect(self.changed)
        self.detect_btn.clicked.connect(self.detect_page_signal.emit)

        self._on_mode_changed()
        self._on_split_mode_changed()
        self._on_insert_position_mode_changed()
        self._on_reorder_position_mode_changed()

    def _on_mode_changed(self):
        """操作模式切换时显示对应的设置控件"""
        idx = self.action_combo.currentIndex()
        self._show_only_widget(idx)
        self.insert_check.setVisible(idx == 1)
        self.delete_check.setVisible(idx == 0)
        self.changed.emit()

    def _show_only_widget(self, index):
        """只显示指定索引对应的设置控件，隐藏其他"""
        widgets = [
            self.extract_widget,
            self.insert_widget,
            self.replace_widget,
            self.split_widget,
            self.reorder_widget,
            self.delete_widget
        ]
        for i, w in enumerate(widgets):
            w.setVisible(i == index)

    def _on_split_mode_changed(self):
        """拆分方式切换时显示/隐藏固定页数或页码范围控件"""
        is_fixed = self.split_combo.currentIndex() == 0
        self.split_count_widget.setVisible(is_fixed)
        self.split_range_widget.setVisible(not is_fixed)
        self.changed.emit()

    def _on_insert_position_mode_changed(self):
        """插入位置模式切换时显示/隐藏自定义页码控件"""
        is_custom = self.insert_position_combo.currentIndex() == 0
        self.insert_position_widget.setVisible(is_custom)
        self.changed.emit()

    def _on_reorder_position_mode_changed(self):
        """重排位置模式切换时显示/隐藏自定义页码控件"""
        is_custom = self.reorder_position_combo.currentIndex() == 0
        self.reorder_position_widget.setVisible(is_custom)
        self.changed.emit()

    def _select_insert_file(self):
        """选择要插入的 PDF 文件"""
        path, _ = QFileDialog.getOpenFileName(self, "选择要插入的PDF文件", "", "PDF文件 (*.pdf)")
        if path:
            self.insert_file_edit.setText(path)
            self.changed.emit()

    def _select_replace_file(self):
        """选择替换来源 PDF 文件"""
        path, _ = QFileDialog.getOpenFileName(self, "选择来源PDF文件", "", "PDF文件 (*.pdf)")
        if path:
            self.replace_file_edit.setText(path)
            self.changed.emit()


def build_panel() -> QWidget:
    """构建面板实例"""
    return OrganizePanel()


def collect_settings(panel: OrganizePanel) -> dict:
    """收集面板设置"""
    return {
        "mode": panel.action_combo.currentIndex(),
        "range_edit": panel.extract_range_edit.text().strip(),
        "delete_check": panel.delete_check.isChecked(),
        "insert_file": panel.insert_file_edit.text().strip(),
        "insert_position_mode": panel.insert_position_combo.currentIndex(),
        "insert_position_page": int(panel.insert_page_edit.text() or 1),
        "insert_position_dir": panel.insert_dir_combo.currentIndex(),
        "replace_target": panel.replace_range_edit.text().strip(),
        "replace_file": panel.replace_file_edit.text().strip(),
        "replace_source": panel.replace_source_edit.text().strip(),
        "split_mode": panel.split_combo.currentIndex(),
        "split_page_count": panel.split_count_spin.value(),
        "split_range_list": panel.split_range_edit.text().strip(),
        "reorder_range": panel.reorder_range_edit.text().strip(),
        "reorder_position_mode": panel.reorder_position_combo.currentIndex(),
        "reorder_target_page": int(panel.reorder_page_edit.text() or 1),
        "reorder_dir": panel.reorder_dir_combo.currentIndex(),
        "delete_range": panel.delete_range_edit.text().strip(),
        "sequential_insert": panel.insert_check.isChecked(),
    }


def prepare_preview(items, settings):
    """生成预览信息"""
    mode_idx = settings.get("mode", 0)
    mode_names = ["提取页面", "插入页面", "替换页面", "拆分页面", "重排页面", "删除页面"]
    mode_name = mode_names[mode_idx] if mode_idx < len(mode_names) else "未知"

    extra = []
    if mode_idx == 0: 
        range_text = settings.get("range_edit", "")
        extra.append(f"范围：{range_text if range_text else '全部'}")
        if settings.get("delete_check", False):
            extra.append("提取后删除")
    elif mode_idx == 1:  
        insert_file = os.path.basename(settings.get("insert_file", ""))
        extra.append(f"插入文件：{insert_file if insert_file else '未选择'}")
        pos_mode = settings.get("insert_position_mode", 0)
        pos_page = settings.get("insert_position_page", 1)
        pos_dir = settings.get("insert_position_dir", 0)
        pos_text = "自定义" if pos_mode == 0 else "最后一页"
        dir_text = "之后" if pos_dir == 1 else "之前"
        extra.append(f"位置：{pos_text}第{pos_page}页{dir_text}")
        if settings.get("sequential_insert", False):
            extra.append("按序插入")
    elif mode_idx == 2:  
        target = settings.get("replace_target", "")
        src_file = os.path.basename(settings.get("replace_file", ""))
        source = settings.get("replace_source", "")
        extra.append(f"替换页：{target}，来源：{src_file}，使用页：{source if source else '全部'}")
    elif mode_idx == 3: 
        split_mode = settings.get("split_mode", 0)
        if split_mode == 0:
            count = settings.get("split_page_count", 5)
            extra.append(f"固定页数：{count}")
        else:
            ranges = settings.get("split_range_list", "")
            extra.append(f"范围：{ranges}")
    elif mode_idx == 4:  
        range_text = settings.get("reorder_range", "")
        pos_mode = settings.get("reorder_position_mode", 0)
        target_page = settings.get("reorder_target_page", 1)
        pos_dir = settings.get("reorder_dir", 0)
        pos_text = "自定义" if pos_mode == 0 else "最后一页"
        dir_text = "之后" if pos_dir == 1 else "之前"
        extra.append(f"移动页：{range_text}，插入{pos_text}第{target_page}页{dir_text}")
    elif mode_idx == 5:
        range_text = settings.get("delete_range", "")
        extra.append(f"删除页：{range_text}")

    extra_text = "，".join(extra) if extra else ""

    for it in items:
        it.preview_extra = {"A": f"页面操作({mode_name})：{extra_text}"}


def _parse_range_list(text: str) -> list:
    """解析页面范围字符串列表"""
    if not text or not text.strip():
        return []
    ranges = []
    parts = text.replace(" ", "").split(",")
    for part in parts:
        if "-" in part:
            start, end = part.split("-")
            start = int(start) if start else 1
            end = int(end) if end else 99999
            if start > end:
                start, end = end, start
            ranges.append([start - 1, end])
        else:
            if part.isdigit():
                p = int(part)
                ranges.append([p - 1, p])
    return ranges


def _extract_pages(src_path: str, out_path: str, page_indices: list):
    """从 PDF 中提取指定页面并保存为新文件"""
    reader = PdfReader(src_path)
    writer = PdfWriter()
    for idx in page_indices:
        if 0 <= idx < len(reader.pages):
            writer.add_page(reader.pages[idx])
    with open(out_path, "wb") as f:
        writer.write(f)


def _extract_remaining_pages(src_path: str, out_path: str, page_indices: list):
    """从 PDF 中提取剩余页面（排除指定页面）并保存"""
    reader = PdfReader(src_path)
    writer = PdfWriter()
    total = len(reader.pages)
    page_set = set(page_indices)
    for i in range(total):
        if i not in page_set:
            writer.add_page(reader.pages[i])
    with open(out_path, "wb") as f:
        writer.write(f)


def _insert_pages(target_path: str, src_path: str, insert_idx: int, out_path: str):
    """在目标 PDF 的指定位置插入来源 PDF 的所有页面"""
    reader_target = PdfReader(target_path)
    reader_src = PdfReader(src_path)
    writer = PdfWriter()

    total_target = len(reader_target.pages)
    if total_target == 0:
        raise ValueError("目标文件没有页面")

    src_pages = list(reader_src.pages)
    if not src_pages:
        raise ValueError("来源文件没有页面")

    target_pages = list(reader_target.pages)

    for i in range(total_target):
        if i == insert_idx:
            for sp in src_pages:
                writer.add_page(sp)
        writer.add_page(target_pages[i])

    if insert_idx >= total_target:
        for sp in src_pages:
            writer.add_page(sp)

    with open(out_path, "wb") as f:
        writer.write(f)


def _insert_single_page(target_path: str, page_to_insert, insert_idx: int, out_path: str):
    """在目标 PDF 的指定位置插入单页"""
    reader_target = PdfReader(target_path)
    writer = PdfWriter()

    total_target = len(reader_target.pages)
    if total_target == 0:
        raise ValueError("目标文件没有页面")

    target_pages = list(reader_target.pages)

    for i in range(total_target):
        if i == insert_idx:
            writer.add_page(page_to_insert)
        writer.add_page(target_pages[i])

    if insert_idx >= total_target:
        writer.add_page(page_to_insert)

    with open(out_path, "wb") as f:
        writer.write(f)


def _replace_pages(target_path: str, src_path: str, target_indices: list, src_indices: list, out_path: str):
    """用来源 PDF 的指定页面替换目标 PDF 的指定页面"""
    reader_target = PdfReader(target_path)
    reader_src = PdfReader(src_path)
    writer = PdfWriter()

    target_pages = list(reader_target.pages)
    src_pages = []
    for idx in src_indices:
        if 0 <= idx < len(reader_src.pages):
            src_pages.append(reader_src.pages[idx])

    if not src_pages:
        raise ValueError("来源页面为空")

    target_idx = 0
    src_idx = 0
    while target_idx < len(target_pages):
        if target_idx in target_indices:
            if src_idx < len(src_pages):
                writer.add_page(src_pages[src_idx])
                src_idx += 1
            else:
                writer.add_page(target_pages[target_idx])
        else:
            writer.add_page(target_pages[target_idx])
        target_idx += 1

    with open(out_path, "wb") as f:
        writer.write(f)


def _split_by_page_count(src_path: str, out_dir: str, base_name: str, page_count: int) -> list:
    """按固定页数拆分 PDF 为多个文件"""
    reader = PdfReader(src_path)
    total = len(reader.pages)
    if total == 0:
        return []
    output_files = []
    for start in range(0, total, page_count):
        end = min(start + page_count, total)
        writer = PdfWriter()
        for i in range(start, end):
            writer.add_page(reader.pages[i])
        out_name = f"{base_name}_第{start//page_count + 1}部分.pdf"
        out_path = os.path.join(out_dir, out_name)
        with open(out_path, "wb") as f:
            writer.write(f)
        output_files.append(out_path)
    return output_files


def _split_by_ranges(src_path: str, out_dir: str, base_name: str, ranges: list) -> list:
    """按指定页码范围拆分 PDF 为多个文件"""
    reader = PdfReader(src_path)
    total = len(reader.pages)
    output_files = []
    for i, (start, end) in enumerate(ranges):
        start = max(0, start)
        end = min(end, total)
        if start >= end:
            continue
        writer = PdfWriter()
        for j in range(start, end):
            writer.add_page(reader.pages[j])
        out_name = f"{base_name}_第{i+1}部分.pdf"
        out_path = os.path.join(out_dir, out_name)
        with open(out_path, "wb") as f:
            writer.write(f)
        output_files.append(out_path)
    return output_files


def _reorder_pages(src_path: str, out_path: str, range_indices: list, insert_idx: int):
    """将指定页面移动到新位置（重排）"""
    reader = PdfReader(src_path)
    total = len(reader.pages)
    if total == 0:
        raise ValueError("文件没有页面")
    if not range_indices:
        raise ValueError("未指定要移动的页面")

    range_set = set(range_indices)
    remaining = []
    moved_pages = []

    for i in range(total):
        if i in range_set:
            moved_pages.append(reader.pages[i])
        else:
            remaining.append(reader.pages[i])

    if not moved_pages:
        raise ValueError("未找到要移动的页面")

    if insert_idx >= len(remaining):
        insert_idx = len(remaining)

    writer = PdfWriter()
    for i in range(len(remaining)):
        if i == insert_idx:
            for p in moved_pages:
                writer.add_page(p)
        writer.add_page(remaining[i])
    if insert_idx >= len(remaining):
        for p in moved_pages:
            writer.add_page(p)

    with open(out_path, "wb") as f:
        writer.write(f)


def _delete_pages(src_path: str, out_path: str, range_indices: list):
    """删除指定页面"""
    reader = PdfReader(src_path)
    total = len(reader.pages)
    if total <= 1:
        raise ValueError("页面数量需大于1页，无法删除")
    if len(range_indices) >= total:
        raise ValueError("删除的页面数量不可大于等于总页数")
    writer = PdfWriter()
    range_set = set(range_indices)
    for i in range(total):
        if i not in range_set:
            writer.add_page(reader.pages[i])
    if len(writer.pages) == 0:
        raise ValueError("删除后页面为空")
    with open(out_path, "wb") as f:
        writer.write(f)


def _get_insert_position(total_pages: int, pos_mode: int, pos_page: int, pos_dir: int) -> int:
    """计算插入位置索引"""
    if pos_mode == 1:
        if pos_dir == 1:
            return total_pages
        else:
            return total_pages - 1
    else:
        insert_idx = pos_page - 1
        if insert_idx < 0:
            insert_idx = 0
        if insert_idx > total_pages:
            insert_idx = total_pages
        if pos_dir == 1:
            insert_idx = min(insert_idx + 1, total_pages)
        return max(0, min(insert_idx, total_pages))


def run_task(file_item, settings):
    """组织不支持单任务模式"""
    raise NotImplementedError("组织页面功能请使用 run_batch，不要使用 run_task")


def run_batch(items, settings, get_output_dir, get_output_name_for_group,
              log_callback=None, progress_callback=None, stop_check=None):
    """批量组织 PDF 页面"""
    if not items:
        return []

    mode = settings.get("mode", 0)
    output_files = []

    if mode == 0:  
        range_text = settings.get("range_edit", "")
        delete_check = settings.get("delete_check", False)
        for item in items:
            if stop_check and stop_check():
                if log_callback:
                    log_callback("⛔ 用户终止任务")
                break

            src = item.input_path
            reader = PdfReader(src)
            total_pages = len(reader.pages)
            indices = parse_page_range(range_text, total_pages)
            if not indices:
                indices = list(range(total_pages))
            out_dir = get_output_dir(item)
            base_name = os.path.splitext(item.output_name)[0] if item.output_name else os.path.splitext(os.path.basename(src))[0]
            out_path = os.path.join(out_dir, f"{base_name}_提取.pdf")
            _extract_pages(src, out_path, indices)
            item.output_name = os.path.basename(out_path)
            item.output_dir = out_dir
            item.status = "完成"
            output_files.append(out_path)

            if delete_check:
                remaining_path = os.path.join(out_dir, f"{base_name}_剩余.pdf")
                _extract_remaining_pages(src, remaining_path, indices)

    elif mode == 1: 
        src_path = settings.get("insert_file", "")
        if not src_path:
            raise ValueError("请选择要插入的PDF文件")
        if not os.path.exists(src_path):
            raise ValueError(f"文件不存在: {src_path}")

        pos_mode = settings.get("insert_position_mode", 0)
        pos_page = settings.get("insert_position_page", 1)
        pos_dir = settings.get("insert_position_dir", 0)
        sequential = settings.get("sequential_insert", False)

        if sequential:
            reader_src = PdfReader(src_path)
            src_pages = list(reader_src.pages)
            total_src_pages = len(src_pages)
            total_targets = len(items)

            if total_src_pages != total_targets:
                raise ValueError(f"源文件有 {total_src_pages} 页，但目标文件有 {total_targets} 个，数量不匹配")

            for idx, item in enumerate(items):
                if stop_check and stop_check():
                    if log_callback:
                        log_callback("⛔ 用户终止任务")
                    break

                target_path = item.input_path
                page_to_insert = src_pages[idx]
                reader_target = PdfReader(target_path)
                total_target_pages = len(reader_target.pages)
                insert_idx = _get_insert_position(total_target_pages, pos_mode, pos_page, pos_dir)

                out_dir = get_output_dir(item)
                base_name = os.path.splitext(item.output_name)[0] if item.output_name else os.path.splitext(os.path.basename(target_path))[0]
                out_path = os.path.join(out_dir, f"{base_name}_插入.pdf")
                _insert_single_page(target_path, page_to_insert, insert_idx, out_path)
                item.output_name = os.path.basename(out_path)
                item.output_dir = out_dir
                item.status = "完成"
                output_files.append(out_path)

        else:
            for item in items:
                if stop_check and stop_check():
                    if log_callback:
                        log_callback("⛔ 用户终止任务")
                    break

                target_path = item.input_path
                reader_target = PdfReader(target_path)
                total_target_pages = len(reader_target.pages)
                insert_idx = _get_insert_position(total_target_pages, pos_mode, pos_page, pos_dir)

                out_dir = get_output_dir(item)
                base_name = os.path.splitext(item.output_name)[0] if item.output_name else os.path.splitext(os.path.basename(target_path))[0]
                out_path = os.path.join(out_dir, f"{base_name}_插入.pdf")
                _insert_pages(target_path, src_path, insert_idx, out_path)
                item.output_name = os.path.basename(out_path)
                item.output_dir = out_dir
                item.status = "完成"
                output_files.append(out_path)

    elif mode == 2:  
        target_text = settings.get("replace_target", "")
        if not target_text:
            raise ValueError("请指定要替换的目标页面范围")
        src_path = settings.get("replace_file", "")
        if not src_path:
            raise ValueError("请选择来源PDF文件")
        if not os.path.exists(src_path):
            raise ValueError(f"文件不存在: {src_path}")

        reader_src = PdfReader(src_path)
        source_text = settings.get("replace_source", "")
        if not source_text.strip():
            src_indices = list(range(len(reader_src.pages)))
        else:
            src_indices = parse_page_range(source_text, len(reader_src.pages))
        if not src_indices:
            raise ValueError("来源页面范围无效")

        for item in items:
            if stop_check and stop_check():
                if log_callback:
                    log_callback("⛔ 用户终止任务")
                break

            src = item.input_path
            reader = PdfReader(src)
            total_pages = len(reader.pages)
            target_indices = parse_page_range(target_text, total_pages)
            if not target_indices:
                raise ValueError("目标页面范围无效")
            out_dir = get_output_dir(item)
            base_name = os.path.splitext(item.output_name)[0] if item.output_name else os.path.splitext(os.path.basename(src))[0]
            out_path = os.path.join(out_dir, f"{base_name}_替换.pdf")
            _replace_pages(src, src_path, target_indices, src_indices, out_path)
            item.output_name = os.path.basename(out_path)
            item.output_dir = out_dir
            item.status = "完成"
            output_files.append(out_path)

    elif mode == 3:  
        split_mode = settings.get("split_mode", 0)
        custom_names = settings.get("custom_names", [])
        for item in items:
            if stop_check and stop_check():
                if log_callback:
                    log_callback("⛔ 用户终止任务")
                break

            src = item.input_path
            out_dir = get_output_dir(item)
            base_name = os.path.splitext(item.output_name)[0] if item.output_name else os.path.splitext(os.path.basename(src))[0]
            if split_mode == 0:
                page_count = settings.get("split_page_count", 5)
                files = _split_by_page_count(src, out_dir, base_name, page_count)
            else:
                range_text = settings.get("split_range_list", "")
                ranges = _parse_range_list(range_text)
                if not ranges:
                    raise ValueError("请输入有效的页码范围")
                files = _split_by_ranges(src, out_dir, base_name, ranges)
            if custom_names:
                for idx, old_path in enumerate(files):
                    if idx < len(custom_names):
                        new_name = f"{custom_names[idx]}.pdf"
                        new_path = os.path.join(out_dir, new_name)
                        os.rename(old_path, new_path)
                        files[idx] = new_path
            for f in files:
                output_files.append(f)
            item.output_name = os.path.basename(files[0]) if files else ""
            item.output_dir = out_dir
            item.status = f"完成（生成 {len(files)} 个文件）"

    elif mode == 4:  
        range_text = settings.get("reorder_range", "")
        if not range_text:
            raise ValueError("请指定要移动的页面范围")
        pos_mode = settings.get("reorder_position_mode", 0)
        target_page = settings.get("reorder_target_page", 1)
        position_dir = settings.get("reorder_dir", 0)

        for item in items:
            if stop_check and stop_check():
                if log_callback:
                    log_callback("⛔ 用户终止任务")
                break

            src = item.input_path
            reader = PdfReader(src)
            total_pages = len(reader.pages)
            range_indices = parse_page_range(range_text, total_pages)
            if not range_indices:
                raise ValueError("页面范围无效")

            if pos_mode == 1:
                insert_idx = total_pages - 1
                if position_dir == 1:
                    insert_idx = total_pages
            else:
                insert_idx = target_page - 1
                if insert_idx < 0:
                    insert_idx = 0
                if insert_idx > total_pages:
                    insert_idx = total_pages
                if position_dir == 1:
                    insert_idx = min(insert_idx + 1, total_pages)

            range_min = min(range_indices)
            range_max = max(range_indices)
            if insert_idx > range_max:
                insert_idx = insert_idx - len(range_indices)
            elif insert_idx <= range_min:
                pass
            else:
                insert_idx = range_min

            insert_idx = max(0, min(insert_idx, total_pages - len(range_indices)))

            out_dir = get_output_dir(item)
            base_name = os.path.splitext(item.output_name)[0] if item.output_name else os.path.splitext(os.path.basename(src))[0]
            out_path = os.path.join(out_dir, f"{base_name}_重排.pdf")
            _reorder_pages(src, out_path, range_indices, insert_idx)
            item.output_name = os.path.basename(out_path)
            item.output_dir = out_dir
            item.status = "完成"
            output_files.append(out_path)

    elif mode == 5: 
        range_text = settings.get("delete_range", "")
        if not range_text:
            raise ValueError("请指定要删除的页面范围")
        for item in items:
            if stop_check and stop_check():
                if log_callback:
                    log_callback("⛔ 用户终止任务")
                break

            src = item.input_path
            reader = PdfReader(src)
            total_pages = len(reader.pages)
            range_indices = parse_page_range(range_text, total_pages)
            if not range_indices:
                raise ValueError("页面范围无效")
            out_dir = get_output_dir(item)
            base_name = os.path.splitext(item.output_name)[0] if item.output_name else os.path.splitext(os.path.basename(src))[0]
            out_path = os.path.join(out_dir, f"{base_name}_删除.pdf")
            _delete_pages(src, out_path, range_indices)
            item.output_name = os.path.basename(out_path)
            item.output_dir = out_dir
            item.status = "完成"
            output_files.append(out_path)

    return output_files
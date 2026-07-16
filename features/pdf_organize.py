# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import re
from PyPDF2 import PdfReader, PdfWriter
from PySide6.QtCore import Signal
from PySide6.QtGui import QIntValidator, QAction, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, 
    QSpinBox, QPushButton, QFileDialog, QMessageBox, QCheckBox, QSizePolicy
)
from core.utils import parse_page_range, resource_path


class OrganizePanel(QWidget):
    changed = Signal()
    detect_page_signal = Signal()

    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("操作模式："))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "提取页面",
            "插入页面",
            "替换页面",
            "拆分页面",
            "重排页面",
            "删除页面"
        ])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self.mode_combo, 1)

        self.sequential_insert_check = QCheckBox("按序插入")
        self.sequential_insert_check.setToolTip("将源文件的第N页插入到列表中第N个文件的指定位置")
        self.sequential_insert_check.setVisible(False)
        mode_row.addWidget(self.sequential_insert_check)

        main_layout.addLayout(mode_row)

        self.extract_widget = QWidget()
        extract_layout = QVBoxLayout(self.extract_widget)
        extract_layout.setContentsMargins(0, 0, 0, 0)
        extract_layout.setSpacing(4)

        extract_row = QHBoxLayout()
        extract_row.addWidget(QLabel("页面范围："))
        self.extract_range = QLineEdit()
        self.extract_range.setPlaceholderText("1-3,5,8-10（留空=全部）")
        extract_row.addWidget(self.extract_range, 1)
        self.extract_delete = QCheckBox("提取后删除页面")
        self.extract_delete.setChecked(False)
        extract_row.addWidget(self.extract_delete)
        extract_layout.addLayout(extract_row)

        main_layout.addWidget(self.extract_widget)

        self.insert_widget = QWidget()
        insert_layout = QVBoxLayout(self.insert_widget)
        insert_layout.setContentsMargins(0, 0, 0, 0)
        insert_layout.setSpacing(6)

        insert_file_row = QHBoxLayout()
        insert_file_row.addWidget(QLabel("插入文件："))
        self.insert_file_path = QLineEdit()
        self.insert_file_path.setPlaceholderText("点击右侧图标选择PDF文件")
        self.insert_file_path.setReadOnly(True)
        insert_file_row.addWidget(self.insert_file_path, 1)
        insert_action = QAction(self)
        insert_action.setIcon(QIcon(resource_path("assets/folder.png")))
        insert_action.setToolTip("选择要插入的PDF文件")
        insert_action.triggered.connect(self._select_insert_file)
        self.insert_file_path.addAction(insert_action, QLineEdit.TrailingPosition)
        insert_layout.addLayout(insert_file_row)

        pos_row = QHBoxLayout()
        pos_row.setSpacing(4)
        pos_row.addWidget(QLabel("插入位置："))
        self.insert_pos_mode = QComboBox()
        self.insert_pos_mode.addItems(["自定义", "最后一页"])
        self.insert_pos_mode.setMinimumWidth(80)
        self.insert_pos_mode.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.insert_pos_mode.currentIndexChanged.connect(self._on_insert_pos_mode_changed)
        pos_row.addWidget(self.insert_pos_mode)

        self.insert_pos_page_container = QWidget()
        container_layout = QHBoxLayout(self.insert_pos_page_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(2)
        container_layout.addWidget(QLabel("第"))
        self.insert_pos_page = QLineEdit()
        self.insert_pos_page.setFixedWidth(40)
        self.insert_pos_page.setPlaceholderText("1")
        self.insert_pos_page.setValidator(QIntValidator(1, 99999))
        container_layout.addWidget(self.insert_pos_page)
        container_layout.addWidget(QLabel("页"))
        pos_row.addWidget(self.insert_pos_page_container)

        self.insert_pos_dir = QComboBox()
        self.insert_pos_dir.addItems(["之前", "之后"])
        self.insert_pos_dir.setMinimumWidth(80)
        self.insert_pos_dir.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        pos_row.addWidget(self.insert_pos_dir)

        insert_layout.addLayout(pos_row)

        main_layout.addWidget(self.insert_widget)

        self.replace_widget = QWidget()
        replace_layout = QVBoxLayout(self.replace_widget)
        replace_layout.setContentsMargins(0, 0, 0, 0)
        replace_layout.setSpacing(6)

        replace_target_row = QHBoxLayout()
        replace_target_row.addWidget(QLabel("替换页面："))
        self.replace_target_range = QLineEdit()
        self.replace_target_range.setPlaceholderText("1-3,5,8-10")
        replace_target_row.addWidget(self.replace_target_range, 1)
        replace_layout.addLayout(replace_target_row)

        replace_file_row = QHBoxLayout()
        replace_file_row.addWidget(QLabel("替换文件："))
        self.replace_file_path = QLineEdit()
        self.replace_file_path.setPlaceholderText("点击右侧图标选择PDF文件")
        self.replace_file_path.setReadOnly(True)
        replace_file_row.addWidget(self.replace_file_path, 1)
        replace_action = QAction(self)
        replace_action.setIcon(QIcon(resource_path("assets/folder.png")))
        replace_action.setToolTip("选择来源PDF文件")
        replace_action.triggered.connect(self._select_replace_file)
        self.replace_file_path.addAction(replace_action, QLineEdit.TrailingPosition)
        replace_layout.addLayout(replace_file_row)

        replace_source_row = QHBoxLayout()
        replace_source_row.addWidget(QLabel("使用页面："))
        self.replace_source_range = QLineEdit()
        self.replace_source_range.setPlaceholderText("留空=全部，示例：1-3,5")
        replace_source_row.addWidget(self.replace_source_range, 1)
        replace_layout.addLayout(replace_source_row)

        main_layout.addWidget(self.replace_widget)

        self.split_widget = QWidget()
        split_layout = QVBoxLayout(self.split_widget)
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.setSpacing(6)

        split_mode_row = QHBoxLayout()
        split_mode_row.addWidget(QLabel("拆分方式："))
        self.split_mode = QComboBox()
        self.split_mode.addItems(["按固定页数", "按指定页码范围"])
        self.split_mode.currentIndexChanged.connect(self._on_split_mode_changed)
        split_mode_row.addWidget(self.split_mode, 1)
        split_layout.addLayout(split_mode_row)

        self.split_count_row = QWidget()
        split_count_row_layout = QHBoxLayout(self.split_count_row)
        split_count_row_layout.setContentsMargins(0, 0, 0, 0)
        split_count_row_layout.addWidget(QLabel("每份页数："))
        self.split_page_count = QSpinBox()
        self.split_page_count.setRange(1, 9999)
        self.split_page_count.setValue(5)
        split_count_row_layout.addWidget(self.split_page_count, 1)
        split_layout.addWidget(self.split_count_row)

        self.split_range_row = QWidget()
        split_range_row_layout = QHBoxLayout(self.split_range_row)
        split_range_row_layout.setContentsMargins(0, 0, 0, 0)
        split_range_row_layout.addWidget(QLabel("页面范围："))
        self.split_range_list = QLineEdit()
        self.split_range_list.setPlaceholderText("1-3,4-6,7-9")
        split_range_row_layout.addWidget(self.split_range_list, 1)
        split_layout.addWidget(self.split_range_row)
        self.split_range_row.setVisible(False)

        main_layout.addWidget(self.split_widget)

        self.reorder_widget = QWidget()
        reorder_layout = QVBoxLayout(self.reorder_widget)
        reorder_layout.setContentsMargins(0, 0, 0, 0)
        reorder_layout.setSpacing(6)

        reorder_range_row = QHBoxLayout()
        reorder_range_row.addWidget(QLabel("页面范围："))
        self.reorder_range = QLineEdit()
        self.reorder_range.setPlaceholderText("3-5")
        reorder_range_row.addWidget(self.reorder_range, 1)
        reorder_layout.addLayout(reorder_range_row)

        reorder_row = QHBoxLayout()
        reorder_row.setSpacing(4)
        reorder_row.addWidget(QLabel("插入至："))
        self.reorder_pos_mode = QComboBox()
        self.reorder_pos_mode.addItems(["自定义", "最后一页"])
        self.reorder_pos_mode.setMinimumWidth(80)
        self.reorder_pos_mode.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.reorder_pos_mode.currentIndexChanged.connect(self._on_reorder_pos_mode_changed)
        reorder_row.addWidget(self.reorder_pos_mode)

        self.reorder_target_page_container = QWidget()
        reorder_container_layout = QHBoxLayout(self.reorder_target_page_container)
        reorder_container_layout.setContentsMargins(0, 0, 0, 0)
        reorder_container_layout.setSpacing(2)
        reorder_container_layout.addWidget(QLabel("第"))
        self.reorder_target_page = QLineEdit()
        self.reorder_target_page.setFixedWidth(40)
        self.reorder_target_page.setPlaceholderText("1")
        self.reorder_target_page.setValidator(QIntValidator(1, 99999))
        reorder_container_layout.addWidget(self.reorder_target_page)
        reorder_container_layout.addWidget(QLabel("页"))
        reorder_row.addWidget(self.reorder_target_page_container)

        self.reorder_dir = QComboBox()
        self.reorder_dir.addItems(["之前", "之后"])
        self.reorder_dir.setMinimumWidth(80)
        self.reorder_dir.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        reorder_row.addWidget(self.reorder_dir)

        reorder_layout.addLayout(reorder_row)

        main_layout.addWidget(self.reorder_widget)

        self.delete_widget = QWidget()
        delete_layout = QVBoxLayout(self.delete_widget)
        delete_layout.setContentsMargins(0, 0, 0, 0)
        delete_layout.setSpacing(6)

        delete_range_row = QHBoxLayout()
        delete_range_row.addWidget(QLabel("页面范围："))
        self.delete_range = QLineEdit()
        self.delete_range.setPlaceholderText("1-3,5,8-10")
        delete_range_row.addWidget(self.delete_range, 1)
        delete_layout.addLayout(delete_range_row)
        
        main_layout.addWidget(self.delete_widget)

        self.btn_detect_page = QPushButton("检测页码")
        self.btn_detect_page.clicked.connect(self.detect_page_signal.emit)
        main_layout.addWidget(self.btn_detect_page)

        main_layout.addStretch()

        self._show_only_widget(0)
        self._on_split_mode_changed()
        self._on_insert_pos_mode_changed()
        self._on_reorder_pos_mode_changed()

        self.mode_combo.currentIndexChanged.connect(self.changed)
        self.extract_range.textChanged.connect(self.changed)
        self.extract_delete.stateChanged.connect(self.changed)
        self.insert_file_path.textChanged.connect(self.changed)
        self.insert_pos_mode.currentIndexChanged.connect(self.changed)
        self.insert_pos_page.textChanged.connect(self.changed)
        self.insert_pos_dir.currentIndexChanged.connect(self.changed)
        self.replace_target_range.textChanged.connect(self.changed)
        self.replace_file_path.textChanged.connect(self.changed)
        self.replace_source_range.textChanged.connect(self.changed)
        self.split_mode.currentIndexChanged.connect(self.changed)
        self.split_page_count.valueChanged.connect(self.changed)
        self.split_range_list.textChanged.connect(self.changed)
        self.reorder_range.textChanged.connect(self.changed)
        self.reorder_pos_mode.currentIndexChanged.connect(self.changed)
        self.reorder_target_page.textChanged.connect(self.changed)
        self.reorder_dir.currentIndexChanged.connect(self.changed)
        self.delete_range.textChanged.connect(self.changed)
        self.sequential_insert_check.stateChanged.connect(self.changed)

    def _on_mode_changed(self):
        idx = self.mode_combo.currentIndex()
        self._show_only_widget(idx)
        self.sequential_insert_check.setVisible(idx == 1)
        self.changed.emit()

    def _show_only_widget(self, index):
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
        is_fixed = self.split_mode.currentIndex() == 0
        self.split_count_row.setVisible(is_fixed)
        self.split_range_row.setVisible(not is_fixed)
        self.changed.emit()

    def _on_insert_pos_mode_changed(self):
        is_custom = self.insert_pos_mode.currentIndex() == 0
        self.insert_pos_page_container.setVisible(is_custom)
        self.changed.emit()

    def _on_reorder_pos_mode_changed(self):
        is_custom = self.reorder_pos_mode.currentIndex() == 0
        self.reorder_target_page_container.setVisible(is_custom)
        self.changed.emit()

    def _select_insert_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择要插入的PDF文件", "", "PDF文件 (*.pdf)")
        if path:
            self.insert_file_path.setText(path)
            self.changed.emit()

    def _select_replace_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择来源PDF文件", "", "PDF文件 (*.pdf)")
        if path:
            self.replace_file_path.setText(path)
            self.changed.emit()


def build_panel() -> QWidget:
    return OrganizePanel()


def collect_settings(panel: OrganizePanel) -> dict:
    return {
        "mode": panel.mode_combo.currentIndex(),
        "extract_range": panel.extract_range.text().strip(),
        "extract_delete": panel.extract_delete.isChecked(),
        "insert_file": panel.insert_file_path.text().strip(),
        "insert_pos_mode": panel.insert_pos_mode.currentIndex(),
        "insert_pos_page": int(panel.insert_pos_page.text() or 1),
        "insert_pos_dir": panel.insert_pos_dir.currentIndex(),
        "replace_target": panel.replace_target_range.text().strip(),
        "replace_file": panel.replace_file_path.text().strip(),
        "replace_source": panel.replace_source_range.text().strip(),
        "split_mode": panel.split_mode.currentIndex(),
        "split_page_count": panel.split_page_count.value(),
        "split_range_list": panel.split_range_list.text().strip(),
        "reorder_range": panel.reorder_range.text().strip(),
        "reorder_pos_mode": panel.reorder_pos_mode.currentIndex(),
        "reorder_target_page": int(panel.reorder_target_page.text() or 1),
        "reorder_dir": panel.reorder_dir.currentIndex(),
        "delete_range": panel.delete_range.text().strip(),
        "sequential_insert": panel.sequential_insert_check.isChecked(),
    }


def prepare_preview(items, settings):
    mode_names = ["提取", "插入", "替换", "拆分", "重排", "删除"]
    mode_idx = settings.get("mode", 0)
    mode_name = mode_names[mode_idx] if mode_idx < len(mode_names) else "未知"
    if mode_idx == 1 and settings.get("sequential_insert", False):
        mode_name += "(按序)"
    for it in items:
        it.preview_extra = {"A": f"页面操作({mode_name})"}


def _parse_range_list(text: str) -> list:
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
    reader = PdfReader(src_path)
    writer = PdfWriter()
    for idx in page_indices:
        if 0 <= idx < len(reader.pages):
            writer.add_page(reader.pages[idx])
    with open(out_path, "wb") as f:
        writer.write(f)


def _extract_remaining_pages(src_path: str, out_path: str, page_indices: list):
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
    raise NotImplementedError("组织页面功能请使用 run_batch，不要使用 run_task")


def run_batch(items, settings, get_output_dir, get_output_name_for_group,
              log_callback=None, progress_callback=None, stop_check=None):
    if not items:
        return []

    mode = settings.get("mode", 0)
    output_files = []

    if mode == 0:  # 提取页面
        range_text = settings.get("extract_range", "")
        extract_delete = settings.get("extract_delete", False)
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

            if extract_delete:
                remaining_path = os.path.join(out_dir, f"{base_name}_剩余.pdf")
                _extract_remaining_pages(src, remaining_path, indices)

    elif mode == 1:  # 插入页面
        src_path = settings.get("insert_file", "")
        if not src_path:
            raise ValueError("请选择要插入的PDF文件")
        if not os.path.exists(src_path):
            raise ValueError(f"文件不存在: {src_path}")

        pos_mode = settings.get("insert_pos_mode", 0)
        pos_page = settings.get("insert_pos_page", 1)
        pos_dir = settings.get("insert_pos_dir", 0)
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

    elif mode == 2:  # 替换页面
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

    elif mode == 3:  # 拆分页面
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

    elif mode == 4:  # 重排页面
        range_text = settings.get("reorder_range", "")
        if not range_text:
            raise ValueError("请指定要移动的页面范围")
        pos_mode = settings.get("reorder_pos_mode", 0)
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

    elif mode == 5:  # 删除页面
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
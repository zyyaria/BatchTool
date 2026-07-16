# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import re
import shutil
from PyPDF2 import PdfMerger
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox
)
from core.utils import get_group_key


class MergePanel(QWidget):
    changed = Signal()

    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setSpacing(8)

        group_row = QHBoxLayout()
        group_row.addWidget(QLabel("分组方式:"))
        self.group_mode = QComboBox()
        self.group_mode.addItems(["按文件名前缀长度", "每N个一组", "按文件夹", "所有文件"])
        self.group_mode.currentIndexChanged.connect(self._toggle_options)
        group_row.addWidget(self.group_mode, 1)

        self.prefix_len = QSpinBox()
        self.prefix_len.setRange(1, 50)
        self.prefix_len.setValue(9)
        self.prefix_len.setFixedWidth(70)
        self.prefix_len.setVisible(False)
        group_row.addWidget(self.prefix_len)

        self.group_size = QSpinBox()
        self.group_size.setRange(2, 9999)
        self.group_size.setValue(5)
        self.group_size.setFixedWidth(70)
        self.group_size.setVisible(False)
        group_row.addWidget(self.group_size)

        v.addLayout(group_row)

        v.addStretch()

        self.group_mode.currentIndexChanged.connect(self.changed)
        self.prefix_len.valueChanged.connect(self.changed)
        self.group_size.valueChanged.connect(self.changed)
        self._toggle_options()

    def _toggle_options(self):
        mode = self.group_mode.currentIndex()
        self.prefix_len.setVisible(mode == 0)
        self.group_size.setVisible(mode == 1)


def build_panel() -> QWidget:
    return MergePanel()


def collect_settings(panel: MergePanel) -> dict:
    return {
        "group_mode": panel.group_mode.currentIndex(),
        "prefix_len": panel.prefix_len.value(),
        "group_size": panel.group_size.value(),
    }


def prepare_preview(items, settings):
    group_mode = settings.get("group_mode", 0)
    prefix_len = settings.get("prefix_len", 9)
    group_size = settings.get("group_size", 5)

    groups = {}
    file_paths = [it.input_path for it in items]
    for it in items:
        key = get_group_key(it.input_path, group_mode, prefix_len, group_size, file_paths)
        groups.setdefault(key, []).append(it.input_path)

    for it in items:
        key = get_group_key(it.input_path, group_mode, prefix_len, group_size, file_paths)
        display_key = "全部文件" if key == "__all__" else (os.path.basename(key) if group_mode == 2 else key)
        it.preview_extra = {"A": f"组「{display_key}」共 {len(groups[key])} 个文件"}
        it.preview_extra["group_key"] = display_key

def run_batch(items, settings, get_output_dir, get_output_name_for_group,
              log_callback=None, progress_callback=None, stop_check=None):
    if not items:
        return []

    group_mode = settings.get("group_mode", 0)
    prefix_len = settings.get("prefix_len", 9)
    group_size = settings.get("group_size", 5)
    output_files = []

    file_paths = [it.input_path for it in items]
    groups = {}
    for item in items:
        key = get_group_key(item.input_path, group_mode, prefix_len, group_size, file_paths)
        groups.setdefault(key, []).append(item)

    for group_key, group_items in groups.items():
        if stop_check and stop_check():
            if log_callback:
                log_callback("⛔ 用户终止任务")
            break
        
        out_dir = get_output_dir(group_items[0])

        if group_key == "__all__":
            base_name = get_output_name_for_group("全部")
        elif group_mode == 2:
            base_name = get_output_name_for_group(os.path.basename(group_key))
        else:
            base_name = get_output_name_for_group(group_key)

        out_name = f"{base_name}.pdf"
        out_path = os.path.join(out_dir, out_name)

        if os.path.exists(out_path):
            counter = 1
            while os.path.exists(os.path.join(out_dir, f"{base_name}_{counter}.pdf")):
                counter += 1
            out_path = os.path.join(out_dir, f"{base_name}_{counter}.pdf")

        if len(group_items) == 1:
            shutil.copy2(group_items[0].input_path, out_path)
        else:
            merger = PdfMerger()
            try:
                for fi in group_items:
                    merger.append(fi.input_path)
                merger.write(out_path)
            finally:
                merger.close()

        output_files.append(out_path)

        for fi in group_items:
            fi.status = "完成"
            fi.output_name = os.path.basename(out_path)
            fi.output_dir = out_dir

    return output_files


def run_task(file_item, settings):
    raise NotImplementedError("合并功能请使用 run_batch，不要使用 run_task")
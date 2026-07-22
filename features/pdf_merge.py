# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import shutil
from PyPDF2 import PdfMerger
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox,
    QSizePolicy
)
from core.utils import get_group_key, get_unique_file_path


class MergePanel(QWidget):
    changed = Signal()

    def __init__(self):
        """初始化设置面板"""
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        row_group = QHBoxLayout()
        self.group_combo = QComboBox()
        self.group_combo.addItems(["按文件名前缀长度", "每 N 个一组", "按文件夹", "所有文件"])
        self.group_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.prefix_spin = QSpinBox()
        self.prefix_spin.setRange(1, 50)
        self.prefix_spin.setValue(9)
        self.prefix_spin.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(2, 9999)
        self.interval_spin.setValue(5)
        self.interval_spin.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        row_group.addWidget(QLabel("分组方式:"))
        row_group.addWidget(self.group_combo, 1)
        row_group.addWidget(self.prefix_spin, 1)
        row_group.addWidget(self.interval_spin, 1)
        layout.addLayout(row_group)

        layout.addStretch()

        self.group_combo.currentIndexChanged.connect(self._toggle_options)
        self.group_combo.currentIndexChanged.connect(self.changed)
        self.prefix_spin.valueChanged.connect(self.changed)
        self.interval_spin.valueChanged.connect(self.changed)

        self._toggle_options()

    def _toggle_options(self):
        """分组方式切换"""
        mode = self.group_combo.currentIndex()
        self.prefix_spin.setVisible(mode == 0)
        self.interval_spin.setVisible(mode == 1)


def build_panel() -> QWidget:
    """构建面板实例"""
    return MergePanel()


def collect_settings(panel: MergePanel) -> dict:
    """收集面板设置"""
    return {
        "group": panel.group_combo.currentIndex(),
        "prefix": panel.prefix_spin.value(),
        "interval": panel.interval_spin.value(),
    }


def prepare_preview(items, settings):
    """生成预览信息"""
    group = settings.get("group", 0)
    prefix = settings.get("prefix", 9)
    interval = settings.get("interval", 5)
    file_paths = [it.input_path for it in items]
    groups = {}
    for it in items:
        key = get_group_key(it.input_path, group, prefix, interval, file_paths)
        groups.setdefault(key, []).append(it.input_path)
    for it in items:
        key = get_group_key(it.input_path, group, prefix, interval, file_paths)
        display_key = "全部文件" if key == "__all__" else (os.path.basename(key) if group == 2 else key)
        it.preview_extra = {
            "A": f"合并：组「{display_key}」共 {len(groups[key])} 个PDF"
        }
        it.preview_extra["group_key"] = display_key


def run_batch(items, settings, get_output_dir, get_output_name_for_group,
              log_callback=None, progress_callback=None, stop_check=None):
    """批量合并 PDF"""
    if not items:
        return []
    group = settings.get("group", 0)
    prefix = settings.get("prefix", 9)
    interval = settings.get("interval", 5)
    output_files = []
    file_paths = [it.input_path for it in items]
    groups = {}
    for item in items:
        key = get_group_key(item.input_path, group, prefix, interval, file_paths)
        groups.setdefault(key, []).append(item)
    for group_key, group_items in groups.items():
        if stop_check and stop_check():
            if log_callback:
                log_callback("⛔ 用户终止任务")
            break
        out_dir = get_output_dir(group_items[0])
        if group_key == "__all__":
            base_name = get_output_name_for_group("全部")
        elif group == 2:
            base_name = get_output_name_for_group(os.path.basename(group_key))
        else:
            base_name = get_output_name_for_group(group_key)
        if not base_name.endswith(".pdf"):
            base_name = f"{base_name}.pdf"
        base, ext = os.path.splitext(base_name)
        out_path = get_unique_file_path(out_dir, base, ext)
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
    """合并不支持单任务模式"""
    raise NotImplementedError("合并功能请使用 run_batch，不要使用 run_task")
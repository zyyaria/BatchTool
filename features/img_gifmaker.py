# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import re
from PIL import Image
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox, 
    QLineEdit, QSizePolicy
)
from core.utils import get_group_key


class GifMakerPanel(QWidget):
    changed = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        group_row = QHBoxLayout()
        group_row.addWidget(QLabel("分组方式:"))
        self.group_mode = QComboBox()
        self.group_mode.addItems(["按文件名前缀长度", "每N个一组", "按文件夹", "所有文件"])
        self.group_mode.currentIndexChanged.connect(self._toggle_options)
        group_row.addWidget(self.group_mode, 1)

        self.prefix_spin = QSpinBox()
        self.prefix_spin.setRange(1, 50)
        self.prefix_spin.setValue(9)
        self.prefix_spin.setFixedWidth(70)
        self.prefix_spin.setVisible(False)
        group_row.addWidget(self.prefix_spin)

        self.group_spin = QSpinBox()
        self.group_spin.setRange(2, 9999)
        self.group_spin.setValue(5)
        self.group_spin.setFixedWidth(70)
        self.group_spin.setVisible(False)
        group_row.addWidget(self.group_spin)

        layout.addLayout(group_row)

        row_duration = QHBoxLayout()
        row_duration.addWidget(QLabel("帧间隔:"))
        self.duration = QSpinBox()
        self.duration.setRange(10, 5000)
        self.duration.setValue(300)
        self.duration.setSuffix(" ms")
        row_duration.addWidget(self.duration, 1)
        layout.addLayout(row_duration)

        row_loop = QHBoxLayout()
        row_loop.addWidget(QLabel("循环次数:"))
        self.loop = QSpinBox()
        self.loop.setRange(0, 999)
        self.loop.setValue(0)
        self.loop.setToolTip("0=无限循环")
        row_loop.addWidget(self.loop, 1)
        layout.addLayout(row_loop)

        size_row = QHBoxLayout()
        size_row.setSpacing(2)
        size_row.addWidget(QLabel("目标尺寸:"))
        self.size_mode = QComboBox()
        self.size_mode.addItems(["保持原尺寸", "自定义"])
        self.size_mode.currentIndexChanged.connect(self._on_size_mode_changed)
        size_row.addWidget(self.size_mode)

        self.target_width = QLineEdit()
        self.target_width.setPlaceholderText("宽 (px)")
        self.target_width.setVisible(False)
        size_row.addWidget(self.target_width, 1)

        self.target_height = QLineEdit()
        self.target_height.setPlaceholderText("高 (px)")
        self.target_height.setVisible(False)
        size_row.addWidget(self.target_height, 1)

        layout.addLayout(size_row)

        layout.addStretch()

        self.group_mode.currentIndexChanged.connect(self.changed)
        self.prefix_spin.valueChanged.connect(self.changed)
        self.group_spin.valueChanged.connect(self.changed)
        self.duration.valueChanged.connect(self.changed)
        self.loop.valueChanged.connect(self.changed)
        self.size_mode.currentIndexChanged.connect(self.changed)
        self.target_width.textChanged.connect(self.changed)
        self.target_height.textChanged.connect(self.changed)

        self._toggle_options()
        self._on_size_mode_changed()

    def _toggle_options(self):
        mode = self.group_mode.currentIndex()
        self.prefix_spin.setVisible(mode == 0)
        self.group_spin.setVisible(mode == 1)

    def _on_size_mode_changed(self):
        is_custom = self.size_mode.currentText() == "自定义"
        self.target_width.setVisible(is_custom)
        self.target_height.setVisible(is_custom)

        if is_custom:
            self.size_mode.setFixedWidth(90)
        else:
            self.size_mode.setMinimumWidth(0)
            self.size_mode.setMaximumWidth(16777215)
            self.size_mode.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.changed.emit()


def build_panel() -> QWidget:
    return GifMakerPanel()


def collect_settings(panel: GifMakerPanel) -> dict:
    return {
        "group_mode": panel.group_mode.currentIndex(),
        "prefix_len": panel.prefix_spin.value(),
        "group_size": panel.group_spin.value(),
        "duration": panel.duration.value(),
        "loop": panel.loop.value(),
        "size_mode": panel.size_mode.currentText(),
        "target_width": panel.target_width.text().strip(),
        "target_height": panel.target_height.text().strip(),
    }


def prepare_preview(items, settings):
    group_mode = settings.get("group_mode", 0)
    prefix_len = settings.get("prefix_len", 9)
    group_size = settings.get("group_size", 5)
    duration = settings.get("duration", 300)
    loop = "无限" if settings.get("loop", 0) == 0 else f"{settings.get('loop')}次"

    file_paths = [it.input_path for it in items]
    groups = {}
    for it in items:
        key = get_group_key(it.input_path, group_mode, prefix_len, group_size, file_paths)
        groups.setdefault(key, []).append(it.input_path)

    for it in items:
        key = get_group_key(it.input_path, group_mode, prefix_len, group_size, file_paths)
        display_key = "全部文件" if key == "__all__" else (os.path.basename(key) if group_mode == 2 else key)
        it.preview_extra = {"A": f"合成GIF：组「{display_key}」共 {len(groups[key])} 张，帧:{duration}ms，循环:{loop}"}
        it.preview_extra["group_key"] = display_key

def run_batch(items, settings, get_output_dir, get_output_name_for_group,
              log_callback=None, progress_callback=None, stop_check=None):
    if not items:
        return []

    group_mode = settings.get("group_mode", 0)
    prefix_len = settings.get("prefix_len", 9)
    group_size = settings.get("group_size", 5)
    duration = settings.get("duration", 300)
    loop = settings.get("loop", 0)
    size_mode = settings.get("size_mode", "保持原尺寸")
    target_w = int(settings.get("target_width") or 1920)
    target_h = int(settings.get("target_height") or 1080)

    file_paths = [it.input_path for it in items]
    groups = {}
    for item in items:
        key = get_group_key(item.input_path, group_mode, prefix_len, group_size, file_paths)
        groups.setdefault(key, []).append(item)

    output_files = []

    for group_key, group_items in groups.items():
        if stop_check and stop_check():
            if log_callback:
                log_callback("⛔ 用户终止任务")
            break
        
        def get_number(fi):
            match = re.search(r'_?(\d+)', os.path.basename(fi.input_path))
            return int(match.group(1)) if match else 0

        group_items.sort(key=get_number)

        if group_key == "__all__":
            out_name = get_output_name_for_group("全部")
        elif group_mode == 2:
            out_name = get_output_name_for_group(os.path.basename(group_key))
        else:
            out_name = get_output_name_for_group(group_key)

        if not out_name.endswith(".gif"):
            out_name += ".gif"
        out_path = os.path.join(get_output_dir(group_items[0]), out_name)

        images = []
        for fi in group_items:
            img = Image.open(fi.input_path)
            if img.mode == "RGBA":
                img = img.convert("RGB")
            if size_mode == "自定义":
                img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            images.append(img)

        if images:
            images[0].save(
                out_path,
                save_all=True,
                append_images=images[1:],
                duration=duration,
                loop=loop,
                format="GIF",
                disposal=2
            )

        output_files.append(out_path)

        for fi in group_items:
            fi.status = "完成"
            fi.output_name = os.path.basename(out_path)
            fi.output_dir = get_output_dir(fi)

    return output_files


def run_task(file_item, settings):
    raise NotImplementedError("GIF 合成功能请使用 run_batch，不要使用 run_task")
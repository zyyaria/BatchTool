# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import re
from PIL import Image
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox,
    QSizePolicy
)
from core.utils import get_group_key, get_unique_file_path


class GifMakerPanel(QWidget):
    changed = Signal()

    def __init__(self):
        """初始化设置面板"""
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        self.group_combo = QComboBox()
        self.group_combo.addItems(["按文件名前缀长度", "每 N 个一组", "按文件夹", "所有文件"])
        self.group_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.prefix_spin = QSpinBox()
        self.prefix_spin.setRange(1, 50)
        self.prefix_spin.setValue(9)
        self.prefix_spin.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.group_spin = QSpinBox()
        self.group_spin.setRange(2, 9999)
        self.group_spin.setValue(5)
        self.group_spin.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(10, 5000)
        self.duration_spin.setValue(300)
        self.duration_spin.setSuffix(" ms")
        self.duration_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.loop_spin = QSpinBox()
        self.loop_spin.setRange(0, 999)
        self.loop_spin.setValue(0)
        self.loop_spin.setToolTip("0=无限循环")
        self.loop_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  
        self.size_combo = QComboBox()
        self.size_combo.addItems(["保持原尺寸", "自定义"])
        self.size_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.size_widget = QWidget()
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 9999)
        self.width_spin.setValue(640)
        self.width_spin.setSuffix(" px")
        self.width_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 9999)
        self.height_spin.setValue(480)
        self.height_spin.setSuffix(" px")
        self.height_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        row_param1 = QHBoxLayout()
        row_param1.addWidget(QLabel("分组方式:"))
        row_param1.addWidget(self.group_combo, 1)
        row_param1.addWidget(self.prefix_spin, 1)
        row_param1.addWidget(self.group_spin, 1)
        row_param2 = QHBoxLayout()
        row_param2.addWidget(QLabel("时间间隔:"))
        row_param2.addWidget(self.duration_spin, 1)
        row_param3 = QHBoxLayout()
        row_param3.addWidget(QLabel("循环次数:"))
        row_param3.addWidget(self.loop_spin, 1)    
        row_param4 = QHBoxLayout()
        row_param4.addWidget(QLabel("目标尺寸:"))
        row_param4.addWidget(self.size_combo, 1)
        row_param5 = QHBoxLayout(self.size_widget)
        row_param5.setContentsMargins(0, 0, 0, 0)
        row_param5.addWidget(QLabel("宽度:"))
        row_param5.addWidget(self.width_spin, 1)
        row_param5.addWidget(QLabel("高度:"))
        row_param5.addWidget(self.height_spin, 1)
        layout.addLayout(row_param1)
        layout.addLayout(row_param2)
        layout.addLayout(row_param3)
        layout.addLayout(row_param4)
        layout.addWidget(self.size_widget)

        layout.addStretch()

        self.group_combo.currentIndexChanged.connect(self._toggle_options)
        self.group_combo.currentIndexChanged.connect(self.changed)
        self.prefix_spin.valueChanged.connect(self.changed)
        self.group_spin.valueChanged.connect(self.changed)
        self.duration_spin.valueChanged.connect(self.changed)
        self.loop_spin.valueChanged.connect(self.changed)
        self.size_combo.currentIndexChanged.connect(self._on_size_combo_changed)
        self.size_combo.currentIndexChanged.connect(self.changed)
        self.width_spin.valueChanged.connect(self.changed)
        self.height_spin.valueChanged.connect(self.changed)

        self._toggle_options()
        self._on_size_combo_changed()

    def _toggle_options(self):
        """分组方式切换时显示/隐藏前缀长度或每组数量控件"""
        mode = self.group_combo.currentIndex()
        self.prefix_spin.setVisible(mode == 0)
        self.group_spin.setVisible(mode == 1)

    def _on_size_combo_changed(self):
        """尺寸模式切换时显示/隐藏自定义宽度高度控件"""
        is_custom = self.size_combo.currentText() == "自定义"
        self.size_widget.setVisible(is_custom)


def build_panel() -> QWidget:
    """构建面板实例"""
    return GifMakerPanel()


def collect_settings(panel: GifMakerPanel) -> dict:
    """收集面板设置"""
    width_text = panel.width_spin.text().strip()
    height_text = panel.height_spin.text().strip()
    if width_text.endswith(" px"):
        width_text = width_text[:-3]
    if height_text.endswith(" px"):
        height_text = height_text[:-3]
    return {
        "group_combo": panel.group_combo.currentIndex(),
        "prefix_len": panel.prefix_spin.value(),
        "group_size": panel.group_spin.value(),
        "duration_spin": panel.duration_spin.value(),
        "loop_spin": panel.loop_spin.value(),
        "size_combo": panel.size_combo.currentText(),
        "width_spin": width_text,
        "height_spin": height_text,
    }


def prepare_preview(items, settings):
    """生成预览信息"""
    group_combo = settings.get("group_combo", 0)
    prefix_len = settings.get("prefix_len", 9)
    group_size = settings.get("group_size", 5)
    duration_spin = settings.get("duration_spin", 300)
    loop_spin = "无限" if settings.get("loop_spin", 0) == 0 else f"{settings.get('loop_spin')}次"
    size_combo = settings.get("size_combo", "保持原尺寸")
    if size_combo == "自定义":
        w = settings.get("width_spin", "640")
        h = settings.get("height_spin", "480")
        size_desc = f"自定义 {w}x{h}"
    else:
        size_desc = "原尺寸"

    file_paths = [it.input_path for it in items]
    groups = {}
    for it in items:
        key = get_group_key(it.input_path, group_combo, prefix_len, group_size, file_paths)
        groups.setdefault(key, []).append(it.input_path)

    for it in items:
        key = get_group_key(it.input_path, group_combo, prefix_len, group_size, file_paths)
        display_key = "全部文件" if key == "__all__" else (os.path.basename(key) if group_combo == 2 else key)
        count = len(groups[key])
        it.preview_extra = {
            "A": f"合成GIF：组「{display_key}」{count}张，帧{duration_spin}ms，循环{loop_spin}，尺寸{size_desc}"
        }
        it.preview_extra["group_key"] = display_key


def run_batch(items, settings, get_output_dir, get_output_name_for_group,
              log_callback=None, progress_callback=None, stop_check=None):
    """批量合成 GIF"""
    if not items:
        return []

    group_combo = settings.get("group_combo", 0)
    prefix_len = settings.get("prefix_len", 9)
    group_size = settings.get("group_size", 5)
    duration_spin = settings.get("duration_spin", 300)
    loop_spin = settings.get("loop_spin", 0)
    size_combo = settings.get("size_combo", "保持原尺寸")
    try:
        target_w = int(settings.get("width_spin") or 1920)
    except ValueError:
        target_w = 1920
    try:
        target_h = int(settings.get("height_spin") or 1080)
    except ValueError:
        target_h = 1080

    file_paths = [it.input_path for it in items]
    groups = {}
    for item in items:
        key = get_group_key(item.input_path, group_combo, prefix_len, group_size, file_paths)
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

        out_dir = get_output_dir(group_items[0])
        if group_key == "__all__":
            base_name = get_output_name_for_group("全部")
        elif group_combo == 2:
            base_name = get_output_name_for_group(os.path.basename(group_key))
        else:
            base_name = get_output_name_for_group(group_key)

        if not base_name.endswith(".gif"):
            base_name = f"{base_name}.gif"

        base, ext = os.path.splitext(base_name)
        out_path = get_unique_file_path(out_dir, base, ext)

        images = []
        for fi in group_items:
            img = Image.open(fi.input_path)
            if img.mode == "RGBA":
                img = img.convert("RGB")
            if size_combo == "自定义":
                img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            images.append(img)

        if images:
            images[0].save(
                out_path,
                save_all=True,
                append_images=images[1:],
                duration=duration_spin,
                loop=loop_spin,
                format="GIF",
                disposal=2
            )

        output_files.append(out_path)

        for fi in group_items:
            fi.status = "完成"
            fi.output_name = os.path.basename(out_path)
            fi.output_dir = out_dir

    return output_files


def run_task(file_item, settings):
    """GIF 合成不支持单任务模式"""
    raise NotImplementedError("GIF 合成功能请使用 run_batch，不要使用 run_task")
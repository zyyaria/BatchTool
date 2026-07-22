# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
from core.utils import ensure_image_mode
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox,
    QSizePolicy
)

try:
    from PIL import Image
except ImportError:
    Image = None


class SplitPanel(QWidget):
    changed = Signal()

    def __init__(self):
        """初始化设置面板"""
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        row_mode = QHBoxLayout()
        self.split_combo = QComboBox()
        self.split_combo.addItems(["横向", "竖向", "网格"])
        self.split_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_mode.addWidget(QLabel("分切模式:"))
        row_mode.addWidget(self.split_combo, 1)
        layout.addLayout(row_mode)

        row_split = QHBoxLayout()
        self.row_widget = QWidget()
        self.row_spin = QSpinBox()
        self.row_spin.setRange(2, 10)
        self.row_spin.setValue(2)
        self.row_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_layout = QHBoxLayout(self.row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(QLabel("分切行数:"))
        row_layout.addWidget(self.row_spin, 1)        
        self.col_widget = QWidget()
        self.col_spin = QSpinBox()
        self.col_spin.setRange(2, 10)
        self.col_spin.setValue(2)
        self.col_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        col_layout = QHBoxLayout(self.col_widget)
        col_layout.setContentsMargins(0, 0, 0, 0)
        col_layout.addWidget(QLabel("分切列数:"))
        col_layout.addWidget(self.col_spin, 1)        
        self.grid_widget = QWidget()
        self.grid_row_spin = QSpinBox()
        self.grid_row_spin.setRange(2, 10)
        self.grid_row_spin.setValue(2)
        self.grid_row_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.grid_col_spin = QSpinBox()
        self.grid_col_spin.setRange(2, 10)
        self.grid_col_spin.setValue(2)
        self.grid_col_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_layout = QHBoxLayout(self.grid_widget)        
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.addWidget(QLabel("行数:"))
        grid_layout.addWidget(self.grid_row_spin, 1)
        grid_layout.addWidget(QLabel("列数:"))
        grid_layout.addWidget(self.grid_col_spin, 1)        
        row_split.addWidget(self.row_widget)
        row_split.addWidget(self.col_widget)
        row_split.addWidget(self.grid_widget)
        layout.addLayout(row_split)

        row_format = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["原格式", "PNG", "JPG", "WEBP"])
        self.format_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_format.addWidget(QLabel("目标格式:"))
        row_format.addWidget(self.format_combo, 1)   
        layout.addLayout(row_format)

        layout.addStretch()

        self.split_combo.currentIndexChanged.connect(self._on_split_combo_changed)
        self.split_combo.currentIndexChanged.connect(self.changed)
        self.format_combo.currentIndexChanged.connect(self.changed)
        self.row_spin.valueChanged.connect(self.changed)
        self.col_spin.valueChanged.connect(self.changed)
        self.grid_row_spin.valueChanged.connect(self.changed)
        self.grid_col_spin.valueChanged.connect(self.changed)

        self._on_split_combo_changed()

    def _on_split_combo_changed(self):
        """分切模式切换"""
        mode = self.split_combo.currentIndex()
        self.row_widget.setVisible(mode == 0)
        self.col_widget.setVisible(mode == 1)
        self.grid_widget.setVisible(mode == 2)


def build_panel() -> QWidget:
    """构建面板实例"""
    return SplitPanel()


def collect_settings(panel: SplitPanel) -> dict:
    """收集面板设置"""
    mode = panel.split_combo.currentIndex()
    if mode == 2:
        rows = panel.grid_row_spin.value()
        cols = panel.grid_col_spin.value()
    else:
        rows = panel.row_spin.value() if mode == 0 else 1
        cols = panel.col_spin.value() if mode == 1 else 1
    return {
        "mode": mode,
        "mode_text": panel.split_combo.currentText(),
        "rows": rows,
        "cols": cols,
        "target_format": panel.format_combo.currentText(),
    }


def prepare_preview(items, settings):
    """生成预览信息"""
    mode = settings.get("mode", 0)
    fmt = settings.get("target_format", "原格式")
    for it in items:
        if mode == 0:
            mode_text = "横向（2行）"
        elif mode == 1:
            mode_text = "竖向（2列）"
        elif mode == 2:
            rows = settings.get("rows", 2)
            cols = settings.get("cols", 3)
            mode_text = f"网格 {rows}×{cols}"
        else:
            mode_text = "未知"
        it.preview_extra = {"A": f"分切：{mode_text}，输出格式{fmt if fmt!='原格式' else '原格式'}"}


def run_task(file_item, settings, custom_names=None):
    """执行单个图片分切任务"""
    file_item.output_paths = []
    if Image is None:
        raise RuntimeError("缺少 Pillow 库，请安装: pip install Pillow")
    src = file_item.input_path
    mode = settings.get("mode", 0)
    rows = settings.get("rows", 2)
    cols = settings.get("cols", 3)
    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)
    try:
        im = Image.open(src)
    except Exception as e:
        raise RuntimeError(f"无法打开图片: {e}")
    w, h = im.size
    parts = []
    if mode == 0:
        half_h = h // 2
        parts = [(0, 0, w, half_h), (0, half_h, w, h)]
    elif mode == 1:
        half_w = w // 2
        parts = [(0, 0, half_w, h), (half_w, 0, w, h)]
    elif mode == 2:
        seg_w = w // cols
        seg_h = h // rows
        for row in range(rows):
            for col in range(cols):
                x1 = col * seg_w
                y1 = row * seg_h
                x2 = (col + 1) * seg_w if col < cols - 1 else w
                y2 = (row + 1) * seg_h if row < rows - 1 else h
                parts.append((x1, y1, x2, y2))
    else:
        raise RuntimeError("不支持的分切模式")
    out_name = file_item.output_name
    ext = os.path.splitext(out_name)[1][1:].lower()
    if not ext:
        ext = "png"
    base_name = os.path.splitext(out_name)[0]
    saved_files = []
    for idx, (x1, y1, x2, y2) in enumerate(parts, start=1):
        cropped = im.crop((x1, y1, x2, y2))
        if custom_names and idx - 1 < len(custom_names):
            name = custom_names[idx - 1]
        else:
            if mode == 2:
                row = (idx - 1) // cols + 1
                col = (idx - 1) % cols + 1
                name = f"{base_name}_r{row}_c{col}"
            else:
                name = f"{base_name}_part_{idx}"
        out_name = f"{name}.{ext}"
        out_path = os.path.join(out_dir, out_name)
        cropped = ensure_image_mode(cropped, ext, fill_white=True)
        save_format = ext.upper()
        if save_format == "JPG":
            save_format = "JPEG"
        cropped.save(out_path, format=save_format, quality=95, optimize=True)
        saved_files.append(out_path)
        file_item.output_paths.append(out_path)
    im.close()
    if saved_files:
        file_item.output_name = os.path.basename(saved_files[0])
        file_item.status = f"完成（生成 {len(saved_files)} 个文件）"
    else:
        file_item.status = "错误（未生成任何文件）"
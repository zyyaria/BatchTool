# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
from core.utils import ensure_image_mode
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox
)


try:
    from PIL import Image
except ImportError:
    Image = None


class SplitPanel(QWidget):
    changed = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("分切模式:"))
        self.mode = QComboBox()
        self.mode.addItems(["水平（上下切）", "垂直（左右切）", "网格"])
        self.mode.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self.mode, 1)
        layout.addLayout(mode_row)

        self.grid_row = QHBoxLayout()
        self.grid_row.addWidget(QLabel("行数:"))
        self.row_spin = QSpinBox()
        self.row_spin.setRange(1, 20)
        self.row_spin.setValue(2)
        self.row_spin.setFixedWidth(110)
        self.grid_row.addWidget(self.row_spin)

        self.grid_row.addStretch(1)

        self.grid_row.addWidget(QLabel("列数:"))
        self.col_spin = QSpinBox()
        self.col_spin.setRange(1, 20)
        self.col_spin.setValue(3)
        self.col_spin.setFixedWidth(110)
        self.grid_row.addWidget(self.col_spin)

        self._hide_grid_row(True)
        layout.addLayout(self.grid_row)

        layout.addStretch()

        self.mode.currentIndexChanged.connect(self.changed)
        self.row_spin.valueChanged.connect(self.changed)
        self.col_spin.valueChanged.connect(self.changed)

        self._on_mode_changed()

    def _hide_grid_row(self, hidden):
        """隐藏或显示整行网格参数"""
        for i in range(self.grid_row.count()):
            widget = self.grid_row.itemAt(i).widget()
            if widget:
                widget.setVisible(not hidden)

    def _on_mode_changed(self):
        is_grid = self.mode.currentIndex() == 2
        self._hide_grid_row(not is_grid)


def build_panel() -> QWidget:
    return SplitPanel()


def collect_settings(panel: SplitPanel) -> dict:
    return {
        "mode": panel.mode.currentIndex(),
        "mode_text": panel.mode.currentText(),
        "rows": panel.row_spin.value(),
        "cols": panel.col_spin.value(),
    }


def prepare_preview(items, settings):
    mode = settings.get("mode", 0)
    if mode == 2:
        rows = settings.get("rows", 2)
        cols = settings.get("cols", 3)
        mode_text = f"网格 {rows}×{cols}"
    else:
        mode_text = settings.get("mode_text", "水平")
    for it in items:
        it.preview_extra = {"A": f"分切: {mode_text}"}


def run_task(file_item, settings, custom_names=None):
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

    ext = os.path.splitext(src)[1][1:].lower()
    if not ext:
        ext = "png"

    base_name = os.path.splitext(file_item.output_name)[0] if file_item.output_name else os.path.splitext(os.path.basename(src))[0]

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
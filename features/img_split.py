# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QSpinBox, QDoubleSpinBox, QPushButton, QButtonGroup, QRadioButton, 
    QSizePolicy
)
from core.utils import ensure_image_mode

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
        self.mode_group = QButtonGroup(self)
        self.btn_split = QPushButton("分切")
        self.btn_split.setCheckable(True)
        self.btn_split.setChecked(True)
        self.btn_split.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_crop = QPushButton("裁剪")
        self.btn_crop.setCheckable(True)
        self.btn_crop.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.mode_group.addButton(self.btn_split)
        self.mode_group.addButton(self.btn_crop)
        row_mode.addWidget(QLabel("模式:"))
        row_mode.addWidget(self.btn_split, 1)
        row_mode.addWidget(self.btn_crop, 1)
        layout.addLayout(row_mode)

        self.split_widget = QWidget()
        split_layout = QHBoxLayout(self.split_widget)
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.addWidget(QLabel("行数:"))
        self.split_row_spin = QSpinBox()
        self.split_row_spin.setRange(1, 99)
        self.split_row_spin.setValue(2)
        self.split_row_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        split_layout.addWidget(self.split_row_spin, 1)
        split_layout.addWidget(QLabel("列数:"))
        self.split_col_spin = QSpinBox()
        self.split_col_spin.setRange(1, 99)
        self.split_col_spin.setValue(2)
        self.split_col_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        split_layout.addWidget(self.split_col_spin, 1)
        layout.addWidget(self.split_widget)

        self.crop_widget = QWidget()
        crop_layout = QVBoxLayout(self.crop_widget)
        crop_layout.setContentsMargins(0, 0, 0, 0)
        crop_layout.setSpacing(8)

        row_crop_type = QHBoxLayout()
        self.radio_ratio = QRadioButton("比例")
        self.radio_ratio.setChecked(True)
        self.radio_size = QRadioButton("尺寸")
        row_crop_type.addWidget(QLabel("裁剪方式:"))
        row_crop_type.addWidget(self.radio_ratio)
        row_crop_type.addWidget(self.radio_size)
        row_crop_type.addStretch()
        crop_layout.addLayout(row_crop_type)

        self.ratio_widget = QWidget()
        ratio_layout = QHBoxLayout(self.ratio_widget)
        ratio_layout.setContentsMargins(0, 0, 0, 0)
        self.ratio_combo = QComboBox()
        self.ratio_combo.addItems(["1:1", "4:3", "16:9", "3:4", "9:16", "自定义"])
        self.ratio_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        ratio_layout.addWidget(QLabel("裁剪比例:"))
        ratio_layout.addWidget(self.ratio_combo, 1)
        crop_layout.addWidget(self.ratio_widget)

        self.ratio_custom_widget = QWidget()
        ratio_custom_layout = QHBoxLayout(self.ratio_custom_widget)
        ratio_custom_layout.setContentsMargins(0, 0, 0, 0)
        self.ratio_w_spin = QDoubleSpinBox()
        self.ratio_w_spin.setRange(0.1, 999.9)
        self.ratio_w_spin.setValue(2.0)
        self.ratio_w_spin.setSingleStep(0.1)
        self.ratio_w_spin.setDecimals(1)
        self.ratio_w_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.ratio_h_spin = QDoubleSpinBox()
        self.ratio_h_spin.setRange(0.1, 999.9)
        self.ratio_h_spin.setValue(1.0)
        self.ratio_h_spin.setSingleStep(0.1)
        self.ratio_h_spin.setDecimals(1)
        self.ratio_h_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        ratio_custom_layout.addWidget(QLabel("宽度:"))
        ratio_custom_layout.addWidget(self.ratio_w_spin, 1)
        ratio_custom_layout.addWidget(QLabel("高度:"))
        ratio_custom_layout.addWidget(self.ratio_h_spin, 1)
        self.ratio_custom_widget.setVisible(False)
        crop_layout.addWidget(self.ratio_custom_widget)

        self.size_widget = QWidget()
        size_layout = QHBoxLayout(self.size_widget)
        size_layout.setContentsMargins(0, 0, 0, 0)
        self.size_combo = QComboBox()
        self.size_combo.addItems([
            "小一寸（22×32mm）",
            "一寸（25×35mm）",
            "大一寸（33×48mm）",
            "小二寸（35×45mm）",
            "二寸（35×49mm）",
            "大二寸（35×53mm）",
            "自定义"
        ])
        self.size_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        size_layout.addWidget(QLabel("裁剪尺寸:"))
        size_layout.addWidget(self.size_combo, 1)
        self.size_widget.setVisible(False)
        crop_layout.addWidget(self.size_widget)

        self.size_custom_widget = QWidget()
        size_custom_layout = QHBoxLayout(self.size_custom_widget)
        size_custom_layout.setContentsMargins(0, 0, 0, 0)
        self.size_w_spin = QSpinBox()
        self.size_w_spin.setRange(1, 9999)
        self.size_w_spin.setValue(55)
        self.size_w_spin.setSuffix(" mm")
        self.size_w_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.size_h_spin = QSpinBox()
        self.size_h_spin.setRange(1, 9999)
        self.size_h_spin.setValue(84)
        self.size_h_spin.setSuffix(" mm")
        self.size_h_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        size_custom_layout.addWidget(QLabel("宽度:"))
        size_custom_layout.addWidget(self.size_w_spin, 1)
        size_custom_layout.addWidget(QLabel("高度:"))
        size_custom_layout.addWidget(self.size_h_spin, 1)
        crop_layout.addWidget(self.size_custom_widget)

        row_position = QHBoxLayout()
        self.position_combo = QComboBox()
        self.position_combo.addItems(["居中", "左上", "右上", "左下", "右下"])
        self.position_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_position.addWidget(QLabel("裁剪位置:"))
        row_position.addWidget(self.position_combo, 1)
        crop_layout.addLayout(row_position)

        layout.addWidget(self.crop_widget)

        row_format = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["原格式", "PNG", "JPG", "WEBP"])
        self.format_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_format.addWidget(QLabel("目标格式:"))
        row_format.addWidget(self.format_combo, 1)
        layout.addLayout(row_format)

        layout.addStretch()

        self.btn_split.clicked.connect(self._on_mode_changed)
        self.btn_crop.clicked.connect(self._on_mode_changed)
        self.radio_ratio.toggled.connect(self._on_crop_type_changed)
        self.radio_size.toggled.connect(self._on_crop_type_changed)
        self.ratio_combo.currentIndexChanged.connect(self._on_ratio_mode_changed)
        self.size_combo.currentIndexChanged.connect(self._on_size_mode_changed)

        self.split_row_spin.valueChanged.connect(self.changed)
        self.split_col_spin.valueChanged.connect(self.changed)
        self.ratio_w_spin.valueChanged.connect(self.changed)
        self.ratio_h_spin.valueChanged.connect(self.changed)
        self.size_w_spin.valueChanged.connect(self.changed)
        self.size_h_spin.valueChanged.connect(self.changed)
        self.position_combo.currentIndexChanged.connect(self.changed)
        self.format_combo.currentIndexChanged.connect(self.changed)

        self._on_mode_changed()
        self._on_crop_type_changed()
        self._on_ratio_mode_changed()
        self._on_size_mode_changed()

    def _on_mode_changed(self):
        """操作模式切换"""
        is_split = self.btn_split.isChecked()
        self.split_widget.setVisible(is_split)
        self.crop_widget.setVisible(not is_split)
        self.changed.emit()

    def _on_crop_type_changed(self):
        """裁剪方式切换"""
        is_ratio = self.radio_ratio.isChecked()
        self.ratio_widget.setVisible(is_ratio)
        self.ratio_custom_widget.setVisible(is_ratio and self.ratio_combo.currentText() == "自定义")
        self.size_widget.setVisible(not is_ratio)
        is_size_custom = (not is_ratio) and self.size_combo.currentText() == "自定义"
        self.size_custom_widget.setVisible(is_size_custom)
        self.changed.emit()

    def _on_ratio_mode_changed(self):
        """比例下拉框切换"""
        is_custom = self.ratio_combo.currentText() == "自定义"
        self.ratio_custom_widget.setVisible(is_custom and self.radio_ratio.isChecked())
        self.changed.emit()

    def _on_size_mode_changed(self):
        """尺寸下拉框切换"""
        is_custom = self.size_combo.currentText() == "自定义"
        self.size_custom_widget.setVisible(is_custom and self.radio_size.isChecked())
        self.changed.emit()

    def _get_crop_size_mm(self) -> tuple:
        """获取尺寸模式的宽高"""
        text = self.size_combo.currentText()
        if text == "自定义":
            return self.size_w_spin.value(), self.size_h_spin.value()
        import re
        match = re.search(r'（([\d.]+)×([\d.]+)mm）', text)
        if match:
            return int(float(match.group(1))), int(float(match.group(2)))
        return 25, 35

    def _get_crop_ratio(self) -> tuple:
        """获取比例模式的宽高比"""
        text = self.ratio_combo.currentText()
        if text == "自定义":
            return self.ratio_w_spin.value(), self.ratio_h_spin.value()
        parts = text.split(":")
        if len(parts) == 2:
            return float(parts[0]), float(parts[1])
        return 1.0, 1.0


def build_panel() -> QWidget:
    """构建面板实例"""
    return SplitPanel()


def collect_settings(panel: SplitPanel) -> dict:
    """收集面板设置"""
    is_split = panel.btn_split.isChecked()
    is_ratio = panel.radio_ratio.isChecked()
    size_w, size_h = panel._get_crop_size_mm()
    ratio_w, ratio_h = panel._get_crop_ratio()
    return {
        "mode": "split" if is_split else "crop",
        "split_rows": panel.split_row_spin.value(),
        "split_cols": panel.split_col_spin.value(),
        "crop_type": "ratio" if is_ratio else "size",
        "ratio_w": ratio_w,
        "ratio_h": ratio_h,
        "size_w": size_w,
        "size_h": size_h,
        "position": panel.position_combo.currentText(),
        "target_format": panel.format_combo.currentText(),
    }


def prepare_preview(items, settings):
    """生成预览信息"""
    mode = settings.get("mode", "split")
    fmt = settings.get("target_format", "原格式")
    for it in items:
        base_name = os.path.splitext(os.path.basename(it.input_path))[0]
        ext = fmt.lower() if fmt != "原格式" else (os.path.splitext(it.input_path)[1][1:].lower() or "png")
        if mode == "split":
            it.output_name = f"{base_name}.{ext}"
        else:
            it.output_name = f"{base_name}_裁剪.{ext}"
        it.locked_name = True
        if mode == "split":
            rows = settings.get("split_rows", 2)
            cols = settings.get("split_cols", 2)
            mode_text = f"分切: {rows}×{cols}"
        else:
            crop_type = settings.get("crop_type", "ratio")
            pos = settings.get("position", "居中")
            if crop_type == "ratio":
                rw = settings.get("ratio_w", 1.0)
                rh = settings.get("ratio_h", 1.0)
                mode_text = f"裁剪比例: {rw}:{rh}（位置: {pos}）"
            else:
                sw = settings.get("size_w", 25.0)
                sh = settings.get("size_h", 35.0)
                mode_text = f"裁剪尺寸: {sw:.1f}×{sh:.1f}mm（位置: {pos}；300 DPI）"
        fmt_display = fmt if fmt != "原格式" else "原格式"
        it.preview_extra = {"A": f"{mode_text}；输出格式: {fmt_display}"}


def run_task(file_item, settings, custom_names=None):
    """执行单个图片分切/裁剪任务"""
    from core.utils import get_unique_file_path
    file_item.output_paths = []
    if Image is None:
        raise RuntimeError("缺少 Pillow 库，请安装: pip install Pillow")
    src = file_item.input_path
    mode = settings.get("mode", "split")
    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)
    try:
        im = Image.open(src)
    except Exception as e:
        raise RuntimeError(f"无法打开图片: {e}")
    w, h = im.size
    src_base = os.path.splitext(os.path.basename(src))[0]
    ext = settings.get("target_format", "原格式")
    ext = ext.lower() if ext != "原格式" else (os.path.splitext(src)[1][1:].lower() or "png")
    if mode == "split":
        rows = settings.get("split_rows", 2)
        cols = settings.get("split_cols", 2)
        seg_w = w // cols
        seg_h = h // rows
        saved_files = []
        idx = 1
        first_out_path = None
        for row in range(rows):
            for col in range(cols):
                x1 = col * seg_w
                y1 = row * seg_h
                x2 = (col + 1) * seg_w if col < cols - 1 else w
                y2 = (row + 1) * seg_h if row < rows - 1 else h
                cropped = im.crop((x1, y1, x2, y2))
                if custom_names and idx - 1 < len(custom_names):
                    name = custom_names[idx - 1]
                else:
                    name = f"{src_base}_r{row + 1}_c{col + 1}"
                out_path = get_unique_file_path(out_dir, name, f".{ext}")
                if first_out_path is None:
                    first_out_path = out_path
                cropped = ensure_image_mode(cropped, ext, fill_white=True)
                save_format = ext.upper()
                if save_format == "JPG":
                    save_format = "JPEG"
                cropped.save(out_path, format=save_format, quality=95, optimize=True)
                saved_files.append(out_path)
                file_item.output_paths.append(out_path)
                idx += 1
        im.close()
        file_item.output_name = os.path.basename(first_out_path) if first_out_path else f"{src_base}.{ext}"
        file_item.locked_name = True
        file_item.status = f"完成（生成 {len(saved_files)} 个文件）"
        return
    else:
        crop_type = settings.get("crop_type", "ratio")
        pos = settings.get("position", "居中")
        if crop_type == "ratio":
            rw = settings.get("ratio_w", 1.0)
            rh = settings.get("ratio_h", 1.0)
            if w / h > rw / rh:
                crop_h = h
                crop_w = int(h * rw / rh)
            else:
                crop_w = w
                crop_h = int(w * rh / rw)
            crop_w = min(crop_w, w)
            crop_h = min(crop_h, h)
            if pos == "居中":
                x1 = (w - crop_w) // 2
                y1 = (h - crop_h) // 2
            elif pos == "左上":
                x1, y1 = 0, 0
            elif pos == "右上":
                x1, y1 = w - crop_w, 0
            elif pos == "左下":
                x1, y1 = 0, h - crop_h
            elif pos == "右下":
                x1, y1 = w - crop_w, h - crop_h
            else:
                x1 = (w - crop_w) // 2
                y1 = (h - crop_h) // 2
            cropped = im.crop((x1, y1, x1 + crop_w, y1 + crop_h))
        else:
            size_w_mm = settings.get("size_w", 25)
            size_h_mm = settings.get("size_h", 35)
            if size_w_mm <= 0:
                size_w_mm = 25
            if size_h_mm <= 0:
                size_h_mm = 35
            TARGET_DPI = 300
            target_w_px = int(size_w_mm / 25.4 * TARGET_DPI)
            target_h_px = int(size_h_mm / 25.4 * TARGET_DPI)
            scale = max(target_w_px / w, target_h_px / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            im_scaled = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
            if pos == "居中":
                x1 = (new_w - target_w_px) // 2
                y1 = (new_h - target_h_px) // 2
            elif pos == "左上":
                x1, y1 = 0, 0
            elif pos == "右上":
                x1, y1 = new_w - target_w_px, 0
            elif pos == "左下":
                x1, y1 = 0, new_h - target_h_px
            elif pos == "右下":
                x1, y1 = new_w - target_w_px, new_h - target_h_px
            else:
                x1 = (new_w - target_w_px) // 2
                y1 = (new_h - target_h_px) // 2
            cropped = im_scaled.crop((x1, y1, x1 + target_w_px, y1 + target_h_px))
        out_path = get_unique_file_path(out_dir, f"{src_base}_裁剪", f".{ext}")
        cropped = ensure_image_mode(cropped, ext, fill_white=True)
        save_format = ext.upper()
        if save_format == "JPG":
            save_format = "JPEG"
        if crop_type == "size":
            cropped.save(out_path, format=save_format, quality=95, optimize=True, dpi=(TARGET_DPI, TARGET_DPI))
        else:
            cropped.save(out_path, format=save_format, quality=95, optimize=True)
        im.close()
        file_item.output_name = os.path.basename(out_path)
        file_item.locked_name = True
        file_item.output_paths = [out_path]
        file_item.status = "完成"
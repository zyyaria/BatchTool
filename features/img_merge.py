# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
from PIL import Image, ImageDraw, ImageFont
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox,
    QPushButton, QSizePolicy, QColorDialog, QCheckBox, QLineEdit
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

        row_size = QHBoxLayout()
        self.size_combo = QComboBox()
        self.size_combo.addItems(["保持原尺寸", "自定义"])
        self.size_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.aspect_check = QCheckBox("保持比例")
        self.aspect_check.setChecked(True)
        self.aspect_check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row_size.addWidget(QLabel("目标尺寸:"))
        row_size.addWidget(self.size_combo, 1)
        row_size.addWidget(self.aspect_check)
        layout.addLayout(row_size)

        self.size_widget = QWidget()
        self.size_widget.setContentsMargins(0, 0, 0, 0)
        row_csize = QHBoxLayout(self.size_widget)
        row_csize.setContentsMargins(0, 0, 0, 0)        
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
        row_csize.addWidget(QLabel("宽度:"))
        row_csize.addWidget(self.width_spin, 1)
        row_csize.addWidget(QLabel("高度:"))
        row_csize.addWidget(self.height_spin, 1)
        layout.addWidget(self.size_widget)

        row_merge = QHBoxLayout()
        self.merge_combo = QComboBox()
        self.merge_combo.addItems(["垂直", "水平", "网格", "台词"])
        self.merge_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.color_btn = QPushButton()
        self.color_btn.setStyleSheet(
            "background-color: #FFFFFF; "
            "border: 1px solid #ccc; "
            "border-radius: 3px; "
            "height: 14px; "
            "min-height: 14px; "
            "max-height: 14px; "
            "width: 20px; "
            "min-width: 20px; "
            "max-width: 20px;"
        )
        self.color_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row_merge.addWidget(QLabel("拼接方式:"))
        row_merge.addWidget(self.merge_combo, 1)
        row_merge.addWidget(QLabel("背景色:"))
        row_merge.addWidget(self.color_btn)
        layout.addLayout(row_merge)

        row_pagram = QHBoxLayout()
        self.spacing_widget = QWidget()
        self.spacing_label = QLabel("间距:")
        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(0, 200)
        self.spacing_spin.setValue(0)
        self.spacing_spin.setSuffix(" px")
        self.spacing_spin.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        spacing_layout = QHBoxLayout(self.spacing_widget)
        spacing_layout.setContentsMargins(0, 0, 0, 0)

        self.col_widget = QWidget()
        self.col_label = QLabel("列数:")
        self.col_spin = QSpinBox()
        self.col_spin.setRange(1, 20)
        self.col_spin.setValue(3)
        self.col_spin.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        col_layout = QHBoxLayout(self.col_widget)
        col_layout.setContentsMargins(0, 0, 0, 0)
        self.offset_widget = QWidget()
        self.offset_label = QLabel("偏移:")
        self.offset_spin = QSpinBox()
        self.offset_spin.setRange(-300, 300)
        self.offset_spin.setValue(-150)
        self.offset_spin.setSuffix(" px")
        self.offset_spin.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        offset_layout = QHBoxLayout(self.offset_widget)
        offset_layout.setContentsMargins(0, 0, 0, 0)
        spacing_layout.addWidget(self.spacing_label)
        spacing_layout.addWidget(self.spacing_spin, 1)        
        col_layout.addWidget(self.col_label)
        col_layout.addWidget(self.col_spin, 1)   
        offset_layout.addWidget(self.offset_label)
        offset_layout.addWidget(self.offset_spin, 1)
        row_pagram.addWidget(self.spacing_widget, 1)
        row_pagram.addWidget(self.col_widget, 1)
        row_pagram.addWidget(self.offset_widget, 1)
        layout.addLayout(row_pagram)

        row_format = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG", "WEBP"])
        self.format_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_format.addWidget(QLabel("目标格式:"))
        row_format.addWidget(self.format_combo, 1)
        layout.addLayout(row_format)

        tag_label = QLabel("标签设置（可选）：")
        tag_label.setStyleSheet("font-weight: 600; margin-top: 4px; margin-left: -3px;")
        tag_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(tag_label)

        row_tag = QHBoxLayout()
        self.index_check = QCheckBox("添加序号")
        self.index_check.setChecked(False)
        self.index_check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.filename_check = QCheckBox("添加文件名")
        self.filename_check.setChecked(False)
        self.filename_check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row_tag.addWidget(QLabel("标签:"))
        row_tag.addWidget(self.index_check)
        row_tag.addWidget(self.filename_check)
        row_tag.addStretch()
        layout.addLayout(row_tag)

        row_tag_pos = QHBoxLayout()
        self.tag_pos_combo = QComboBox()
        self.tag_pos_combo.addItems(["每张图下方", "每张图上方"])
        self.tag_pos_combo.setCurrentIndex(1)
        self.tag_pos_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_tag_pos.addWidget(QLabel("位置:"))
        row_tag_pos.addWidget(self.tag_pos_combo, 1)
        layout.addLayout(row_tag_pos)

        row_tag_size = QHBoxLayout()
        self.tag_height_spin = QSpinBox()
        self.tag_height_spin.setRange(10, 100)
        self.tag_height_spin.setValue(40)
        self.tag_height_spin.setSuffix(" px")
        self.tag_height_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.tag_size_spin = QSpinBox()
        self.tag_size_spin.setRange(8, 48)
        self.tag_size_spin.setValue(24)
        self.tag_size_spin.setSuffix(" pt")
        self.tag_size_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_tag_size.addWidget(QLabel("高度:"))
        row_tag_size.addWidget(self.tag_height_spin, 1)
        row_tag_size.addWidget(QLabel("大小:"))
        row_tag_size.addWidget(self.tag_size_spin, 1)
        layout.addLayout(row_tag_size)

        title_label = QLabel("标题设置（可选）：")
        title_label.setStyleSheet("font-weight: 600; margin-top: 4px; margin-left: -3px;")
        title_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(title_label)

        row_title = QHBoxLayout()
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("输入标题（留空则不显示）")
        self.title_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_title.addWidget(QLabel("标题:"))
        row_title.addWidget(self.title_edit, 1)
        layout.addLayout(row_title)

        row_title_pos = QHBoxLayout()
        self.title_pos_combo = QComboBox()
        self.title_pos_combo.addItems(["顶部", "底部"])
        self.title_pos_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_title_pos.addWidget(QLabel("位置:"))
        row_title_pos.addWidget(self.title_pos_combo, 1)
        layout.addLayout(row_title_pos)

        row_title_size = QHBoxLayout()
        self.title_height_spin = QSpinBox()
        self.title_height_spin.setRange(20, 200)
        self.title_height_spin.setValue(60)
        self.title_height_spin.setSuffix(" px")
        self.title_height_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.title_size_spin = QSpinBox()
        self.title_size_spin.setRange(10, 72)
        self.title_size_spin.setValue(32)
        self.title_size_spin.setSuffix(" pt")
        self.title_size_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_title_size.addWidget(QLabel("高度:"))
        row_title_size.addWidget(self.title_height_spin, 1)
        row_title_size.addWidget(QLabel("大小:"))
        row_title_size.addWidget(self.title_size_spin, 1)
        layout.addLayout(row_title_size)
        
        layout.addStretch()

        self.group_combo.currentIndexChanged.connect(self._on_group_changed)
        self.group_combo.currentIndexChanged.connect(self.changed)
        self.prefix_spin.valueChanged.connect(self.changed)
        self.interval_spin.valueChanged.connect(self.changed)
        self.size_combo.currentIndexChanged.connect(self._on_size_changed)
        self.size_combo.currentIndexChanged.connect(self.changed)
        self.width_spin.valueChanged.connect(self.changed)
        self.height_spin.valueChanged.connect(self.changed)
        self.aspect_check.stateChanged.connect(self.changed)
        self.merge_combo.currentIndexChanged.connect(self._on_stitch_merge_changed)
        self.merge_combo.currentIndexChanged.connect(self.changed)
        self.color_btn.clicked.connect(lambda: self._choose_color(self.color_btn))
        self.color_btn.clicked.connect(self.changed)
        self.spacing_spin.valueChanged.connect(self.changed)
        self.col_spin.valueChanged.connect(self.changed)
        self.offset_spin.valueChanged.connect(self.changed)
        self.format_combo.currentIndexChanged.connect(self.changed)
        self.index_check.stateChanged.connect(self.changed)
        self.filename_check.stateChanged.connect(self.changed)
        self.tag_pos_combo.currentIndexChanged.connect(self.changed)
        self.tag_height_spin.valueChanged.connect(self.changed)
        self.tag_size_spin.valueChanged.connect(self.changed)
        self.title_edit.textChanged.connect(self.changed)
        self.title_pos_combo.currentIndexChanged.connect(self.changed)
        self.title_height_spin.valueChanged.connect(self.changed)
        self.title_size_spin.valueChanged.connect(self.changed)

        self._on_group_changed()
        self._on_size_changed()
        self._on_stitch_merge_changed()

    def _on_group_changed(self):
        """分组方式切换"""
        mode = self.group_combo.currentIndex()
        self.prefix_spin.setVisible(mode == 0)
        self.interval_spin.setVisible(mode == 1)

    def _on_size_changed(self):
        """尺寸模式切换"""
        is_custom = self.size_combo.currentIndex() == 1
        self.size_widget.setVisible(is_custom)
        self.aspect_check.setVisible(is_custom)

    def _on_stitch_merge_changed(self):
        """拼接方式切换"""
        mode = self.merge_combo.currentText()
        is_grid = (mode == "网格")
        is_subtitle = (mode == "台词")
        self.spacing_widget.setVisible(True)
        self.col_widget.setVisible(is_grid)
        self.offset_widget.setVisible(is_subtitle)

    def _choose_color(self, btn):
        """颜色选择器"""
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name().upper()
            btn.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #ccc; border-radius: 3px;")
            btn.setProperty("color_hex", hex_color)
            self.changed.emit()


def build_panel() -> QWidget:
    """构建面板实例"""
    return MergePanel()


def collect_settings(panel: MergePanel) -> dict:
    """收集面板设置"""
    bg_hex = panel.color_btn.property("color_hex")
    if not bg_hex:
        bg_hex = "#FFFFFF"
    return {
        "group": panel.group_combo.currentIndex(),
        "prefix": panel.prefix_spin.value(),
        "interval": panel.interval_spin.value(),
        "size": panel.size_combo.currentIndex(),
        "target_width": panel.width_spin.value(),
        "target_height": panel.height_spin.value(),
        "keep_ratio": panel.aspect_check.isChecked(),
        "merge": panel.merge_combo.currentText(),
        "color": bg_hex,
        "spacing": panel.spacing_spin.value(),
        "grid": panel.col_spin.value(),
        "offset": panel.offset_spin.value(),
        "format": panel.format_combo.currentText().lower(),
        "index_check": panel.index_check.isChecked(),
        "filename_check": panel.filename_check.isChecked(),
        "tag_position": panel.tag_pos_combo.currentText(),
        "tag_height": panel.tag_height_spin.value(),
        "tag_size": panel.tag_size_spin.value(),
        "title": panel.title_edit.text().strip(),
        "title_position": panel.title_pos_combo.currentText(),
        "title_height": panel.title_height_spin.value(),
        "title_size": panel.title_size_spin.value(),
    }


def prepare_preview(items, settings):
    """生成预览信息"""
    group_idx = settings.get("group", 0)
    prefix = settings.get("prefix", 9)
    interval = settings.get("interval", 5)
    file_paths = [it.input_path for it in items]
    groups = {}
    for it in items:
        key = get_group_key(it.input_path, group_idx, prefix, interval, file_paths)
        groups.setdefault(key, []).append(it.input_path)
    for it in items:
        key = get_group_key(it.input_path, group_idx, prefix, interval, file_paths)
        display_key = "全部文件" if key == "__all__" else (os.path.basename(key) if group_idx == 2 else key)
        layout_text = settings.get("merge", "垂直")
        fmt = settings.get("format", "png").upper()
        it.preview_extra = {
            "A": f"拼接：{layout_text}，组「{display_key}」共 {len(groups[key])} 张，输出{fmt}"
        }
        it.preview_extra["group_key"] = display_key


def run_batch(items, settings, get_output_dir, get_output_name_for_group,
              log_callback=None, progress_callback=None, stop_check=None):
    """批量拼接图片"""
    if not items:
        return []
    group_idx = settings.get("group", 0)
    prefix = settings.get("prefix", 9)
    interval = settings.get("interval", 5)
    layout = settings.get("merge", "垂直")
    grid_cols = settings.get("grid", 3)
    subtitle_offset = settings.get("offset", -150)
    spacing = settings.get("spacing", 0)
    bg_color = settings.get("color", "#FFFFFF")
    format_combo = settings.get("format", "png")
    index_check = settings.get("index_check", False)
    filename_check = settings.get("filename_check", False)
    tag_position = settings.get("tag_position", "每张图上方")
    tag_height = settings.get("tag_height", 40)
    tag_size = settings.get("tag_size", 24)
    title_text = settings.get("title", "")
    title_position = settings.get("title_position", "顶部")
    title_height = settings.get("title_height", 60)
    title_font_size = settings.get("title_size", 32)
    size_idx = settings.get("size", 0)
    target_w = settings.get("target_width", 640)
    target_h = settings.get("target_height", 480)
    keep_ratio = settings.get("keep_ratio", True)
    custom_names = settings.get("custom_names", [])
    is_subtitle = (layout == "台词")
    if is_subtitle:
        spacing = 0
    file_paths = [it.input_path for it in items]
    groups = {}
    for item in items:
        key = get_group_key(item.input_path, group_idx, prefix, interval, file_paths)
        groups.setdefault(key, []).append(item)
    output_files = []
    processed = 0
    for group_key, group_items in groups.items():
        if stop_check and stop_check():
            if log_callback:
                log_callback("⛔ 用户终止任务")
            break
        if progress_callback:
            progress_callback(int(processed / len(groups) * 100))
        if log_callback:
            display_key = "全部文件" if group_key == "__all__" else group_key
            log_callback(f"正在拼接组：{display_key}（共 {len(group_items)} 张）")
        images = []
        for fi in group_items:
            try:
                im = Image.open(fi.input_path)
                if im.mode not in ("RGB", "RGBA"):
                    im = im.convert("RGBA")
                if size_idx == 1:
                    if keep_ratio:
                        im.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
                    else:
                        im = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
                images.append(im)
            except Exception as e:
                if log_callback:
                    log_callback(f"加载失败 {os.path.basename(fi.input_path)}: {e}")
                continue
        if not images:
            continue
        if is_subtitle:
            try:
                stitched = _stitch_subtitle(images, offset=subtitle_offset)
            except Exception as e:
                for fi in group_items:
                    fi.status = "错误"
                if log_callback:
                    log_callback(f"台词拼接组 {group_key} 失败: {e}")
                continue
        else:
            labels = []
            for idx, fi in enumerate(group_items, start=1):
                parts = []
                if index_check:
                    parts.append(str(idx))
                if filename_check:
                    base_name = os.path.splitext(os.path.basename(fi.input_path))[0]
                    parts.append(base_name)
                labels.append(" ".join(parts))
            try:
                stitched = _stitch_images(
                    images, labels,
                    layout=layout,
                    grid_cols=grid_cols,
                    spacing=spacing,
                    bg_color=bg_color,
                    tag_position=tag_position,
                    tag_height=tag_height,
                    tag_size=tag_size,
                    title_text=title_text,
                    title_position=title_position,
                    title_height=title_height,
                    title_font_size=title_font_size,
                    index_check=index_check,
                    filename_check=filename_check
                )
            except Exception as e:
                for fi in group_items:
                    fi.status = "错误"
                if log_callback:
                    log_callback(f"拼接组 {group_key} 失败: {e}")
                continue
        out_dir = get_output_dir(group_items[0])
        if group_key == "__all__":
            base_name = get_output_name_for_group("全部")
        elif group_idx == 2:
            base_name = get_output_name_for_group(os.path.basename(group_key))
        else:
            base_name = get_output_name_for_group(group_key)
        if custom_names and processed < len(custom_names):
            base_name = custom_names[processed]
        base, ext = os.path.splitext(base_name)
        out_path = get_unique_file_path(out_dir, base, f".{format_combo}")
        save_format = format_combo.upper()
        if save_format == "JPG":
            save_format = "JPEG"
        if save_format in ("JPEG", "BMP") and stitched.mode == "RGBA":
            bg = Image.new("RGB", stitched.size, (255, 255, 255))
            bg.paste(stitched, mask=stitched.split()[3])
            stitched = bg
        stitched.save(out_path, format=save_format, quality=90, optimize=True)
        stitched.close()
        for im in images:
            im.close()
        output_files.append(out_path)
        for fi in group_items:
            fi.status = "完成"
            fi.output_name = os.path.basename(out_path)
            fi.output_dir = out_dir
        processed += 1
    if log_callback:
        log_callback("✅ 全部拼接完成！")
    return output_files


def _detect_subtitle_region(img):
    """检测图片底部字幕区域"""
    width, height = img.size
    if img.mode != "L":
        gray = img.convert("L")
    else:
        gray = img
    threshold = 30
    for y in range(height - 1, -1, -1):
        row = gray.crop((0, y, width, y + 1))
        extrema = row.getextrema()
        if extrema[1] > threshold:
            return y
    return height // 2


def _stitch_subtitle(images, offset=0):
    """将多张图片按字幕区域拼接"""
    if not images:
        return None
    result = images[0].copy()
    for idx, img in enumerate(images[1:], start=2):
        y_start = _detect_subtitle_region(img) + offset
        y_start = max(0, min(y_start, img.height - 10))
        width, height = img.size
        subtitle = img.crop((0, y_start, width, height))
        new_height = result.height + subtitle.height
        new_width = max(result.width, subtitle.width)
        canvas = Image.new("RGBA", (new_width, new_height), (255, 255, 255))
        canvas.paste(result, ((new_width - result.width) // 2, 0))
        canvas.paste(subtitle, ((new_width - subtitle.width) // 2, result.height))
        result = canvas
    return result


def _stitch_images(
    images, labels,
    layout="垂直",
    grid_cols=3,
    spacing=0,
    bg_color="#FFFFFF",
    tag_position="每张图下方",
    tag_height=30,
    tag_size=14,
    title_text="",
    title_position="顶部",
    title_height=60,
    title_font_size=24,
    index_check=True,
    filename_check=True
):
    """通用图片拼接函数"""
    def get_chinese_font(size):
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/simhei.ttf",
        ]
        for path in font_paths:
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
        return ImageFont.load_default()
    font = get_chinese_font(tag_size)
    title_font = get_chinese_font(title_font_size)
    bg_color = bg_color.lstrip('#')
    bg_rgb = tuple(int(bg_color[i:i+2], 16) for i in (0, 2, 4)) if len(bg_color) == 6 else (255, 255, 255)
    has_labels = any(l for l in labels)
    if layout == "垂直":
        processed = []
        max_width = 0
        for im, label in zip(images, labels):
            w, h = im.size
            tag_height_actual = tag_height if has_labels and label else 0
            if tag_position == "每张图上方":
                img_with_label = Image.new("RGBA", (w, h + tag_height_actual), bg_rgb + (255,))
                draw = ImageDraw.Draw(img_with_label)
                draw.rectangle([(0, 0), (w, tag_height_actual)], fill=bg_rgb + (255,))
                draw.text((5, 0), label, fill=(0, 0, 0, 255), font=font)
                img_with_label.paste(im, (0, tag_height_actual), im if im.mode == "RGBA" else None)
            else:
                img_with_label = Image.new("RGBA", (w, h + tag_height_actual), bg_rgb + (255,))
                img_with_label.paste(im, (0, 0), im if im.mode == "RGBA" else None)
                draw = ImageDraw.Draw(img_with_label)
                draw.rectangle([(0, h), (w, h + tag_height_actual)], fill=bg_rgb + (255,))
                draw.text((5, h), label, fill=(0, 0, 0, 255), font=font)
            processed.append(img_with_label)
            max_width = max(max_width, img_with_label.width)
        for i, img in enumerate(processed):
            if img.width < max_width:
                new_img = Image.new("RGBA", (max_width, img.height), bg_rgb + (255,))
                x = (max_width - img.width) // 2
                new_img.paste(img, (x, 0), img if img.mode == "RGBA" else None)
                processed[i] = new_img
        total_width = max_width
        total_height = sum(img.height for img in processed) + spacing * (len(processed) - 1)
        canvas = Image.new("RGBA", (total_width, total_height), bg_rgb + (255,))
        y = 0
        for img in processed:
            canvas.paste(img, (0, y), img if img.mode == "RGBA" else None)
            y += img.height + spacing
    elif layout == "水平":
        processed = []
        max_height = 0
        for im, label in zip(images, labels):
            w, h = im.size
            tag_height_actual = tag_height if has_labels and label else 0
            if tag_position == "每张图上方":
                img_with_label = Image.new("RGBA", (w, h + tag_height_actual), bg_rgb + (255,))
                draw = ImageDraw.Draw(img_with_label)
                draw.rectangle([(0, 0), (w, tag_height_actual)], fill=bg_rgb + (255,))
                draw.text((5, 0), label, fill=(0, 0, 0, 255), font=font)
                img_with_label.paste(im, (0, tag_height_actual), im if im.mode == "RGBA" else None)
            else:
                img_with_label = Image.new("RGBA", (w, h + tag_height_actual), bg_rgb + (255,))
                img_with_label.paste(im, (0, 0), im if im.mode == "RGBA" else None)
                draw = ImageDraw.Draw(img_with_label)
                draw.rectangle([(0, h), (w, h + tag_height_actual)], fill=bg_rgb + (255,))
                draw.text((5, h), label, fill=(0, 0, 0, 255), font=font)
            processed.append(img_with_label)
            max_height = max(max_height, img_with_label.height)
        for i, img in enumerate(processed):
            if img.height < max_height:
                new_img = Image.new("RGBA", (img.width, max_height), bg_rgb + (255,))
                y = (max_height - img.height) // 2
                new_img.paste(img, (0, y), img if img.mode == "RGBA" else None)
                processed[i] = new_img
        total_height = max_height
        total_width = sum(img.width for img in processed) + spacing * (len(processed) - 1)
        canvas = Image.new("RGBA", (total_width, total_height), bg_rgb + (255,))
        x = 0
        for img in processed:
            canvas.paste(img, (x, 0), img if img.mode == "RGBA" else None)
            x += img.width + spacing
    elif layout == "网格":
        max_w = max(im.width for im in images)
        max_h = max(im.height for im in images)
        cell_w, cell_h = max_w, max_h
        scaled_imgs = []
        for im in images:
            ratio = min(cell_w / im.width, cell_h / im.height)
            new_w = int(im.width * ratio)
            new_h = int(im.height * ratio)
            canvas_im = Image.new("RGBA", (cell_w, cell_h), bg_rgb + (255,))
            x = (cell_w - new_w) // 2
            y = (cell_h - new_h) // 2
            canvas_im.paste(im.resize((new_w, new_h), Image.Resampling.LANCZOS), (x, y))
            scaled_imgs.append(canvas_im)
        unit_height = cell_h + (tag_height if has_labels else 0)
        unit_width = cell_w
        final_units = []
        for i, im in enumerate(scaled_imgs):
            label = labels[i] if has_labels else ""
            if label and has_labels:
                if tag_position == "每张图上方":
                    unit = Image.new("RGBA", (unit_width, unit_height), bg_rgb + (255,))
                    draw = ImageDraw.Draw(unit)
                    draw.rectangle([(0, 0), (unit_width, tag_height)], fill=bg_rgb + (255,))
                    draw.text((5, 0), label, fill=(0, 0, 0, 255), font=font)
                    unit.paste(im, (0, tag_height))
                else:
                    unit = Image.new("RGBA", (unit_width, unit_height), bg_rgb + (255,))
                    unit.paste(im, (0, 0))
                    draw = ImageDraw.Draw(unit)
                    draw.rectangle([(0, cell_h), (unit_width, unit_height)], fill=bg_rgb + (255,))
                    draw.text((5, cell_h), label, fill=(0, 0, 0, 255), font=font)
                final_units.append(unit)
            else:
                final_units.append(im)
        num_images = len(final_units)
        cols = min(grid_cols, num_images)
        rows = (num_images + cols - 1) // cols
        total_width = cols * unit_width + (cols - 1) * spacing
        total_height = rows * unit_height + (rows - 1) * spacing
        canvas = Image.new("RGBA", (total_width, total_height), bg_rgb + (255,))
        y = 0
        for row in range(rows):
            x = 0
            for col in range(cols):
                idx = row * cols + col
                if idx >= num_images:
                    break
                canvas.paste(final_units[idx], (x, y))
                x += unit_width + spacing
            y += unit_height + spacing
    if title_text:
        title_height_actual = title_height
        if title_position == "顶部":
            new_canvas = Image.new("RGBA", (canvas.width, canvas.height + title_height_actual), bg_rgb + (255,))
            draw = ImageDraw.Draw(new_canvas)
            draw.rectangle([(0, 0), (canvas.width, title_height_actual)], fill=bg_rgb + (255,))
            try:
                bbox = draw.textbbox((0, 0), title_text, font=title_font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            except:
                tw, th = draw.textsize(title_text, font=title_font)
            x = (canvas.width - tw) // 2
            y = (title_height_actual - th) // 2
            draw.text((x, y), title_text, fill=(0, 0, 0, 255), font=title_font)
            new_canvas.paste(canvas, (0, title_height_actual), canvas if canvas.mode == "RGBA" else None)
            canvas = new_canvas
        else:
            new_canvas = Image.new("RGBA", (canvas.width, canvas.height + title_height_actual), bg_rgb + (255,))
            new_canvas.paste(canvas, (0, 0), canvas if canvas.mode == "RGBA" else None)
            draw = ImageDraw.Draw(new_canvas)
            draw.rectangle([(0, canvas.height), (canvas.width, canvas.height + title_height_actual)], fill=bg_rgb + (255,))
            try:
                bbox = draw.textbbox((0, 0), title_text, font=title_font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            except:
                tw, th = draw.textsize(title_text, font=title_font)
            x = (canvas.width - tw) // 2
            y = canvas.height + (title_height_actual - th) // 2
            draw.text((x, y), title_text, fill=(0, 0, 0, 255), font=title_font)
            canvas = new_canvas
    return canvas


def run_task(file_item, settings):
    """不支持单任务模式"""
    raise NotImplementedError("图片拼接功能请使用 run_batch，不要使用 run_task")
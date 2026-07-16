# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import re
from PIL import Image, ImageDraw, ImageFont
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, 
    QCheckBox, QLineEdit, QGroupBox, QFormLayout, QPushButton, QColorDialog, 
    QSizePolicy, QFrame
)
from core.utils import get_group_key


def _detect_subtitle_region(img):
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


class StitchPanel(QWidget):
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

        layout.addLayout(group_row)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("布局模式:"))
        self.layout_mode = QComboBox()
        self.layout_mode.addItems(["垂直", "水平", "网格", "台词拼接"])
        self.layout_mode.currentIndexChanged.connect(self._on_layout_mode_changed)
        mode_row.addWidget(self.layout_mode, 1)

        mode_row.addWidget(QLabel("背景色:"))
        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setFixedSize(24, 18)
        self.bg_color_btn.setStyleSheet(
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
        self.bg_color_btn.clicked.connect(self._choose_color)
        mode_row.addWidget(self.bg_color_btn)

        layout.addLayout(mode_row)

        self.param_row = QHBoxLayout()
        self.param_row.setSpacing(6)

        self.spacing_label = QLabel("间距:")
        self.spacing = QSpinBox()
        self.spacing.setRange(0, 200)
        self.spacing.setValue(0)
        self.spacing.setSuffix(" px")

        self.grid_label = QLabel("每行张数:")
        self.grid_cols = QSpinBox()
        self.grid_cols.setRange(1, 20)
        self.grid_cols.setValue(3)
        self.grid_cols.setSuffix(" 张")

        self.offset_label = QLabel("偏移量:")
        self.subtitle_offset = QSpinBox()
        self.subtitle_offset.setRange(-300, 300)
        self.subtitle_offset.setValue(-150)
        self.subtitle_offset.setSuffix(" px")

        self.grid_label.setVisible(False)
        self.grid_cols.setVisible(False)
        self.offset_label.setVisible(False)
        self.subtitle_offset.setVisible(False)

        self.param_row.addWidget(self.spacing_label)
        self.param_row.addWidget(self.spacing)
        self.param_row.addWidget(self.grid_label)
        self.param_row.addWidget(self.grid_cols)
        self.param_row.addWidget(self.offset_label)
        self.param_row.addWidget(self.subtitle_offset)

        layout.addLayout(self.param_row)

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("输出格式:"))
        self.out_format = QComboBox()
        self.out_format.addItems(["PNG", "JPG", "WEBP"])
        fmt_row.addWidget(self.out_format, 1)
        layout.addLayout(fmt_row)

        layout.addSpacing(6)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setFixedHeight(2)
        layout.addWidget(line)

        layout.addSpacing(6)

        title_label = QLabel("标签设置（可选）：")
        title_label.setStyleSheet("font-weight: 600; margin-top: 4px; margin-left: -3px;")
        layout.addWidget(title_label)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("标签:"))
        self.add_index = QCheckBox("添加序号")
        self.add_index.setChecked(False)
        row1.addWidget(self.add_index)

        self.add_filename = QCheckBox("添加文件名")
        self.add_filename.setChecked(False)
        row1.addWidget(self.add_filename)

        row1.addStretch()
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("标签位置:"))
        self.label_position = QComboBox()
        self.label_position.addItems(["每张图下方", "每张图上方"])
        self.label_position.setCurrentIndex(1)
        row2.addWidget(self.label_position, 1)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("标签高度:"))
        self.label_height = QSpinBox()
        self.label_height.setRange(10, 100)
        self.label_height.setValue(40)
        self.label_height.setSuffix(" px")
        row3.addWidget(self.label_height, 1)
        layout.addLayout(row3)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("标签大小:"))
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 48)
        self.font_size.setValue(24)
        self.font_size.setSuffix(" pt")
        row4.addWidget(self.font_size, 1)
        layout.addLayout(row4)

        title_label = QLabel("标题设置（可选）：")
        title_label.setStyleSheet("font-weight: 600; margin-top: 4px; margin-left: -3px;")
        layout.addWidget(title_label)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("标题:"))
        self.title_text = QLineEdit()
        self.title_text.setPlaceholderText("输入标题（留空则不显示）")
        row4.addWidget(self.title_text, 1)
        layout.addLayout(row4)

        row5 = QHBoxLayout()
        row5.addWidget(QLabel("标题位置:"))
        self.title_position = QComboBox()
        self.title_position.addItems(["顶部", "底部"])
        row5.addWidget(self.title_position, 1)
        layout.addLayout(row5)

        row5 = QHBoxLayout()
        row5.addWidget(QLabel("标题高度:"))
        self.title_height = QSpinBox()
        self.title_height.setRange(20, 200)
        self.title_height.setValue(60)
        self.title_height.setSuffix(" px")
        row5.addWidget(self.title_height, 1)
        layout.addLayout(row5)

        row6 = QHBoxLayout()
        row6.addWidget(QLabel("标题大小:"))
        self.title_font_size = QSpinBox()
        self.title_font_size.setRange(10, 72)
        self.title_font_size.setValue(32)
        self.title_font_size.setSuffix(" pt")
        row6.addWidget(self.title_font_size, 1)
        layout.addLayout(row6)

        layout.addStretch()

        self.group_mode.currentIndexChanged.connect(self._toggle_options)
        self.group_mode.currentIndexChanged.connect(self.changed)
        self.prefix_len.valueChanged.connect(self.changed)
        self.group_size.valueChanged.connect(self.changed)
        self.layout_mode.currentIndexChanged.connect(self.changed)
        self.grid_cols.valueChanged.connect(self.changed)
        self.subtitle_offset.valueChanged.connect(self.changed)
        self.spacing.valueChanged.connect(self.changed)
        self.bg_color_btn.clicked.connect(self.changed)
        self.out_format.currentIndexChanged.connect(self.changed)
        self.add_index.stateChanged.connect(self.changed)
        self.add_filename.stateChanged.connect(self.changed)
        self.label_position.currentIndexChanged.connect(self.changed)
        self.label_height.valueChanged.connect(self.changed)
        self.font_size.valueChanged.connect(self.changed)
        self.title_text.textChanged.connect(self.changed)
        self.title_position.currentIndexChanged.connect(self.changed)
        self.title_height.valueChanged.connect(self.changed)
        self.title_font_size.valueChanged.connect(self.changed)

        self._toggle_options()
        self._on_layout_mode_changed()

    def _toggle_options(self):
        mode = self.group_mode.currentIndex()
        self.prefix_len.setVisible(mode == 0)
        self.group_size.setVisible(mode == 1)

    def _on_layout_mode_changed(self):
        mode = self.layout_mode.currentText()
        is_grid = (mode == "网格")
        is_subtitle = (mode == "台词拼接")

        self.grid_label.setVisible(is_grid)
        self.grid_cols.setVisible(is_grid)
        self.offset_label.setVisible(is_subtitle)
        self.subtitle_offset.setVisible(is_subtitle)

        self.spacing.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.grid_cols.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.subtitle_offset.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        if is_grid:
            self.spacing.setFixedWidth(90)
            self.grid_cols.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        elif is_subtitle:
            self.spacing.setFixedWidth(90)
            self.subtitle_offset.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.spacing.setValue(0)
        else:
            self.spacing.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.spacing.setFixedWidth(16777215)

    def _choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name().upper()
            self.bg_color_btn.setStyleSheet(
                f"background-color: {hex_color}; border: 1px solid #ccc; border-radius: 4px;"
            )
            self.bg_color_btn.setProperty("color_hex", hex_color)
            self.changed.emit()


def build_panel() -> QWidget:
    return StitchPanel()


def collect_settings(panel: StitchPanel) -> dict:
    bg_hex = panel.bg_color_btn.property("color_hex")
    if not bg_hex:
        bg_hex = "#FFFFFF"
    return {
        "group_mode": panel.group_mode.currentIndex(),
        "prefix_len": panel.prefix_len.value(),
        "group_size": panel.group_size.value(),
        "layout": panel.layout_mode.currentText(),
        "grid_cols": panel.grid_cols.value(),
        "subtitle_offset": panel.subtitle_offset.value(),
        "spacing": panel.spacing.value(),
        "bg_color": bg_hex,
        "add_index": panel.add_index.isChecked(),
        "add_filename": panel.add_filename.isChecked(),
        "label_position": panel.label_position.currentText(),
        "label_height": panel.label_height.value(),
        "font_size": panel.font_size.value(),
        "title_text": panel.title_text.text().strip(),
        "title_position": panel.title_position.currentText(),
        "title_height": panel.title_height.value(),
        "title_font_size": panel.title_font_size.value(),
        "out_format": panel.out_format.currentText().lower(),
    }


def prepare_preview(items, settings):
    group_mode = settings.get("group_mode", 0)
    prefix_len = settings.get("prefix_len", 9)
    group_size = settings.get("group_size", 5)
    layout = settings.get("layout", "垂直")
    grid_cols = settings.get("grid_cols", 3)

    file_paths = [it.input_path for it in items]
    groups = {}
    for it in items:
        key = get_group_key(it.input_path, group_mode, prefix_len, group_size, file_paths)
        groups.setdefault(key, []).append(it.input_path)

    for it in items:
        key = get_group_key(it.input_path, group_mode, prefix_len, group_size, file_paths)
        display_key = "全部文件" if key == "__all__" else (os.path.basename(key) if group_mode == 2 else key)
        grid_hint = f"，每行{grid_cols}张" if layout == "网格" else ""
        if layout == "台词拼接":
            grid_hint = "（第一张全图，后续裁剪字幕）"
        it.preview_extra = {"A": f"拼接({layout})：组「{display_key}」共 {len(groups[key])} 张{grid_hint}"}
        it.preview_extra["group_key"] = display_key

def run_batch(items, settings, get_output_dir, get_output_name_for_group,
              log_callback=None, progress_callback=None, stop_check=None):
    if not items:
        return []

    group_mode = settings.get("group_mode", 0)
    prefix_len = settings.get("prefix_len", 9)
    group_size = settings.get("group_size", 5)
    layout = settings.get("layout", "垂直")
    grid_cols = settings.get("grid_cols", 3)
    subtitle_offset = settings.get("subtitle_offset", -150)
    spacing = settings.get("spacing", 0)
    bg_color = settings.get("bg_color", "#FFFFFF")
    add_index = settings.get("add_index", False)
    add_filename = settings.get("add_filename", False)
    label_position = settings.get("label_position", "每张图上方")
    label_height = settings.get("label_height", 40)
    font_size = settings.get("font_size", 24)
    title_text = settings.get("title_text", "")
    title_position = settings.get("title_position", "顶部")
    title_height = settings.get("title_height", 60)
    title_font_size = settings.get("title_font_size", 32)
    out_format = settings.get("out_format", "png")

    is_subtitle = (layout == "台词拼接")

    if is_subtitle:
        spacing = 0

    file_paths = [it.input_path for it in items]
    groups = {}
    for item in items:
        key = get_group_key(item.input_path, group_mode, prefix_len, group_size, file_paths)
        groups.setdefault(key, []).append(item)

    output_files = []
    total_groups = len(groups)
    processed = 0

    for group_key, group_items in groups.items():
        if stop_check and stop_check():
            if log_callback:
                log_callback("⛔ 用户终止任务")
            break

        processed += 1

        if progress_callback:
            progress_callback(int(processed / total_groups * 100))

        if log_callback:
            display_key = "全部文件" if group_key == "__all__" else group_key
            log_callback(f"正在拼接组：{display_key}（共 {len(group_items)} 张）")

        images = []
        for fi in group_items:
            try:
                im = Image.open(fi.input_path)
                if im.mode not in ("RGB", "RGBA"):
                    im = im.convert("RGBA")
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
                if add_index:
                    parts.append(str(idx))
                if add_filename:
                    base_name = os.path.splitext(os.path.basename(fi.input_path))[0]
                    parts.append(base_name)
                labels.append(" ".join(parts))

            try:
                stitched = stitch_images(
                    images, labels,
                    layout=layout,
                    grid_cols=grid_cols,
                    spacing=spacing,
                    bg_color=bg_color,
                    label_position=label_position,
                    label_height=label_height,
                    font_size=font_size,
                    title_text=title_text,
                    title_position=title_position,
                    title_height=title_height,
                    title_font_size=title_font_size,
                    add_index=add_index,
                    add_filename=add_filename
                )
            except Exception as e:
                for fi in group_items:
                    fi.status = "错误"
                if log_callback:
                    log_callback(f"拼接组 {group_key} 失败: {e}")
                continue

        if group_key == "__all__":
            base_out = get_output_name_for_group("全部")
        elif group_mode == 2:
            base_out = get_output_name_for_group(os.path.basename(group_key))
        else:
            base_out = get_output_name_for_group(group_key)

        out_dir = get_output_dir(group_items[0])
        out_name = f"{base_out}.{out_format}"
        out_path = os.path.join(out_dir, out_name)

        if os.path.exists(out_path):
            counter = 1
            while os.path.exists(os.path.join(out_dir, f"{base_out}_{counter}.{out_format}")):
                counter += 1
            out_path = os.path.join(out_dir, f"{base_out}_{counter}.{out_format}")

        save_format = out_format.upper()
        if save_format == "JPG":
            save_format = "JPEG"
        if save_format in ("JPEG", "BMP") and stitched.mode == "RGBA":
            bg = Image.new("RGB", stitched.size, (255, 255, 255))
            bg.paste(stitched, mask=stitched.split()[3])
            stitched = bg
        stitched.save(out_path, format=save_format, quality=90, optimize=True)
        stitched.close()

        output_files.append(out_path)

        for fi in group_items:
            fi.status = "完成"
            fi.output_name = os.path.basename(out_path)
            fi.output_dir = out_dir

    if log_callback:
        log_callback("✅ 全部拼接完成！")

    return output_files


def stitch_images(
    images, labels,
    layout="垂直",
    grid_cols=3,
    spacing=0,
    bg_color="#FFFFFF",
    label_position="每张图下方",
    label_height=30,
    font_size=14,
    title_text="",
    title_position="顶部",
    title_height=60,
    title_font_size=24,
    add_index=True,
    add_filename=True
):
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

    font = get_chinese_font(font_size)
    title_font = get_chinese_font(title_font_size)

    bg_color = bg_color.lstrip('#')
    bg_rgb = tuple(int(bg_color[i:i+2], 16) for i in (0, 2, 4)) if len(bg_color) == 6 else (255, 255, 255)

    has_labels = any(l for l in labels)

    if layout == "垂直":
        processed = []
        max_width = 0
        total_height = 0
        for im, label in zip(images, labels):
            w, h = im.size
            label_height_actual = label_height if has_labels and label else 0
            if label_position == "每张图上方":
                img_with_label = Image.new("RGBA", (w, h + label_height_actual), bg_rgb + (255,))
                draw = ImageDraw.Draw(img_with_label)
                draw.rectangle([(0, 0), (w, label_height_actual)], fill=bg_rgb + (255,))
                draw.text((5, 0), label, fill=(0, 0, 0, 255), font=font)
                img_with_label.paste(im, (0, label_height_actual), im if im.mode == "RGBA" else None)
            else:
                img_with_label = Image.new("RGBA", (w, h + label_height_actual), bg_rgb + (255,))
                img_with_label.paste(im, (0, 0), im if im.mode == "RGBA" else None)
                draw = ImageDraw.Draw(img_with_label)
                draw.rectangle([(0, h), (w, h + label_height_actual)], fill=bg_rgb + (255,))
                draw.text((5, h), label, fill=(0, 0, 0, 255), font=font)

            processed.append(img_with_label)
            max_width = max(max_width, img_with_label.width)
            total_height += img_with_label.height

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
            label_height_actual = label_height if has_labels and label else 0
            if label_position == "每张图上方":
                img_with_label = Image.new("RGBA", (w, h + label_height_actual), bg_rgb + (255,))
                draw = ImageDraw.Draw(img_with_label)
                draw.rectangle([(0, 0), (w, label_height_actual)], fill=bg_rgb + (255,))
                draw.text((5, 0), label, fill=(0, 0, 0, 255), font=font)
                img_with_label.paste(im, (0, label_height_actual), im if im.mode == "RGBA" else None)
            else:
                img_with_label = Image.new("RGBA", (w, h + label_height_actual), bg_rgb + (255,))
                img_with_label.paste(im, (0, 0), im if im.mode == "RGBA" else None)
                draw = ImageDraw.Draw(img_with_label)
                draw.rectangle([(0, h), (w, h + label_height_actual)], fill=bg_rgb + (255,))
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

        unit_height = cell_h + (label_height if has_labels else 0)
        unit_width = cell_w

        final_units = []
        for i, im in enumerate(scaled_imgs):
            label = labels[i] if has_labels else ""
            if label and has_labels:
                if label_position == "每张图上方":
                    unit = Image.new("RGBA", (unit_width, unit_height), bg_rgb + (255,))
                    draw = ImageDraw.Draw(unit)
                    draw.rectangle([(0, 0), (unit_width, label_height)], fill=bg_rgb + (255,))
                    draw.text((5, 0), label, fill=(0, 0, 0, 255), font=font)
                    unit.paste(im, (0, label_height))
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
    raise NotImplementedError("拼接功能请使用 run_batch，不要使用 run_task")
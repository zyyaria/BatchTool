# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import re
import math
from PIL import Image, ImageSequence
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox,
    QCheckBox, QSizePolicy, QStackedWidget, QPushButton, QColorDialog
)
from core.utils import get_group_key, get_unique_file_path


class ToGifPanel(QWidget):
    changed = Signal()

    def __init__(self):
        """初始化设置面板"""
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        row_mode = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["多图合成 GIF", "多个 GIF 拼接"])
        self.mode_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_mode.addWidget(QLabel("合成模式:"))
        row_mode.addWidget(self.mode_combo, 1)
        layout.addLayout(row_mode)

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

        self.size_widget = QWidget()
        self.size_widget.setContentsMargins(0, 0, 0, 0)
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

        row_param = QHBoxLayout()
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(10, 5000)
        self.duration_spin.setValue(300)
        self.duration_spin.setSuffix(" ms")
        self.duration_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.loop_spin = QSpinBox()
        self.loop_spin.setRange(0, 999)
        self.loop_spin.setValue(0)
        self.loop_spin.setToolTip("0=无限循环")
        self.loop_spin.setSuffix(" 次")
        self.loop_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_param.addWidget(QLabel("速度:"))
        row_param.addWidget(self.duration_spin, 1)
        row_param.addWidget(QLabel("重复:"))
        row_param.addWidget(self.loop_spin, 1)
        layout.addLayout(row_param)
        
        self.reframe_widget = QWidget()
        reframe_layout = QVBoxLayout(self.reframe_widget)
        reframe_layout.setContentsMargins(0, 0, 0, 0)

        row_play = QHBoxLayout()
        self.play_combo = QComboBox()
        self.play_combo.addItems(["顺序播放", "同时叠加"])
        self.play_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_play.addWidget(QLabel("排列方式:"))
        row_play.addWidget(self.play_combo, 1)
        reframe_layout.addLayout(row_play)

        self.sim_widget = QWidget()
        sim_layout = QVBoxLayout(self.sim_widget)
        sim_layout.setContentsMargins(0, 0, 0, 0)        

        row_sync = QHBoxLayout()    
        self.sync_combo = QComboBox()
        self.sync_combo.addItems(["按最短时长截断", "按最长时长循环"])
        self.sync_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_sync.addWidget(QLabel("对齐方式:"))
        row_sync.addWidget(self.sync_combo, 1)      

        row_merge = QHBoxLayout()        
        self.merge_combo = QComboBox()
        self.merge_combo.addItems(["水平", "垂直", "网格"])
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

        row_pagram = QHBoxLayout()
        self.row_label = QLabel("行数:")
        self.row_spin = QSpinBox()
        self.row_spin.setRange(1, 20)
        self.row_spin.setValue(2)
        self.row_spin.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.col_label = QLabel("列数:")
        self.col_spin = QSpinBox()
        self.col_spin.setRange(1, 20)
        self.col_spin.setValue(2)
        self.col_spin.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        row_pagram.addWidget(self.row_label)
        row_pagram.addWidget(self.row_spin, 1)
        row_pagram.addWidget(self.col_label)
        row_pagram.addWidget(self.col_spin, 1)

        row_margin = QHBoxLayout()
        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(0, 200)
        self.margin_spin.setValue(0)
        self.margin_spin.setSuffix(" px")
        self.margin_spin.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.padding_spin = QSpinBox()
        self.padding_spin.setRange(0, 200)
        self.padding_spin.setValue(0)
        self.padding_spin.setSuffix(" px")
        self.padding_spin.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        row_margin.addWidget(QLabel("边距:"))
        row_margin.addWidget(self.margin_spin, 1)
        row_margin.addWidget(QLabel("间距:"))
        row_margin.addWidget(self.padding_spin, 1)

        sim_layout.addLayout(row_sync)
        sim_layout.addLayout(row_merge)
        sim_layout.addLayout(row_pagram)
        sim_layout.addLayout(row_margin)
        sim_layout.addStretch()

        reframe_layout.addWidget(self.sim_widget)
        reframe_layout.addStretch()
        layout.addWidget(self.reframe_widget)

        layout.addStretch()

        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self.mode_combo.currentIndexChanged.connect(self.changed)
        self.group_combo.currentIndexChanged.connect(self._on_group_changed)
        self.group_combo.currentIndexChanged.connect(self.changed)
        self.prefix_spin.valueChanged.connect(self.changed)
        self.interval_spin.valueChanged.connect(self.changed)
        self.size_combo.currentIndexChanged.connect(self._on_size_changed)
        self.size_combo.currentIndexChanged.connect(self.changed)
        self.width_spin.valueChanged.connect(self.changed)
        self.height_spin.valueChanged.connect(self.changed)
        self.loop_spin.valueChanged.connect(self.changed)
        self.aspect_check.stateChanged.connect(self.changed)
        self.duration_spin.valueChanged.connect(self.changed)
        self.play_combo.currentIndexChanged.connect(self._on_play_changed)
        self.play_combo.currentIndexChanged.connect(self.changed)
        self.merge_combo.currentIndexChanged.connect(self._on_sim_merge_changed)
        self.merge_combo.currentIndexChanged.connect(self.changed)
        self.color_btn.clicked.connect(lambda: self._choose_color(self.color_btn))
        self.color_btn.clicked.connect(self.changed)
        self.row_spin.valueChanged.connect(self.changed)
        self.col_spin.valueChanged.connect(self.changed)
        self.margin_spin.valueChanged.connect(self.changed)
        self.padding_spin.valueChanged.connect(self.changed)
        self.sync_combo.currentIndexChanged.connect(self.changed)

        self._on_mode_changed()
        self._on_group_changed()
        self._on_size_changed()
        self._on_play_changed()
        self._on_sim_merge_changed()

    def _on_mode_changed(self):
        """合成模式切换"""
        idx = self.mode_combo.currentIndex()
        self.reframe_widget.setVisible(idx == 1)

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

    def _on_play_changed(self):
        """播放类型切换"""
        is_sim = self.play_combo.currentIndex() == 1
        self.sim_widget.setVisible(is_sim)

    def _on_sim_merge_changed(self):
        """拼接方式切换"""
        mode = self.merge_combo.currentText()
        is_grid = (mode == "网格")
        self.row_label.setVisible(is_grid)
        self.row_spin.setVisible(is_grid)
        self.col_label.setVisible(is_grid)
        self.col_spin.setVisible(is_grid)

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
    return ToGifPanel()


def collect_settings(panel: ToGifPanel) -> dict:
    """收集面板设置"""
    return {
        "mode": panel.mode_combo.currentIndex(), 
        "group": panel.group_combo.currentIndex(),
        "prefix": panel.prefix_spin.value(),
        "interval": panel.interval_spin.value(),
        "size": panel.size_combo.currentIndex(),
        "target_width": panel.width_spin.value(),
        "target_height": panel.height_spin.value(),
        "keep_ratio": panel.aspect_check.isChecked(),
        "loop": panel.loop_spin.value(),
        "duration": panel.duration_spin.value(),
        "play": panel.play_combo.currentIndex(),
        "merge": panel.merge_combo.currentText(),
        "color": panel.color_btn.property("color_hex") or "#FFFFFF",
        "grid_rows": panel.row_spin.value(),
        "grid_cols": panel.col_spin.value(),
        "margin": panel.margin_spin.value(),
        "padding": panel.padding_spin.value(),
        "sync": panel.sync_combo.currentIndex(),
    }


def prepare_preview(items, settings):
    """生成预览信息"""
    group_idx = settings.get("group", 0)
    prefix = settings.get("prefix", 9)
    interval = settings.get("interval", 5)
    mode = settings.get("mode", 0)
    file_paths = [it.input_path for it in items]
    groups = {}
    for it in items:
        key = get_group_key(it.input_path, group_idx, prefix, interval, file_paths)
        groups.setdefault(key, []).append(it.input_path)
    for it in items:
        key = get_group_key(it.input_path, group_idx, prefix, interval, file_paths)
        display_key = "全部文件" if key == "__all__" else (os.path.basename(key) if group_idx == 2 else key)
        duration = settings.get("duration", 300)
        loop = settings.get("loop", 0)
        loop_text = "无限" if loop == 0 else str(loop)
        if mode == 1:
            play = settings.get("play", 0)
            if play == 0:
                extra = f"顺序播放，速度{duration}ms，循环{loop_text}"
            else:
                merge = settings.get("merge", "水平")
                sync = settings.get("sync", 0)
                sync_text = "截断" if sync == 0 else "循环"
                extra = f"同时叠加，拼接{merge}，{sync_text}，速度{duration}ms，循环{loop_text}"
            it.preview_extra = {
                "A": f"GIF拼接，组「{display_key}」{len(groups[key])}个，{extra}"
            }
        else: 
            it.preview_extra = {
                "A": f"多图合成GIF，组「{display_key}」{len(groups[key])}张，帧间隔{duration}ms，循环{loop_text}"
            }
        it.preview_extra["group_key"] = display_key


def run_batch(items, settings, get_output_dir, get_output_name_for_group,
              log_callback=None, progress_callback=None, stop_check=None):
    """批量合成GIF"""
    if not items:
        return []
    mode = settings.get("mode", 0)

    if mode == 1:
        return _run_merge_batch(items, settings, get_output_dir, get_output_name_for_group,
                                log_callback, progress_callback, stop_check)
    else:
        return _run_compose_batch(items, settings, get_output_dir, get_output_name_for_group,
                                  log_callback, progress_callback, stop_check)
    

def _run_compose_batch(items, settings, get_output_dir, get_output_name_for_group,
                       log_callback, progress_callback, stop_check):
    """多图合成GIF（每张图作为一帧）"""
    group_idx = settings.get("group", 0)
    prefix = settings.get("prefix", 9)
    interval = settings.get("interval", 5)
    duration = settings.get("duration", 300)
    loop = settings.get("loop", 0)
    size_idx = settings.get("size", 0)
    custom_w = settings.get("target_width", 640)
    custom_h = settings.get("target_height", 480)
    keep_ratio = settings.get("keep_ratio", True)
    custom_names = settings.get("custom_names", [])
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
            log_callback(f"正在合成GIF组：{display_key}（共 {len(group_items)} 张图片）")
        def get_number(fi):
            match = re.search(r'_?(\d+)', os.path.basename(fi.input_path))
            return int(match.group(1)) if match else 0
        group_items.sort(key=get_number)
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
        out_path = get_unique_file_path(out_dir, base, ".gif")
        images = []
        for fi in group_items:
            img = Image.open(fi.input_path)
            if img.mode == "RGBA":
                img = img.convert("RGB")
            if size_idx == 1:
                if keep_ratio:
                    img.thumbnail((custom_w, custom_h), Image.Resampling.LANCZOS)
                else:
                    img = img.resize((custom_w, custom_h), Image.Resampling.LANCZOS)
            images.append(img)
        if images:
            images[0].save(
                out_path,
                save_all=True,
                append_images=images[1:],
                duration=duration,
                loop=loop if loop >= 0 else 0,
                format="GIF",
                disposal=2
            )
        output_files.append(out_path)
        for fi in group_items:
            fi.status = "完成"
            fi.output_name = os.path.basename(out_path)
            fi.output_dir = out_dir
            fi.processed = True
        processed += 1
    if log_callback:
        log_callback("✅ 全部GIF合成完成！")
    return output_files


def _run_merge_batch(items, settings, get_output_dir, get_output_name_for_group,
                     log_callback, progress_callback, stop_check):
    """多个GIF拼接为一个GIF"""
    group_idx = settings.get("group", 0)
    prefix = settings.get("prefix", 9)
    interval = settings.get("interval", 5)
    duration = settings.get("duration", 300)
    loop = settings.get("loop", 0)
    play = settings.get("play", 0)  
    sync = settings.get("sync", 0)  
    merge = settings.get("merge", "水平")
    color = settings.get("color", "#FFFFFF")
    grid_rows = settings.get("grid_rows", 2)
    grid_cols = settings.get("grid_cols", 3)
    margin = settings.get("margin", 0)
    padding = settings.get("padding", 0)
    size_idx = settings.get("size", 0)
    custom_w = settings.get("target_width", 640)
    custom_h = settings.get("target_height", 480)
    keep_ratio = settings.get("keep_ratio", True)
    custom_names = settings.get("custom_names", [])
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
            log_callback(f"正在拼接GIF组：{display_key}（共 {len(group_items)} 个GIF）")
        frames_list = []
        for fi in group_items:
            try:
                frames = _get_gif_frames(fi.input_path)
                if not frames:
                    raise ValueError("空GIF")
                frames_list.append(frames)
            except Exception as e:
                if log_callback:
                    log_callback(f"⚠️ 跳过 {os.path.basename(fi.input_path)}：{e}")
                continue
        if not frames_list:
            if log_callback:
                log_callback(f"⚠️ 组 {group_key} 没有有效GIF，跳过")
            continue
        if play == 0:
            result_frames = _merge_sequential(frames_list, duration, size_idx, custom_w, custom_h, keep_ratio)
        else:
            result_frames = _merge_simultaneous(frames_list, merge, color, grid_rows, grid_cols,
                                                margin, padding, sync, duration, size_idx,
                                                custom_w, custom_h, keep_ratio)
        if not result_frames:
            if log_callback:
                log_callback(f"⚠️ 合成失败：无帧数据")
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
        out_path = get_unique_file_path(out_dir, base, ".gif")
        try:
            result_frames[0].save(
                out_path,
                save_all=True,
                append_images=result_frames[1:],
                duration=duration,
                loop=loop if loop >= 0 else 0,
                optimize=True
            )
            for frame in result_frames:
                frame.close()
            for frames in frames_list:
                for f in frames:
                    f.close()            
            output_files.append(out_path)
            for fi in group_items:
                fi.status = "完成"
                fi.output_name = os.path.basename(out_path)
                fi.output_dir = out_dir
                fi.processed = True
        except Exception as e:
            if log_callback:
                log_callback(f"❌ 保存失败：{e}")
            for fi in group_items:
                fi.status = "错误"
        processed += 1
    if log_callback:
        log_callback("✅ 全部GIF拼接完成！")
    return output_files


def _get_gif_frames(gif_path):
    """提取GIF所有帧"""
    frames = []
    with Image.open(gif_path) as im:
        for frame in ImageSequence.Iterator(im):
            frames.append(frame.copy())
    return frames


def _merge_sequential(frames_list, duration, size_idx, custom_w, custom_h, keep_ratio):
    """顺序拼接：将所有帧依次连接"""
    all_frames = []
    if size_idx == 0:
        target_w = frames_list[0][0].width if frames_list else 200
        target_h = frames_list[0][0].height if frames_list else 200
    else:
        target_w = int(custom_w) if custom_w else 200
        target_h = int(custom_h) if custom_h else 200
    for frames in frames_list:
        for frame in frames:
            if size_idx == 1:
                if keep_ratio:
                    frame.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
                else:
                    frame = frame.resize((target_w, target_h), Image.Resampling.LANCZOS)
            all_frames.append(frame)
    return all_frames


def _merge_simultaneous(frames_list, merge, color, grid_rows, grid_cols,
                        margin, padding, sync, duration, size_idx,
                        custom_w, custom_h, keep_ratio):
    """同时叠加：按帧对齐拼成一帧"""
    if size_idx == 0:
        sim_w = frames_list[0][0].width if frames_list else 400
        sim_h = frames_list[0][0].height if frames_list else 400
    else:
        sim_w = int(custom_w) if custom_w else 400
        sim_h = int(custom_h) if custom_h else 400
    frame_counts = [len(frames) for frames in frames_list]
    if sync == 0:
        target_frame_count = min(frame_counts) if frame_counts else 1
    else:
        target_frame_count = max(frame_counts) if frame_counts else 1
    adjusted_frames = []
    for frames in frames_list:
        if len(frames) >= target_frame_count:
            adjusted_frames.append(frames[:target_frame_count])
        else:
            new_frames = []
            while len(new_frames) < target_frame_count:
                for f in frames:
                    new_frames.append(f.copy())
                    if len(new_frames) >= target_frame_count:
                        break
            adjusted_frames.append(new_frames)
    num_gifs = len(adjusted_frames)
    if merge == "水平":
        cols = num_gifs
        rows = 1
    elif merge == "垂直":
        cols = 1
        rows = num_gifs
    else: 
        cols = grid_cols
        rows = math.ceil(num_gifs / grid_cols)
    cell_width = sim_w + padding * 2
    cell_height = sim_h + padding * 2
    canvas_w = cols * cell_width + margin * 2
    canvas_h = rows * cell_height + margin * 2
    color_clean = color.lstrip('#')
    bg_rgb = tuple(int(color_clean[i:i+2], 16) for i in (0, 2, 4)) if len(color_clean) == 6 else (255, 255, 255)
    result_frames = []
    for frame_idx in range(target_frame_count):
        canvas = Image.new("RGB", (canvas_w, canvas_h), bg_rgb)
        for gif_idx in range(num_gifs):
            row = gif_idx // cols
            col = gif_idx % cols
            x = margin + col * cell_width + padding
            y = margin + row * cell_height + padding
            frame = adjusted_frames[gif_idx][frame_idx]
            if size_idx == 1:
                if keep_ratio:
                    ratio = max(sim_w / frame.width, sim_h / frame.height)
                    new_w = int(frame.width * ratio)
                    new_h = int(frame.height * ratio)
                    resized = frame.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    left = (new_w - sim_w) // 2
                    top = (new_h - sim_h) // 2
                    frame = resized.crop((left, top, left + sim_w, top + sim_h))
                else:
                    frame = frame.resize((sim_w, sim_h), Image.Resampling.LANCZOS)
            if frame.mode == 'RGBA':
                canvas.paste(frame, (x, y), frame)
            else:
                canvas.paste(frame, (x, y))
        result_frames.append(canvas)
    return result_frames


def run_task(file_item, settings):
    """不支持单任务模式"""
    raise NotImplementedError("GIF合成功能请使用 run_batch，不要使用 run_task")
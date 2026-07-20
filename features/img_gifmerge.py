# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import math
from PIL import Image, ImageSequence
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox,
    QPushButton, QSizePolicy, QColorDialog, QCheckBox
)
from core.utils import get_group_key, get_unique_file_path


class GifMergePanel(QWidget):
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
        self.play_combo = QComboBox()
        self.play_combo.addItems(["顺序播放", "同时播放"])
        self.play_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(10, 5000)
        self.speed_spin.setValue(300)
        self.speed_spin.setSuffix(" ms")
        self.speed_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.loop_spin = QSpinBox()
        self.loop_spin.setRange(-1, 999)
        self.loop_spin.setValue(0)
        self.loop_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        row_param1 = QHBoxLayout()
        row_param1.addWidget(QLabel("分组方式:"))
        row_param1.addWidget(self.group_combo, 1)
        row_param1.addWidget(self.prefix_spin, 1)
        row_param1.addWidget(self.group_spin, 1)
        row_param2 = QHBoxLayout()
        row_param2.addWidget(QLabel("播放类型:"))
        row_param2.addWidget(self.play_combo, 1)
        row_param3 = QHBoxLayout()
        row_param3.addWidget(QLabel("播放速度:"))
        row_param3.addWidget(self.speed_spin, 1)
        row_param4 = QHBoxLayout()
        row_param4.addWidget(QLabel("重复次数:"))
        row_param4.addWidget(self.loop_spin, 1)
        layout.addLayout(row_param1)        
        layout.addLayout(row_param2)        
        layout.addLayout(row_param3)        
        layout.addLayout(row_param4)

        self.seq_widget = QWidget()
        self.seq_widget.setContentsMargins(0, 0, 0, 0)
        self.size_combo = QComboBox()
        self.size_combo.addItems(["保持原尺寸", "自定义"])
        self.size_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.custom_size_widget = QWidget()
        self.custom_size_widget.setContentsMargins(0, 0, 0, 0)
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
        self.seq_aspect_check = QCheckBox("保持比例")
        self.seq_aspect_check.setChecked(True)
        self.seq_aspect_check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        row_seq1 = QHBoxLayout()
        row_seq1.addWidget(QLabel("目标尺寸:"))
        row_seq1.addWidget(self.size_combo, 1)
        row_seq1.addWidget(self.seq_aspect_check)
        row_seq2 = QHBoxLayout(self.custom_size_widget)
        row_seq2.setContentsMargins(0, 0, 0, 0)
        row_seq2.addWidget(QLabel("宽度:"))
        row_seq2.addWidget(self.width_spin, 1)
        row_seq2.addWidget(QLabel("高度:"))
        row_seq2.addWidget(self.height_spin, 1)
        seq_layout = QVBoxLayout(self.seq_widget)
        seq_layout.setContentsMargins(0, 0, 0, 0)
        seq_layout.addLayout(row_seq1)
        seq_layout.addWidget(self.custom_size_widget)
        layout.addWidget(self.seq_widget)

        self.sim_widget = QWidget()
        self.sim_widget.setContentsMargins(0, 0, 0, 0)
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
        self.grid_rows_label = QLabel("行数:")
        self.grid_rows_spin = QSpinBox()
        self.grid_rows_spin.setRange(1, 20)
        self.grid_rows_spin.setValue(2)
        self.grid_rows_spin.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.grid_cols_label = QLabel("列数:")
        self.grid_cols_spin = QSpinBox()
        self.grid_cols_spin.setRange(1, 20)
        self.grid_cols_spin.setValue(2)
        self.grid_cols_spin.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
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
        self.sync_combo = QComboBox()
        self.sync_combo.addItems(["按最短时长截断", "按最长时长循环"])
        self.sync_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.sim_aspect_check = QCheckBox("保持比例")
        self.sim_aspect_check.setChecked(True)
        self.sim_aspect_check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)        
        self.sim_width_spin = QSpinBox()
        self.sim_width_spin.setRange(16, 1920)
        self.sim_width_spin.setValue(400)
        self.sim_width_spin.setSuffix(" px")
        self.sim_width_spin.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.sim_height_spin = QSpinBox()
        self.sim_height_spin.setRange(16, 1080)
        self.sim_height_spin.setValue(400)
        self.sim_height_spin.setSuffix(" px")
        self.sim_height_spin.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        x_label = QLabel(" × ")
        x_label.setFixedWidth(12)
        x_label.setAlignment(Qt.AlignCenter)
        x_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        row_sim1 = QHBoxLayout()
        row_sim1.addWidget(QLabel("拼接方式:"))
        row_sim1.addWidget(self.merge_combo, 1)
        row_sim1.addWidget(QLabel("背景色:"))
        row_sim1.addWidget(self.color_btn)
        row_sim2 = QHBoxLayout()
        row_sim2.addWidget(self.grid_rows_label)
        row_sim2.addWidget(self.grid_rows_spin, 1)
        row_sim2.addWidget(self.grid_cols_label)
        row_sim2.addWidget(self.grid_cols_spin, 1)
        row_sim3 = QHBoxLayout()
        row_sim3.addWidget(QLabel("边距:"))
        row_sim3.addWidget(self.margin_spin, 1)
        row_sim3.addWidget(QLabel("间距:"))
        row_sim3.addWidget(self.padding_spin, 1)
        row_sim4 = QHBoxLayout()
        row_sim4.addWidget(QLabel("播放时长:"))
        row_sim4.addWidget(self.sync_combo, 1)
        row_sim4.addWidget(self.sim_aspect_check)
        row_sim5 = QHBoxLayout()
        row_sim5.addWidget(QLabel("目标尺寸:"))
        row_sim5.addWidget(self.sim_width_spin, 1)
        row_sim5.addWidget(x_label)
        row_sim5.addWidget(self.sim_height_spin, 1)
        sim_layout = QVBoxLayout(self.sim_widget)
        sim_layout.setContentsMargins(0, 0, 0, 0)
        sim_layout.addLayout(row_sim1)
        sim_layout.addLayout(row_sim2)
        sim_layout.addLayout(row_sim3)
        sim_layout.addLayout(row_sim4)
        sim_layout.addLayout(row_sim5)
        layout.addWidget(self.sim_widget)

        layout.addStretch()

        self.group_combo.currentIndexChanged.connect(self._on_group_changed)
        self.group_combo.currentIndexChanged.connect(self.changed)
        self.prefix_spin.valueChanged.connect(self.changed)
        self.group_spin.valueChanged.connect(self.changed)
        self.play_combo.currentIndexChanged.connect(self._on_play_changed)
        self.play_combo.currentIndexChanged.connect(self.changed)
        self.speed_spin.valueChanged.connect(self.changed)
        self.loop_spin.valueChanged.connect(self.changed)
        self.size_combo.currentIndexChanged.connect(self._on_seq_size_changed)
        self.size_combo.currentIndexChanged.connect(self.changed)
        self.width_spin.valueChanged.connect(self.changed)
        self.height_spin.valueChanged.connect(self.changed)
        self.seq_aspect_check.stateChanged.connect(self.changed)
        self.merge_combo.currentIndexChanged.connect(self._on_layout_changed)
        self.merge_combo.currentIndexChanged.connect(self.changed)
        self.color_btn.clicked.connect(self._on_bg_color_clicked)
        self.color_btn.clicked.connect(self.changed)
        self.margin_spin.valueChanged.connect(self.changed)
        self.padding_spin.valueChanged.connect(self.changed)
        self.grid_rows_spin.valueChanged.connect(self.changed)
        self.grid_cols_spin.valueChanged.connect(self.changed)
        self.sync_combo.currentIndexChanged.connect(self.changed)
        self.sim_aspect_check.stateChanged.connect(self.changed)
        self.sim_width_spin.valueChanged.connect(self.changed)
        self.sim_height_spin.valueChanged.connect(self.changed)

        self._on_group_changed()
        self._on_play_changed()
        self._on_seq_size_changed()
        self._on_layout_changed()

    def _on_group_changed(self):
        """分组方式切换时显示/隐藏前缀长度或每组数量控件"""
        mode = self.group_combo.currentIndex()
        self.prefix_spin.setVisible(mode == 0)
        self.group_spin.setVisible(mode == 1)

    def _on_play_changed(self):
        """播放类型切换时显示对应的设置面板"""
        is_seq = (self.play_combo.currentIndex() == 0)
        self.seq_widget.setVisible(is_seq)
        self.sim_widget.setVisible(not is_seq)
        if not is_seq:
            self._update_grid_visibility()

    def _on_seq_size_changed(self):
        """顺序播放的尺寸模式切换时显示/隐藏自定义宽高"""
        is_custom = (self.size_combo.currentIndex() == 1)
        self.custom_size_widget.setVisible(is_custom)
        self.seq_aspect_check.setVisible(is_custom)

    def _on_layout_changed(self):
        """拼接方式切换时显示/隐藏网格行列数"""
        self._update_grid_visibility()
        self.changed.emit()

    def _update_grid_visibility(self):
        """根据当前拼接方式更新网格行列数的可见性"""
        is_grid = (self.merge_combo.currentIndex() == 2)
        self.grid_rows_label.setVisible(is_grid)
        self.grid_rows_spin.setVisible(is_grid)
        self.grid_cols_label.setVisible(is_grid)
        self.grid_cols_spin.setVisible(is_grid)

    def _on_bg_color_clicked(self):
        """弹出颜色选择器设置背景色"""
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name().upper()
            self.color_btn.setStyleSheet(
                f"background-color: {hex_color}; border: 1px solid #ccc; border-radius: 3px;"
            )
            self.color_btn.setProperty("color_hex", hex_color)
            self.changed.emit()


def build_panel() -> QWidget:
    """构建面板实例"""
    return GifMergePanel()


def collect_settings(panel: GifMergePanel) -> dict:
    """收集面板设置"""
    bg_hex = panel.color_btn.property("color_hex")
    if not bg_hex:
        bg_hex = "#FFFFFF"

    return {
        "group_combo": panel.group_combo.currentIndex(),
        "prefix_len": panel.prefix_spin.value(),
        "group_size": panel.group_spin.value(),
        "play_combo": panel.play_combo.currentIndex(),
        "speed_spin": panel.speed_spin.value(),
        "loop_spin": panel.loop_spin.value(),
        "size_combo": panel.size_combo.currentIndex(),
        "target_width": panel.width_spin.value(),
        "target_height": panel.height_spin.value(),
        "merge_combo": panel.merge_combo.currentIndex(),
        "bg_color": bg_hex,
        "margin": panel.margin_spin.value(),
        "padding": panel.padding_spin.value(),
        "grid_rows": panel.grid_rows_spin.value(),
        "grid_cols": panel.grid_cols_spin.value(),
        "sync_combo": panel.sync_combo.currentIndex(),
        "sim_keep_ratio": panel.sim_aspect_check.isChecked(),
        "sim_width": panel.sim_width_spin.value(),
        "sim_height": panel.sim_height_spin.value(),
        "seq_keep_ratio": panel.seq_aspect_check.isChecked(),
    }


def prepare_preview(items, settings):
    """生成预览信息"""
    group_idx = settings.get("group_combo", 0)
    prefix_len = settings.get("prefix_len", 9)
    group_size = settings.get("group_size", 5)
    play_map = ["顺序播放", "同时播放"]
    play_text = play_map[settings.get("play_combo", 0)]
    speed = settings.get("speed_spin", 100)
    loop = settings.get("loop_spin", 0)
    duration_align_text = ["按最短时长截断", "按最长时长循环"][settings.get("sync_combo", 0)]
    sim_keep_ratio_text = "保持比例" if settings.get("sim_keep_ratio", True) else "拉伸"
    seq_keep_text = "保持比例" if settings.get("seq_keep_ratio", True) else "拉伸"

    file_paths = [it.input_path for it in items]
    groups = {}
    for it in items:
        key = get_group_key(it.input_path, group_idx, prefix_len, group_size, file_paths)
        groups.setdefault(key, []).append(it.input_path)

    for it in items:
        key = get_group_key(it.input_path, group_idx, prefix_len, group_size, file_paths)
        display_key = "全部文件" if key == "__all__" else (os.path.basename(key) if group_idx == 2 else key)

        if getattr(it, "processed", False):
            base = os.path.splitext(it.output_name)[0]
        else:
            base = os.path.splitext(os.path.basename(it.input_path))[0]
        it.output_name = base + ".gif"

        if play_text == "顺序播放":
            ratio_text = seq_keep_text
        else:
            ratio_text = sim_keep_ratio_text

        it.preview_extra = {
            "A": f"组「{display_key}」共 {len(groups[key])} 个文件，{play_text}, {speed}ms, 循环:{loop}，{duration_align_text}，{ratio_text}"
        }
        it.preview_extra["group_key"] = display_key


def _get_gif_frames(gif_path):
    """提取 GIF 的所有帧和每帧延迟"""
    frames = []
    delays = []
    with Image.open(gif_path) as im:
        for frame in ImageSequence.Iterator(im):
            frames.append(frame.copy())
            try:
                delay = im.info.get('duration', 100)
            except Exception:
                delay = 100
            delays.append(delay)
    return frames, delays


def _resize_frame(frame, target_size, sim_keep_ratio=True):
    """缩放单帧图像"""
    if sim_keep_ratio:
        frame.thumbnail(target_size, Image.Resampling.LANCZOS)
    else:
        frame = frame.resize(target_size, Image.Resampling.LANCZOS)
    return frame


def _create_canvas(size, bg_color):
    """创建指定尺寸和背景色的画布"""
    if bg_color:
        bg = Image.new('RGB', size, bg_color)
    else:
        bg = Image.new('RGBA', size, (0, 0, 0, 0))
    return bg


def _merge_sequential(frames_list, delays_list, settings):
    """顺序拼接多个 GIF：将所有帧依次连接"""
    all_frames = []
    all_delays = []
    size_combo = settings.get('size_combo', 0)
    custom_w = settings.get('target_width')
    custom_h = settings.get('target_height')
    seq_keep_ratio = settings.get('seq_keep_ratio', True)

    if size_combo == 0:
        target_w = frames_list[0][0].width if frames_list else 200
        target_h = frames_list[0][0].height if frames_list else 200
    else:
        target_w = int(custom_w) if custom_w else 200
        target_h = int(custom_h) if custom_h else 200

    for gif_idx, frames in enumerate(frames_list):
        for frame in frames:
            frame = _resize_frame(frame, (target_w, target_h), sim_keep_ratio=seq_keep_ratio)
            all_frames.append(frame)
            if gif_idx < len(delays_list) and delays_list[gif_idx]:
                all_delays.append(delays_list[gif_idx][0])
            else:
                all_delays.append(settings.get('speed_spin', 100))

    return all_frames, all_delays


def _merge_simultaneous(frames_list, delays_list, settings):
    """同时拼接多个 GIF：按帧序号对齐，拼成一帧"""
    layout_idx = settings.get('merge_combo', 0)
    margin = settings.get('margin', 0)
    padding = settings.get('padding', 0)
    sim_w = settings.get('sim_width', 200)
    sim_h = settings.get('sim_height', 200)
    bg_color = settings.get('bg_color', '#FFFFFF')
    grid_rows = settings.get('grid_rows', 2)
    grid_cols = settings.get('grid_cols', 3)
    sync_idx = settings.get('sync_combo', 0)

    frame_counts = [len(frames) for frames in frames_list]
    if sync_idx == 0:
        target_frame_count = min(frame_counts) if frame_counts else 1
    else:
        target_frame_count = max(frame_counts) if frame_counts else 1

    adjusted_frames = []
    adjusted_delays = []
    for frames, delays in zip(frames_list, delays_list):
        if len(frames) >= target_frame_count:
            adjusted_frames.append(frames[:target_frame_count])
            adjusted_delays.append(delays[:target_frame_count])
        else:
            new_frames = []
            new_delays = []
            while len(new_frames) < target_frame_count:
                for i, f in enumerate(frames):
                    new_frames.append(f.copy())
                    new_delays.append(delays[i % len(delays)])
                    if len(new_frames) >= target_frame_count:
                        break
            adjusted_frames.append(new_frames)
            adjusted_delays.append(new_delays)

    num_gifs = len(adjusted_frames)

    if layout_idx == 0:
        cols = num_gifs
        rows = 1
    elif layout_idx == 1:
        cols = 1
        rows = num_gifs
    else:
        cols = grid_cols
        rows = math.ceil(num_gifs / grid_cols)

    cell_width = sim_w + padding * 2
    cell_height = sim_h + padding * 2
    canvas_w = cols * cell_width + margin * 2
    canvas_h = rows * cell_height + margin * 2

    canvas = _create_canvas((canvas_w, canvas_h), bg_color)

    result_frames = []
    result_delays = []

    for frame_idx in range(target_frame_count):
        frame_canvas = canvas.copy()

        for gif_idx in range(num_gifs):
            row = gif_idx // cols
            col = gif_idx % cols
            x = margin + col * cell_width + padding
            y = margin + row * cell_height + padding

            frame = adjusted_frames[gif_idx][frame_idx]

            sim_keep_ratio = settings.get('sim_keep_ratio', True)
            if sim_keep_ratio:
                frame = _resize_frame(frame, (sim_w, sim_h), sim_keep_ratio=True)
            else:
                frame = _resize_frame(frame, (sim_w, sim_h), sim_keep_ratio=False)

            if frame.mode == 'RGBA':
                frame_canvas.paste(frame, (x, y), frame)
            else:
                frame_canvas.paste(frame, (x, y))

        result_frames.append(frame_canvas)
        result_delays.append(settings.get('speed_spin', 100))

    return result_frames, result_delays


def run_batch(items, settings, get_output_dir, get_output_name_for_group,
              log_callback=None, progress_callback=None, stop_check=None):
    """批量合并 GIF"""
    if not items:
        return []

    group_idx = settings.get("group_combo", 0)
    prefix_len = settings.get("prefix_len", 9)
    group_size = settings.get("group_size", 5)
    play_idx = settings.get('play_combo', 0)
    speed = settings.get('speed_spin', 100)
    loop = settings.get('loop_spin', 0)
    custom_names = settings.get("custom_names", [])

    file_paths = [it.input_path for it in items]
    groups = {}
    for item in items:
        key = get_group_key(item.input_path, group_idx, prefix_len, group_size, file_paths)
        groups.setdefault(key, []).append(item)

    output_files = []
    total_groups = len(groups)
    processed = 0

    for group_key, group_items in groups.items():
        if stop_check and stop_check():
            if log_callback:
                log_callback("⛔ 用户终止任务")
            break

        if progress_callback:
            progress_callback(int(processed / total_groups * 100))

        if log_callback:
            display_key = "全部文件" if group_key == "__all__" else group_key
            log_callback(f"正在合并GIF组：{display_key}（共 {len(group_items)} 个文件）")

        frames_list = []
        delays_list = []
        for fi in group_items:
            try:
                frames, delays = _get_gif_frames(fi.input_path)
                frames_list.append(frames)
                delays_list.append(delays)
            except Exception as e:
                if log_callback:
                    log_callback(f"❌ 读取 {os.path.basename(fi.input_path)} 失败：{e}")
                continue

        if not frames_list:
            if log_callback:
                log_callback(f"⚠️ 组 {group_key} 没有有效GIF，跳过")
            continue

        if play_idx == 0:
            result_frames, result_delays = _merge_sequential(frames_list, delays_list, settings)
        else:
            result_frames, result_delays = _merge_simultaneous(frames_list, delays_list, settings)

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

        out_name = f"{base_name}.gif"
        base, ext = os.path.splitext(out_name)
        out_path = get_unique_file_path(out_dir, base, ext)

        try:
            result_frames[0].save(
                out_path,
                save_all=True,
                append_images=result_frames[1:],
                duration=result_delays if result_delays else speed,
                loop=loop if loop >= 0 else 0,
                optimize=True
            )
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
        log_callback("✅ 全部GIF合并完成！")

    return output_files

def run_task(file_item, settings):
    """GIF 合并不支持单任务模式"""
    raise NotImplementedError("GIF 合并功能请使用 run_batch，不要使用 run_task")
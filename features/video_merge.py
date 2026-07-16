# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import shutil
import subprocess
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox,
    QPushButton, QFileDialog, QMessageBox
)
from core.utils import get_group_key, load_app_config, save_app_config, get_ffmpeg_path


class VideoMergePanel(QWidget):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.ffmpeg_path = get_ffmpeg_path()
        v = QVBoxLayout(self)
        v.setSpacing(8)

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

        v.addLayout(group_row)

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("输出格式:"))
        self.out_format = QComboBox()
        self.out_format.addItems(["mp4", "mkv", "avi", "mov"])
        fmt_row.addWidget(self.out_format, 1)
        v.addLayout(fmt_row)

        codec_row = QHBoxLayout()
        codec_row.addWidget(QLabel("编码方式:"))
        self.codec_mode = QComboBox()
        self.codec_mode.addItems(["直接合并（快速）", "重新编码（兼容）"])
        self.codec_mode.currentIndexChanged.connect(self._on_codec_mode_changed)
        codec_row.addWidget(self.codec_mode, 1)
        v.addLayout(codec_row)

        self.encoder_widget = QWidget()
        encoder_row = QHBoxLayout(self.encoder_widget)
        encoder_row.setContentsMargins(0, 0, 0, 0)
        encoder_row.addWidget(QLabel("视频编码器:"))
        self.video_codec = QComboBox()
        self.video_codec.addItems([
            "libx264（推荐）",
            "libx265（文件更小）",
            "h264_nvenc（显卡加速）",
            "hevc_nvenc（显卡加速）"
        ])
        encoder_row.addWidget(self.video_codec, 1)
        v.addWidget(self.encoder_widget)

        self.preset_widget = QWidget()
        preset_row = QHBoxLayout(self.preset_widget)
        preset_row.setContentsMargins(0, 0, 0, 0)
        preset_row.addWidget(QLabel("预设:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["快速", "平衡", "高质量"])
        preset_row.addWidget(self.preset_combo, 1)
        v.addWidget(self.preset_widget)

        ffmpeg_row = QHBoxLayout()
        ffmpeg_row.addWidget(QLabel("FFmpeg 路径:"))
        self.ffmpeg_path_label = QLabel(self.ffmpeg_path if self.ffmpeg_path else "未找到")
        self.ffmpeg_path_label.setWordWrap(False)
        self.ffmpeg_path_label.setStyleSheet("color: #555;")
        if self.ffmpeg_path:
            self.ffmpeg_path_label.setToolTip(self.ffmpeg_path)
        self.ffmpeg_path_label.setMinimumWidth(200)
        ffmpeg_row.addWidget(self.ffmpeg_path_label, 1)
        v.addLayout(ffmpeg_row)

        self.ffmpeg_btn = QPushButton("手动指定 FFmpeg 路径")
        self.ffmpeg_btn.clicked.connect(self.select_ffmpeg_path)
        v.addWidget(self.ffmpeg_btn)

        v.addStretch()

        self.group_mode.currentIndexChanged.connect(self.changed)
        self.prefix_spin.valueChanged.connect(self.changed)
        self.group_spin.valueChanged.connect(self.changed)
        self.out_format.currentIndexChanged.connect(self.changed)
        self.codec_mode.currentIndexChanged.connect(self.changed)
        self.video_codec.currentIndexChanged.connect(self.changed)
        self.preset_combo.currentIndexChanged.connect(self.changed)

        self._toggle_options()
        self._on_codec_mode_changed()

    def _toggle_options(self):
        mode = self.group_mode.currentIndex()
        self.prefix_spin.setVisible(mode == 0)
        self.group_spin.setVisible(mode == 1)

    def _on_codec_mode_changed(self):
        is_direct = self.codec_mode.currentIndex() == 0
        self.encoder_widget.setVisible(not is_direct)
        self.preset_widget.setVisible(not is_direct)

    def select_ffmpeg_path(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 FFmpeg 可执行文件", "",
            "FFmpeg 可执行文件 (ffmpeg.exe);;所有文件 (*.*)"
        )
        if path:
            try:
                subprocess.run([path, "-version"], capture_output=True, check=True)
                save_app_config("ffmpeg_path", path)
                self.ffmpeg_path = path
                self.ffmpeg_path_label.setText(path)
                self.ffmpeg_path_label.setToolTip(path)
                QMessageBox.information(self, "成功", "FFmpeg 路径已设置并保存。")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"所选文件不是有效的 FFmpeg 可执行文件：{e}")


def build_panel() -> QWidget:
    return VideoMergePanel()


def collect_settings(panel: VideoMergePanel) -> dict:
    return {
        "group_mode": panel.group_mode.currentIndex(),
        "prefix_len": panel.prefix_spin.value(),
        "group_size": panel.group_spin.value(),
        "out_format": panel.out_format.currentText(),
        "codec_mode": panel.codec_mode.currentIndex(),
        "video_codec": panel.video_codec.currentText(),
        "preset": panel.preset_combo.currentText(),
    }


def prepare_preview(items, settings):
    group_mode = settings.get("group_mode", 0)
    prefix_len = settings.get("prefix_len", 9)
    group_size = settings.get("group_size", 5)
    out_format = settings.get("out_format", "mp4")

    file_paths = [it.input_path for it in items]
    groups = {}
    for it in items:
        key = get_group_key(it.input_path, group_mode, prefix_len, group_size, file_paths)
        groups.setdefault(key, []).append(it.input_path)

    for it in items:
        key = get_group_key(it.input_path, group_mode, prefix_len, group_size, file_paths)
        display_key = "全部文件" if key == "__all__" else (os.path.basename(key) if group_mode == 2 else key)
        it.preview_extra = {"A": f"视频合并：组「{display_key}」共 {len(groups[key])} 个 → .{out_format}"}
        it.preview_extra["group_key"] = display_key


def merge_videos(video_paths: list, output_path: str, settings: dict):
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        raise RuntimeError("未找到 FFmpeg，请安装并添加到 PATH，或手动指定路径")

    codec_mode = settings.get("codec_mode", 0)
    out_format = settings.get("out_format", "mp4")
    video_codec = settings.get("video_codec", "libx264")
    preset_map = {"快速": "fast", "平衡": "medium", "高质量": "slow"}
    preset = preset_map.get(settings.get("preset", "平衡"), "medium")

    if len(video_paths) == 1:
        shutil.copy2(video_paths[0], output_path)
        return

    list_path = os.path.join(os.path.dirname(output_path), "ffmpeg_list.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for path in video_paths:
            abs_path = os.path.abspath(path)
            f.write(f"file '{abs_path.replace('\\', '/')}'\n")

    try:
        if codec_mode == 0:
            cmd = [
                ffmpeg,
                "-f", "concat",
                "-safe", "0",
                "-i", list_path,
                "-c", "copy",
                "-y",
                output_path
            ]
        else:
            cmd = [
                ffmpeg,
                "-f", "concat",
                "-safe", "0",
                "-i", list_path,
                "-c:v", video_codec,
                "-preset", preset,
                "-c:a", "aac",
                "-b:a", "192k",
                "-y",
                output_path
            ]

        subprocess.run(cmd, check=True, capture_output=True, text=True)

    finally:
        if os.path.exists(list_path):
            os.remove(list_path)


def run_batch(items, settings, get_output_dir, get_output_name_for_group,
              log_callback=None, progress_callback=None, stop_check=None):
    if not items:
        return []

    group_mode = settings.get("group_mode", 0)
    prefix_len = settings.get("prefix_len", 9)
    group_size = settings.get("group_size", 5)
    out_format = settings.get("out_format", "mp4")

    file_paths = [it.input_path for it in items]
    groups = {}
    for item in items:
        key = get_group_key(item.input_path, group_mode, prefix_len, group_size, file_paths)
        groups.setdefault(key, []).append(item)

    output_files = []
    total_groups = len(groups)
    processed = 0

    for group_key, group_items in groups.items():
        if progress_callback:
            progress_callback(int(processed / total_groups * 100))

        if stop_check and stop_check():
            if log_callback:
                log_callback("⛔ 用户终止任务")
            break

        if log_callback:
            display_key = "全部文件" if group_key == "__all__" else group_key
            log_callback(f"正在合并组：{display_key}（共 {len(group_items)} 个文件）")

        out_dir = get_output_dir(group_items[0])

        if group_key == "__all__":
            base_name = get_output_name_for_group("全部")
        elif group_mode == 2:
            base_name = get_output_name_for_group(os.path.basename(group_key))
        else:
            base_name = get_output_name_for_group(group_key)

        out_name = f"{base_name}.{out_format}"
        out_path = os.path.join(out_dir, out_name)

        if os.path.exists(out_path):
            counter = 1
            while os.path.exists(os.path.join(out_dir, f"{base_name}_{counter}.{out_format}")):
                counter += 1
            out_path = os.path.join(out_dir, f"{base_name}_{counter}.{out_format}")

        video_paths = [fi.input_path for fi in group_items]

        try:
            merge_videos(video_paths, out_path, settings)
            output_files.append(out_path)
            for fi in group_items:
                fi.status = "完成"
                fi.output_name = os.path.basename(out_path)
                fi.output_dir = out_dir
        except Exception as e:
            for fi in group_items:
                fi.status = "错误"
            if log_callback:
                log_callback(f"❌ 组「{group_key}」合并失败：{e}")
            raise

        processed += 1

    if log_callback:
        log_callback("✅ 全部视频合并完成！")

    return output_files


def run_task(file_item, settings):
    raise NotImplementedError("视频合并功能请使用 run_batch，不要使用 run_task")
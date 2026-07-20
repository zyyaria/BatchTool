# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import sys
import shutil
import subprocess
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox,
    QPushButton, QFileDialog, QMessageBox, QSizePolicy
)
from core.utils import get_group_key, save_app_config, get_ffmpeg_path, get_unique_file_path


class VideoMergePanel(QWidget):
    changed = Signal()

    def __init__(self):
        """初始化设置面板"""
        super().__init__()
        self.ffmpeg_path = get_ffmpeg_path()
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
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp4", "mkv", "avi", "mov"])
        self.format_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(["直接合并（快速）", "重新编码（兼容）"])
        self.codec_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.encoder_widget = QWidget()
        self.encoder_combo = QComboBox()
        self.encoder_combo.addItems(["libx264（推荐）", "libx265（文件更小）", "h264_nvenc（显卡加速）", "hevc_nvenc（显卡加速）"])
        self.encoder_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.preset_widget = QWidget()
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["快速", "平衡", "高质量"])
        self.preset_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  

        row_param1 = QHBoxLayout()
        row_param1.addWidget(QLabel("分组方式:"))
        row_param1.addWidget(self.group_combo, 1)
        row_param1.addWidget(self.prefix_spin, 1)
        row_param1.addWidget(self.group_spin, 1)
        row_param2 = QHBoxLayout()
        row_param2.addWidget(QLabel("目标格式:"))
        row_param2.addWidget(self.format_combo, 1)       
        row_param3 = QHBoxLayout()
        row_param3.addWidget(QLabel("编码方式:"))
        row_param3.addWidget(self.codec_combo, 1)        
        row_param4 = QHBoxLayout(self.encoder_widget)
        row_param4.setContentsMargins(0, 0, 0, 0)
        row_param4.addWidget(QLabel("视频编码器:"))
        row_param4.addWidget(self.encoder_combo, 1)
        row_param5 = QHBoxLayout(self.preset_widget)
        row_param5.setContentsMargins(0, 0, 0, 0)
        row_param5.addWidget(QLabel("预设:"))
        row_param5.addWidget(self.preset_combo, 1)
        layout.addLayout(row_param1)
        layout.addLayout(row_param2)
        layout.addLayout(row_param3)
        layout.addWidget(self.encoder_widget)
        layout.addWidget(self.preset_widget)

        self.ffmpeg_label = QLabel(self.ffmpeg_path if self.ffmpeg_path else "未找到")
        self.ffmpeg_label.setWordWrap(False)
        self.ffmpeg_label.setStyleSheet("color: #555;")
        self.ffmpeg_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        if self.ffmpeg_path:
            self.ffmpeg_label.setToolTip(self.ffmpeg_path)
        self.ffmpeg_btn = QPushButton("手动指定 FFmpeg 路径")
        self.ffmpeg_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)        
        
        row_ffmpeg = QHBoxLayout()
        row_ffmpeg.addWidget(QLabel("FFmpeg 路径:"))
        row_ffmpeg.addWidget(self.ffmpeg_label, 1)
        layout.addLayout(row_ffmpeg)
        layout.addWidget(self.ffmpeg_btn, 1)

        layout.addStretch()

        self.group_combo.currentIndexChanged.connect(self._toggle_options)
        self.group_combo.currentIndexChanged.connect(self.changed)
        self.prefix_spin.valueChanged.connect(self.changed)
        self.group_spin.valueChanged.connect(self.changed)
        self.format_combo.currentIndexChanged.connect(self.changed)
        self.codec_combo.currentIndexChanged.connect(self._on_codec_combo_changed)
        self.codec_combo.currentIndexChanged.connect(self.changed)
        self.encoder_combo.currentIndexChanged.connect(self.changed)
        self.preset_combo.currentIndexChanged.connect(self.changed)
        self.ffmpeg_btn.clicked.connect(self.select_ffmpeg_path)

        self._toggle_options()
        self._on_codec_combo_changed()

    def _toggle_options(self):
        mode = self.group_combo.currentIndex()
        self.prefix_spin.setVisible(mode == 0)
        self.group_spin.setVisible(mode == 1)

    def _on_codec_combo_changed(self):
        is_direct = self.codec_combo.currentIndex() == 0
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
                self.ffmpeg_label.setText(path)
                self.ffmpeg_label.setToolTip(path)
                QMessageBox.information(self, "成功", "FFmpeg 路径已设置并保存。")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"所选文件不是有效的 FFmpeg 可执行文件：{e}")


def build_panel() -> QWidget:
    """构建面板实例"""
    return VideoMergePanel()


def collect_settings(panel: VideoMergePanel) -> dict:
    """收集面板设置"""
    encoder_text = panel.encoder_combo.currentText()
    encoder = encoder_text.split('（')[0] if '（' in encoder_text else encoder_text
    return {
        "group_combo": panel.group_combo.currentIndex(),
        "prefix_len": panel.prefix_spin.value(),
        "group_size": panel.group_spin.value(),
        "format_combo": panel.format_combo.currentText(),
        "codec_combo": panel.codec_combo.currentIndex(),
        "encoder_combo": encoder,
        "preset": panel.preset_combo.currentText(),
    }


def prepare_preview(items, settings):
    """生成预览信息"""
    group_combo = settings.get("group_combo", 0)
    prefix_len = settings.get("prefix_len", 9)
    group_size = settings.get("group_size", 5)
    format_combo = settings.get("format_combo", "mp4")
    codec_combo = settings.get("codec_combo", 0)
    encoder_combo = settings.get("encoder_combo", "libx264（推荐）")
    preset = settings.get("preset", "平衡")

    file_paths = [it.input_path for it in items]
    groups = {}
    for it in items:
        key = get_group_key(it.input_path, group_combo, prefix_len, group_size, file_paths)
        groups.setdefault(key, []).append(it.input_path)

    for it in items:
        key = get_group_key(it.input_path, group_combo, prefix_len, group_size, file_paths)
        display_key = "全部文件" if key == "__all__" else (os.path.basename(key) if group_combo == 2 else key)
        count = len(groups[key])
        method = "直接合并" if codec_combo == 0 else f"重新编码（{encoder_combo}，{preset}）"
        it.preview_extra = {
            "A": f"视频合并：组「{display_key}」{count}个 → .{format_combo}，{method}"
        }
        it.preview_extra["group_key"] = display_key


def merge_videos(video_paths: list, output_path: str, settings: dict):
    """使用 FFmpeg 合并多个视频"""
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        raise RuntimeError("未找到 FFmpeg，请安装并添加到 PATH，或手动指定路径")

    codec_combo = settings.get("codec_combo", 0)
    format_combo = settings.get("format_combo", "mp4")
    encoder_combo = settings.get("encoder_combo", "libx264")
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
        if codec_combo == 0:
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
                "-c:v", encoder_combo,
                "-preset", preset,
                "-c:a", "aac",
                "-b:a", "192k",
                "-y",
                output_path
            ]

        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )

    finally:
        if os.path.exists(list_path):
            os.remove(list_path)


def run_batch(items, settings, get_output_dir, get_output_name_for_group,
              log_callback=None, progress_callback=None, stop_check=None):
    """批量合并视频"""
    if not items:
        return []

    group_combo = settings.get("group_combo", 0)
    prefix_len = settings.get("prefix_len", 9)
    group_size = settings.get("group_size", 5)
    format_combo = settings.get("format_combo", "mp4")

    file_paths = [it.input_path for it in items]
    groups = {}
    for item in items:
        key = get_group_key(item.input_path, group_combo, prefix_len, group_size, file_paths)
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
            display_key = "全部文件" if group_key == "__all__" else (os.path.basename(group_key) if group_combo == 2 else group_key)
            log_callback(f"正在合并组：{display_key}（共 {len(group_items)} 个文件）")

        out_dir = get_output_dir(group_items[0])

        if group_key == "__all__":
            base_name = get_output_name_for_group("全部")
        elif group_combo == 2:
            base_name = get_output_name_for_group(os.path.basename(group_key))
        else:
            base_name = get_output_name_for_group(group_key)

        if not base_name.endswith(f".{format_combo}"):
            base_name = f"{base_name}.{format_combo}"

        base, ext = os.path.splitext(base_name)
        out_path = get_unique_file_path(out_dir, base, ext)

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
    """视频合并不支持单任务模式"""
    raise NotImplementedError("视频合并功能请使用 run_batch，不要使用 run_task")
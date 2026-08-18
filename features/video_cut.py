# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import sys
import subprocess
from PySide6.QtCore import Signal, QTime, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QLineEdit, QCheckBox, QSizePolicy, QTimeEdit
)
from core.utils import get_ffmpeg_path, resource_path, select_ffmpeg_path


class VideoCutPanel(QWidget):
    changed = Signal()

    def __init__(self):
        """初始化设置面板"""
        super().__init__()
        self.ffmpeg_path = get_ffmpeg_path()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        row_ffmpeg = QHBoxLayout()
        self.ffmpeg_edit = QLineEdit()
        self.ffmpeg_edit.setText(self.ffmpeg_path if self.ffmpeg_path else "")
        self.ffmpeg_edit.setReadOnly(True)
        self.ffmpeg_edit.setPlaceholderText("未找到 FFmpeg，点击右侧图标选择")
        self.ffmpeg_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.ffmpeg_action = QAction(self)
        self.ffmpeg_action.setIcon(QIcon(resource_path("assets/folder.png")))
        self.ffmpeg_action.setToolTip("选择 FFmpeg 可执行文件")
        self.ffmpeg_action.triggered.connect(lambda: select_ffmpeg_path(self, self.ffmpeg_edit))
        self.ffmpeg_edit.addAction(self.ffmpeg_action, QLineEdit.TrailingPosition)
        row_ffmpeg.addWidget(QLabel("FFmpeg 路径:"))
        row_ffmpeg.addWidget(self.ffmpeg_edit, 1)
        layout.addLayout(row_ffmpeg)
        
        row_time = QHBoxLayout()    
        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("HH:mm:ss")
        self.start_time.setTime(QTime(0, 0, 0))
        self.start_time.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        to_label = QLabel("至")
        to_label.setAlignment(Qt.AlignCenter)
        to_label.setFixedWidth(12)
        to_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)             
        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("HH:mm:ss")
        self.end_time.setTime(QTime(0, 0, 0))
        self.end_time.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        row_time.addWidget(QLabel("截取时间:"))
        row_time.addWidget(self.start_time, 1)
        row_time.addWidget(to_label)
        row_time.addWidget(self.end_time, 1)
        layout.addLayout(row_time)

        row_fps = QHBoxLayout()
        self.fps_mode_combo = QComboBox()
        self.fps_mode_combo.addItems(["原帧率", "自定义"])
        self.fps_mode_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.fps_custom_combo = QComboBox()
        self.fps_custom_combo.addItems(["15", "24", "25", "30", "60"])
        self.fps_custom_combo.setCurrentIndex(3) 
        self.fps_custom_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.fps_custom_combo.setVisible(False)
        row_fps.addWidget(QLabel("输出帧率:"))
        row_fps.addWidget(self.fps_mode_combo, 1)
        row_fps.addWidget(self.fps_custom_combo, 1)
        layout.addLayout(row_fps)

        row_format = QHBoxLayout()   
        self.format_combo = QComboBox()
        self.format_combo.addItems(["原格式", "mp4", "mkv", "avi", "mov"])
        self.format_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.reencode_check = QCheckBox("重新编码")
        self.reencode_check.setChecked(False)
        self.reencode_check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)    
        row_format.addWidget(QLabel("目标格式:"))
        row_format.addWidget(self.format_combo, 1)
        row_format.addWidget(self.reencode_check) 
        layout.addLayout(row_format)
        
        layout.addStretch()

        self.start_time.timeChanged.connect(self.changed)
        self.end_time.timeChanged.connect(self.changed)
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        self.reencode_check.stateChanged.connect(self.changed)
        self.fps_mode_combo.currentIndexChanged.connect(self._on_fps_mode_changed)
        self.fps_mode_combo.currentIndexChanged.connect(self.changed)
        self.fps_custom_combo.currentIndexChanged.connect(self.changed)

        self._on_fps_mode_changed()

    def _update_reencode_state(self):
        """统一更新重新编码复选框状态"""
        fmt = self.format_combo.currentText()
        is_custom_fps = self.fps_mode_combo.currentIndex() == 1
        need_reencode = (fmt != "原格式") or is_custom_fps
        if need_reencode:
            self.reencode_check.setChecked(True)
            self.reencode_check.setEnabled(False)
            if fmt != "原格式" and is_custom_fps:
                self.reencode_check.setToolTip("改变目标格式 + 自定义帧率，必须重新编码")
            elif fmt != "原格式":
                self.reencode_check.setToolTip("改变目标格式必须重新编码，不可取消")
            else:
                self.reencode_check.setToolTip("自定义帧率必须重新编码，不可取消")
        else:
            self.reencode_check.setChecked(False)
            self.reencode_check.setEnabled(True)
            self.reencode_check.setToolTip("")

    def _on_fps_mode_changed(self):
        """输出帧率模式切换"""
        is_custom = self.fps_mode_combo.currentIndex() == 1
        self.fps_custom_combo.setVisible(is_custom)
        self._update_reencode_state()

    def _on_format_changed(self):
        """目标格式切换"""
        fmt = self.format_combo.currentText()
        is_custom_fps = self.fps_mode_combo.currentIndex() == 1
        need_reencode = (fmt != "原格式") or is_custom_fps
        if need_reencode:
            self.reencode_check.setChecked(True)
            self.reencode_check.setEnabled(False)
            if fmt != "原格式":
                self.reencode_check.setToolTip("改变目标格式必须重新编码，不可取消")
            else:
                self.reencode_check.setToolTip("自定义帧率必须重新编码，不可取消")
        else:
            self.reencode_check.setEnabled(True)
            self.reencode_check.setToolTip("")
        self._update_reencode_state()


def build_panel() -> QWidget:
    """构建面板实例"""
    return VideoCutPanel()


def collect_settings(panel: VideoCutPanel) -> dict:
    """收集面板设置"""
    start = panel.start_time.time()
    end = panel.end_time.time()
    fps_mode = panel.fps_mode_combo.currentIndex()
    return {
        "start_h": start.hour(),
        "start_m": start.minute(),
        "start_s": start.second(),
        "end_h": end.hour(),
        "end_m": end.minute(),
        "end_s": end.second(),
        "format": panel.format_combo.currentText(),
        "reencode": panel.reencode_check.isChecked(),
        "fps_mode": fps_mode,
        "fps_value": int(panel.fps_custom_combo.currentText()) if fps_mode == 1 else None,        
    }


def prepare_preview(items, settings):
    """生成预览信息"""
    sh = settings.get("start_h", 0)
    sm = settings.get("start_m", 0)
    ss = settings.get("start_s", 0)
    eh = settings.get("end_h", 0)
    em = settings.get("end_m", 0)
    es = settings.get("end_s", 0)
    fmt = settings.get("format", "原格式")
    reencode = settings.get("reencode", False)
    fps_mode = settings.get("fps_mode", 0)
    if fps_mode == 0:
        fps_display = "原帧率"
    else:
        fps_val = settings.get("fps_value", 30)
        fps_display = f"{fps_val} fps"
    start_str = f"{sh:02d}:{sm:02d}:{ss:02d}"
    end_str = f"{eh:02d}:{em:02d}:{es:02d}"
    for it in items:
        base = os.path.splitext(os.path.basename(it.input_path))[0]
        it.preview_extra = {
            "A": f"截取 {start_str} → {end_str}，输出{fmt if fmt!='原格式' else '原格式'}，{'重新编码' if reencode else '直接复制'}，{fps_display}"
        }


def _to_seconds(h, m, s):
    """将时分秒转换为总秒数"""
    return h * 3600 + m * 60 + s


def cut_video(input_path, output_path, start_sec, duration_sec, reencode=False, fps=None):
    """使用 FFmpeg 截取视频片段，支持自定义输出帧率"""
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        raise RuntimeError("未找到 FFmpeg，请安装并添加到 PATH，或手动指定路径")
    cmd = [ffmpeg, "-ss", str(start_sec), "-i", input_path]
    if duration_sec > 0:
        cmd.extend(["-t", str(duration_sec)])
    if fps is not None:
        cmd.extend(["-r", str(fps)])
        cmd.extend(["-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "-b:a", "128k"])
    elif not reencode:
        cmd.extend(["-c", "copy"])
    else:
        cmd.extend(["-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "-b:a", "128k"])
    cmd.extend(["-y", output_path])
    subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore',
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )


def run_task(file_item, settings):
    """执行单个视频截取任务"""
    sh = settings.get("start_h", 0)
    sm = settings.get("start_m", 0)
    ss = settings.get("start_s", 0)
    eh = settings.get("end_h", 0)
    em = settings.get("end_m", 0)
    es = settings.get("end_s", 0)
    start_sec = _to_seconds(sh, sm, ss)
    end_sec = _to_seconds(eh, em, es)
    if end_sec <= start_sec:
        raise ValueError("结束时间必须大于开始时间")
    duration_sec = end_sec - start_sec
    format = settings.get("format", "原格式")
    reencode = settings.get("reencode", False)
    fps_mode = settings.get("fps_mode", 0)
    if fps_mode == 1:
        fps = settings.get("fps_value", 30)
        reencode = True 
    else:
        fps = None
    src = file_item.input_path
    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, file_item.output_name)
    cut_video(src, out_path, start_sec, duration_sec, reencode, fps)
    file_item.status = "完成"
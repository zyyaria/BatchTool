# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import sys
import subprocess
import json
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, 
    QPushButton, QFileDialog, QMessageBox, QSizePolicy, QLineEdit, 
    QApplication
)
from core.utils import get_ffmpeg_path, resource_path, select_ffmpeg_path


class VideoChapterPanel(QWidget):
    changed = Signal()
    log_signal = Signal(str)

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
        
        row_import = QHBoxLayout()
        label = QLabel("全局书签列表")
        label.setStyleSheet("font-weight: 600; margin-top: 4px; margin-left: -3px")
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.import_btn = QPushButton("从文本文件导入")
        self.import_btn.setStyleSheet("font-size: 11px; padding: 4px 12px; min-height: 24px;")
        self.import_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row_import.addWidget(label)
        row_import.addStretch()
        row_import.addWidget(self.import_btn)
        layout.addLayout(row_import)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText(
            "每行一个章节，时间 标题（空格或 Tab 分隔）\n\n"
            "示例：\n"
            "00:00:00  片头\n"
            "00:00:30  开场白\n"
            "00:05:00  第一部分"
        )
        self.text_edit.setFixedHeight(150)
        self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.text_edit, 1)

        row_btn = QHBoxLayout()
        self.detect_btn = QPushButton("检测章节标记")
        self.detect_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.clear_btn = QPushButton("清除章节")
        self.clear_btn.setStyleSheet("background-color: #f44336; color: white;")
        self.clear_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_btn.addWidget(self.detect_btn, 1)
        row_btn.addWidget(self.clear_btn, 1)
        layout.addLayout(row_btn)

        layout.addStretch()

        self.import_btn.clicked.connect(self.import_from_file)
        self.detect_btn.clicked.connect(self.detect_chapters)
        self.clear_btn.clicked.connect(self.clear_chapters)
        self.text_edit.textChanged.connect(self.changed)

    def import_from_file(self):
        """从文本文件导入书签数据"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择章节数据文件", "",
            "文本文件 (*.txt);;CSV文件 (*.csv);;所有文件 (*.*)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_edit.setPlainText(content)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"读取文件失败：{e}")

    def detect_chapters(self):
        """检测视频文件的章节标记，并将结果输出到日志"""
        parent = self.parent()
        while parent and not hasattr(parent, 'preview_mgr'):
            parent = parent.parent()
        if not parent:
            QMessageBox.warning(self, "提示", "无法获取主窗口")
            return
        items = parent.preview_mgr.items
        if not items:
            QMessageBox.warning(self, "提示", "请先添加视频文件")
            return
        ffmpeg = get_ffmpeg_path()
        if not ffmpeg:
            QMessageBox.warning(self, "提示", "未找到 FFmpeg")
            return
        ffprobe = os.path.join(os.path.dirname(ffmpeg), "ffprobe")
        if not os.path.exists(ffprobe):
            ffprobe = "ffprobe"
        parent.append_log("")
        parent.append_log("========== 章节检测 ==========")
        for i, item in enumerate(items, 1):
            QApplication.processEvents()
            try:
                cmd = [
                    ffprobe,
                    "-v", "error",
                    "-show_entries", "format:chapters",
                    "-of", "json",
                    item.input_path
                ]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
                data = json.loads(result.stdout)
                chapters = data.get("chapters", [])
                if chapters:
                    parent.append_log(f"{i}. {os.path.basename(item.input_path)}:")
                    for ch in chapters:
                        start_time = float(ch.get("start_time", 0))
                        title = ch.get("tags", {}).get("title", "未命名")
                        h = int(start_time // 3600)
                        m = int((start_time % 3600) // 60)
                        s = start_time % 60
                        time_str = f"{h:02d}:{m:02d}:{s:05.2f}".replace(".", ":")
                        parent.append_log(f"   {time_str}  {title}")
                else:
                    parent.append_log(f"{i}. {os.path.basename(item.input_path)}: 无章节")
            except Exception as e:
                parent.append_log(f"{i}. {os.path.basename(item.input_path)}: ❌ {str(e)}")
        parent.append_log("========== 检测完成 ==========")

    def clear_chapters(self):
        """清除视频文件的章节标记（彻底清除）"""
        parent = self.parent()
        while parent and not hasattr(parent, 'preview_mgr'):
            parent = parent.parent()
        if not parent:
            QMessageBox.warning(self, "提示", "无法获取主窗口")
            return
        items = parent.preview_mgr.items
        if not items:
            QMessageBox.warning(self, "提示", "请先添加视频文件")
            return
        reply = QMessageBox.question(
            self, "确认清除",
            "确定要清除所有视频的章节标记吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        ffmpeg = get_ffmpeg_path()
        if not ffmpeg:
            QMessageBox.warning(self, "提示", "未找到 FFmpeg")
            return
        cleared = []
        failed = []
        for item in items:
            QApplication.processEvents()
            original_path = item.input_path
            ext = os.path.splitext(original_path)[1]
            temp_path = original_path + ".temp" + ext
            try:
                cmd = [
                    ffmpeg,
                    "-i", original_path,
                    "-map", "0",
                    "-c", "copy",
                    "-map_metadata", "-1",
                    "-map_chapters", "-1",
                    "-movflags", "+faststart",
                    "-y",
                    temp_path
                ]
                subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
                if self._has_chapters(temp_path):
                    cmd2 = [
                        ffmpeg,
                        "-i", original_path,
                        "-map", "0:v",
                        "-map", "0:a",
                        "-c", "copy",
                        "-map_metadata", "-1",
                        "-movflags", "+faststart",
                        "-y",
                        temp_path
                    ]
                    subprocess.run(
                        cmd2,
                        check=True,
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                    )
                os.replace(temp_path, original_path)
                cleared.append(os.path.basename(original_path))
                item.custom_chapters = ""
            except Exception as e:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                failed.append(f"{os.path.basename(original_path)}: {e}")
        if cleared:
            parent.append_log(f"已清除：{', '.join(cleared)}")
            parent.append_log("提示：如果播放器仍显示章节，请重启播放器清除缓存。")
        if failed:
            parent.append_log(f"❌ 清除失败：{', '.join(failed)}")
        if not cleared and not failed:
            parent.append_log("所有文件均无章节，无需清除")
        parent.refresh_feature_preview()
        parent.refresh_table()

    def _has_chapters(self, video_path: str) -> bool:
        """检测视频文件是否包含章节"""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format:chapters",
                "-of", "json",
                video_path
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            data = json.loads(result.stdout)
            chapters = data.get("chapters", [])
            return len(chapters) > 0
        except:
            return True
        

def build_panel() -> QWidget:
    """构建面板实例"""
    return VideoChapterPanel()


def collect_settings(panel: VideoChapterPanel) -> dict:
    """收集面板设置"""
    return {
        "text": panel.text_edit.toPlainText(),
    }


def prepare_preview(items, settings):
    """生成预览信息"""
    global_text = settings.get("text", "").strip()
    for it in items:
        custom_text = getattr(it, "custom_chapters", "")
        text_to_use = custom_text if custom_text.strip() else global_text
        count = 0
        if text_to_use:
            for line in text_to_use.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    count += 1
        it.preview_extra = {"A": f"视频章节：{count}条"}


def parse_chapters(text: str) -> list:
    """解析用户输入的章节文本"""
    chapters = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if '\t' in line:
            parts = line.split('\t')
        else:
            parts = line.split(None, 1)
        if len(parts) < 2:
            continue
        time_str = parts[0].strip()
        title = parts[1].strip()
        seconds = _parse_time(time_str)
        if seconds is None:
            continue
        chapters.append((seconds, title))
    return chapters


def _parse_time(time_str: str) -> float:
    """将时间字符串转换为秒数"""
    parts = time_str.split(":")
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    elif len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    return None


def write_chapters_to_video(input_path: str, output_path: str, chapters: list, overwrite: bool):
    """将章节写入视频文件（从 input_path 读取，写入 output_path）"""
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        raise RuntimeError("未找到 FFmpeg")
    if not chapters:
        return
    if os.path.abspath(input_path) == os.path.abspath(output_path):
        temp_path = output_path + ".temp" + os.path.splitext(output_path)[1]
        _write_chapters_internal(input_path, temp_path, chapters)
        os.replace(temp_path, output_path)
    else:
        _write_chapters_internal(input_path, output_path, chapters)


def _write_chapters_internal(input_path: str, output_path: str, chapters: list):
    """内部写入函数"""
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        raise RuntimeError("未找到 FFmpeg")
    metadata_lines = [";FFMETADATA1"]
    for i, (sec, title) in enumerate(chapters):
        start = sec * 1000000
        if i + 1 < len(chapters):
            end = chapters[i + 1][0] * 1000000
        else:
            end = (sec + 60) * 1000000
        metadata_lines.append(f"[CHAPTER]")
        metadata_lines.append("TIMEBASE=1/1000000")
        metadata_lines.append(f"START={int(start)}")
        metadata_lines.append(f"END={int(end)}")
        metadata_lines.append(f"title={title}")
    metadata_path = input_path + ".metadata"
    with open(metadata_path, "w", encoding="utf-8") as f:
        f.write("\n".join(metadata_lines))
    try:
        cmd = [
            ffmpeg,
            "-i", input_path,
            "-i", metadata_path,
            "-map_metadata", "1",
            "-c", "copy",
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
        if os.path.exists(metadata_path):
            os.remove(metadata_path)


def run_task(file_item, settings):
    """不支持单任务模式"""
    raise NotImplementedError("视频章节编辑功能请使用 run_batch，不要使用 run_task")


def run_batch(items, settings, get_output_dir, get_output_name_for_group,
              log_callback=None, progress_callback=None, stop_check=None):
    """批量写入章节（生成新文件，不覆盖原文件）"""
    if not items:
        return []
    text = settings.get("text", "")
    output_files = []
    processed = 0
    for item in items:
        if stop_check and stop_check():
            if log_callback:
                log_callback("⛔ 用户终止任务")
            break
        if progress_callback:
            progress_callback(int(processed / len(items) * 100))
        custom_text = getattr(item, "custom_chapters", "")
        text_to_use = custom_text if custom_text.strip() else text
        chapters = parse_chapters(text_to_use)
        if not chapters:
            if log_callback:
                log_callback(f"⚠️ 跳过 {os.path.basename(item.input_path)}：无有效章节数据")
            item.status = "完成"
            continue
        try:
            out_dir = item.output_dir or get_output_dir(item)
            out_path = os.path.join(out_dir, item.output_name)
            write_chapters_to_video(item.input_path, out_path, chapters, overwrite=True)
            item.output_paths = [out_path]
            item.status = "完成"
            output_files.append(out_path)
        except Exception as e:
            item.status = "错误"
            if log_callback:
                log_callback(f"❌ {os.path.basename(item.input_path)}：{e}")
        processed += 1
    if log_callback:
        log_callback("✅ 全部章节写入完成！")
    return output_files
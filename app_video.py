# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import sys
import subprocess
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QApplication, QMessageBox, QDialog, QLabel, QPlainTextEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout
)
from core.base import BaseMainWindow
from core.utils import resource_path, get_ffmpeg_path
from core.version import VIDEO_VERSION
from core.help import get_video_help_text
from features import VIDEO_FEATURES


class VideoMainWindow(BaseMainWindow):
    def __init__(self):
        """初始化视频主窗口"""
        super().__init__(
            app_title=f"视频批量处理工具  v{VIDEO_VERSION}    ©张小鱼",
            feature_modules=VIDEO_FEATURES,
            icon_path="assets/logo_video.ico",
            help_text=get_video_help_text()
        )

    def _connect_extra_signals(self, feat, panel):
        """连接视频功能特有的信号"""
        super()._connect_extra_signals(feat, panel)

    def on_cell_double_clicked(self, item):
        """双击单元格处理，支持在'设置'列双击编辑单个文件的章节"""
        row = item.row()
        fi = self.preview_mgr.items[row]
        col = item.column()
        idx = self.feature_box.currentIndex()
        if idx < 0:
            return
        feature_name = self.feature_modules[idx]["name"]
        if feature_name == "视频章节编辑" and col == self.COL_PREVIEW:
            self._edit_chapters_for_file(row, fi)
            return
        super().on_cell_double_clicked(item)

    def _edit_chapters_for_file(self, row, fi):
        """弹出对话框编辑单个文件的自定义章节"""
        idx = self.feature_box.currentIndex()
        panel = self.feature_panels[idx]
        global_text = panel.text_edit.toPlainText()
        default_text = getattr(fi, "custom_chapters", "") if getattr(fi, "custom_chapters", "") else global_text
        dialog = QDialog(self)
        dialog.setWindowTitle(f"编辑章节 - {os.path.basename(fi.input_path)}")
        dialog.setMinimumSize(500, 400)
        layout = QVBoxLayout(dialog)
        info = QLabel("修改该章节数据（留空则使用全局规则）")
        info.setStyleSheet("color: #666;")
        layout.addWidget(info)
        text_edit = QPlainTextEdit()
        text_edit.setPlainText(default_text)
        text_edit.setPlaceholderText("00:00:00  片头\n00:00:30  开场白")
        layout.addWidget(text_edit)
        btn_row = QHBoxLayout()
        btn_ok = QPushButton("确定")
        btn_cancel = QPushButton("取消")
        btn_clear = QPushButton("清空（使用全局规则）")
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel.clicked.connect(dialog.reject)
        def clear_and_accept():
            text_edit.clear()
            dialog.accept()
        btn_clear.clicked.connect(clear_and_accept)
        btn_row.addWidget(btn_clear)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)
        if dialog.exec() == QDialog.Accepted:
            new_text = text_edit.toPlainText().strip()
            fi.custom_chapters = new_text
            self.refresh_table()
            if new_text:
                self.append_log(f"已为 {os.path.basename(fi.input_path)} 设置自定义章节")
            else:
                self.append_log(f"已清除 {os.path.basename(fi.input_path)} 的自定义章节，将使用全局规则")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    icon_path = resource_path("assets/logo_video.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    app.setFont(QFont("Microsoft YaHei" if sys.platform.startswith("win") else "Arial", 10))
    window = VideoMainWindow()
    window.show()
    sys.exit(app.exec())
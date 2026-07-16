# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QFont
from core.base import BaseMainWindow
from core.utils import resource_path, VIDEO_VERSION
from core.help import get_video_help_text
from features import VIDEO_FEATURES


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("assets/logo_video.ico")))
    app.setFont(QFont("Microsoft YaHei" if sys.platform.startswith("win") else "Arial", 10))

    window = BaseMainWindow(
        app_title=f"视频批量处理工具  v{VIDEO_VERSION}    ©张小鱼",
        feature_modules=VIDEO_FEATURES,
        icon_path="assets/logo_video.ico",
        help_text=get_video_help_text()
    )
    window.show()
    sys.exit(app.exec())
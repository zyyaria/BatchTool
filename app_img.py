# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import sys
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import QApplication
from core.base import BaseMainWindow
from core.utils import resource_path, IMG_VERSION
from core.help import get_img_help_text
from features import IMG_FEATURES


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("assets/logo_img.ico")))
    app.setFont(QFont("Microsoft YaHei" if sys.platform.startswith("win") else "Arial", 10))

    window = BaseMainWindow(
        app_title=f"IMG 批量处理工具  v{IMG_VERSION}    ©张小鱼",
        feature_modules=IMG_FEATURES,
        icon_path="assets/logo_img.ico",
        help_text=get_img_help_text()
    )
    window.show()
    sys.exit(app.exec())
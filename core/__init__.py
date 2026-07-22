# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

from .base import (
    FileItem,
    OutputPath,
    FileListModel,
    Worker,
    WorkerSignals,
    BatchWorker,
    BatchThread,
    UIMixin,
    BaseMainWindow,
    NamingRulesDialog,
)

from .utils import (
    resource_path,
    sanitize_base_name,
    get_group_key,
    parse_page_range,
    load_app_config,
    save_app_config,
    ensure_image_mode,
    NamingRules,
    NamingRule,
    get_ffmpeg_path,
    set_ffmpeg_path,
)

from .version import (
    PDF_VERSION,
    IMG_VERSION,
    VIDEO_VERSION,
    BATCH_VERSION,
)

from .help import (
    GENERAL_HELP_TEXT,
    get_about_text,
    get_pdf_help_text,
    get_img_help_text,
    get_video_help_text,
)
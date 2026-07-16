# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import fitz
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, 
    QCheckBox, QPushButton, QSizePolicy
)


PAGE_SIZES = {
    "A0": (2384, 3370),
    "A1": (1684, 2384),
    "A2": (1191, 1684),
    "A3": (842, 1191),
    "A4": (595, 842),
    "A5": (420, 595),
    "A6": (298, 420),
    "Letter": (612, 792),
    "Legal": (612, 1008)
}
SIZE_NAMES = {v: k for k, v in PAGE_SIZES.items()}


class ResizePanel(QWidget):
    changed = Signal()
    detect_requested = Signal()

    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)

        preset_row = QHBoxLayout()
        preset_row.setSpacing(2)
        preset_row.addWidget(QLabel("预设尺寸:"))
        self.size_combo = QComboBox()
        self.size_combo.addItems(["A0", "A1", "A2", "A3", "A4", "A5", "A6", "Letter", "Legal", "自定义"])
        self.size_combo.setCurrentText("A4")
        self.size_combo.currentIndexChanged.connect(self._toggle_custom_size)
        preset_row.addWidget(self.size_combo, 1)

        self.width_mm = QLineEdit()
        self.width_mm.setPlaceholderText("宽 (cm)")
        self.width_mm.setVisible(False)
        preset_row.addWidget(self.width_mm, 1)

        self.height_mm = QLineEdit()
        self.height_mm.setPlaceholderText("高 (cm)")
        self.height_mm.setVisible(False)
        preset_row.addWidget(self.height_mm, 1)

        preset_row.addStretch()
        main_layout.addLayout(preset_row)

        pos_row = QHBoxLayout()
        pos_row.setSpacing(8)
        pos_row.addWidget(QLabel("内容位置:"))
        self.position_combo = QComboBox()
        self.position_combo.addItems(["居中", "左上", "右上", "左下", "右下"])
        self.position_combo.setCurrentText("居中")
        pos_row.addWidget(self.position_combo, 1)

        self.smart_orientation = QCheckBox("智能保持方向")
        self.smart_orientation.setChecked(True)
        pos_row.addWidget(self.smart_orientation)

        main_layout.addLayout(pos_row)

        self.btn_detect = QPushButton("检测页面尺寸")
        self.btn_detect.setMinimumHeight(32)
        main_layout.addWidget(self.btn_detect)

        main_layout.addStretch()

        self.size_combo.currentTextChanged.connect(self.changed)
        self.position_combo.currentIndexChanged.connect(self.changed)
        self.smart_orientation.stateChanged.connect(self.changed)
        self.width_mm.textChanged.connect(self.changed)
        self.height_mm.textChanged.connect(self.changed)
        self.btn_detect.clicked.connect(self.detect_requested.emit)

    def _toggle_custom_size(self):
        text = self.size_combo.currentText()
        is_custom = (text == "自定义")

        self.width_mm.setVisible(is_custom)
        self.height_mm.setVisible(is_custom)

        if is_custom:
            self.size_combo.setFixedWidth(90)
        else:
            self.size_combo.setMinimumWidth(0)
            self.size_combo.setMaximumWidth(16777215)
            self.size_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.changed.emit()


def build_panel() -> QWidget:
    return ResizePanel()


def collect_settings(panel: ResizePanel) -> dict:
    size_name = panel.size_combo.currentText()
    if size_name == "自定义":
        try:
            w_cm = float(panel.width_mm.text() or "21.0")
            h_cm = float(panel.height_mm.text() or "29.7")
            w_pt = w_cm * 72 / 2.54
            h_pt = h_cm * 72 / 2.54
            page_size = (w_pt, h_pt)
        except:
            page_size = (595, 842)
    else:
        page_size = PAGE_SIZES[size_name]
    return {
        "page_size_name": size_name,
        "page_size": page_size,
        "position": panel.position_combo.currentText(),
        "smart_orientation": panel.smart_orientation.isChecked(),
    }


def prepare_preview(items, settings):
    size_name = settings.get("page_size_name", "A4")
    if size_name == "自定义":
        page_size = settings.get("page_size", (0, 0))
        w, h = page_size
        w_cm = w * 2.54 / 72
        h_cm = h * 2.54 / 72
        size_name = f"{w_cm:.1f}×{h_cm:.1f}cm"

    pos = settings.get("position", "居中")
    smart = "开启" if settings.get("smart_orientation", True) else "关闭"
    for it in items:
        it.preview_extra = {"A": f"{size_name}，{pos}，智能方向: {smart}"}


def match_standard_size(w_pt: float, h_pt: float, tolerance: float = 2.0):
    for (sw, sh), name in SIZE_NAMES.items():
        if abs(w_pt - sw) <= tolerance and abs(h_pt - sh) <= tolerance:
            return (name, sw, sh)
        if abs(w_pt - sh) <= tolerance and abs(h_pt - sw) <= tolerance:
            return (name, sw, sh)
    return (None, w_pt, h_pt)


def detect_page_sizes(file_paths: list) -> dict:
    result = {}
    for file_path in file_paths:
        file_result = {"valid": True, "error": None, "pages": [], "summary": ""}
        if not os.path.exists(file_path):
            file_result["valid"] = False
            file_result["error"] = "文件不存在"
            result[file_path] = file_result
            continue
        if not file_path.lower().endswith(".pdf"):
            file_result["valid"] = False
            file_result["error"] = "不是PDF文件"
            result[file_path] = file_result
            continue
        try:
            doc = fitz.open(file_path)
            if doc.needs_pass:
                file_result["valid"] = False
                file_result["error"] = "PDF受密码保护"
                doc.close()
                result[file_path] = file_result
                continue
            sizes = {}
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                rect = page.rect
                w, h = rect.width, rect.height
                matched, sw, sh = match_standard_size(w, h)
                page_info = {
                    "num": page_num + 1,
                    "width": round(w, 1),
                    "height": round(h, 1),
                    "matched": matched
                }
                file_result["pages"].append(page_info)
                key = matched if matched else f"{round(w,1)}x{round(h,1)}"
                sizes[key] = sizes.get(key, 0) + 1
            doc.close()
            if len(sizes) == 1:
                file_result["summary"] = list(sizes.keys())[0]
            else:
                parts = []
                for k, count in sizes.items():
                    parts.append(f"{k}×{count}页")
                file_result["summary"] = "混合: " + ", ".join(parts)
            result[file_path] = file_result
        except Exception as e:
            file_result["valid"] = False
            file_result["error"] = f"读取失败: {str(e)}"
            result[file_path] = file_result
    return result


def pt_to_cm(pt: float) -> float:
    return round(pt * 25.4 / 72 / 10, 1)


def format_detect_result(result: dict) -> str:
    total_files = len(result)
    lines = []
    lines.append(f"检测结果（共 {total_files} 个文件）")
    lines.append("")
    all_matched_same = True
    first_summary = None
    for file_path, info in result.items():
        if not info["valid"]:
            continue
        if first_summary is None:
            first_summary = info["summary"]
        elif info["summary"] != first_summary:
            all_matched_same = False
            break
    if all_matched_same and first_summary is not None and "混合" not in first_summary:
        lines.append(f"✅ 所有有效文件均为 {first_summary}")
        lines.append("")
        lines.append("（已自动设置目标尺寸）")
    elif all_matched_same and first_summary is not None and "混合" in first_summary:
        lines.append(f"⚠️ 所有文件的页面尺寸分布一致：{first_summary}")
        lines.append("   请手动选择统一的目标尺寸")
    else:
        lines.append("各文件详情：")
        lines.append("")
    for idx, (file_path, info) in enumerate(result.items(), 1):
        base_name = os.path.basename(file_path)
        if not info["valid"]:
            lines.append(f"{idx}. ❌ {base_name}：{info['error']}")
            continue
        if len(info["pages"]) <= 1:
            p = info["pages"][0]
            if p["matched"]:
                lines.append(f"{idx}. {base_name} → {p['matched']}（{pt_to_cm(p['width'])} x {pt_to_cm(p['height'])} cm）")
            else:
                lines.append(f"{idx}. {base_name} → 未知尺寸（{pt_to_cm(p['width'])} x {pt_to_cm(p['height'])} cm）")
        else:
            merged = []
            for p in info["pages"]:
                key = p["matched"] if p["matched"] else f"{p['width']}x{p['height']}"
                if merged and merged[-1]["key"] == key:
                    merged[-1]["end"] = p["num"]
                else:
                    merged.append({"key": key, "start": p["num"], "end": p["num"]})
            parts = []
            for m in merged:
                if m["key"] in PAGE_SIZES:
                    display_key = m["key"]
                else:
                    try:
                        w, h = m["key"].split("x")
                        display_key = f"{pt_to_cm(float(w))}x{pt_to_cm(float(h))} cm"
                    except:
                        display_key = m["key"]
                if m["start"] == m["end"]:
                    parts.append(f"第{m['start']}页：{display_key}")
                else:
                    parts.append(f"第{m['start']}-{m['end']}页：{display_key}")
            lines.append(f"{idx}. {base_name}")
            for part in parts:
                lines.append(f"   {part}")
    return "\n".join(lines)


def get_detect_summary_for_autoset(result: dict) -> str:
    first_matched = None
    for file_path, info in result.items():
        if not info["valid"]:
            continue
        if "混合" in info["summary"]:
            return None
        if info["summary"] not in PAGE_SIZES:
            return None
        if first_matched is None:
            first_matched = info["summary"]
        elif info["summary"] != first_matched:
            return None
    return first_matched


def _resize_pdf(input_path: str, output_path: str, page_size, position: str, smart_orientation: bool):
    target_width_pt, target_height_pt = page_size
    src_doc = fitz.open(input_path)
    new_doc = fitz.open()
    for page_num in range(len(src_doc)):
        src_page = src_doc.load_page(page_num)
        orig_rect = src_page.rect
        orig_w = orig_rect.width
        orig_h = orig_rect.height
        tw, th = target_width_pt, target_height_pt
        if smart_orientation:
            orig_is_landscape = orig_w > orig_h
            target_is_landscape = tw > th
            if orig_is_landscape != target_is_landscape:
                tw, th = th, tw
        scale_x = tw / orig_w
        scale_y = th / orig_h
        scale = min(scale_x, scale_y)
        scaled_w = orig_w * scale
        scaled_h = orig_h * scale
        if position == "居中":
            dx = (tw - scaled_w) / 2
            dy = (th - scaled_h) / 2
        elif position == "左上":
            dx = 0
            dy = th - scaled_h
        elif position == "右上":
            dx = tw - scaled_w
            dy = th - scaled_h
        elif position == "左下":
            dx = 0
            dy = 0
        elif position == "右下":
            dx = tw - scaled_w
            dy = 0
        else:
            dx = (tw - scaled_w) / 2
            dy = (th - scaled_h) / 2
        new_page = new_doc.new_page(width=tw, height=th)
        target_rect = fitz.Rect(dx, dy, dx + scaled_w, dy + scaled_h)
        new_page.show_pdf_page(target_rect, src_doc, page_num)
    new_doc.save(output_path)
    new_doc.close()
    src_doc.close()


def run_task(file_item, settings: dict):
    src = file_item.input_path
    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)
    base_name = os.path.splitext(file_item.output_name)[0] if file_item.output_name else os.path.splitext(os.path.basename(src))[0]
    out_name = base_name + ".pdf"
    out_path = os.path.join(out_dir, out_name)
    file_item.output_name = out_name
    page_size = settings.get("page_size")
    if page_size is None:
        raise ValueError("未指定页面尺寸")
    position = settings.get("position", "居中")
    smart = settings.get("smart_orientation", True)
    _resize_pdf(src, out_path, page_size, position, smart)
    file_item.status = "完成"
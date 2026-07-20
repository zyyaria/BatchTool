# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import sys
import json
from typing import List


PDF_VERSION = "1.7.2"
IMG_VERSION = "1.7.0"
VIDEO_VERSION = "1.3.2"
BATCH_VERSION = "1.3.2"


def resource_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def sanitize_base_name(base: str) -> str:
    """清理文件名中的非法字符"""
    invalid = '<>:"/\\|?*' if os.name == "nt" else "/"
    return "".join(ch for ch in base if ch not in invalid).strip()


def get_group_key(file_path: str, group_mode: int, prefix_len: int, group_size: int, all_items: list) -> str:
    """根据分组模式生成组标识"""
    base = os.path.splitext(os.path.basename(file_path))[0]
    if group_mode == 0:
        return base[:prefix_len]
    elif group_mode == 1:
        try:
            idx = all_items.index(file_path)
            return f"组_{idx // group_size + 1}"
        except ValueError:
            return "组_1"
    elif group_mode == 2:
        return os.path.dirname(file_path)
    else:
        return "__all__"


def parse_page_range(text: str, total_pages: int) -> List[int]:
    """解析页面范围字符串"""
    if not text or not text.strip():
        return list(range(total_pages))
    pages = set()
    parts = text.replace(" ", "").split(",")
    for part in parts:
        if '-' in part:
            start, end = part.split('-')
            start = int(start) if start else 1
            end = int(end) if end else total_pages
            if start > end:
                start, end = end, start
            pages.update(range(start - 1, min(end, total_pages)))
        else:
            if part.isdigit():
                p = int(part) - 1
                if 0 <= p < total_pages:
                    pages.add(p)
    return sorted(pages)


CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "app_config.json")


def load_app_config(key: str, default: str = "") -> str:
    """从应用配置文件加载指定键的值"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(key, default)
        except:
            pass
    return default


def save_app_config(key: str, value: str) -> bool:
    """将键值保存到应用配置文件"""
    try:
        data = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data[key] = value
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except:
        return False


def ensure_image_mode(im, target_format: str, fill_white: bool = True):
    """将 PIL Image 转换为目标格式所需的色彩模式"""
    from PIL import Image
    fmt = target_format.lower() if target_format else ""
    if fmt in ("jpg", "jpeg", "bmp", "ico"):
        if fill_white and im.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", im.size, (255, 255, 255))
            if im.mode == "P":
                im = im.convert("RGBA")
            mask = im.split()[3] if im.mode == "RGBA" else None
            bg.paste(im, mask=mask)
            im = bg
        elif im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
    elif fmt == "png":
        if im.mode == "RGBA" and not im.getchannel("A").getextrema()[1]:
            im = im.convert("RGB")
    elif fmt == "gif":
        if im.mode != "P":
            im = im.convert("P", palette=Image.Palette.ADAPTIVE)
    elif fmt == "ico":
        if im.mode != "RGBA":
            im = im.convert("RGBA")
    return im


class NamingRule:
    def __init__(self, rule_type: str, params: dict = None, enabled: bool = True):
        """初始化命名规则"""
        self.rule_type = rule_type
        self.params = params or {}
        self.enabled = enabled
    
    def get_description(self) -> str:
        """生成规则的简要描述"""
        if self.rule_type == "insert":
            text = self.params.get("text", "")
            mode = self.params.get("mode", "prefix")
            if not text:
                return "插入（未配置）"
            mode_names = {
                "prefix": "作为前缀",
                "suffix": "作为后缀",
                "position": f"在位置{self.params.get('position', 1)}",
                "after_text": f"到「{self.params.get('after_text', '')}」之后",
                "before_text": f"到「{self.params.get('before_text', '')}」之前",
                "replace": "替换当前名称"
            }
            if mode == "position" and self.params.get("from_right", False):
                mode_names["position"] = f"在位置{self.params.get('position', 1)}（从右到左）"
            return f"插入「{text}」{mode_names.get(mode, mode)}"
        
        elif self.rule_type == "user_input":
            names = self.params.get("names", [])
            mode = self.params.get("mode", "replace")
            mode_names = {
                "replace": "替换",
                "insert_before": "插入前",
                "insert_after": "插入后"
            }
            count = len(names)
            if count == 0:
                return "用户输入（未配置）"
            preview = names[0] if count == 1 else f"{names[0]}...等{count}项"
            return f"用户输入 [{preview}] {mode_names.get(mode, mode)}"
        
        return "未知规则"
    
    def apply(self, name: str, index: int = 0) -> str:
        """将规则应用到文件名，index 用于用户输入规则时的索引"""
        if not self.enabled:
            return name
        
        result = name
        
        if self.rule_type == "insert":
            text = self.params.get("text", "")
            mode = self.params.get("mode", "prefix")
            
            if not text:
                return result
            
            if mode == "prefix":
                result = text + result
            elif mode == "suffix":
                result = result + text
            elif mode == "position":
                pos = self.params.get("position", 1) - 1
                if self.params.get("from_right", False):
                    pos = len(result) - pos
                pos = max(0, min(pos, len(result)))
                result = result[:pos] + text + result[pos:]
            elif mode == "after_text":
                target = self.params.get("after_text", "")
                idx = result.find(target)
                if idx >= 0:
                    result = result[:idx + len(target)] + text + result[idx + len(target):]
            elif mode == "before_text":
                target = self.params.get("before_text", "")
                idx = result.find(target)
                if idx >= 0:
                    result = result[:idx] + text + result[idx:]
            elif mode == "replace":
                result = text
        
        elif self.rule_type == "user_input":
            names = self.params.get("names", [])
            mode = self.params.get("mode", "replace")
            
            if names and index < len(names):
                user_name = names[index]
                if mode == "replace":
                    result = user_name
                elif mode == "insert_before":
                    result = user_name + result
                elif mode == "insert_after":
                    result = result + user_name
        
        return result
    
    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "rule_type": self.rule_type,
            "params": self.params,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """从字典反序列化"""
        return cls(
            rule_type=data.get("rule_type", "insert"),
            params=data.get("params", {}),
            enabled=data.get("enabled", True)
        )


class NamingRules:
    def __init__(self):
        """初始化命名规则集合"""
        self.enabled = False
        self.rules: List[NamingRule] = []
    
    def apply(self, base_name: str, index: int = 0) -> str:
        """按顺序应用所有规则到基础文件名"""
        if not self.enabled:
            return base_name
        result = base_name
        for rule in self.rules:
            result = rule.apply(result, index)
        return result
    
    def apply_to_many(self, base_name: str, count: int) -> List[str]:
        """为 count 个文件生成对应的命名列表"""
        return [self.apply(base_name, i) for i in range(count)]
    
    def get_preview(self, base_name: str = "示例", index: int = 0) -> str:
        """返回预览结果"""
        if not self.enabled:
            return "保留原名"
        return self.apply(base_name, index)
    
    def add_rule(self, rule_type: str, params: dict = None, enabled: bool = True):
        """添加一条规则"""
        self.rules.append(NamingRule(rule_type, params, enabled))
    
    def remove_rule(self, index: int):
        """移除指定索引的规则"""
        if 0 <= index < len(self.rules):
            self.rules.pop(index)
    
    def move_rule(self, from_idx: int, to_idx: int):
        """移动规则顺序"""
        if 0 <= from_idx < len(self.rules) and 0 <= to_idx < len(self.rules):
            rule = self.rules.pop(from_idx)
            self.rules.insert(to_idx, rule)
    
    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "enabled": self.enabled,
            "rules": [r.to_dict() for r in self.rules]
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """从字典反序列化"""
        rules = cls()
        rules.enabled = data.get("enabled", False)
        for r_data in data.get("rules", []):
            rules.rules.append(NamingRule.from_dict(r_data))
        return rules
    

def find_ffmpeg():
    """自动查找 FFmpeg 可执行文件路径"""
    saved_path = load_app_config("ffmpeg_path")
    if saved_path and os.path.exists(saved_path):
        return saved_path

    import shutil
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path

    common_paths = [
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"D:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"D:\Portable\FFmpeg\bin\ffmpeg.exe",
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    return None


def get_ffmpeg_path():
    """获取 FFmpeg 路径，返回 None 表示未找到"""
    return find_ffmpeg()


def set_ffmpeg_path(path: str) -> bool:
    """手动设置 FFmpeg 路径并保存到配置，返回是否成功"""
    if not os.path.exists(path):
        return False
    try:
        import subprocess
        subprocess.run([path, "-version"], capture_output=True, check=True)
        save_app_config("ffmpeg_path", path)
        return True
    except:
        return False
    

def get_unique_file_path(directory: str, base_name: str, ext: str) -> str:
    """获取唯一的文件路径"""
    out_path = os.path.join(directory, f"{base_name}{ext}")
    if not os.path.exists(out_path):
        return out_path
    counter = 1
    while True:
        new_path = os.path.join(directory, f"{base_name}_{counter}{ext}")
        if not os.path.exists(new_path):
            return new_path
        counter += 1
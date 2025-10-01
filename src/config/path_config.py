import os
import re
import sys
import time
from os import path


def get_timestamp() -> str:
    """获取当前时间戳"""
    return str(int(time.time() * 1000))


def get_executable_dir() -> str:
    """获取可执行文件所在的目录"""
    if getattr(sys, 'frozen', False):
        # 如果是PyInstaller打包的可执行文件
        return os.path.dirname(sys.executable)
    else:
        # 如果是源码运行，返回项目根目录
        return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """清理文件名，移除不允许的字符，但保留中文字符"""
    # Windows 不允许的字符，但不包括中文字符
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    
    # 移除或替换非法字符
    filename = re.sub(invalid_chars, '_', filename)
    
    # 移除换行符和制表符，但保留普通空格和中文
    filename = re.sub(r'[\n\r\t]+', ' ', filename)
    
    # 移除多余的空格，但保留中文字符
    filename = re.sub(r' +', ' ', filename).strip()
    
    # 移除文件名开头和结尾的点和空格
    filename = filename.strip('. ')
    
    # 限制文件名长度（注意中文字符的长度）
    if len(filename) > max_length:
        filename = filename[:max_length].rstrip()
    
    # 如果文件名为空，使用默认名称
    if not filename:
        filename = "untitled"
    
    return filename


class ScrapeDataPathBuilder:
    DATA_FOLDER_NAME = "scraped_data"
    _BASE_DIR = None  # 改为私有变量
    
    @classmethod
    def get_base_dir(cls) -> str:
        """获取基础目录"""
        if cls._BASE_DIR is None:
            cls._BASE_DIR = os.path.join(get_executable_dir(), cls.DATA_FOLDER_NAME)
        return cls._BASE_DIR
    
    @classmethod
    def set_base_dir(cls, base_dir: str) -> None:
        """设置自定义基础目录"""
        cls._BASE_DIR = base_dir
        os.makedirs(cls._BASE_DIR, exist_ok=True)

    def __init__(self, item_dir) -> None:
        self.item_dir = item_dir

    @classmethod
    def get_instance_scrape(cls, forum_name: str, tid: int, title: str) -> "ScrapeDataPathBuilder":
        # 使用动态获取的BASE_DIR
        base_dir = cls.get_base_dir()
        os.makedirs(base_dir, exist_ok=True)
        
        # 清理论坛名称和标题
        clean_forum_name = sanitize_filename(forum_name)
        clean_title = sanitize_filename(title)
        
        # 构建文件夹名称
        folder_name = f"[{clean_forum_name}][{tid}]{clean_title}_{int(time.time() * 1000)}"
        folder_name = sanitize_filename(folder_name)
        
        item_dir = os.path.join(base_dir, folder_name)
        os.makedirs(item_dir, exist_ok=True)
        
        return cls(item_dir)

    @classmethod
    def get_instance_scrape_update(cls, source_path: str) -> "ScrapeDataPathBuilder":
        return ScrapeDataPathBuilder(source_path)

    def get_item_dir(self) -> str:
        return self.item_dir

    def get_scrape_info_path(self) -> str:
        return path.join(self.item_dir, "scrape_info.json")

    def get_thread_dir(self, tid: int) -> str:
        return path.join(self.item_dir, "threads", f"{tid}")

    def get_scrape_log_path(self, tid: int, timestamp: int) -> str:
        return path.join(self.item_dir, "threads", f"{tid}", f"scrape.{timestamp}.log")

    def get_content_db_path(self, tid: int):
        return path.join(self.item_dir, "threads", f"{tid}", "content.db")

    def get_forum_info_path(self, tid) -> str:
        return path.join(self.item_dir, "threads", f"{tid}", "forum.json")

    def get_forum_avatar_dir(self, tid: int) -> str:
        return path.join(self.item_dir, "threads", f"{tid}", "forum_avatar")

    def get_thread_info_path(self, tid) -> str:
        return path.join(self.item_dir, "threads", f"{tid}", "thread.json")

    def get_user_avatar_dir(self, tid: int):
        avatar_dir = path.join(self.item_dir, "threads", f"{tid}", "user_avatar")
        os.makedirs(avatar_dir, exist_ok=True)
        return avatar_dir

    def get_post_assets_dir(self, tid: int) -> str:
        return path.join(self.item_dir, "threads", f"{tid}", "post_assets")

    def get_post_image_dir(self, tid: int):
        image_dir = path.join(self.item_dir, "threads", f"{tid}", "post_assets", "images")
        os.makedirs(image_dir, exist_ok=True)
        return image_dir

    def get_post_video_dir(self, tid: int):
        video_dir = path.join(self.item_dir, "threads", f"{tid}", "post_assets", "videos")
        os.makedirs(video_dir, exist_ok=True)
        return video_dir

    def get_post_voice_dir(self, tid: int):
        voice_dir = path.join(self.item_dir, "threads", f"{tid}", "post_assets", "voices")
        os.makedirs(voice_dir, exist_ok=True)
        return voice_dir

    @staticmethod
    def get_forum_small_avatar_filename(forum_name: str):
        clean_forum_name = sanitize_filename(forum_name, max_length=50)
        return f"f_{clean_forum_name}_small-avatar_{get_timestamp()}"

    @staticmethod
    def get_forum_small_avatar_filename_pattern():
        return r".*small.*"

    @staticmethod
    def get_forum_origin_avatar_filename(forum_name: str):
        clean_forum_name = sanitize_filename(forum_name, max_length=50)
        return f"f_{clean_forum_name}_origin-avatar_{get_timestamp()}"

    @staticmethod
    def get_forum_origin_avatar_filename_pattern():
        return r".*origin.*"

    @staticmethod
    def get_user_avatar_filename(portrait: str):
        clean_portrait = sanitize_filename(portrait, max_length=50)
        return f"{clean_portrait}_{get_timestamp()}"

    @staticmethod
    def get_user_avatar_filename_pattern(portrait: str):
        clean_portrait = re.escape(sanitize_filename(portrait, max_length=50))
        return rf".*{clean_portrait}.*"

    @staticmethod
    def get_post_image_filename(pid: int, idx: int):
        return f"p_{pid}_{idx}_{get_timestamp()}"

    @staticmethod
    def get_post_video_filename(pid: int, idx: int):
        return f"p_{pid}_{idx}_{get_timestamp()}"

    @staticmethod
    def get_post_voice_filename(pid: int, idx: int, voice_hash: str):
        clean_voice_hash = sanitize_filename(voice_hash, max_length=50)
        return f"p_{pid}_{idx}_{clean_voice_hash}"

    @staticmethod
    def get_post_assets_filename_pattern(pid: int):
        return rf".*p_{pid}_.*"

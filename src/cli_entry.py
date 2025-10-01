import asyncio
import os
import sys
from enum import IntEnum, auto
import argparse
import glob

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

import orjson
import questionary

# 修改这些导入语句
try:
    from modules.scrape_module import scrape, scrape_multiple_from_file
    from modules.scrape_update_module import scrape_update
    from scrape_config import DownloadUserAvatarMode, ScrapeConfig, ScrapeConfigKeys, PostFilterType
    from tieba_auth import TiebaAuth
    from utils.cli_questionary import InfoStyle
    from utils.common import counter_gen, json_dumps
    from utils.msg_printer import PrintColor
except ImportError:
    # 如果直接导入失败，尝试相对导入
    from .modules.scrape_module import scrape, scrape_multiple_from_file
    from .modules.scrape_update_module import scrape_update
    from .scrape_config import DownloadUserAvatarMode, ScrapeConfig, ScrapeConfigKeys, PostFilterType
    from .tieba_auth import TiebaAuth
    from .utils.cli_questionary import InfoStyle
    from .utils.common import counter_gen, json_dumps
    from .utils.msg_printer import PrintColor

counter = counter_gen()
next(counter)  # 预激一次生成器

TIEBA_AUTH_FILENAME = "tieba_auth.json"


def read_tieba_auth() -> None:
    tieba_auth_file_path = os.path.join(os.getcwd(), TIEBA_AUTH_FILENAME)

    try:
        with open(tieba_auth_file_path, "r", encoding="utf-8") as f:
            TiebaAuth.from_dict(orjson.loads(f.read()))
    except Exception:
        BDUSS = questionary.text("未配置BDUSS, 请输入: ").ask()
        TiebaAuth.BDUSS = BDUSS
        with open(tieba_auth_file_path, "w", encoding="utf-8") as f:
            f.write(json_dumps(TiebaAuth.to_dict()))


SCRAPE_CONFIG_FILENAME = "scrape_config.json"
scrape_config_file_path = os.path.join(os.getcwd(), SCRAPE_CONFIG_FILENAME)


def read_scrape_config() -> None:
    try:
        with open(scrape_config_file_path, "r", encoding="utf-8") as f:
            ScrapeConfig.from_dict(orjson.loads(f.read()))
    except FileNotFoundError:
        if questionary.confirm("未找到配置文件, 是否使用默认配置并生成文件?").ask():
            write_scrape_config()
        else:
            sys.exit()
    except orjson.JSONDecodeError:
        if questionary.confirm("配置文件格式错误导致解析失败, 是否使用默认配置并生成文件?").ask():
            write_scrape_config()
        else:
            sys.exit()
    except ValueError as err:
        if questionary.confirm(f"配置变量错误: {str(err)}, 是否使用默认配置并生成文件?").ask():
            write_scrape_config()
        else:
            sys.exit()


def write_scrape_config() -> None:
    with open(scrape_config_file_path, "w", encoding="utf-8") as f:
        f.write(json_dumps(ScrapeConfig.to_dict()))


def set_scrape_config() -> None:
    counter.send((0, 1))
    set_scrape_config_choice = [
        questionary.Choice(
            f"{next(counter)}. 过滤帖子({ScrapeConfigKeys.POST_FILTER_TYPE})",
            ScrapeConfigKeys.POST_FILTER_TYPE,
        ),
        questionary.Choice(
            f"{next(counter)}. 头像保存模式({ScrapeConfigKeys.DOWNLOAD_USER_AVATAR_MODE})",
            ScrapeConfigKeys.DOWNLOAD_USER_AVATAR_MODE,
        ),
        questionary.Choice(
            f"{next(counter)}. 是否爬取转发的原帖({ScrapeConfigKeys.SCRAPE_SHARE_ORIGIN})",
            ScrapeConfigKeys.SCRAPE_SHARE_ORIGIN,
        ),
        questionary.Choice(
            f"{next(counter)}. 是否更新转发的原帖({ScrapeConfigKeys.UPDATE_SHARE_ORIGIN})",
            ScrapeConfigKeys.UPDATE_SHARE_ORIGIN,
        ),
        questionary.Choice(
            f"{next(counter)}. 退出",
            "exit",
        ),
    ]

    while True:
        scrape_config_key = questionary.select("选择配置项", choices=set_scrape_config_choice).ask()
        if ScrapeConfigKeys.POST_FILTER_TYPE == scrape_config_key:
            counter.send((0, 1))
            post_filter_type_choices = [
                questionary.Choice(
                    f"{next(counter)}. '所有的 post' + 'post 下的所有 subpost'({PostFilterType.ALL})",
                    PostFilterType.ALL,
                ),
                questionary.Choice(
                    f"{next(counter)}. 'thread_author 的 post' + 'post 下的所有 subpost'({PostFilterType.AUTHOR_POSTS_WITH_SUBPOSTS})",
                    PostFilterType.AUTHOR_POSTS_WITH_SUBPOSTS,
                ),
                questionary.Choice(
                    f"{next(counter)}. 'thread_author 的 post' + 'post 下 thread_author 的 subpost'({PostFilterType.AUTHOR_POSTS_WITH_AUTHOR_SUBPOSTS})",
                    PostFilterType.AUTHOR_POSTS_WITH_AUTHOR_SUBPOSTS,
                ),
                questionary.Choice(
                    f"{next(counter)}. 'thread_author 的 post 和 thread_author 回复过的 post' + 'post 下所有的 subpost'({PostFilterType.AUTHOR_AND_REPLIED_POSTS_WITH_SUBPOSTS})",
                    PostFilterType.AUTHOR_AND_REPLIED_POSTS_WITH_SUBPOSTS,
                ),
                questionary.Choice(
                    f"{next(counter)}. 'thread_author 的 post 和 thread_author 回复过的 post' + 'post 下 thread_author 的 subpost'({PostFilterType.AUTHOR_AND_REPLIED_POSTS_WITH_AUTHOR_SUBPOSTS})",
                    PostFilterType.AUTHOR_AND_REPLIED_POSTS_WITH_AUTHOR_SUBPOSTS,
                ),
            ]
            post_filter_type = questionary.select("选择帖子过滤模式", choices=post_filter_type_choices).ask()
            ScrapeConfig.POST_FILTER_TYPE = post_filter_type
            write_scrape_config()
        elif ScrapeConfigKeys.DOWNLOAD_USER_AVATAR_MODE == scrape_config_key:
            counter.send((0, 1))
            download_user_avatar_mode_choices = [
                questionary.Choice(
                    f"{next(counter)}. 不保存({DownloadUserAvatarMode.NONE})", DownloadUserAvatarMode.NONE
                ),
                questionary.Choice(
                    f"{next(counter)}. 保存低清({DownloadUserAvatarMode.LOW})", DownloadUserAvatarMode.LOW
                ),
                questionary.Choice(
                    f"{next(counter)}. 保存高清({DownloadUserAvatarMode.HIGH})", DownloadUserAvatarMode.HIGH
                ),
            ]
            download_user_avatar_mode = questionary.select(
                "选择头像保存模式", choices=download_user_avatar_mode_choices
            ).ask()
            ScrapeConfig.DOWNLOAD_USER_AVATAR_MODE = download_user_avatar_mode
            write_scrape_config()
        elif ScrapeConfigKeys.SCRAPE_SHARE_ORIGIN == scrape_config_key:
            scrape_share_origin = questionary.confirm("是否爬取转发的原帖?").ask()
            ScrapeConfig.SCRAPE_SHARE_ORIGIN = scrape_share_origin
            write_scrape_config()
        elif ScrapeConfigKeys.UPDATE_SHARE_ORIGIN == scrape_config_key:
            update_share_origin = questionary.confirm("是否更新转发的原帖?").ask()
            ScrapeConfig.UPDATE_SHARE_ORIGIN = update_share_origin
            write_scrape_config()
        elif "exit" == scrape_config_key:
            break


class ProgramFeatures(IntEnum):
    SCRAPE = auto()
    SCRAPE_FROM_FILE = auto()
    SCRAPE_UPDATE = auto()
    EXPORT_TO_READABLE = auto()
    MODIFY_SCRAPE_CONFIG = auto()


async def scrape_update_all(base_path):
    """更新指定目录下所有帖子数据"""
    if not os.path.exists(base_path):
        print(f"{PrintColor.RED}路径不存在: {base_path}{PrintColor.RESET}")
        return

    # 查找所有子文件夹
    folders = [d for d in glob.glob(os.path.join(base_path, "*")) if os.path.isdir(d)]

    if not folders:
        print(f"{PrintColor.YELLOW}在 {base_path} 目录下未找到子文件夹{PrintColor.RESET}")
        # 尝试直接更新此文件夹
        await scrape_update(base_path)
        return

    # 按文件夹名倒序排序
    folders.sort(key=lambda x: os.path.basename(x), reverse=True)

    print(f"{PrintColor.GREEN}找到 {len(folders)} 个帖子文件夹，开始更新...{PrintColor.RESET}")
    for folder in folders:
        print(f"{PrintColor.CYAN}正在更新: {os.path.basename(folder)}{PrintColor.RESET}")
        await scrape_update(folder)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="贴吧帖子归档工具")

    # 创建子命令解析器
    subparsers = parser.add_subparsers(dest='command', help='要执行的命令')
    
    # 爬取帖子命令
    scrape_parser = subparsers.add_parser('scrape', help='爬取帖子')
    scrape_parser.add_argument('tid', type=int, nargs='?', help='要爬取的帖子tid，不指定则从tid_list.txt读取')
    scrape_parser.add_argument('--file', type=str, default='tid_list.txt', help='tid列表文件路径，默认为tid_list.txt')
    
    # 更新帖子命令
    update_parser = subparsers.add_parser('update', help='更新本地帖子数据')
    update_parser.add_argument('path', type=str, help='本地帖子数据的路径')
    
    # 导出为可读文件命令
    export_parser = subparsers.add_parser('export', help='导出为可读文件(未实现)')
    
    # 配置命令
    config_parser = subparsers.add_parser('config', help='修改爬取配置')
    config_parser.add_argument('--post-filter', type=int, choices=[1, 2, 3, 4, 5], 
                             help='帖子过滤模式 (1-5 对应不同模式)')
    config_parser.add_argument('--avatar-mode', type=int, choices=[1, 2, 3], 
                             help='头像保存模式 (1=不保存, 2=低清, 3=高清)')
    config_parser.add_argument('--scrape-share', type=int, choices=[0, 1], 
                             help='是否爬取转发的原帖 (0=否, 1=是)')
    config_parser.add_argument('--update-share', type=int, choices=[0, 1], 
                             help='是否更新转发的原帖 (0=否, 1=是)')
    
    # 保留原来的功能选择方式
    parser.add_argument('--feature', type=int, choices=[1, 2, 3, 4, 5], 
                      help='功能选择: 1=爬取帖子, 2=从文件批量爬取, 3=更新本地帖子数据, 4=导出为可读文件, 5=修改爬取配置')
    parser.add_argument('--tid', type=int, help='要爬取的帖子tid')
    parser.add_argument('--file', type=str, default='tid_list.txt', help='tid列表文件路径，默认为tid_list.txt')
    parser.add_argument('--path', type=str, help='本地帖子数据的路径')
    parser.add_argument('--post-filter', type=int, choices=[1, 2, 3, 4, 5], 
                      help='帖子过滤模式 (1-5 对应不同模式)')
    parser.add_argument('--avatar-mode', type=int, choices=[1, 2, 3], 
                      help='头像保存模式 (1=不保存, 2=低清, 3=高清)')
    parser.add_argument('--scrape-share', type=int, choices=[0, 1], 
                      help='是否爬取转发的原帖 (0=否, 1=是)')
    parser.add_argument('--update-share', type=int, choices=[0, 1], 
                      help='是否更新转发的原帖 (0=否, 1=是)')
    parser.add_argument('--data-dir', type=str, help='自定义数据保存目录')
    
    return parser.parse_args()


def main():
    try:
        args = parse_args()
        
        # 如果没有参数，检查是否存在 tid_list.txt 文件
        if len(sys.argv) == 1:
            if os.path.exists('tid_list.txt'):
                print(f"{PrintColor.GREEN}检测到 tid_list.txt 文件，是否从文件批量爬取？{PrintColor.RESET}")
                choice = input("输入 y 使用文件批量爬取，输入其他字符进入交互式模式: ").strip().lower()
                if choice == 'y':
                    read_tieba_auth()
                    read_scrape_config()
                    asyncio.run(scrape_multiple_from_file('tid_list.txt'))
                    return
            interactive_main()
            return
        
        # 首先处理子命令
        if hasattr(args, 'command') and args.command:
            if args.command == 'scrape':
                read_tieba_auth()
                read_scrape_config()
                if args.tid:
                    asyncio.run(scrape(args.tid))
                else:
                    # 没有指定tid，从文件读取
                    asyncio.run(scrape_multiple_from_file(args.file))
                return
            
            elif args.command == 'update':
                read_tieba_auth()
                read_scrape_config()
                asyncio.run(scrape_update_all(args.path))
                return
            
            elif args.command == 'export':
                print(f"{PrintColor.RED}该功能尚未实现{PrintColor.RESET}")
                return
            
            elif args.command == 'config':
                read_scrape_config()
                config_changed = False
                
                # 处理各种配置参数
                if args.post_filter:
                    # 枚举值通常从1开始，而不是从0开始，需要正确映射
                    filter_map = {
                        1: PostFilterType.ALL,
                        2: PostFilterType.AUTHOR_POSTS_WITH_SUBPOSTS,
                        3: PostFilterType.AUTHOR_POSTS_WITH_AUTHOR_SUBPOSTS,
                        4: PostFilterType.AUTHOR_AND_REPLIED_POSTS_WITH_SUBPOSTS,
                        5: PostFilterType.AUTHOR_AND_REPLIED_POSTS_WITH_AUTHOR_SUBPOSTS
                    }
                    filter_type = filter_map.get(args.post_filter)
                    if filter_type is not None:
                        ScrapeConfig.POST_FILTER_TYPE = filter_type
                        config_changed = True
                
                if args.avatar_mode:
                    # 同样为头像模式创建映射
                    avatar_map = {
                        1: DownloadUserAvatarMode.NONE,
                        2: DownloadUserAvatarMode.LOW,
                        3: DownloadUserAvatarMode.HIGH
                    }
                    avatar_mode = avatar_map.get(args.avatar_mode)
                    if avatar_mode is not None:
                        ScrapeConfig.DOWNLOAD_USER_AVATAR_MODE = avatar_mode
                        config_changed = True
                
                if args.scrape_share is not None:
                    ScrapeConfig.SCRAPE_SHARE_ORIGIN = bool(args.scrape_share)
                    config_changed = True
                
                if args.update_share is not None:
                    ScrapeConfig.UPDATE_SHARE_ORIGIN = bool(args.update_share)
                    config_changed = True
                
                if config_changed:
                    write_scrape_config()
                    print(f"{PrintColor.GREEN}配置已更新{PrintColor.RESET}")
                else:
                    set_scrape_config()  # 没有提供具体配置参数，进入交互式配置
                return
        
        # 然后处理传统的 --feature 参数方式
        if args.feature:
            feature = args.feature
            
            if feature == 1:  # 爬取帖子
                try:
                    read_tieba_auth()
                    read_scrape_config()
                    if not args.tid:
                        tid = int(input("请输入要爬取的帖子的tid: "))
                    else:
                        tid = args.tid
                    asyncio.run(scrape(tid))
                except ValueError:
                    print(f"{PrintColor.RED}tid 必须为整数{PrintColor.RESET}")
            
            elif feature == 2:  # 从文件批量爬取
                read_tieba_auth()
                read_scrape_config()
                file_path = args.file if args.file != 'tid_list.txt' else input("请输入tid列表文件路径(默认tid_list.txt): ") or 'tid_list.txt'
                asyncio.run(scrape_multiple_from_file(file_path))
                    
            elif feature == 3:  # 更新本地帖子数据
                read_tieba_auth()
                read_scrape_config()
                if not args.path:
                    path = input("请输入本地帖子数据的路径: ")
                else:
                    path = args.path
                asyncio.run(scrape_update_all(path))
                
            elif feature == 4:  # 导出为可读文件
                print(f"{PrintColor.RED}该功能尚未实现{PrintColor.RESET}")
                
            elif feature == 5:  # 修改爬取配置
                read_scrape_config()
                config_changed = False
                
                # 处理各种配置参数
                if args.post_filter:
                    # 枚举值通常从1开始，而不是从0开始，需要正确映射
                    filter_map = {
                        1: PostFilterType.ALL,
                        2: PostFilterType.AUTHOR_POSTS_WITH_SUBPOSTS,
                        3: PostFilterType.AUTHOR_POSTS_WITH_AUTHOR_SUBPOSTS,
                        4: PostFilterType.AUTHOR_AND_REPLIED_POSTS_WITH_SUBPOSTS,
                        5: PostFilterType.AUTHOR_AND_REPLIED_POSTS_WITH_AUTHOR_SUBPOSTS
                    }
                    filter_type = filter_map.get(args.post_filter)
                    if filter_type is not None:
                        ScrapeConfig.POST_FILTER_TYPE = filter_type
                        config_changed = True
                
                if args.avatar_mode:
                    # 同样为头像模式创建映射
                    avatar_map = {
                        1: DownloadUserAvatarMode.NONE,
                        2: DownloadUserAvatarMode.LOW,
                        3: DownloadUserAvatarMode.HIGH
                    }
                    avatar_mode = avatar_map.get(args.avatar_mode)
                    if avatar_mode is not None:
                        ScrapeConfig.DOWNLOAD_USER_AVATAR_MODE = avatar_mode
                        config_changed = True
                
                if args.scrape_share is not None:
                    ScrapeConfig.SCRAPE_SHARE_ORIGIN = bool(args.scrape_share)
                    config_changed = True
                
                if args.update_share is not None:
                    ScrapeConfig.UPDATE_SHARE_ORIGIN = bool(args.update_share)
                    config_changed = True
                
                if config_changed:
                    write_scrape_config()
                    print(f"{PrintColor.GREEN}配置已更新{PrintColor.RESET}")
                else:
                    set_scrape_config()  # 没有提供具体配置参数，进入交互式配置
        
        # 如果有直接配置参数但没有指定feature
        elif args.post_filter or args.avatar_mode or args.scrape_share is not None or args.update_share is not None:
            read_scrape_config()
            config_changed = False
            
            if args.post_filter:
                filter_map = {
                    1: PostFilterType.ALL,
                    2: PostFilterType.AUTHOR_POSTS_WITH_SUBPOSTS,
                    3: PostFilterType.AUTHOR_POSTS_WITH_AUTHOR_SUBPOSTS,
                    4: PostFilterType.AUTHOR_AND_REPLIED_POSTS_WITH_SUBPOSTS,
                    5: PostFilterType.AUTHOR_AND_REPLIED_POSTS_WITH_AUTHOR_SUBPOSTS
                }
                filter_type = filter_map.get(args.post_filter)
                if filter_type is not None:
                    ScrapeConfig.POST_FILTER_TYPE = filter_type
                    config_changed = True
            if args.avatar_mode:
                avatar_map = {
                    1: DownloadUserAvatarMode.NONE,
                    2: DownloadUserAvatarMode.LOW,
                    3: DownloadUserAvatarMode.HIGH
                }
                avatar_mode = avatar_map.get(args.avatar_mode)
                if avatar_mode is not None:
                    ScrapeConfig.DOWNLOAD_USER_AVATAR_MODE = avatar_mode
                    config_changed = True
            
            if args.scrape_share is not None:
                ScrapeConfig.SCRAPE_SHARE_ORIGIN = bool(args.scrape_share)
                config_changed = True
            
            if args.update_share is not None:
                ScrapeConfig.UPDATE_SHARE_ORIGIN = bool(args.update_share)
                config_changed = True
            
            if config_changed:
                write_scrape_config()
                print(f"{PrintColor.GREEN}配置已更新{PrintColor.RESET}")
        
        # 直接指定tid参数，自动执行爬取
        elif args.tid:
            read_tieba_auth()
            read_scrape_config()
            asyncio.run(scrape(args.tid))
        
        # 直接指定path参数，自动执行更新
        elif args.path:
            read_tieba_auth()
            read_scrape_config()
            asyncio.run(scrape_update_all(args.path))
        
        # 指定了文件参数，从文件批量爬取
        elif args.file and args.file != 'tid_list.txt':
            read_tieba_auth()
            read_scrape_config()
            asyncio.run(scrape_multiple_from_file(args.file))
        
        # 没有有效参数，进入交互式模式
        else:
            interactive_main()
    
    except Exception as e:
        print(f"{PrintColor.RED}发生错误: {str(e)}{PrintColor.RESET}")
        import traceback
        traceback.print_exc()


def interactive_main():
    """原来的交互式主函数"""
    counter.send((0, 1))

    features_choices = [
        questionary.Choice(
            f"{next(counter)}. 爬取帖子",
            ProgramFeatures.SCRAPE,
        ),
        questionary.Choice(
            f"{next(counter)}. 从文件批量爬取帖子",
            ProgramFeatures.SCRAPE_FROM_FILE,
        ),
        questionary.Choice(
            f"{next(counter)}. 更新本地的帖子数据",
            ProgramFeatures.SCRAPE_UPDATE,
        ),
        questionary.Choice(
            f"{next(counter)}. 导出为可读文件(未实现)",
            ProgramFeatures.EXPORT_TO_READABLE,
        ),
        questionary.Choice(
            f"{next(counter)}. 修改爬取配置",
            ProgramFeatures.MODIFY_SCRAPE_CONFIG,
        ),
    ]
    while True:
        selected_features = questionary.select("选择功能", choices=features_choices, style=InfoStyle).ask()

        if ProgramFeatures.SCRAPE == selected_features:
            try:
                read_tieba_auth()
                read_scrape_config()
                tid = int(questionary.text("请输入要爬取的帖子的tid: ").ask())
                asyncio.run(scrape(tid))
            except ValueError:
                print(f"{PrintColor.RED}tid 必须为整数{PrintColor.RESET}")
        elif ProgramFeatures.SCRAPE_FROM_FILE == selected_features:
            read_tieba_auth()
            read_scrape_config()
            file_path = questionary.text("请输入tid列表文件路径", default="tid_list.txt").ask()
            asyncio.run(scrape_multiple_from_file(file_path))
        elif ProgramFeatures.SCRAPE_UPDATE == selected_features:
            read_tieba_auth()
            read_scrape_config()
            path = input("请输入本地帖子数据的路径: ")
            asyncio.run(scrape_update_all(path))
        elif ProgramFeatures.EXPORT_TO_READABLE == selected_features:
            print(f"{PrintColor.RED}该功能尚未实现{PrintColor.RESET}")
        elif ProgramFeatures.MODIFY_SCRAPE_CONFIG == selected_features:
            set_scrape_config()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
算法竞赛补题自动收集与排序系统

自动收集Codeforces/AtCoder/LeetCode未解决题目，
获取Clist难度评级，统一排序并导出。
"""

import yaml
import os
import sys
from typing import List, Dict

from crawlers.codeforces import CodeforcesCrawler
from crawlers.atcoder import AtCoderCrawler
from crawlers.leetcode import LeetCodeCrawler
from clist.fetcher import ClistFetcher
from exporter.export import Exporter
from models.problem import Problem


def load_config(config_path: str = 'config.yaml') -> Dict:
    """加载配置文件"""
    if not os.path.exists(config_path):
        print(f"错误: 配置文件不存在: {config_path}")
        print("请先复制并编辑 config.yaml 文件，填入您的账号信息")
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config


def crawl_single_platform(platform:str, config: Dict) -> List[Problem]:
    problems: List[Problem] = []

    # 获取配置信息
    handle = config.get('handle', '').strip()
    cookies = config.get('cookies', {})

    # 声明爬虫
    global crawler
    if not handle and not cookies:
        print(f'Warning:⚠️[{platform}信息配置不全，已经跳过]')
        return problems
    elif not handle:
        crawler = LeetCodeCrawler(cookies=cookies)
    else:
        if platform == 'codeforces':
            crawler = CodeforcesCrawler(
                handle=handle,
                include_gym=config.get('include_gym', True)
            )
        else:
            crawler = AtCoderCrawler(
                handle=handle,
                contest_only=config.get('contest_only', True)
            )

    print(f'[{platform}] 开始爬取：')
    try:
        # 获取未解决的题目（原有功能）
        unsolved = crawler.get_unsolved_problems()
        problems.extend(unsolved)
        print(f"  成功: 找到 {len(unsolved)} 道未解决题目")

        # 获取比赛未尝试的题目（新功能）
        if config.get('include_contest_unattempted', False):
            unattempted = crawler.get_contest_unattempted_problems()
            problems.extend(unattempted)
            print(f"  成功: 找到 {len(unattempted)} 道比赛未尝试题目")
    except Exception as e:
        print(f"  错误: {e}")
    return problems


def crawl_all_problems(config: Dict) -> List[Problem]:
    """爬取所有平台的未解决题目"""
    all_problems = []
    platforms_config = config.get('platforms', {})

    if platforms_config.get('codeforces', {}).get('enabled', False):
        all_problems.extend(crawl_single_platform('codeforces', platforms_config['codeforces']))
    if platforms_config.get('atcoder', {}).get('enabled', False):
        all_problems.extend(crawl_single_platform('atcoder', platforms_config['atcoder']))
    if platforms_config.get('leetcode', {}).get('enabled', False):
        all_problems.extend(crawl_single_platform('leetcode', platforms_config['leetcode']))

    # 去重（根据problem_id）
    unique_problems = {}
    for problem in all_problems:
        if problem.problem_id not in unique_problems:
            unique_problems[problem.problem_id] = problem

    deduped_problems = list(unique_problems.values())
    if len(all_problems) > len(deduped_problems):
        print(f"\n[去重] 去重前: {len(all_problems)} 道, 去重后: {len(deduped_problems)} 道")

    return deduped_problems


def fetch_ratings(problems: List[Problem], config: Dict) -> None:
    """获取Clist难度评级"""
    clist_config = config.get('clist', {})
    api_key = clist_config.get('api_key', '').strip()

    if not api_key:
        print("\n[Clist] 未配置API Key，跳过rating获取")
        return

    print(f"\n[Clist] 开始获取 {len(problems)} 道题目的rating...")

    try:
        fetcher = ClistFetcher(api_key=api_key)
        fetcher.fetch_ratings_batch(problems)

    except Exception as e:
        print(f"  错误: {e}")


def export_results(problems: List[Problem], config: Dict) -> None:
    """导出结果"""
    export_config = config.get('export', {})
    output_dir = export_config.get('output_dir', './output')
    formats = export_config.get('formats', ['json', 'csv', 'markdown'])

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 文件路径
    json_path = os.path.join(output_dir, export_config.get('json_file', 'problems.json'))
    csv_path = os.path.join(output_dir, export_config.get('csv_file', 'problems.csv'))
    md_path = os.path.join(output_dir, export_config.get('markdown_file', 'README.md'))

    print(f"\n[导出] 开始导出到 {output_dir}...")

    try:
        # 更新平台优先级
        if 'sort' in config and 'platform_priority' in config['sort']:
            Exporter.PLATFORM_PRIORITY = config['sort']['platform_priority']

        # 导出
        if 'json' in formats:
            Exporter.export_json(problems, json_path)
        if 'csv' in formats:
            Exporter.export_csv(problems, csv_path)
        if 'markdown' in formats:
            Exporter.export_markdown(problems, md_path)

        print(f"\n完成! 共导出 {len(problems)} 道题目到 {output_dir}")

    except Exception as e:
        print(f"  错误: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print(" " * 10 + "算法竞赛补题自动收集与排序系统")
    print("=" * 60)

    # 加载配置
    config = load_config()

    # 爬取未解决题目
    problems = crawl_all_problems(config)

    if not problems:
        print("\n未找到任何未解决题目，程序退出")
        return

    # 获取Clist rating
    fetch_ratings(problems, config)

    # 导出结果
    export_results(problems, config)


if __name__ == '__main__':
    main()

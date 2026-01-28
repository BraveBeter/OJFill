import csv
import json
from typing import List
from models.problem import Problem


class Exporter:
    """数据导出器"""

    # 平台优先级配置
    PLATFORM_PRIORITY = {
        'codeforces': 1,
        'atcoder': 2,
        'leetcode': 3
    }

    @staticmethod
    def sort_problems(problems: List[Problem]) -> List[Problem]:
        """
        排序题目列表

        排序规则：
        1. 主键：Clist rating（升序，None排在最后）
        2. 次键：平台优先级

        Args:
            problems: 题目列表

        Returns:
            排序后的题目列表
        """
        def sort_key(problem: Problem):
            # rating作为主键（None排在最后）
            rating = problem.clist_rating if problem.clist_rating is not None else 99999
            # 平台优先级作为次键
            priority = Exporter.PLATFORM_PRIORITY.get(problem.platform, 99)
            return (rating, priority)

        return sorted(problems, key=sort_key)

    @staticmethod
    def export_json(problems: List[Problem], output_path: str = 'problems.json'):
        """
        导出为JSON格式

        Args:
            problems: 题目列表
            output_path: 输出文件路径
        """
        # 转换为字典列表
        data = [problem.to_dict() for problem in problems]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"已导出JSON: {output_path} ({len(problems)} 道题目)")

    @staticmethod
    def export_csv(problems: List[Problem], output_path: str = 'problems.csv'):
        """
        导出为CSV格式

        Args:
            problems: 题目列表
            output_path: 输出文件路径
        """
        fieldnames = ['platform', 'problem_id', 'contest_id', 'problem_index',
                      'title', 'url', 'clist_rating']

        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for problem in problems:
                writer.writerow(problem.to_dict())

        print(f"已导出CSV: {output_path} ({len(problems)} 道题目)")

    @staticmethod
    def export_markdown(problems: List[Problem], output_path: str = 'README.md'):
        """
        导出为Markdown表格

        Args:
            problems: 题目列表
            output_path: 输出文件路径
        """
        problems = Exporter.sort_problems(problems)
        lines = [
            "# 算法竞赛补题清单\n",
            f"**生成时间**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"**题目数量**: {len(problems)}\n",
            "---\n",
            "## 题目列表（按难度排序）\n",
            "\n",
            "| # | 平台 | 题目 | 难度 Rating | 链接 |",
            "|---|------|------|-------------|------|"
        ]

        for i, problem in enumerate(problems, 1):
            platform = problem.platform.upper()
            problem_id = problem.problem_id
            rating = problem.clist_rating if problem.clist_rating else "N/A"
            title = problem.title if problem.title else ""
            url = problem.url

            # Markdown链接格式
            link = f"[{title}]({url})" if title else url

            lines.append(f"| {i} | {platform} | {problem_id} | {rating} | {link} |")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"已导出Markdown: {output_path} ({len(problems)} 道题目)")

    @staticmethod
    def export_all(problems: List[Problem],
                   json_path: str = 'problems.json',
                   csv_path: str = 'problems.csv',
                   md_path: str = 'README.md'):
        """
        导出所有格式

        Args:
            problems: 题目列表
            json_path: JSON文件路径
            csv_path: CSV文件路径
            md_path: Markdown文件路径
        """
        # 先排序
        sorted_problems = Exporter.sort_problems(problems)

        # 导出所有格式
        Exporter.export_json(sorted_problems, json_path)
        Exporter.export_csv(sorted_problems, csv_path)
        Exporter.export_markdown(sorted_problems, md_path)

        return sorted_problems

from datetime import datetime, timedelta

import requests
from typing import List, Dict
from models.problem import Problem


class AtCoderCrawler:
    """AtCoder未解决题目爬虫

    使用AtCoder Problems非官方API（https://kenkoooo.com/atcoder/）
    """

    API_BASE = "https://kenkoooo.com/atcoder/atcoder-api/v3"

    def __init__(self, handle: str, contest_only: bool = True):
        """
        初始化AtCoder爬虫

        Args:
            handle: AtCoder用户名
            contest_only: 是否只爬取比赛题目（默认True）
        """
        self.handle = handle
        self.contest_only = contest_only
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_submissions(self) -> List[Dict]:
        """
        获取用户所有提交记录

        Returns:
            提交记录列表
        """
        url = f"{self.API_BASE}/user/submissions"
        end_time = datetime.now()
        start_time = end_time - timedelta(days=730)
        params = {
            'user': self.handle,
            'from_second': int(start_time.timestamp()),
            'to_second': int(end_time.timestamp()),
        }

        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            print("所有的atc提交题目:", response.json())

            return response.json()

        except requests.RequestException as e:
            raise Exception(f"获取AtCoder提交记录失败: {e}")

    def fetch_problems_map(self) -> Dict[str, Dict]:
        """
        获取所有题目的映射表

        Returns:
            {problem_id: problem_info}
        """
        url = "https://kenkoooo.com/atcoder/resources/problems.json"

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            problems = response.json()


            print("所有的atc题目题单长度:", len(problems))
            # 构建problem_id到problem_info的映射
            return {p['id']: p for p in problems}

        except requests.RequestException as e:
            print(f"获取题目列表失败: {e}")
            return {}

    def get_unsolved_problems(self) -> List[Problem]:
        """
        获取未解决的题目列表

        Returns:
            未解决题目列表
        """
        submissions = self.fetch_submissions()
        problems_map = self.fetch_problems_map()

        # 按题目分组：{problem_id: [submissions]}
        problem_submissions: Dict[str, List[Dict]] = {}
        for sub in submissions:
            problem_id = sub.get('problem_id')

            if problem_id not in problem_submissions:
                problem_submissions[problem_id] = []
            problem_submissions[problem_id].append(sub)

        # 筛选未解决的题目（从未AC过）
        unsolved = []
        for problem_id, subs in problem_submissions.items():
            has_ac = any(sub.get('result') == 'AC' for sub in subs)

            if not has_ac:
                # 获取题目信息
                problem_info = problems_map.get(problem_id, {})
                title = problem_info.get('title', '')
                contest_id = problem_info.get('contest_id', '')

                # 如果只爬比赛题，过滤掉practice题
                if self.contest_only:
                    # AtCoder的practice题通常contest_id包含'practice'
                    if 'practice' in contest_id.lower():
                        continue

                problem = Problem(
                    platform='atcoder',
                    contest_id=contest_id,
                    problem_index=problem_id,  # AtCoder使用完整problem_id
                    title=title
                )
                # 覆盖URL以使用正确的problem_id
                problem.url = f"https://atcoder.jp/contests/{contest_id}/tasks/{problem_id}"
                unsolved.append(problem)

        return unsolved

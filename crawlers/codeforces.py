import requests
from typing import List, Dict
from models.problem import Problem


class CodeforcesCrawler:
    """Codeforces未解决题目爬虫"""

    API_BASE = "https://codeforces.com/api"

    def __init__(self, handle: str, include_gym: bool = True):
        """
        初始化CF爬虫

        Args:
            handle: Codeforces用户名
            include_gym: 是否包含Gym题目（默认包含）
        """
        self.handle = handle
        self.include_gym = include_gym
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
        url = f"{self.API_BASE}/user.status"
        params = {
            'handle': self.handle,
            'from': 1,
            'count': 10000  # CF API限制每次最多10000条
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data['status'] != 'OK':
                raise Exception(f"API返回错误: {data.get('comment', 'Unknown error')}")

            return data['result']

        except requests.RequestException as e:
            raise Exception(f"获取提交记录失败: {e}")

    def get_unsolved_problems(self) -> List[Problem]:
        """
        获取未解决的题目列表

        Returns:
            未解决题目列表
        """
        submissions = self.fetch_submissions()

        # 按题目分组：{(contest_id, index): [submissions]}
        problem_submissions: Dict[tuple, List[Dict]] = {}
        for sub in submissions:
            # 跳过非比赛提交（如果设置了不包含Gym）
            if not self.include_gym:
                contest_id = sub.get('problem', {}).get('contestId')
                if isinstance(contest_id, int) and contest_id >= 100000:
                    # Gym的contestId通常>=100000
                    continue

            problem = sub.get('problem', {})
            key = (
                problem.get('contestId'),
                problem.get('index')
            )

            if key not in problem_submissions:
                problem_submissions[key] = []
            problem_submissions[key].append(sub)

        # 筛选未解决的题目（从未AC过）
        unsolved = []
        for key, subs in problem_submissions.items():
            contest_id, problem_index = key
            has_ac = any(sub.get('verdict') == 'OK' for sub in subs)

            if not has_ac:
                # 获取题目信息（从第一次提交中获取）
                problem_info = subs[0].get('problem', {})
                title = problem_info.get('name', '')

                problem = Problem(
                    platform='codeforces',
                    contest_id=str(contest_id),
                    problem_index=problem_index,
                    title=title
                )
                unsolved.append(problem)

        return unsolved

    def fetch_problem_info(self, contest_id: str, problem_index: str) -> Dict:
        """
        获取单道题目的详细信息（可选功能）

        Args:
            contest_id: 比赛ID
            problem_index: 题目编号（如A、B、C...）

        Returns:
            题目详细信息
        """
        url = f"{self.API_BASE}/problemset.problems"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data['status'] != 'OK':
                return {}

            # 在题目列表中查找
            problems = data['result']['problems']
            problem_map = {}
            for p in problems:
                if p.get('contestId') == int(contest_id) and p.get('index') == problem_index:
                    return p

            return {}

        except Exception as e:
            print(f"获取题目详情失败: {e}")
            return {}

    def fetch_user_contests(self) -> List[Dict]:
        """
        获取用户参加过的比赛列表
        Returns:
            比赛列表
        """
        url = f"{self.API_BASE}/user.rating"
        params = {'handle': self.handle}

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data['status'] != 'OK':
                return []

            return data['result']

        except requests.RequestException as e:
            raise Exception(f"获取用户比赛列表失败: {e}")

    def fetch_contest_problems(self, contest_id: int) -> List[Dict]:
        """
        获取指定比赛的题目列表

        Args:
            contest_id: 比赛ID

        Returns:
            题目列表
        """
        url = f"{self.API_BASE}/contest.standings"
        params = {
            'contestId': contest_id,
            'showUnofficial': False
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data['status'] != 'OK':
                return []

            # 获取题目列表
            problems = data['result'].get('problems', [])
            return problems

        except requests.RequestException as e:
            print(f"获取比赛 {contest_id} 的题目列表失败: {e}")
            return []

    def get_contest_unattempted_problems(self) -> List[Problem]:
        """
        获取用户参加过的比赛中未尝试的题目
        Returns:
            未尝试题目列表
        """
        print("  正在获取比赛未尝试的题目...")

        # 获取用户的所有提交记录
        submissions = self.fetch_submissions()

        # 构建已尝试题目的集合 {(contest_id, problem_index)}
        attempted_problems = set()
        for sub in submissions:
            problem = sub.get('problem', {})
            contest_id = problem.get('contestId')
            problem_index = problem.get('index')
            if contest_id and problem_index:
                attempted_problems.add((contest_id, problem_index))

        # 获取用户参加的比赛列表
        contests = self.fetch_user_contests()
        print(f"  找到 {len(contests)} 场参加过的比赛")

        # 获取每场比赛的题目，筛选出未尝试的
        unattempted = []
        for contest in contests:
            contest_id = contest.get('contestId')

            # 跳过 Gym（如果设置了不包含Gym）
            if not self.include_gym and contest_id >= 100000:
                continue

            # 获取比赛的题目列表
            problems = self.fetch_contest_problems(contest_id)

            for problem in problems:
                problem_index = problem.get('index')
                key = (contest_id, problem_index)

                # 如果这个题目没有被尝试过
                if key not in attempted_problems:
                    title = problem.get('name', '')
                    problem_obj = Problem(
                        platform='codeforces',
                        contest_id=str(contest_id),
                        problem_index=problem_index,
                        title=title
                    )
                    unattempted.append(problem_obj)

        print(f"  找到 {len(unattempted)} 道比赛未尝试的题目")
        return unattempted

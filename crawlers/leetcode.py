import requests
import json
from typing import List, Dict, Optional
from models.problem import Problem


class LeetCodeCrawler:
    """LeetCode未解决题目爬虫

    使用LeetCode GraphQL API（需要cookie）
    """

    GRAPHQL_URL = "https://leetcode.com/graphql"

    def __init__(self, cookies: Dict[str, str]):
        """
        初始化LeetCode爬虫

        Args:
            cookies: LeetCode登录cookie，格式为 {key: value}
                    可以从浏览器开发者工具中获取
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json',
            'Origin': 'https://leetcode.com',
            'Referer': 'https://leetcode.com/'
        })

        # 设置cookies
        cookie_str = '; '.join([f"{k}={v}" for k, v in cookies.items()])
        self.session.headers.update({'Cookie': cookie_str})

    def fetch_submissions(self) -> List[Dict]:
        """
        获取用户最近的提交记录

        Returns:
            提交记录列表
        """
        query = """
        query getRecentSubmissionList($limit: Int!, $lastKey: String) {
            recentSubmissionList(limit: $limit, lastKey: $lastKey) {
                title
                titleSlug
                status
                lang
                timestamp
                url
                isPending
            }
        }
        """

        variables = {
            "limit": 50  # 可以根据需要调整
        }

        try:
            response = self.session.post(
                self.GRAPHQL_URL,
                json={'query': query, 'variables': variables},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if 'errors' in data:
                raise Exception(f"GraphQL错误: {data['errors']}")

            return data.get('data', {}).get('recentSubmissionList', [])

        except requests.RequestException as e:
            raise Exception(f"获取LeetCode提交记录失败: {e}")

    def fetch_solved_problems(self) -> set[str]:
        """
        获取用户已解决的题目列表

        Returns:
            已解决题目的titleSlug集合
        """
        query = """
        query getUserProfile($username: String!) {
            matchedUser(username: $username) {
                submitStats: submitStatsGlobal {
                    acSubmissionNum {
                        difficulty
                        count
                    }
                }
            }
        }
        """

        # 先获取用户名（从cookie中推测）
        # 这里使用另一种方法：获取所有已解决的题目

        query2 = """
        query problemSolvedBeatsStats($username: String!) {
            userQuestionStats(userSlug: $username) {
                questionsSolved {
                    difficulty
                    count
                }
            }
        }
        """

        # 使用更直接的方法：通过 submissions 获取AC的题目
        submissions = self.fetch_submissions()
        solved = set()

        for sub in submissions:
            if sub.get('status') == 'ACCEPTED':
                solved.add(sub.get('titleSlug'))

        return solved

    def get_unsolved_problems(self) -> List[Problem]:
        """
        获取未解决的题目列表

        注意：这个方法基于"最近提交记录"，可能不完整。
        如果需要完整的题目列表，需要额外的API调用。

        Returns:
            未解决题目列表
        """
        submissions = self.fetch_submissions()
        solved = self.fetch_solved_problems()

        # 按题目分组
        problem_submissions: Dict[str, List[Dict]] = {}
        for sub in submissions:
            title_slug = sub.get('titleSlug')
            if title_slug not in problem_submissions:
                problem_submissions[title_slug] = []
            problem_submissions[title_slug].append(sub)

        # 筛选未解决的题目
        unsolved = []
        for title_slug, subs in problem_submissions.items():
            has_ac = any(sub.get('status') == 'ACCEPTED' for sub in subs)

            if not has_ac:
                # 获取题目信息
                title = subs[0].get('title', '')
                url = subs[0].get('url', '')

                problem = Problem(
                    platform='leetcode',
                    contest_id=title_slug,  # LeetCode使用titleSlug作为ID
                    problem_index='',
                    title=title,
                    url=url
                )

                unsolved.append(problem)

        return unsolved

    def get_all_attempted_problems(self) -> List[Problem]:
        """
        获取所有尝试过但未解决的题目

        Returns:
            未解决题目列表
        """
        submissions = self.fetch_submissions()
        problem_status: Dict[str, bool] = {}  # {title_slug: has_ac}

        for sub in submissions:
            title_slug = sub.get('titleSlug')
            is_accepted = sub.get('status') == 'ACCEPTED'

            if title_slug not in problem_status:
                problem_status[title_slug] = is_accepted
            else:
                # 如果已经有AC记录，保持为True
                problem_status[title_slug] = problem_status[title_slug] or is_accepted

        # 筛选未解决的题目
        unsolved = []
        for title_slug, has_ac in problem_status.items():
            if not has_ac:
                # 从提交记录中获取题目信息
                sub_info = next(
                    (s for s in submissions if s.get('titleSlug') == title_slug),
                    {}
                )

                problem = Problem(
                    platform='leetcode',
                    contest_id=title_slug,
                    problem_index='',
                    title=sub_info.get('title', ''),
                    url=sub_info.get('url', '')
                )

                unsolved.append(problem)

        return unsolved

import requests
import time
from typing import Optional, Dict, List
from models.problem import Problem


class ClistFetcher:
    """Clist难度评级获取器

    从Clist.by获取题目的难度rating
    """

    API_BASE = "https://clist.by:443/api/v4/"
    PROBLEM_CACHE: Dict[str, Dict] = {}

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化Clist Fetcher

        Args:
            api_key: Clist API Key（如果需要认证）
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        if api_key:
            self.session.headers.update({
                'Authorization': f'{api_key}'
            })

    def search_problem(self, platform: str,  problem_title: str, max_retries: int = 3) -> Optional[Dict]:
        """
        搜索题目并获取rating

        Args:
            platform: 平台名称 (codeforces, atcoder, leetcode)
            problem_title: 题目名称
            max_retries: 最大重试次数（默认3次）

        Returns:
            题目信息（包含rating），如果未找到返回None
        """
        # 构建查询字符串
        if platform == 'codeforces':
            resource = 'codeforces.com'
        elif platform == 'atcoder':
            resource = 'atcoder.jp'
        elif platform == 'leetcode':
            resource = 'leetcode.com'
        else:
            return None

        # 检查缓存
        cache_key = f"{platform}-{problem_title}"
        if cache_key in self.PROBLEM_CACHE:
            return self.PROBLEM_CACHE[cache_key]

        # 重试机制：处理 429 Too Many Requests 错误
        for attempt in range(max_retries):
            try:
                # 使用Clist API搜索题目
                url = f"{self.API_BASE}problem/"
                params = {
                    'resource': resource,
                    'name': problem_title,
                }

                response = self.session.get(url, params=params, timeout=10)

                # 处理 429 错误
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        # 指数退避：第一次等待15秒，第二次30秒，第三次60秒
                        wait_time = 15 * (2 ** attempt)
                        print(f"  速率限制，等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"  ⚠️  达到最大重试次数，跳过此题目")
                        return None

                response.raise_for_status()

                data = response.json()

                if data.get('objects'):
                    problem_info = data['objects'][0]
                    # 缓存结果
                    self.PROBLEM_CACHE[cache_key] = problem_info
                    return problem_info

                return None

            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    # 等待后重试
                    wait_time = 5 * (attempt + 1)
                    print(f"  请求失败，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"获取Clist rating失败 ({platform} {problem_title}): {e}")
                    return None

        return None

    def fetch_rating(self, problem: Problem) -> Optional[int]:
        """
        获取单个题目的rating

        Args:
            problem: 题目对象

        Returns:
            题目rating，如果获取失败返回None
        """
        problem_info = self.search_problem(
            problem.platform,
            problem.title
        )

        if problem_info:
            # Clist返回的rating字段
            rating = problem_info.get('rating')
            if rating:
                return int(rating)

        return None

    def fetch_ratings_batch(self, problems: List[Problem], delay: float = 5.0) -> None:
        """
        批量获取题目的rating

        Args:
            problems: 题目列表，会直接修改对象的clist_rating字段
            delay: 每次请求之间的延迟时间（秒），默认5秒
                  Clist API 对未认证用户限制严格，建议至少5秒
        """
        total = len(problems)
        success_count = 0
        fail_count = 0

        print(f"ℹ️  Clist API 延迟设置为 {delay} 秒/请求")
        if not self.api_key:
            print("⚠️  警告: 未配置 Clist API Key，速率限制可能较严格")
            print("   如需更快的请求速度，请在配置中添加 CLIST_API_KEY")

        for i, problem in enumerate(problems, 1):
            print(f"获取rating: {i}/{total} ({problem.platform} {problem.contest_id} {problem.problem_index})")

            rating = self.fetch_rating(problem)

            if rating is not None:
                problem.clist_rating = rating
                success_count += 1
            else:
                fail_count += 1

            # 避免频繁请求 - 增加延迟时间以避免速率限制
            if i < total:
                time.sleep(delay)

        print(f"  成功: {success_count}/{total} 道题目获取到rating")
        if fail_count > 0:
            print(f"  失败: {fail_count}/{total} 道题目未能获取rating")

    def get_contest_problems(self, platform: str, contest_id: str) -> List[Dict]:
        """
        获取某个比赛的所有题目信息（可选功能）

        Args:
            platform: 平台名称
            contest_id: 比赛ID

        Returns:
            题目信息列表
        """
        try:
            url = f"{self.API_BASE}contest/"
            params = {
                'resource': f"{platform}.com" if platform != 'atcoder' else 'atcoder.jp',
                'id': contest_id
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('objects'):
                contest = data['objects'][0]
                return contest.get('problems', [])

            return []

        except Exception as e:
            print(f"获取比赛题目失败: {e}")
            return []


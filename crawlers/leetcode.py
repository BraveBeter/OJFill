import tls_client
from typing import List, Dict
from models.problem import Problem


class LeetCodeCrawler:
    """LeetCode未解决题目爬虫

    使用 tls_client 绕过 TLS 指纹检测 (更稳定的方案)
    """

    GRAPHQL_URL = "https://leetcode.cn/graphql"

    def __init__(self, cookies: Dict[str, str]):
        """
        初始化 LeetCode 爬虫
        """
        # 1. 初始化 Session，指定模拟 Chrome 112
        # random_tls_extension_order=True 有助于进一步混淆指纹
        self.session = tls_client.Session(
            client_identifier="chrome_112",
            random_tls_extension_order=True
        )

        # 2. 构造基础 Headers
        # 注意：tls_client 的 headers update 逻辑比较简单，建议一次性写好
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
            'Content-Type': 'application/json',
            'Origin': 'https://leetcode.cn',
            'Referer': 'https://leetcode.cn/u/me/',
            'Accept-Language': 'en-US,en;q=0.9'
        }

        # 3. 处理 CSRF Token (这是 LeetCode 400 错误的关键)
        csrf_token = cookies.get('csrftoken')
        if csrf_token:
            headers['x-csrftoken'] = csrf_token
        else:
            print("⚠️ 警告: Cookies 中未找到 csrftoken，请求可能会失败。")

        # 将 headers 应用到 session
        self.session.headers.update(headers)

        # 4. 设置 Cookies
        # tls_client 处理 cookies 需要将其转换为简单的字典或字符串
        # 我们直接将传入的字典设置进去
        self.session.cookies.update(cookies)

    def fetch_submissions(self) -> List[Dict]:
        """
        获取用户最近的提交记录
        """
        # 首先尝试通过 REST API 获取（这是最可靠的方法）
        try:
            return self._fetch_via_rest_api()
        except Exception as e:
            print(f"REST API 失败，尝试 GraphQL: {e}")

        # 如果 REST API 失败，尝试 GraphQL
        return self._fetch_via_graphql()

    def _fetch_via_graphql(self) -> List[Dict]:
        """通过 GraphQL 获取"""
        # 尝试多种查询
        queries_to_try = [
            # 方案1: 不带 categorySlug，获取所有题目
            """
            query getProblemsetQuestionList {
                problemsetQuestionList {
                    questions {
                        title
                        titleSlug
                        status
                    }
                }
            }
            """,
            # 方案2: 带 limit 参数
            """
            query getProblemsetQuestionList {
                problemsetQuestionList(limit: 3000) {
                    questions {
                        title
                        titleSlug
                        status
                    }
                }
            }
            """
        ]

        for i, query in enumerate(queries_to_try):
            try:
                response = self.session.post(
                    self.GRAPHQL_URL,
                    json={'query': query, 'variables': {}},
                    timeout_seconds=15
                )

                if response.status_code == 200:
                    data = response.json()
                    if 'errors' not in data:
                        print("使用 GraphQL 查询成功")
                        return self._extract_data_from_response(data, 0)

            except Exception as e:
                print(f"GraphQL 查询 {i} 失败: {e}")
                continue

        raise Exception("所有 API 均失败")

    def _extract_data_from_response(self, data: dict, query_type: int) -> List[Dict]:
        """从成功的响应中提取数据"""
        results = []

        if query_type == 0:
            # problemsetQuestionList
            questions = data.get('data', {}).get('problemsetQuestionList', {}).get('questions', [])
            print(f"获取到 {len(questions)} 道题目")

            ac_count = 0
            notac_count = 0
            no_status_count = 0

            for q in questions:
                status = q.get('status')

                # 统计
                if status == 'ac':
                    ac_count += 1
                elif status in ['notac', 'tried', 'Attempted']:
                    notac_count += 1
                else:
                    no_status_count += 1

                # 只处理有状态的题目（已解决或尝试过）
                if status is not None and status != '':
                    results.append({
                        'title': q.get('title'),
                        'titleSlug': q.get('titleSlug'),
                        'status': 'ACCEPTED' if status == 'ac' else 'NOT_ACCEPTED',
                        'timestamp': None,
                        'url': f"https://leetcode.cn/problems/{q.get('titleSlug')}/",
                        'lang': None
                    })

            print(f"AC题目: {ac_count}, 未AC题目: {notac_count}, 未尝试题目: {no_status_count}")
            print(f"返回有交互的题目: {len(results)} 道")
        elif query_type == 1:
            # questionList
            questions = data.get('data', {}).get('questionList', [])
            for q in questions:
                status = q.get('status')
                results.append({
                    'title': q.get('title'),
                    'titleSlug': q.get('titleSlug'),
                    'status': 'ACCEPTED' if status == 'ac' else 'NOT_ACCEPTED',
                    'timestamp': None,
                    'url': f"https://leetcode.cn/problems/{q.get('titleSlug')}/",
                    'lang': None
                })
        elif query_type == 2:
            # dailyCodingChallengeV2 - 这个只有每日一题，不太够用
            # 但至少能证明 API 是通的
            question = data.get('data', {}).get('dailyCodingChallengeV2', {}).get('challenge', {}).get('question', {})
            if question:
                results.append({
                    'title': question.get('title'),
                    'titleSlug': question.get('titleSlug'),
                    'status': 'NOT_ACCEPTED',  # 未知状态
                    'timestamp': None,
                    'url': f"https://leetcode.cn/problems/{question.get('titleSlug')}/",
                    'lang': None
                })

        return results

    def _fetch_via_rest_api(self) -> List[Dict]:
        """通过 REST API 获取数据"""
        # LeetCode 的 REST API 是获取用户题目状态最可靠的方法
        # 尝试多个可能的 URL
        api_urls = [
            "https://leetcode.cn/api/problems/all",
            "https://leetcode.com/api/problems/all",  # 尝试 .com 域名
        ]

        last_error = None

        for api_url in api_urls:
            try:
                print(f"尝试 REST API: {api_url}")
                response = self.session.get(api_url, timeout_seconds=15, allow_redirects=True)

                if response.status_code not in [200, 301, 302]:
                    last_error = f"HTTP Error {response.status_code}"
                    continue

                # 如果是重定向，跟随重定向
                if response.status_code in [301, 302]:
                    redirect_url = response.headers.get('Location', '')
                    if redirect_url:
                        print(f"重定向到: {redirect_url}")
                        response = self.session.get(redirect_url, timeout_seconds=15, allow_redirects=True)

                if response.status_code != 200:
                    last_error = f"HTTP Error {response.status_code}"
                    continue

                data = response.json()

                # 这个 API 返回的格式是：
                # {
                #   "stat_status_pairs": [
                #     {
                #       "stat": {...},
                #       "status": "ac" | "notac" | null,
                #       "difficulty": "Easy" | "Medium" | "Hard"
                #     }
                #   ]
                # }

                if 'stat_status_pairs' not in data:
                    last_error = "响应数据格式不正确，缺少 stat_status_pairs 字段"
                    continue

                problems = data.get('stat_status_pairs', [])
                print(f"通过 REST API 获取到 {len(problems)} 道题目")

                results = []
                ac_count = 0
                notac_count = 0
                no_status_count = 0

                for p in problems:
                    if not isinstance(p, dict):
                        continue

                    stat = p.get('stat', {})
                    status = p.get('status')

                    # 统计
                    if status == 'ac':
                        ac_count += 1
                    elif status in ['notac', 'tried', 'Attempted']:
                        notac_count += 1
                    else:
                        no_status_count += 1

                    # 只记录有交互的题目（已解决或尝试过但未解决）
                    if status is not None and status != '':
                        results.append({
                            'title': stat.get('question__title', ''),
                            'titleSlug': stat.get('question__title_slug', ''),
                            'status': 'ACCEPTED' if status == 'ac' else 'NOT_ACCEPTED',
                            'timestamp': None,
                            'url': f"https://leetcode.cn/problems/{stat.get('question__title_slug', '')}/",
                            'lang': None
                        })

                print(f"AC题目: {ac_count}, 未AC题目: {notac_count}, 未尝试题目: {no_status_count}")
                print(f"返回有交互的题目: {len(results)} 道")

                return results

            except Exception as e:
                last_error = str(e)
                print(f"API {api_url} 失败: {e}")
                continue

        raise Exception(f"REST API 获取失败: {last_error}")


    def get_unsolved_problems(self) -> List[Problem]:
        """
        获取所有尝试过但未解决的题目
        Returns:
            未解决题目列表
        """
        submissions = self.fetch_submissions()
        problem_status: Dict[str, bool] = {}  # {title_slug: has_ac}

        for sub in submissions:
            # print(sub)
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
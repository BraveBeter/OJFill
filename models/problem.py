from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Problem:
    """统一的题目数据模型"""
    platform: str
    contest_id: str
    problem_index: str
    title: Optional[str] = None
    url: str = ""
    clist_rating: Optional[int] = None

    def __post_init__(self):
        """生成problem_id和URL"""
        if self.platform == "codeforces":
            self.problem_id = f"CF-{self.contest_id}-{self.problem_index}"
            if not self.url:
                self.url = f"https://codeforces.com/contest/{self.contest_id}/problem/{self.problem_index}"
        elif self.platform == "atcoder":
            self.problem_id = f"AT-{self.contest_id}-{self.problem_index.lower()}"
            if not self.url:
                self.url = f"https://atcoder.jp/contests/{self.contest_id}/tasks/{self.problem_index}"
        elif self.platform == "leetcode":
            self.problem_id = f"LC-{self.contest_id}"
            if not self.url:
                self.url = f"https://leetcode.com/problems/{self.contest_id}/"
        else:
            self.problem_id = f"{self.platform.upper()}-{self.contest_id}-{self.problem_index}"

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "platform": self.platform,
            "problem_id": self.problem_id,
            "contest_id": self.contest_id,
            "problem_index": self.problem_index,
            "title": self.title,
            "url": self.url,
            "clist_rating": self.clist_rating
        }

# pylint: disable-all # Pylint seems to crash when looking into praw.
# mypy: ignore-errors
# Mypy doesn't have praw stubs libraries.
import datetime
from typing import Iterator, Optional

import praw
from praw.models import Subreddit

from src.config.config import CONFIG


class RedditClient:
    __DATA_FILE: str = "kpopSubReddit.txt"
    __LIMIT_NB_POSTS_RETRIEVED: Optional[int] = None

    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=CONFIG.REDDIT_CLIENT_ID,
            client_secret=CONFIG.REDDIT_CLIENT_SECRET,
            user_agent=CONFIG.REDDIT_USER_AGENT,
        )

    def getPosts(self):
        subredditName: str = "kpop"
        subreddit: Subreddit = self.reddit.subreddit(subredditName)
        posts: Iterator = subreddit.new(limit=self.__LIMIT_NB_POSTS_RETRIEVED)

        with open(CONFIG.DATA_PATH + self.__DATA_FILE, mode="wb") as file:
            for post in posts:
                if post.link_flair_text.upper() in CONFIG.REDDIT_FLAIR_TAGS:
                    date = datetime.datetime.fromtimestamp(post.created).strftime(
                        "%Y/%m/%d"
                    )
                    print(
                        f"{post.link_flair_text} {post.title} {post.shortlink} {date}."
                    )
                    file.write(
                        f"{post.link_flair_text} {post.title} {post.shortlink} {date}.\n".encode(
                            "utf-8"
                        )
                    )

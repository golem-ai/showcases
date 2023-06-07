import datetime

from src.config.config import CONFIG
from src.domain.showcase import Showcase
from src.service.core.core import Core
from src.service.core.response import Response
from src.service.redditClient import RedditClient


def cleanLines(lines: list[str]) -> list[str]:
    return [
        line
        for line in lines
        if line
        and line != "\n"
        and not line.startswith("#")
        and not line.startswith("\n#")
    ]


def worker():
    if CONFIG.REDDIT_CLIENT_ID and CONFIG.REDDIT_CLIENT_SECRET:
        RedditClient().getPosts()

    for file in CONFIG.DATA_FILES:
        print(f"{datetime.datetime.now()}\t\tGet text")
        with open(file, encoding="utf-8") as content:
            lines: list[str] = cleanLines(content.read().split("\n"))

        print(f"{datetime.datetime.now()}\t\tCreate analyses")
        analysesIDs: list[str] = Core.createAnalyses(lines)

        print(f"{datetime.datetime.now()}\t\tGet analyses")
        responses: list[Response] = Core.getAnalyses(analysesIDs)

        print(f"{datetime.datetime.now()}\t\tCreate graph")
        graphShowcase: Showcase = Showcase()
        for response in responses:
            graphShowcase.generateFromCoreResponse(response)
        graphShowcase.stop()


if __name__ == "__main__":
    print(f"{datetime.datetime.now()}\t\tStart job")
    worker()
    print(f"{datetime.datetime.now()}\t\tJob done")

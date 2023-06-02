import os

import psutil
from dotenv import load_dotenv


class Config:
    def __init__(self):
        self.DATA_PATH: str = "/demo/src/data/"
        self.DATA_FILES: list[str] = [
            f"{self.DATA_PATH}kpopSubReddit.txt",
        ]

        load_dotenv()

        self.ACCESS_KEY_SECRET: str = os.getenv("ACCESS_KEY_SECRET", "")
        self.ACCESS_KEY_ID: str = os.getenv("ACCESS_KEY_ID", "")
        self.ENVIRONMENT_ID: str = os.getenv("ENVIRONMENT_ID", "")
        self.CONSOLE_HOST: str = os.getenv("CONSOLE_HOST", "")
        self.DB_HOST: str = os.getenv("DB_HOST", "")

        self.CPU_COUNT: int = self.__CPUCount()

        self.REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID", "")
        self.REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET", "")
        self.REDDIT_USER_AGENT: str = "KpopDemo"
        self.REDDIT_FLAIR_TAGS: list[str] = [
            "[Dance Cover]".upper(),
            "[Song Cover]".upper(),
            "[Dance Challenge]".upper(),
            "[Performance]".upper(),
            "[Music Show]".upper(),
            "[Live]".upper(),
        ]

    def __CPUCount(self) -> int:
        cpuCount = psutil.cpu_count()
        if cpuCount is None:
            return 1
        return cpuCount - 1


CONFIG = Config()


class Neo4JConfig:
    def __init__(self):
        """
        Nodes which do the action
        """
        self.DOER: str = "doer"
        self.doers: list[str] = ["member", "group"]
        """
            Nodes on which the action is being made
        """
        self.TARGET: str = "target"
        """
        Nodes will be chosen by order of priority.
        Example:
            With the sentence "Ukrainians have taken back Kiev in Ukraine",
            We will add this relation to neo4j (Ukrainians)-[militaryAction]->(Kiev).
            With the sentence "Ukrainians have taken back Ukraine"
            We will add this relation to neo4j (Ukrainians)-[militaryAction]->(Ukraine).
        """
        self.targets: list[str] = ["member", "group", "soloArtist", "musicShow", "show"]

        self.ACTION: str = "action"
        self.actions: list[str] = [
            "flairCover",
            "flairNewRelease",
            "flairDanceChallenge",
        ]
        """
            The action's attributes
            Key: archetype's name which we will take the value from
            Value: field name in neo4j
        """
        self.action_attributes: dict[str, str] = {
            "date": "date",
            "url": "url",
        }


NEO4J_CONFIG = Neo4JConfig()

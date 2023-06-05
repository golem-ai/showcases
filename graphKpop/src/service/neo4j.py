# pylint: disable-all # Pylint seems to crash when looking into neo4j.
import re
from typing import Optional

from neo4j import GraphDatabase, Driver

from src.config.config import NEO4J_CONFIG


class Neo4j:
    def __init__(self, uri: str):
        self.driver: Driver = GraphDatabase.driver(uri)

    def close(self):
        self.driver.close()

    def __runQuery(self, query: str):
        with self.driver.session() as session:
            _ = session.run(query)

    def __cleanNodeString(self, node: str) -> str:
        return re.sub("[^0-9a-zA-Z _]+", "", node)

    def createNode(
        self, nodeName: str, nodeValue: str, attributes: Optional[dict[str, str]] = None
    ):
        nodeName = self.__cleanNodeString(nodeName)
        nodeValue = self.__cleanNodeString(nodeValue)
        nodeValue = nodeValue.strip("'\"")
        query: str = f"MERGE (a:{nodeName} {{ name: '{nodeValue}' }})"
        if attributes:
            for key, value in attributes.items():
                query += f" SET a.{key} = {value}"
        print(query)
        self.__runQuery(query)

    def createRelationship(
        self,
        doerNode: str,
        doerValue: str,
        targetNode: str,
        targetValue: str,
        action: str,
        actionAttribute: dict[str, list[str]],
    ):
        doerNode = self.__cleanNodeString(doerNode)
        doerValue = self.__cleanNodeString(doerValue)
        targetNode = self.__cleanNodeString(targetNode)
        targetValue = self.__cleanNodeString(targetValue)
        action = self.__cleanNodeString(action.replace(" ", "_"))

        query: str = (
            f"MATCH (a: {doerNode} {{ name: '{doerValue}' }}) ,"
            f"( b: {targetNode} {{ name: '{targetValue}' }} ) MERGE (a)-[c:{action}]->(b)"
        )
        for key, value in actionAttribute.items():
            if len(value) == 1:
                query += f" SET c.{NEO4J_CONFIG.action_attributes[key]} = '{value[0]}'"
            else:
                query += f" SET c.{key} = '{value}'"

        print(query)
        self.__runQuery(query)

    def cleanDB(self):
        query: str = "MATCH (n) DETACH DELETE n"
        print(query)
        self.__runQuery(query)

from dataclasses import dataclass
from typing import Optional

from src.config.config import NEO4J_CONFIG, CONFIG
from src.service.core.response import Response, Parameter, Interaction
from src.service.neo4j import Neo4j


class Node:
    def __init__(self, name: str, value: str, parents: Optional[list["Node"]] = None):
        self.name: str = name
        self.value: str = value
        self.parents: list["Node"] = []
        if parents:
            self.parents = parents


@dataclass
class Relation:
    name: str
    attributes: dict[str, list[str]]


class Demo:
    PARENT_LINK: str = "IN"
    NODE_ATTRIBUTE_VALUE: str = "Value"

    def __init__(self):
        self.neo4jClient = Neo4j(CONFIG.DB_HOST)

    def stop(self):
        self.neo4jClient.close()

    def __createNodes(self, nodes: list[Node]) -> None:
        for node in nodes:
            self.neo4jClient.createNode(nodeName=node.name, nodeValue=node.value)

    def __createChildrenParentsRelations(self, nodes: list[Node]) -> list[Node]:
        parents: list[Node] = []
        for node in nodes:
            for parent in node.parents:
                self.neo4jClient.createRelationship(
                    doerNode=node.name,
                    doerValue=node.value,
                    targetNode=parent.name,
                    targetValue=parent.value,
                    action=self.PARENT_LINK,
                    actionAttribute={},
                )
                parents.append(parent)
        return [node for node in nodes if node not in parents]

    def __insertNodesAndRelations(
        self, doers: list[Node], targets: list[Node], actions: list[Relation]
    ) -> None:
        self.__createNodes(doers + targets)
        doers = self.__createChildrenParentsRelations(doers)
        targets = self.__createChildrenParentsRelations(targets)

        for doer in doers:
            for action in actions:
                targetsNodes: list[Node] = targets.copy()
                if not targets:
                    targetsNodes = [doer]

                for target in targetsNodes:
                    self.neo4jClient.createRelationship(
                        doerNode=doer.name,
                        doerValue=doer.value,
                        targetNode=target.name,
                        targetValue=target.value,
                        action=action.name,
                        actionAttribute=action.attributes,
                    )

    def __getActionAttributes(self, name: str, value: str) -> dict[str, list[str]]:
        actionAttributes: dict[str, list[str]] = {}
        name = name.split("-")[-1]
        if name in NEO4J_CONFIG.action_attributes:
            if name not in actionAttributes:
                actionAttributes[name] = []
            actionAttributes[name].append(value)
        return actionAttributes

    def __getNodes(
        self, parameter: Parameter, nodeNames: list[str]
    ) -> tuple[list[Node], dict[str, list[str]]]:
        nodes: list[Node] = []
        actionAttributes: dict[str, list[str]] = {}
        if parameter.archetype in nodeNames:
            for value in parameter.values:
                nodes.append(Node(name=parameter.archetype, value=value.id))
                for capture in value.capture:
                    actionAttributes.update(
                        self.__getActionAttributes(capture.name, capture.value)
                    )
                if not value.capture:
                    actionAttributes.update(
                        self.__getActionAttributes(parameter.name, value.value)
                    )
        else:
            for value in parameter.values:
                for capture in value.capture:
                    actionAttributes.update(
                        self.__getActionAttributes(capture.name, capture.value)
                    )
                    for nodeName in nodeNames:
                        childArchetype: str = capture.name.split("-")[-1]
                        if childArchetype == nodeName:
                            nodes.append(Node(name=childArchetype, value=capture.value))
                            break

            for node in nodes:
                idx = [idx for idx, name in enumerate(nodeNames) if node.name == name][
                    0
                ]
                parents: list[Node] = [
                    nodeParent
                    for nodeParent in nodes
                    if nodeParent.name in nodeNames[idx + 1 :]  # noqa: E203
                ]
                node.parents = parents

        return nodes, actionAttributes

    def __getNodesAndRelations(
        self, interaction: Interaction
    ) -> tuple[list[Node], list[Node], list[Relation]]:
        doers: list[Node] = []
        targets: list[Node] = []
        actions: list[Relation] = []
        actionAttributes: dict[str, list[str]] = {}
        for parameter in interaction.parameters:
            if parameter.name == NEO4J_CONFIG.DOER:
                doers, actionAttributesDoer = self.__getNodes(
                    parameter, NEO4J_CONFIG.doers
                )
                actionAttributes.update(actionAttributesDoer)

            elif parameter.name == NEO4J_CONFIG.TARGET:
                targets, actionAttributesTarget = self.__getNodes(
                    parameter, NEO4J_CONFIG.targets
                )
                actionAttributes.update(actionAttributesTarget)

            elif parameter.name == NEO4J_CONFIG.ACTION:
                nodes, actionAttributes = self.__getNodes(
                    parameter, NEO4J_CONFIG.actions
                )
                actionAttributes.update(actionAttributes)
                for node in nodes:
                    actions.append(Relation(node.value, {}))
            else:
                for value in parameter.values:
                    for capture in value.capture:
                        actionAttributes.update(
                            self.__getActionAttributes(capture.name, capture.value)
                        )
                    if not value.capture:
                        actionAttributes.update(
                            self.__getActionAttributes(parameter.name, value.value)
                        )

        for action in actions:
            action.attributes = actionAttributes

        return doers, targets, actions

    def generateFromCoreResponse(self, response: Response) -> None:
        for interaction in response.interactions:
            doers, targets, actions = self.__getNodesAndRelations(interaction)

            self.__insertNodesAndRelations(doers, targets, actions)

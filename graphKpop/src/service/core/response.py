from dataclasses import dataclass
from typing import Optional


@dataclass
class Capture:
    name: str
    value: str


class Value:
    def __init__(
        self,
        archetypeId: str,
        value: str,
        capture: Optional[list[Capture]] = None,
    ):
        self.id: str = archetypeId
        self.value: str = ""
        if value:
            self.value = value
        self.capture = []
        if capture:
            self.capture = capture


@dataclass
class Parameter:
    archetype: str
    name: str
    values: list[Value]


@dataclass
class Interaction:
    name: str
    parameters: list[Parameter]


class Response:
    def __init__(self, response: dict):
        self.interactions: list[Interaction] = []
        for interaction in response.get("interactions", []):
            self.interactions.append(
                Interaction(
                    interaction["idInteraction"],
                    self.__getParameters(interaction["parametersDetail"]),
                )
            )

    @staticmethod
    def __getParameters(parametersCore) -> list[Parameter]:
        parameters: list[Parameter] = []
        for parameterName in parametersCore:
            values: list[Value] = []
            if parametersCore[parameterName]["values"]:
                for value in parametersCore[parameterName]["values"]:
                    captures: list[Capture] = []
                    if "capture" in value["value"]:
                        for capture in value["value"]["capture"]:
                            captures.append(
                                Capture(
                                    name=capture,
                                    value=value["value"]["capture"][capture],
                                )
                            )

                    values.append(
                        Value(
                            archetypeId=value["value"]["id"],
                            value=value["value"]["found"],
                            capture=captures,
                        )
                    )

                parameters.append(
                    Parameter(
                        archetype=parametersCore[parameterName]["archetype"],
                        name=parameterName,
                        values=values,
                    )
                )
        return parameters

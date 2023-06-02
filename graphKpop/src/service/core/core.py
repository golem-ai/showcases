import json
import signal
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any, Optional

import requests
from requests import ReadTimeout, Response as HTTPResponse, RequestException

from src.config.config import CONFIG
from src.service.core.response import Response


class Core:
    RETRY_NUMBER = 3
    __REQUEST_TIMEOUT = 6000000
    __STATUS_FINISHED = "FINISHED"
    __STATUS_ERROR = "ERROR"

    @staticmethod
    def __request(
        url: str, method: Callable, headers: dict, params: Optional[dict] = None
    ) -> HTTPResponse:
        retry = 0
        while retry < Core.RETRY_NUMBER:
            try:
                response = method(url=url, headers=headers, json=params, timeout=2)
                response.raise_for_status()
                return response
            except ReadTimeout as error:  # noqa: F841 # pylint: disable=W0612
                print(f"Connection timed out, retrying {retry + 1}/{Core.RETRY_NUMBER}")
                retry += 1
        raise ReadTimeout("Could not analyse request: request timed out")

    @staticmethod
    def __createAnalysis(text: str) -> str:
        params: dict[str, str] = {"text": text}
        headers: dict[str, str] = {"Authorization": CONFIG.ACCESS_KEY_SECRET}

        response: HTTPResponse = Core.__request(
            url=f"{CONFIG.CONSOLE_HOST}environment/{CONFIG.ENVIRONMENT_ID}/analyses?appId={CONFIG.ACCESS_KEY_ID}",
            method=requests.post,
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        analysisID: str = json.loads(response.text)["id"]
        return analysisID

    @staticmethod
    def createAnalyses(texts: list[str]) -> list[str]:
        analysesIDs: list[str] = []
        with ThreadPoolExecutor(max_workers=CONFIG.CPU_COUNT * 4) as executor:
            futureResults = {
                executor.submit(
                    Core.__createAnalysis,
                    text,
                ): text
                for text in texts
            }
            for future in futureResults:
                try:
                    analysesIDs.append(future.result())
                except ReadTimeout as createAnalysisError:
                    print(f"Error creating analysis: {createAnalysisError}")
        return analysesIDs

    @staticmethod
    def __getAnalysis(analysisID: str) -> tuple[dict[str, Any], str]:
        headers: dict[str, str] = {"Authorization": CONFIG.ACCESS_KEY_SECRET}
        response: HTTPResponse = Core.__request(
            url=f"{CONFIG.CONSOLE_HOST}analyses/{analysisID}/result?appId={CONFIG.ACCESS_KEY_ID}",
            method=requests.get,
            headers=headers,
        )
        responseDict: dict[str, Any] = json.loads(response.text)
        return responseDict, analysisID

    @staticmethod
    def __timeoutHandler(signum, frame):
        raise TimeoutError("Request timeout")

    @staticmethod
    def getAnalyses(analysesIDs: list[str]) -> list[Response]:
        responses: dict[str, Response] = {}
        signal.signal(signal.SIGALRM, Core.__timeoutHandler)
        signal.alarm(Core.__REQUEST_TIMEOUT)
        analysesIDsDone: list[str] = []
        while len(responses) < len(analysesIDs):
            with ThreadPoolExecutor(max_workers=CONFIG.CPU_COUNT * 4) as executor:
                futureResults = {
                    executor.submit(
                        Core.__getAnalysis,
                        analysisID,
                    ): analysisID
                    for analysisID in analysesIDs
                    if analysisID not in analysesIDsDone
                }
                for future in futureResults:
                    try:
                        response, analysisID = future.result()
                        if response["status"] == Core.__STATUS_FINISHED:
                            assert "result" in response.keys()
                            responses[analysisID] = Response(response["result"])
                            analysesIDsDone.append(analysisID)
                        elif response["status"] == Core.__STATUS_ERROR:
                            raise Exception(
                                f"Stopping, there was an error in the analysis {analysisID}"
                            )

                    except RequestException as createAnalysisError:
                        print(f"Error creating analysis: {createAnalysisError}")
            time.sleep(2)

        signal.alarm(0)
        return list(responses.values())

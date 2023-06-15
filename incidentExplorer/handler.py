import os

from requests import Response
# Use the package we installed
from slack_bolt import App
import requests
import time
import json
from datetime import datetime

# Initializes your app with your bot token and signing secret
app: App = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

# Standard entrypoint to a Scaleway serverless function
def handle(event, context):
    body: dict = json.loads(event["body"])
    # This is send by slack when you subscribe to events <https://api.slack.com/apis/connections/events-api#handshake>
    if "challenge" in body:
        return body["challenge"]

    if "X-Slack-Retry-Num" in event["headers"]:
        return "ok"

    text: dict = body["event"]["text"]

    # Your APP_ID & secret can be created directly in the golem.ai Console in the project you wish to call
    appId: str = os.environ.get("GOLEM_APP_ID", "")
    headers: dict[str, str] = {"Authorization": os.environ.get("GOLEM_SECRET", "")}

    query: dict[str, str] = {"text": text}

    # This create an analysis and return an id.
    url: str = f"https://api.console.golem.ai/environment/12250/analyses?appId={appId}"
    response: Response = requests.post(url, headers=headers, json=query)

    id: str = response.json()["id"]

    # We can then query here to get the analysis result.
    # Note that we could also setup a webhook in the console to receive a call in another app once the analysis is finished !
    url = f"https://api.console.golem.ai/analyses/{id}/result?appId={appId}"

    nluResult: dict = {}
    while True:
        response = requests.get(url, headers=headers)

        if response.json()["status"] == "FINISHED":
            nluResult = response.json()["result"]
            break
        elif response.json()["status"] == "ERROR":
            exit()

        time.sleep(1)

    queryUrl: str = ""
    data: dict = {}
    metadata: dict = {}
    
    # We could detect multiple interactions/queries in a single message, here we're just going to assume there is only one.
    interaction = nluResult["interactions"][0]
    ressource = interaction["parameters"]["Ressource"]["values"][0]
    queryUrl = f'{"/".join(ressource["parents"])}/{ressource["value"]}'  # Using the hierarchy in the Ressource archetype, we can directly grab the url from the configuration

    metadata: dict = json.loads(
        interaction["parameters"]["Ressource"]["values"][0]["metadata"]
    )  # We added some metadata in our configuration to display in slack using emojis

    for parameter in interaction["parameters"]["Parameters"]["values"]:
        if parameter["parents"] is None:  # All values detected in the "Parameters" archetype should have a parent (otherwise we don't know to which filter the value should be applied)
            continue

        filterValue: dict = parameter["references"]["parameter"][0]  # This is the value for the filter (IE: the status detected)

        if parameter["parents"][0] == "custom_field"  # Custom fields have one more level of imbrication
            queryParameter = f'{parameter["parents"][0]}[{filterValue["parents"][0]}][{parameter["value"]}]'
            if queryParameter not in data:
                data[queryParameter] = []

            data[queryParameter].append(filterValue["value"])
            continue

        if parameter["parents"][0] == "created_at":
            # We can't query this on the incident.io API, so we'll have to handle it after the query
            queryParameter = f"{parameter['parents'][0]}[{parameter['value']}]"
            if queryParameter not in data:
                data[queryParameter] = []

            # We're using an experimental feature with dates called "PostProcessing"
            # It allow us to define in archetype values such as : "last month|date:today().add_month(-1).set_day(1)"
            # And the AI will then execute the custom functions to returns an object containing, the day, month and year matching "last month".
            if parameter["value"] == "date_range":
                afterPostProcessedDate = parameter["references"]["after"][0][
                    "postProcessing"
                ]
                beforePostProcessedDate = parameter["references"]["before"][0][
                    "postProcessing"
                ]

                data[
                    queryParameter
                ] = f"{afterPostProcessedDate['year']}-{afterPostProcessedDate['month']}-{afterPostProcessedDate['day']}~{beforePostProcessedDate['year']}-{beforePostProcessedDate['month']}-{beforePostProcessedDate['day']}"
                continue

            if parameter["value"] == "date_range_relative":
                postProcessedDates = parameter["references"]["range"][0][
                    "postProcessing"
                ]

                queryParameter = f"{parameter['parents'][0]}[date_range]"
                data[
                    queryParameter
                ] = f"{postProcessedDates['left_year']}-{postProcessedDates['left_month']}-{postProcessedDates['left_day']}~{postProcessedDates['right_year']}-{postProcessedDates['right_month']}-{postProcessedDates['right_day']}"
                continue

            postProcessedDate: dict = filterValue["postProcessing"]
            data[
                queryParameter
            ] = f"{postProcessedDate['year']}-{postProcessedDate['month']}-{postProcessedDate['day']}"
            continue

        # The rest of the filters can all be handled by the same bit of code.
        queryParameter = f"{parameter['parents'][0]}[{parameter['value']}]"
        if queryParameter not in data:
            data[queryParameter] = []

        data[queryParameter].append(filterValue["value"])

    incidentKey: str = os.environ.get("INCIDENT_API_KEY", "")
    res: Response = requests.get(
        queryUrl, headers={"Authorization": f"Bearer {incidentKey}"}, params=data
    )
    incidentResponse: dict = res.json()

    incidents: list[dict] = []
    for incident in incidentResponse["incidents"]:
        createdAt = datetime.strptime(incident["created_at"].split("T")[0], "%Y-%m-%d")
        if "created_at[lte]" in data:
            cutoffDate = datetime.strptime(data["created_at[lte]"], "%Y-%m-%d")
            if createdAt.date() > cutoffDate.date():
                continue

        if "created_at[gte]" in data:
            cutoffDate = datetime.strptime(data["created_at[gte]"], "%Y-%m-%d")
            if createdAt.date() < cutoffDate.date():
                continue

        if "created_at[date_range]" in data:
            firstCutoffDate = datetime.strptime(
                data["created_at[date_range]"].split("~")[0], "%Y-%m-%d"
            )
            secondCutoffDate = datetime.strptime(
                data["created_at[date_range]"].split("~")[1], "%Y-%m-%d"
            )
            if (
                createdAt.date() < firstCutoffDate.date()
                or createdAt.date() > secondCutoffDate.date()
            ):
                continue

        incidents.append(incident)

    blocks: list[dict] = slack_message(incidents, queryUrl, data, metadata)

    app.client.chat_postMessage(
        text="Incident list",
        channel=body["event"]["channel"],
        blocks=blocks,
        thread_ts=body["event"]["thread_ts"]
        if "thread_ts" in body["event"]
        else body["event"]["ts"],
    )


def slack_message(incidents: list[dict], url: str, data: dict, metadata: dict) -> list[dict]:
    blocks: list[dict] = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{len(incidents)} incidents matched :",
            },
        },
        {"type": "divider"},
    ]

    for incident in incidents:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{incident['name']} - {metadata[incident['severity']['name']]} {incident['severity']['name']} - {metadata[incident['incident_status']['name']]} {incident['incident_status']['name']}",
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": ":arrow_right:"},
                    "value": "AAAA",
                    "url": incident["permalink"],
                    "action_id": "button-action",
                },
            }
        )
    blocks.append(
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "Powered by Golem.ai"},
                {
                    "type": "image",
                    "image_url": "https://cdn.golem.ai/images/stonesButPng.png",
                    "alt_text": "golem.ai",
                },
            ],
        }
    )
    return blocks

import requests
from requests import Response
import os

incidentKey: str = os.environ.get("INCIDENT_API_KEY", "")
response: Response = requests.get(
    "https://api.incident.io/v1/severities",
    headers={"Authorization": f"Bearer {incidentKey}"},
)

data: dict = response.json()
custom_fields = data["custom_fields"]

archetype: str = ""
for field in custom_fields["custom_fields"]:
    archetype += field["id"] + "\n"
    for value in field["options"]:
        archetype += f"->{value['id']};{value['value']}\n"
    archetype += "\n"

print(archetype)


response: Response = requests.get(
    "https://api.incident.io/v1/severities",
    headers={"Authorization": f"Bearer {incidentKey}"},
)
data: dict = response.json()
severities = data["severities"]

archetype = "#ID_ON\n\n"
for field in severities:
    archetype += f"->{field['id']};{field['name']}\n"

print(archetype)

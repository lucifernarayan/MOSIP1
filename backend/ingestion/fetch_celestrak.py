import requests
import json
import os

url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=json"

headers = {
    "User-Agent": "MOSIP/1.0"
}

response = requests.get(url, headers=headers)

print("Status:", response.status_code)

if response.status_code == 200:

    data = response.json()

    os.makedirs("data/raw", exist_ok=True)

    with open(
        "data/raw/celestrak_active.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(data, f)

    print("Saved:", len(data), "satellites")

else:

    print(response.text[:500])
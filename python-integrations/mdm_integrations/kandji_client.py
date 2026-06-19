import sys
import json
import os
import time
import requests
from requests.adapters import HTTPAdapter

KANDJI_SUBDOMAIN = os.environ["KANDJI_SUBDOMAIN"]
KANDJI_API_TOKEN = os.environ["KANDJI_API_TOKEN"]
KANDJI_API_URL = f"https://{KANDJI_SUBDOMAIN}.api.kandji.io/api"
HEADERS = {
    "Authorization": f"Bearer {KANDJI_API_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json;charset=utf-8",
    "Cache-Control": "no-cache",
}


def http_errors(resp, resp_code, err_msg):
    if resp_code == requests.codes["bad_request"]:
        print(f"\n\t{err_msg}")
        print(f"\tResponse msg: {resp.text}\n")
    elif resp_code == requests.codes["unauthorized"]:
        print("Make sure that you have the required permissions to access this data.")
        sys.exit(f"\t{err_msg}")
    elif resp_code == requests.codes["forbidden"]:
        print("The API key may be invalid or missing.")
        sys.exit(f"\t{err_msg}")
    elif resp_code == requests.codes["not_found"]:
        print("\nWe cannot find the one that you are looking for...")
        print("Move along...")
        print(f"\tError: {err_msg}")
        print(f"\tResponse msg: {resp}")
    elif resp_code == requests.codes["too_many_requests"]:
        print("You have reached the rate limit ...")
        print("Try again later ...")
        sys.exit(f"\t{err_msg}")
    elif resp_code == requests.codes["internal_server_error"]:
        print("The service is having a problem...")
        sys.exit(err_msg)
    elif resp_code == requests.codes["service_unavailable"]:
        print("Unable to reach the service. Try again later...")
    else:
        print("Something really bad must have happened...")
        print(err_msg)
        sys.exit()


def kandji_api(method, endpoint, params=None, payload=None):
    attom_adapter = HTTPAdapter(max_retries=3)
    session = requests.Session()
    session.mount(KANDJI_API_URL, attom_adapter)

    try:
        response = session.request(
            method,
            KANDJI_API_URL + endpoint,
            data=payload,
            headers=HEADERS,
            params=params,
            timeout=30,
        )

        if response:
            try:
                data = response.json()
            except Exception:
                data = response.text

        response.raise_for_status()

    except requests.exceptions.RequestException as err:
        http_errors(resp=response, resp_code=response.status_code, err_msg=err)
        data = {"error": f"{response.status_code}", "api resp": f"{err}"}

    return data


def get_devices(params=None):
    count = 0
    limit = 300
    offset = 0
    data = []

    while True:
        params.update({"limit": f"{limit}", "offset": f"{offset}"})
        response = kandji_api(method="GET", endpoint="/v1/prism/device_information", params=params)

        if isinstance(response, list):
            count += len(response)
            offset += limit
            if len(response) == 0:
                break

            for record in response:
                data.append(record)
        else:
            print("Error in API response:")
            print(response)
            break

    if len(data) < 1:
        print("No devices found...\n")
        sys.exit()

    return data


def fetch_kandji_data():
    params_dict = {}
    device_information = get_devices(params=params_dict)
    return device_information


def main():
    while True:
        data = fetch_kandji_data()
        print(json.dumps(data, indent=4))
        time.sleep(60)


if __name__ == "__main__":
    main()

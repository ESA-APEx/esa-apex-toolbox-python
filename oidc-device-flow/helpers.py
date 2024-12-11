import time
import webbrowser

import requests


def get_discovery_document(url):
    response = requests.get(url)
    return response.json()


def request_device_code(discovery_doc, client_credentials):
    data = {}
    data.update(client_credentials)
    data.update({"scope": "offline_access"})
    response = requests.post(discovery_doc["device_authorization_endpoint"], data=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to obtain device code. Status code: {response.status_code}")
        print(f"Response content: {response.content}")
        return None


def poll_for_access_token(discovery_doc, client_credentials, device_code, interval, timeout):
    payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "device_code": device_code,
        "client_id": client_credentials["client_id"],
    }
    start_time = time.time()
    print("\nWaiting for device to be authorized ...")
    while time.time() - start_time < timeout:
        response = requests.post(discovery_doc["token_endpoint"], data=payload)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            error = response.json().get("error", "")
            if error == "authorization_pending":
                print("Waiting for device to be authorized ...")
                time.sleep(interval)
            else:
                return None
        else:
            return None


def device_login(discovery_doc, client_credentials):
    device_code_response = request_device_code(discovery_doc, client_credentials)
    if device_code_response:
        verification_uri_complete = device_code_response.get("verification_uri_complete", None)
        webbrowser.open(verification_uri_complete)
        if verification_uri_complete:
            print(f"The following URL has been opened in your browser: {verification_uri_complete}")
        else:
            print("Something went wrong")

        interval = device_code_response["interval"]
        timeout = device_code_response["expires_in"]
        device_login = poll_for_access_token(
            discovery_doc,
            client_credentials,
            device_code_response["device_code"],
            interval,
            timeout,
        )
        if device_login:
            print("Device login successfull")
            return device_login
        else:
            print("Failed to obtain an device login")
            return None
    else:
        print("Failed to obtain device code")
        return None

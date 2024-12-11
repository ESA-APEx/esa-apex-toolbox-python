from helpers import device_login, get_discovery_document

discovery_doc = get_discovery_document("https://auth.apex.esa.int/realms/apex/.well-known/openid-configuration")

client_credentials = {"client_id": "project-a-catalogue-dev-browser"}

response = device_login(discovery_doc, client_credentials)

print("\n\nScopes: %s" % response["scope"])

print(
    "\naccess token ( Expires after %s seconds ):\n-------------------------------------------------------------------------------------------------------------------"
    % response["expires_in"]
)
print(response["access_token"])
print(
    "-------------------------------------------------------------------------------------------------------------------"
)

print(
    "\nRefresh token ( Expires after %s seconds ):\n-------------------------------------------------------------------------------------------------------------------"
    % response["refresh_expires_in"]
)
print(response["refresh_token"])
print(
    "-------------------------------------------------------------------------------------------------------------------\n"
)

import os
import json
import requests
from google.cloud import secretmanager


team_project = 'heda-prod-2664'

secrets = secretmanager.SecretManagerServiceClient()
secret = secrets.access_secret_version(name=f'projects/{team_project}/secrets/quarto/versions/latest')
env = json.loads(secret.payload.data.decode('UTF-8'))

# A list of file paths to be uploaded
files_to_upload = [
    "make_dashboard.html"
]

multipart_form_data = {}
for file_path in files_to_upload:
    file_name = os.path.basename(file_path)
    with open(file_path, 'rb') as file:
        # Read the file contents and store them in the dictionary
        file_contents = file.read()
        multipart_form_data[file_name] = (file_name, file_contents)

# Send the request with all files in the dictionary
response = requests.put(f"https://{env['ENV']}/quarto/update/{env['QUARTO_ID_heda']}",
                        headers={"Authorization": f"Bearer {env['TEAM_TOKEN_heda2']}"},
                        files=multipart_form_data)
response.raise_for_status()
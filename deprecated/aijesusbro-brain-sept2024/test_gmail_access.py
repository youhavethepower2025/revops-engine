
import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build

def main():
    creds = None
    token_file = '/Users/aijesusbro/AI Projects/token_2.json'
    client_secrets_file = '/Users/aijesusbro/AI Projects/credentials.json'

    if os.path.exists(token_file):
        creds = google.oauth2.credentials.Credentials.from_authorized_user_file(token_file, ['https://www.googleapis.com/auth/gmail.readonly'])

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, ['https://www.googleapis.com/auth/gmail.readonly'])
            creds = flow.run_local_server(port=0)
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    print('Labels for account 2:')
    if not labels:
        print('No labels found.')
    else:
        for label in labels:
            print(label['name'])

if __name__ == '__main__':
    main()

import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth import get_google_credentials

def get_drive_items(service, parent_id=None, drive_id=None):
    items = []
    page_token = None
    while True:
        try:
            # Construct the query to search within the shared drive if drive_id is provided
            query = "trashed = false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            if drive_id:
                 query += f" and '{drive_id}' in collections"

            response = service.files().list(
                q=query,
                spaces='drive',
                corpora='drive' if drive_id else 'user',
                driveId=drive_id if drive_id else None,
                includeItemsFromAllDrives=True if drive_id else None,
                supportsAllDrives=True if drive_id else None,
                fields='nextPageToken, files(id, name, mimeType)',
                pageToken=page_token
            ).execute()
            items.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        except HttpError as error:
            print(f'An error occurred: {error}')
            break
    return items

def build_drive_tree(credentials, drive_id):
    tree = {}
    try:
        drive_service = build('drive', 'v3', credentials=credentials)
        # Fetch the root folder ID of the shared drive
        root_folder = drive_service.files().list(
            q=f"mimeType='application/vnd.google-apps.folder' and name='{drive_service.drives().get(driveId=drive_id).execute()['name']}'",
            corpora='drive',
            driveId=drive_id,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields='files(id)'
        ).execute().get('files', [])

        if not root_folder:
             print(f'Could not find the root folder for shared drive ID {drive_id}.')
             return tree # Return empty tree if root not found
        
        root_folder_id = root_folder[0]['id']

        tree = _build_drive_tree_recursive(drive_service, parent_id=root_folder_id, drive_id=drive_id)

    except Exception as e:
        print(f"Error building Drive tree: {e}")
    return tree

def _build_drive_tree_recursive(service, parent_id=None, drive_id=None):
    tree = {}
    items = get_drive_items(service, parent_id, drive_id)
    for item in items:
        item_id = item['id']
        item_name = item['name']
        mime_type = item['mimeType']
        if mime_type == 'application/vnd.google-apps.folder':
            tree[item_id] = {'name': item_name, 'children': _build_drive_tree_recursive(service, item_id, drive_id)}
        else:
            tree[item_id] = {'name': item_name, 'is_file': True}
    return tree

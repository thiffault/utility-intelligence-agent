"""
NotebookLM Integration

Uploads intelligence reports to Google NotebookLM as sources.

SETUP REQUIRED:
1. Enable Google Drive API in Google Cloud Console
2. Create a service account and download credentials JSON
3. Set GOOGLE_SERVICE_ACCOUNT_JSON env var to the path of the credentials file
4. Set NOTEBOOKLM_DRIVE_FOLDER_ID env var to the target Google Drive folder ID
   (Reports uploaded here automatically appear as sources in a linked NotebookLM notebook)

HOW IT WORKS:
- Reports are uploaded to a designated Google Drive folder as .md files
- In NotebookLM, add that Drive folder as a source — new reports auto-sync

ALTERNATIVE (manual):
- Download any report from the output/ folder
- Upload directly to NotebookLM via the web UI
"""

import os
from pathlib import Path

_drive_available = False

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    _drive_available = True
except ImportError:
    pass


def upload_to_drive(filepath: str) -> str | None:
    """
    Upload a report file to Google Drive.

    Args:
        filepath: Local path to the report file.

    Returns:
        Google Drive file URL, or None if upload failed.
    """
    if not _drive_available:
        return None

    creds_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    folder_id = os.environ.get("NOTEBOOKLM_DRIVE_FOLDER_ID")

    if not creds_path or not folder_id:
        print("[NotebookLM] Google Drive not configured. Set GOOGLE_SERVICE_ACCOUNT_JSON and NOTEBOOKLM_DRIVE_FOLDER_ID.")
        return None

    try:
        credentials = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=["https://www.googleapis.com/auth/drive.file"]
        )
        service = build("drive", "v3", credentials=credentials)

        file_path = Path(filepath)
        file_metadata = {
            "name": file_path.name,
            "parents": [folder_id],
            "mimeType": "text/markdown"
        }
        media = MediaFileUpload(filepath, mimetype="text/markdown")

        uploaded = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink"
        ).execute()

        url = uploaded.get("webViewLink", "")
        print(f"[NotebookLM] Uploaded to Drive: {url}")
        return url

    except Exception as e:
        print(f"[NotebookLM] Upload failed: {e}")
        return None


def is_configured() -> bool:
    """Check if Google Drive integration is configured."""
    return (
        _drive_available
        and bool(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON"))
        and bool(os.environ.get("NOTEBOOKLM_DRIVE_FOLDER_ID"))
    )

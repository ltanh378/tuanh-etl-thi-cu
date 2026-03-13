import pandas as pd
import json, os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

# Auth Google Drive
credentials = service_account.Credentials.from_service_account_info(
    json.loads(os.getenv('SERVICE_JSON')), scopes=['https://www.googleapis.com/auth/drive']
)
service = build('drive', 'v3', credentials=credentials)

def download_raw_files(raw_folder_id):
    results = service.files().list(q=f"'{raw_folder_id}' in parents").execute()
    files = results.get('files', [])
    xlsx_files = [f for f in files if f['name'].endswith('.xlsx')]
    
    dfs = []
    for file in xlsx_files:
        request = service.files().get_media(fileId=file['id'])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        fh.seek(0)
        df = pd.read_excel(fh)
        dfs.append(df)
    
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

def clean_thi_cu_data(df):
    # Fix date column
    df['Ngày thi'] = pd.to_datetime(df['Ngày thi'], format='%Y-%m-%d')
    
    # Calculate pass rate
    df['Tỷ lệ Pass %'] = (df['Số lượt Pass thực tế'] / df['Số lượt thi thực tế'].replace(0, 1) * 100).round(2)
    
    # Clean text
    df['Tên đề'] = df['Tên đề'].str.strip()
    
    # Sort by date desc
    return df.sort_values('Ngày thi', ascending=False)

# MAIN ETL
df_raw = download_raw_files(os.getenv('RAW_FOLDER_ID'))
df_clean = clean_thi_cu_data(df_raw)

# Save CSV
df_clean.to_csv('final_thi_cu.csv', index=False, encoding='utf-8-sig')

# Upload to clean folder (OVERWRITE same filename)
file_metadata = {
    'name': 'final_thi_cu.csv',
    'parents': [os.getenv('CLEAN_FOLDER_ID')]
}
media = MediaFileUpload('final_thi_cu.csv', mimetype='text/csv')
service.files().create(body=file_metadata, media_body=media, fields='id').execute()

print(f"✅ ETL hoàn thành: {len(df_raw)} → {len(df_clean)} rows")

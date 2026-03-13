import pandas as pd
import json, os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from supabase import create_client, Client
import io

# Google Drive (download raw)
credentials = service_account.Credentials.from_service_account_info(
    json.loads(os.getenv('SERVICE_JSON')), 
    scopes=['https://www.googleapis.com/auth/drive']
)
drive_service = build('drive', 'v3', credentials=credentials)

# Supabase (upload clean)
supabase: Client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))

print("🚀 ETL Thi Cú → Supabase...")

# Download Excel → ETL
raw_folder_id = os.getenv('RAW_FOLDER_ID')
results = drive_service.files().list(q=f"'{raw_folder_id}' in parents").execute()
xlsx_files = [f for f in results.get('files', []) if f['name'].endswith('.xlsx')]

if not xlsx_files:
    print("⚠️ No new Excel files")
    exit(0)

dfs = []
for file in xlsx_files:
    request = drive_service.files().get_media(fileId=file['id'])
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    while not downloader.done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    df = pd.read_excel(fh)
    dfs.append(df)

# Clean data thi cu
df_clean = pd.concat(dfs, ignore_index=True)
df_clean['Ngày thi'] = pd.to_datetime(df_clean['Ngày thi'])
df_clean['Tỷ lệ Pass %'] = (df_clean['Số lượt Pass thực tế'] / df_clean['Số lượt thi thực tế'].replace(0, 1) * 100).round(2)
df_clean = df_clean.sort_values('Ngày thi', ascending=False)

print(f"✅ ETL: {len(df_clean)} rows clean")

# Upload Supabase Storage
with open('final_thi_cu.csv', 'w', encoding='utf-8-sig') as f:
    df_clean.to_csv(f, index=False)

with open('final_thi_cu.csv', 'rb') as f:
    supabase.storage.from_('powerbi-data').upload('final_thi_cu.csv', f)

print("🎉 UPLOAD SUPABASE THÀNH CÔNG!")
print("🔗 Power BI connect: postgresql://postgres:[PASS]@db.xyz.supabase.co:5432/postgres")

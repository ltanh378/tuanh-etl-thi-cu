import pandas as pd
import json, os, sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from supabase import create_client, Client
import io

print("🚀 ETL Thi Cú → Supabase FINAL...")

# Google Drive (download raw)
credentials = service_account.Credentials.from_service_account_info(
    json.loads(os.getenv('SERVICE_JSON')), 
    scopes=['https://www.googleapis.com/auth/drive']
)
drive_service = build('drive', 'v3', credentials=credentials)

# Supabase (upload clean)
supabase: Client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))

# Download Excel → ETL (giữ nguyên code cũ đã OK)
raw_folder_id = os.getenv('RAW_FOLDER_ID')
results = drive_service.files().list(q=f"'{raw_folder_id}' in parents").execute()
xlsx_files = [f for f in results.get('files', []) if f['name'].endswith('.xlsx')]

dfs = []
for file in xlsx_files:
    print(f"⏳ Đang đọc {file['name']}...")
    request = drive_service.files().get_media(fileId=file['id'])
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    fh.seek(0)
    df = pd.read_excel(fh)
    dfs.append(df)
    print(f"✅ {file['name']}: {len(df)} rows")

# Clean data
df_clean = pd.concat(dfs, ignore_index=True)
df_clean['Ngày thi'] = pd.to_datetime(df_clean['Ngày thi'])
df_clean['Tỷ lệ Pass %'] = (df_clean['Số lượt Pass thực tế'] / df_clean['Số lượt thi thực tế'].replace(0, 1) * 100).round(2)
df_clean = df_clean.sort_values('Ngày thi', ascending=False)

print(f"✅ ETL: {len(df_clean)} rows")

# 🔥 UPLOAD SUPABASE với upsert (overwrite)
df_clean.to_csv('final_thi_cu.csv', index=False, encoding='utf-8-sig')

with open('final_thi_cu.csv', 'rb') as f:
    response = supabase.storage.from_('powerbi-data').upload(
        'final_thi_cu.csv', 
        f, 
        options={"upsert": True}  # ← QUAN TRỌNG: Overwrite file cũ
    )

print("🎉 SUPABASE UPLOAD 100% THÀNH CÔNG!")
print(f"📊 Rows: {len(df_clean)}")
print(f"🔗 Power BI URL: https://{os.getenv('SUPABASE_URL').split('//')[1]}/storage/v1/object/public/powerbi-data/final_thi_cu.csv")

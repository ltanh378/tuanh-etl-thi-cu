import pandas as pd
import json, os, sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from supabase import create_client, Client
import io

print("🚀 ETL Thi Cú → Supabase 100%...")

# Google Drive auth (đã OK)
credentials = service_account.Credentials.from_service_account_info(
    json.loads(os.getenv('SERVICE_JSON')), 
    scopes=['https://www.googleapis.com/auth/drive']
)
drive_service = build('drive', 'v3', credentials=credentials)

# Supabase auth
supabase: Client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))

# Download + ETL (đã OK 222 rows)
raw_folder_id = os.getenv('RAW_FOLDER_ID')
results = drive_service.files().list(q=f"'{raw_folder_id}' in parents").execute()
xlsx_files = [f for f in results.get('files', []) if f['name'].endswith('.xlsx')]

dfs = []
for file in xlsx_files:
    print(f"⏳ {file['name']}...")
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

# Clean data thi cu
df_clean = pd.concat(dfs, ignore_index=True)
df_clean['Ngày thi'] = pd.to_datetime(df_clean['Ngày thi'])
df_clean['Tỷ lệ Pass %'] = (df_clean['Số lượt Pass thực tế'] / df_clean['Số lượt thi thực tế'].replace(0, 1) * 100).round(2)
df_clean['Tình trạng'] = df_clean['Số lượt thi thực tế'].apply(lambda x: 'Chưa thi' if x == 0 else 'Đã thi')
df_clean = df_clean.sort_values('Ngày thi', ascending=False)

print(f"✅ ETL: {len(df_clean)} rows")

# 🔥 SUPABASE UPLOAD - SYNTAX OFFICIAL DOCS
df_clean.to_csv('final_thi_cu.csv', index=False, encoding='utf-8-sig')

with open('final_thi_cu.csv', 'rb') as f:
    supabase.storage.from_('powerbi-data').upload(
        path='final_thi_cu.csv',
        file=f,
        file_options={
            "content-type": "text/csv; charset=utf-8",
            "cache-control": "3600",
            "upsert": True
        }
    )

print("🎉 SUPABASE UPLOAD ✅")
print(f"📊 {len(df_clean)} rows")
print(f"🔗 Power BI: https://{os.getenv('SUPABASE_URL').split('//')[1]}/storage/v1/object/public/powerbi-data/final_thi_cu.csv")

import pandas as pd
import json, os, sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from supabase import create_client, Client
import io

print("🚀 ETL Thi Cú → Supabase...")

# Google Drive auth (download raw Excel)
credentials = service_account.Credentials.from_service_account_info(
    json.loads(os.getenv('SERVICE_JSON')), 
    scopes=['https://www.googleapis.com/auth/drive']
)
drive_service = build('drive', 'v3', credentials=credentials)

# Supabase auth (upload clean CSV)
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

# Download Excel files
raw_folder_id = os.getenv('RAW_FOLDER_ID')
results = drive_service.files().list(q=f"'{raw_folder_id}' in parents").execute()
xlsx_files = [f for f in results.get('files', []) if f['name'].endswith('.xlsx')]

print(f"📥 Tìm thấy {len(xlsx_files)} file Excel")

if not xlsx_files:
    print("⚠️ Không có file mới → Skip")
    sys.exit(0)

dfs = []
for file in xlsx_files:
    print(f"⏳ Đang đọc {file['name']}...")
    request = drive_service.files().get_media(fileId=file['id'])
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:  # ← FIX: dùng done thay vì downloader.done
        status, done = downloader.next_chunk()
    fh.seek(0)
    df = pd.read_excel(fh)
    dfs.append(df)
    print(f"✅ {file['name']}: {len(df)} rows")

# 🔥 ETL Logic thi cú
df_clean = pd.concat(dfs, ignore_index=True)
df_clean['Ngày thi'] = pd.to_datetime(df_clean['Ngày thi'])
df_clean['Tỷ lệ Pass %'] = (df_clean['Số lượt Pass thực tế'] / df_clean['Số lượt thi thực tế'].replace(0, 1) * 100).round(2)
df_clean['Tình trạng'] = df_clean['Số lượt thi thực tế'].apply(lambda x: 'Chưa thi' if x == 0 else 'Đã thi')
df_clean = df_clean.sort_values('Ngày thi', ascending=False)

print(f"✅ ETL hoàn thành: {len(df_clean)} rows")

# 💾 Save CSV
df_clean.to_csv('final_thi_cu.csv', index=False, encoding='utf-8-sig')

# 📤 Upload Supabase Storage
with open('final_thi_cu.csv', 'rb') as f:
    supabase.storage.from_('powerbi-data').upload('final_thi_cu.csv', f)

print("🎉 UPLOAD SUPABASE THÀNH CÔNG!")
print("🔗 Power BI URL: https://[YOUR_SUPABASE].supabase.co/storage/v1/object/public/powerbi-data/final_thi_cu.csv")

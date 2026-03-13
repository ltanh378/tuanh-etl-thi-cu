import pandas as pd
import json, os, sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

print("🚀 Bắt đầu ETL Thi Cú FINAL...")

try:
    # Auth Google Drive
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(os.getenv('SERVICE_JSON')), 
        scopes=['https://www.googleapis.com/auth/drive']
    )
    service = build('drive', 'v3', credentials=credentials)
    print("✅ Google Drive auth OK")
    
    # Download raw files
    raw_folder_id = os.getenv('RAW_FOLDER_ID')
    results = service.files().list(q=f"'{raw_folder_id}' in parents and trashed=false").execute()
    files = results.get('files', [])
    xlsx_files = [f for f in files if f['name'].endswith('.xlsx')]
    
    print(f"📥 Tìm thấy {len(xlsx_files)} file Excel")
    
    if not xlsx_files:
        print("⚠️ Không có file mới → Skip ETL")
        sys.exit(0)
    
    dfs = []
    for file in xlsx_files:
        print(f"⏳ Đang đọc {file['name']}...")
        request = service.files().get_media(fileId=file['id'])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        df = pd.read_excel(fh)
        dfs.append(df)
        print(f"✅ {file['name']}: {len(df)} rows")
    
    # 🔥 ETL Logic cho data thi cú
    df_raw = pd.concat(dfs, ignore_index=True)
    df_raw['Ngày thi'] = pd.to_datetime(df_raw['Ngày thi'])
    df_raw['Tỷ lệ Pass %'] = (df_raw['Số lượt Pass thực tế'] / df_raw['Số lượt thi thực tế'].replace(0, 1) * 100).round(2)
    df_raw['Tình trạng'] = df_raw['Số lượt thi thực tế'].apply(lambda x: 'Chưa thi' if x == 0 else 'Đã thi')
    df_clean = df_raw.sort_values('Ngày thi', ascending=False)
    
    # 💾 Save FINAL CSV (KHÔNG UPLOAD - Power BI đọc trực tiếp)
    df_clean.to_csv('final_thi_cu.csv', index=False, encoding='utf-8-sig')
    print(f"💾 EXPORT HOÀN THÀNH: {len(df_clean)} rows")
    print("📊 CỘT MỚI: Ngày thi, Tỷ lệ Pass %, Tình trạng")
    print("🔗 DOWNLOAD FILE TẠI: ${{ github.workspace }}/final_thi_cu.csv")
    
    print("🎉 ETL 100% THÀNH CÔNG! Sẵn sàng Power BI!")
    
except Exception as e:
    print(f"❌ Lỗi: {str(e)}")
    sys.exit(1)

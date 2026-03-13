# 🚀 ETL TỰ ĐỘNG: Excel → Power BI Dashboard

> **Hệ thống ETL tự động hoàn chỉnh sử dụng GitHub Actions + Supabase Storage + Power BI**  
> 💰 Chi phí: **0đ** | ⏱️ Setup: **45 phút** | 🔄 Auto: **6 lần/ngày**

---

## 📋 MỤC LỤC

1. [Tổng quan](#-tổng-quan)
2. [Kiến trúc hệ thống](#-kiến-trúc-hệ-thống)
3. [Hướng dẫn Setup](#-hướng-dẫn-setup)
4. [Code hoàn chỉnh](#-code-hoàn-chỉnh)
5. [Kết nối Power BI](#-kết-nối-power-bi)
6. [Troubleshooting](#-troubleshooting)
7. [FAQ](#-faq)

---

## 🎯 TỔNG QUAN

### Vấn đề
- Team upload Excel thô vào Google Drive
- Cần dashboard Power BI cập nhật tự động
- Không có budget cho server/database

### Giải pháp
```
Excel thô → GitHub Actions ETL → Supabase CSV → Power BI Dashboard
(Google Drive)   (4h/lần tự động)   (Free 500MB)    (Auto refresh)
```

### Kết quả
- ✅ **0đ chi phí** (free tier đủ dùng)
- ✅ **Tự động 100%** (chỉ cần upload Excel)
- ✅ **Dashboard luôn mới** (refresh 8 lần/ngày)
- ✅ **Không cần server** (serverless architecture)

---

## 🏗️ KIẾN TRÚC HỆ THỐNG

```
┌──────────────────────────────────────────────────────────────┐
│                    GOOGLE DRIVE                              │
│  📁 ETL/raw_data/                                           │
│     ├── data_sample.xlsx (Team upload)                      │
│     ├── du_lieu_thang_03.xlsx                               │
│     └── ... (các file Excel khác)                           │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 │ ⏰ Trigger: Cron schedule (0 */4 * * *)
                 │           = 6 lần/ngày (0h,4h,8h,12h,16h,20h UTC)
                 ↓
┌──────────────────────────────────────────────────────────────┐
│              GITHUB ACTIONS (Ubuntu Runner)                  │
│  1️⃣ Download tất cả .xlsx từ Google Drive                     │
│  2️⃣ ETL với Pandas:                                           │
│     • Concat multiple files                                  │
│     • Clean data (datetime, tính toán)                       │
│     • Transform (222 rows → final_thi_cu.csv)                │
│  3️⃣ Upload CSV lên Supabase Storage                         │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 │ Upload via REST API
                 ↓
┌──────────────────────────────────────────────────────────────┐
│                  SUPABASE STORAGE                            │
│  🪣 Bucket: powerbi-data (Public)                           │
│     └── final_thi_cu.csv (Overwrite mỗi lần chạy)          │
│                                                              │
│  📡 Public URL (cố định):                                   │
│  https://[project].supabase.co/storage/v1/object/          │
│         public/powerbi-data/final_thi_cu.csv                │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 │ HTTP GET (Anonymous access)
                 ↓
┌──────────────────────────────────────────────────────────────┐
│                   POWER BI SERVICE                           │
│  📊 Dataset: Thi Cú Data (Web source)                       │
│  🔄 Scheduled Refresh: 8 lần/ngày                           │
│  📈 Dashboard: Live metrics                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## 🛠️ HƯỚNG DẪN SETUP

### ⏱️ Tổng thời gian: 45 phút

---

### **Bước 1: Google Drive Setup (5 phút)**

1. **Tạo cấu trúc thư mục**
   ```
   📁 ETL/
      └── 📁 raw_data/  ← Folder này chứa Excel files
   ```

2. **Lấy Folder ID**
   - Mở folder `raw_data` trong browser
   - Copy ID từ URL: `https://drive.google.com/drive/folders/[FOLDER_ID_27_KÝ_TỰ]`
   - Lưu lại: `RAW_FOLDER_ID = _______________`

3. **Upload file Excel mẫu**
   - Kéo thả file `.xlsx` vào folder `raw_data`
   - Đảm bảo có ít nhất 1 file để test

---

### **Bước 2: Google Service Account (10 phút)**

1. **Tạo Project**
   - Vào [Google Cloud Console](https://console.cloud.google.com)
   - Click **New Project** → Đặt tên: `etl-thi-cu`
   - Click **Create**

2. **Enable Google Drive API**
   - Sidebar → **APIs & Services** → **Library**
   - Search: `Google Drive API`
   - Click **Enable**

3. **Tạo Service Account**
   - Sidebar → **IAM & Admin** → **Service Accounts**
   - Click **Create Service Account**
   - Name: `etl-service`
   - Click **Create and Continue**
   - Role: chọn **Basic** → **Editor** (hoặc bỏ qua)
   - Click **Done**

4. **Download JSON Key**
   - Click vào service account vừa tạo
   - Tab **Keys** → **Add Key** → **Create new key**
   - Chọn **JSON** → Click **Create**
   - File `etl-thi-cu.json` sẽ tải về máy → **LƯU KỸ FILE NÀY**

5. **Share Google Drive Folder**
   - Mở file JSON, copy email `client_email`: `etl-service@etl-thi-cu.iam.gserviceaccount.com`
   - Quay lại Google Drive folder `raw_data`
   - Click **Share** → Paste email service account
   - Role: **Editor** → Click **Send**

---

### **Bước 3: Supabase Setup (10 phút)**

1. **Tạo Project**
   - Vào [supabase.com](https://supabase.com) → Sign in
   - Click **New Project**
   - Project name: `thi-cu-db`
   - Database password: tạo mật khẩu mạnh (lưu lại)
   - Region: **Southeast Asia (Singapore)** (gần VN nhất)
   - Pricing plan: **Free** (500MB storage)
   - Click **Create new project** → Đợi ~2 phút

2. **Tạo Storage Bucket**
   - Sidebar → **Storage**
   - Click **New bucket**
   - Name: `powerbi-data`
   - ✅ **Public bucket** = **ON** (QUAN TRỌNG!)
   - Click **Create bucket**

3. **Thiết lập Policies (Bảo mật)**
   - Sidebar → **SQL Editor**
   - Click **New query**
   - Paste code sau:

   ```sql
   -- Policy 1: Cho phép public đọc files
   CREATE POLICY "Public read access"
   ON storage.objects FOR SELECT
   TO public
   USING (bucket_id = 'powerbi-data');

   -- Policy 2: Cho phép anon user upload (cho GitHub Actions)
   CREATE POLICY "Anon upload access"
   ON storage.objects FOR INSERT
   TO anon
   WITH CHECK (bucket_id = 'powerbi-data');

   -- Policy 3: Cho phép anon user xóa (cho upsert)
   CREATE POLICY "Anon delete access"
   ON storage.objects FOR DELETE
   TO anon
   USING (bucket_id = 'powerbi-data');
   ```

   - Click **Run** → Thấy "Success. No rows returned"

4. **Lấy API Credentials**
   - Sidebar → **Settings** → **API**
   - Copy 2 giá trị:
     ```
     Project URL: https://xxxxxxxx.supabase.co
     anon public key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
     ```
   - Lưu lại để dùng ở bước sau

---

### **Bước 4: GitHub Repository (5 phút)**

1. **Tạo Repository**
   - Vào [github.com](https://github.com) → **New repository**
   - Repository name: `tuanh-etl-thi-cu`
   - Public hoặc Private (tùy thích)
   - ✅ Add README
   - Click **Create repository**

2. **Clone về máy** (hoặc upload trực tiếp trên web)
   ```bash
   git clone https://github.com/[your-username]/tuanh-etl-thi-cu.git
   cd tuanh-etl-thi-cu
   ```

3. **Tạo cấu trúc file** (xem phần Code bên dưới)

---

### **Bước 5: GitHub Secrets (5 phút)**

1. **Vào Settings**
   - Repository → **Settings** → **Secrets and variables** → **Actions**

2. **Thêm 4 Secrets**
   
   Click **New repository secret** cho từng giá trị:

   | Name | Value | Nguồn |
   |------|-------|-------|
   | `RAW_FOLDER_ID` | `1AbC...XyZ` (27 ký tự) | Google Drive folder ID |
   | `SERVICE_JSON` | `{"type": "service_account"...}` | **TOÀN BỘ** nội dung file JSON |
   | `SUPABASE_URL` | `https://xxx.supabase.co` | Supabase Project URL |
   | `SUPABASE_ANON_KEY` | `eyJhbGci...` | Supabase anon public key |

   **⚠️ Lưu ý:**
   - `SERVICE_JSON`: Copy **TOÀN BỘ** nội dung file JSON (kể cả dấu `{}`)
   - Không có dấu cách thừa, không xuống dòng

3. **Verify**
   - Kiểm tra cả 4 secrets đều hiển thị trong list
   - Secrets sẽ bị ẩn (`***`), không xem được lại

---

### **Bước 6: Test Run (10 phút)**

1. **Push code lên GitHub** (xem phần Code)

2. **Chạy thử manual**
   - Repository → **Actions** tab
   - Click workflow **Thi Cú ETL → Supabase**
   - Click **Run workflow** → **Run workflow**
   - Đợi ~1-2 phút

3. **Kiểm tra logs**
   ```
   🚀 ETL Thi Cú → Supabase 100%...
   ⏳ data_sample.xlsx...
   ✅ data_sample.xlsx: 222 rows
   ✅ ETL: 222 rows
   🎉 SUPABASE UPLOAD ✅
   📊 222 rows
   🔗 Power BI: https://xxx.supabase.co/storage/v1/object/public/powerbi-data/final_thi_cu.csv
   ```

4. **Verify Supabase**
   - Supabase → **Storage** → `powerbi-data`
   - Thấy file `final_thi_cu.csv`
   - Click file → **Get URL** → Copy URL

5. **Test URL trong browser**
   - Paste URL vào browser
   - Phải tải được file CSV (không lỗi 403/404)
   - ✅ Setup thành công!

---

## 💾 CODE HOÀN CHỈNH

### **File 1: `.github/workflows/etl.yml`**

```yaml
name: Thi Cú ETL → Supabase

on:
  schedule:
    # Chạy 6 lần/ngày: 0h, 4h, 8h, 12h, 16h, 20h (UTC)
    - cron: '0 */4 * * *'
  
  # Cho phép chạy manual từ Actions tab
  workflow_dispatch:

jobs:
  etl:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Setup Python 3.11
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install pandas openpyxl google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib supabase
    
    - name: Run ETL Script
      env:
        RAW_FOLDER_ID: ${{ secrets.RAW_FOLDER_ID }}
        SERVICE_JSON: ${{ secrets.SERVICE_JSON }}
        SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
        SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_ANON_KEY }}
      run: python etl_supabase.py
```

---

### **File 2: `etl_supabase.py`**

```python
import pandas as pd
import json, os, sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from supabase import create_client, Client
import io

print("🚀 ETL Thi Cú → Supabase 100%...")

# ============================================================================
# 1. GOOGLE DRIVE AUTHENTICATION
# ============================================================================
credentials = service_account.Credentials.from_service_account_info(
    json.loads(os.getenv('SERVICE_JSON')), 
    scopes=['https://www.googleapis.com/auth/drive']
)
drive_service = build('drive', 'v3', credentials=credentials)

# ============================================================================
# 2. SUPABASE AUTHENTICATION
# ============================================================================
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'), 
    os.getenv('SUPABASE_ANON_KEY')
)

# ============================================================================
# 3. DOWNLOAD EXCEL FILES FROM GOOGLE DRIVE
# ============================================================================
raw_folder_id = os.getenv('RAW_FOLDER_ID')
results = drive_service.files().list(
    q=f"'{raw_folder_id}' in parents and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'"
).execute()
xlsx_files = results.get('files', [])

if not xlsx_files:
    print("❌ Không tìm thấy file .xlsx nào trong folder!")
    sys.exit(1)

dfs = []
for file in xlsx_files:
    print(f"⏳ {file['name']}...")
    
    # Download file
    request = drive_service.files().get_media(fileId=file['id'])
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    
    fh.seek(0)
    
    # Read Excel
    df = pd.read_excel(fh)
    dfs.append(df)
    print(f"✅ {file['name']}: {len(df)} rows")

# ============================================================================
# 4. ETL TRANSFORMATION
# ============================================================================
# Concat all Excel files
df_clean = pd.concat(dfs, ignore_index=True)

# Transform data (tùy chỉnh theo cấu trúc Excel của bạn)
df_clean['Ngày thi'] = pd.to_datetime(df_clean['Ngày thi'])
df_clean['Tỷ lệ Pass %'] = (
    df_clean['Số lượt Pass thực tế'] / 
    df_clean['Số lượt thi thực tế'].replace(0, 1) * 100
).round(2)
df_clean['Tình trạng'] = df_clean['Số lượt thi thực tế'].apply(
    lambda x: 'Chưa thi' if x == 0 else 'Đã thi'
)

# Sort by date
df_clean = df_clean.sort_values('Ngày thi', ascending=False)

print(f"✅ ETL: {len(df_clean)} rows")

# ============================================================================
# 5. UPLOAD TO SUPABASE STORAGE
# ============================================================================
# Save to CSV
csv_filename = 'final_thi_cu.csv'
df_clean.to_csv(csv_filename, index=False, encoding='utf-8-sig')

# Upload with upsert behavior
with open(csv_filename, 'rb') as f:
    # Remove old file (if exists)
    try:
        supabase.storage.from_('powerbi-data').remove([csv_filename])
    except:
        pass  # File doesn't exist yet
    
    # Upload new file
    supabase.storage.from_('powerbi-data').upload(
        path=csv_filename,
        file=f,
        file_options={
            "content-type": "text/csv; charset=utf-8",
            "cache-control": "3600"
        }
    )

# ============================================================================
# 6. OUTPUT RESULTS
# ============================================================================
print("🎉 SUPABASE UPLOAD ✅")
print(f"📊 {len(df_clean)} rows")
print(f"🔗 Power BI: https://{os.getenv('SUPABASE_URL').split('//')[1]}/storage/v1/object/public/powerbi-data/{csv_filename}")
```

---

### **File 3: `requirements.txt`**

```txt
pandas==2.2.0
openpyxl==3.1.2
google-api-python-client==2.116.0
google-auth==2.27.0
google-auth-httplib2==0.2.0
google-auth-oauthlib==1.2.0
supabase==2.3.4
```

---

### **File 4: `.gitignore`**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# Secrets
*.json
etl-*.json
.env

# Data files
*.csv
*.xlsx
*.xls

# IDE
.vscode/
.idea/
*.swp
*.swo
```

---

## 📊 KẾT NỐI POWER BI

### **Power BI Desktop**

1. **Get Data**
   - Mở Power BI Desktop
   - Click **Get Data** → **Web**
   - Paste URL (lấy từ logs GitHub Actions hoặc Supabase):
     ```
     https://[your-project].supabase.co/storage/v1/object/public/powerbi-data/final_thi_cu.csv
     ```
   - Click **OK**

2. **Authentication**
   - Chọn **Anonymous**
   - Click **Connect**

3. **Load Data**
   - Preview data hiển thị
   - Click **Load**
   - Tạo visualizations

4. **Publish lên Power BI Service**
   - File → **Publish** → **Publish to Power BI**
   - Chọn workspace
   - Click **Select**

---

### **Power BI Service (Auto Refresh)**

1. **Vào Workspace**
   - Truy cập [app.powerbi.com](https://app.powerbi.com)
   - Chọn workspace vừa publish

2. **Cấu hình Dataset**
   - Click vào **Dataset** (biểu tượng ⚡)
   - Chọn **Settings**

3. **Scheduled Refresh**
   - Expand **Scheduled refresh**
   - ✅ Enable: **ON**
   - Frequency: **Daily**
   - Time: Add 8 time slots:
     - 1:00 AM (sau GitHub Actions 0h UTC)
     - 5:00 AM (sau GitHub Actions 4h UTC)
     - 9:00 AM (sau GitHub Actions 8h UTC)
     - 1:00 PM (sau GitHub Actions 12h UTC)
     - 5:00 PM (sau GitHub Actions 16h UTC)
     - 9:00 PM (sau GitHub Actions 20h UTC)
     - ... (tùy chỉnh theo múi giờ VN = UTC+7)
   - Click **Apply**

4. **Test Refresh**
   - Click **Refresh now**
   - Kiểm tra **Refresh history**
   - ✅ Thành công!

---

## 🔧 TROUBLESHOOTING

### **1. GitHub Actions Fails: "FileNotFoundError"**

**Nguyên nhân:** Không tìm thấy file Excel trong Google Drive

**Fix:**
```bash
# Kiểm tra:
1. RAW_FOLDER_ID đúng không? (27 ký tự)
2. Service account đã được share folder với quyền Editor chưa?
3. Folder có file .xlsx nào không?
```

---

### **2. Supabase Upload Error: "Bucket not found"**

**Nguyên nhân:** Bucket `powerbi-data` chưa tạo hoặc chưa public

**Fix:**
```sql
-- Vào Supabase SQL Editor, chạy:
SELECT * FROM storage.buckets WHERE id = 'powerbi-data';

-- Nếu empty, tạo bucket:
INSERT INTO storage.buckets (id, name, public)
VALUES ('powerbi-data', 'powerbi-data', true);
```

---

### **3. Power BI: "Unable to connect"**

**Nguyên nhân:** URL sai hoặc bucket không public

**Fix:**
```bash
# 1. Test URL trong browser:
https://[project].supabase.co/storage/v1/object/public/powerbi-data/final_thi_cu.csv

# 2. Nếu lỗi 404:
- Vào Supabase Storage → powerbi-data
- Click file → Get URL → Copy đúng URL

# 3. Nếu lỗi 403:
- Storage → powerbi-data → Settings
- Public bucket = ON
```

---

### **4. Data không update trong Power BI**

**Nguyên nhân:** Scheduled refresh chưa chạy hoặc cache

**Fix:**
```bash
# 1. Kiểm tra Refresh History:
Power BI Service → Dataset → Settings → Refresh history

# 2. Force refresh:
Dataset → ... → Refresh now

# 3. Clear cache Power BI Desktop:
File → Options → Data Load → Clear cache
```

---

### **5. GitHub Actions Error: "TypeError: Header value must be str"**

**Nguyên nhân:** Đã fix ở code mới, nhưng nếu vẫn gặp

**Fix:**
```python
# Xóa dòng này trong file_options:
"upsert": True  # ❌ KHÔNG DÙNG

# Code mới đã xử lý bằng cách remove + upload
```

---

## ❓ FAQ

### **Q1: Chi phí thực tế là bao nhiêu?**

**A:** Hoàn toàn **0đ** nếu nằm trong limits:
- GitHub Actions: 2,000 phút/tháng (free plan)
  - Mỗi run ~2 phút → 6 runs/ngày × 30 = 360 phút/tháng ✅
- Supabase Free: 500MB storage + 50,000 requests/tháng
  - 1 file CSV ~50KB → dùng <1MB ✅
- Power BI: Free Desktop + Service (có phí nếu dùng Pro features)

---

### **Q2: Có thể chạy nhiều hơn 6 lần/ngày không?**

**A:** Có! Sửa cron trong `.github/workflows/etl.yml`:
```yaml
# Mỗi 2 giờ (12 lần/ngày):
- cron: '0 */2 * * *'

# Mỗi giờ (24 lần/ngày):
- cron: '0 * * * *'

# Cụ thể giờ (ví dụ: 8h, 12h, 17h):
- cron: '0 8,12,17 * * *'
```

**⚠️ Lưu ý:** Nhiều lần = tốn quota GitHub Actions nhanh hơn

---

### **Q3: Xử lý nhiều file CSV khác nhau?**

**A:** Sửa code để tạo nhiều files:
```python
# Thay vì 1 file:
datasets = {
    'thi_cu': df_thi_cu,
    'diem_thi': df_diem,
    'hoc_vien': df_hocvien
}

for name, df in datasets.items():
    csv_file = f'{name}.csv'
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    
    with open(csv_file, 'rb') as f:
        try:
            supabase.storage.from_('powerbi-data').remove([csv_file])
        except:
            pass
        supabase.storage.from_('powerbi-data').upload(
            path=csv_file, file=f,
            file_options={"content-type": "text/csv; charset=utf-8"}
        )
```

Trong Power BI: Add multiple Web sources cho mỗi file

---

### **Q4: Có thể dùng PostgreSQL Table thay vì CSV không?**

**A:** Có! Xem hướng dẫn riêng trong [ADVANCED.md](ADVANCED.md) (tạo file này nếu cần)

**Tóm tắt:**
- Tạo table trong Supabase
- Dùng `supabase.table('thi_cu').upsert(data).execute()`
- Power BI connect qua PostgreSQL connector

**Ưu:** Query SQL phức tạp, relationships
**Nhược:** Setup phức tạp hơn, cần tạo schema

---

### **Q5: Bảo mật dữ liệu như thế nào?**

**A:** Hiện tại public bucket (để Power BI đọc dễ). Nâng cao:

1. **Private bucket + Signed URLs:**
   ```python
   # Tạo URL tạm thời (1 giờ):
   url = supabase.storage.from_('powerbi-data').create_signed_url(
       'final_thi_cu.csv', 3600
   )
   ```
   **Nhược:** Power BI phải update URL mỗi giờ

2. **Row Level Security (nếu dùng PostgreSQL table)**

3. **API Gateway với authentication**

---

### **Q6: Logs GitHub Actions ở đâu?**

**A:**
```bash
Repository → Actions tab → Click run → Expand "Run ETL Script"
```

Logs hiển thị:
- Download files từ Drive
- Transform steps
- Upload Supabase
- **Public URL** (copy dùng cho Power BI)

---

### **Q7: Làm sao biết cron chạy thành công?**

**A:**
1. **Email notification** (GitHub Settings → Notifications)
2. **Actions tab:** Xem history chạy
3. **Supabase Storage:** Check timestamp file CSV
4. **Power BI:** Data mới xuất hiện

---

### **Q8: Có thể chạy ngay lập tức thay vì đợi cron?**

**A:** Có 2 cách:
1. **Manual trigger:**
   - Actions tab → Workflow → **Run workflow**
   
2. **Push code:**
   - Thêm `push:` trong workflow:
     ```yaml
     on:
       push:
         branches: [main]
       schedule:
         - cron: '0 */4 * * *'
     ```

---

## 📈 MONITORING & METRICS

### **Theo dõi hiệu năng**

Thêm vào cuối `etl_supabase.py`:

```python
import datetime

print("\n📊 METRICS:")
print(f"⏰ Timestamp: {datetime.datetime.now().isoformat()}")
print(f"📁 Files processed: {len(xlsx_files)}")
print(f"📊 Total rows: {len(df_clean)}")
print(f"💾 CSV size: {os.path.getsize(csv_filename) / 1024:.2f} KB")
```

Logs sẽ hiển thị trong GitHub Actions.

---

## 🚀 NEXT STEPS

1. **✅ Setup xong?** Test manual run
2. **✅ Power BI connected?** Publish lên Service
3. **✅ Auto refresh working?** Monitor 1 tuần

**Nâng cao:**
- [ ] Add email notifications (AWS SES/SendGrid)
- [ ] Error handling & retry logic
- [ ] Data validation before upload
- [ ] Versioning (lưu historical data)
- [ ] Multiple environments (dev/prod)

---

## 📞 SUPPORT

**Issues:** [GitHub Issues](https://github.com/[username]/tuanh-etl-thi-cu/issues)

**Docs:**
- [GitHub Actions](https://docs.github.com/actions)
- [Supabase Storage](https://supabase.com/docs/guides/storage)
- [Power BI Web Connector](https://learn.microsoft.com/power-bi/connect-data/desktop-connect-to-web)

---

## 📝 CHANGELOG

### v1.0.0 (2026-03-13)
- ✅ Initial setup
- ✅ Google Drive integration
- ✅ Supabase CSV upload
- ✅ Power BI Web connector
- ✅ GitHub Actions automation

---

## 📄 LICENSE

MIT License - Free to use

---

**Made with ❤️ for automated ETL workflows**

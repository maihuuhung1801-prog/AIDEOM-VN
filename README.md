<<<<<<< HEAD
# 🇻🇳 AIDEOM-VN — AI-driven Economic Optimization Model for Vietnam

> **Đồ án môn học Bài 12** — Hệ thống tối ưu hoá phát triển kinh tế số Việt Nam 2026–2030  
> Tích hợp 6 module: Dự báo · Sẵn sàng số · Phân bổ ngân sách · Lao động · Rủi ro · Dashboard

---

## 📁 Cấu trúc dự án

```
AIDEOM_VN/
├── data/
│   ├── vietnam_macro_2020_2025.csv       # GDP, TFP, lao động lịch sử
│   ├── vietnam_regions_2024.csv          # Chỉ số 6 vùng kinh tế
│   └── vietnam_sectors_2024.csv          # Chỉ số 10 ngành kinh tế
├── modules/
│   ├── m1_forecast.py      # M1: Dự báo GDP 2026–2030 (Cobb-Douglas)
│   ├── m2_readiness.py     # M2: Đánh giá sẵn sàng số (TOPSIS + Entropy)
│   ├── m3_allocation.py    # M3: Tối ưu phân bổ ngân sách (SLSQP)
│   ├── m4_labor.py         # M4: Mô phỏng lao động (Markov Chain)
│   └── m5_risk.py          # M5: Đánh giá rủi ro + Monte Carlo
├── dashboard/
│   └── m6_dashboard.py     # M6: Streamlit Dashboard (4 tab)
├── tests/
│   └── test_modules.py     # Unit tests (pytest) — 25+ test cases
├── requirements.txt
└── README.md
```

---

## ⚡ Cài đặt & Chạy nhanh

### 1. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 2. Chạy unit tests
```bash
cd AIDEOM_VN
pytest tests/test_modules.py -v
```

### 3. Chạy Dashboard Streamlit
```bash
streamlit run dashboard/m6_dashboard.py
```

> Dashboard tự động tải dữ liệu và hiển thị 4 tab phân tích.

---

## 🗺️ 5 Kịch bản chính sách

| ID | Tên | Đặc điểm | K / D / AI / H |
|----|-----|-----------|----------------|
| **S1** | Truyền thống | Vốn vật chất & FDI | 70 / 10 / 10 / 10 % |
| **S2** | Số hóa nhanh | Hạ tầng số & thanh toán | 25 / 45 / 15 / 15 % |
| **S3** | AI dẫn dắt | AI, bán dẫn, dữ liệu lớn | 20 / 20 / 45 / 15 % |
| **S4** | Bao trùm số | Vùng yếu, SME, nông nghiệp | 30 / 20 / 10 / 40 % |
| **S5** | Tối ưu cân bằng | Kết quả mô hình AIDEOM-VN | 28 / 25 / 22 / 25 % |

---

## 🔬 Mô hình toán học

### Hàm sản xuất Cobb-Douglas mở rộng
$$Y_t = A_t \cdot K_t^{0.33} \cdot L_t^{0.42} \cdot D_t^{0.10} \cdot AI_t^{0.08} \cdot H_t^{0.07}$$

### TOPSIS (M2)
Đánh giá sẵn sàng số với trọng số Entropy, 6 tiêu chí vùng / 5 tiêu chí ngành.

### Tối ưu ngân sách (M3)
`scipy.optimize.minimize (SLSQP)` — 24 biến, 14 ràng buộc ngân sách và cơ cấu.

### Markov Chain lao động (M4)
Ma trận chuyển trạng thái $N_{10 \times 10}$ — thay thế AI + tạo việc làm số.

### Rủi ro đa chiều (M5)
Composite Risk = 0.45 × Cyber + 0.35 × Môi trường + 0.20 × Phụ thuộc  
Monte Carlo 5,000 mô phỏng → VaR₉₅, CVaR₉₅.

---

## 📊 Kết quả tổng hợp 2030 (ước tính)

| Kịch bản | GDP 2030 | NetJob ròng | Rủi ro tổng hợp |
|----------|----------|-------------|-----------------|
| S1 Truyền thống | ~17,500 tỷ | +250,000 | Thấp (0.18) |
| S2 Số hóa nhanh | ~20,200 tỷ | +680,000 | TB (0.32) |
| S3 AI dẫn dắt   | ~21,800 tỷ | -120,000 | Cao (0.58) |
| S4 Bao trùm số  | ~18,500 tỷ | +920,000 | Thấp (0.22) |
| **S5 Cân bằng** | **~20,800 tỷ** | **+540,000** | **TB (0.30)** |

---

## 🏗️ Kiến trúc hệ thống

```
M1 Forecast ──┐
M2 Readiness ─┤
M3 Allocation ┼──► M6 Dashboard (Streamlit)
M4 Labor ─────┤     ├── Tab 1: Tổng quan
M5 Risk ──────┘     ├── Tab 2: Phân bổ ngân sách
                     ├── Tab 3: So sánh kịch bản
                     └── Tab 4: Cảnh báo rủi ro
```

---

## 📚 Nguồn dữ liệu

- **GSO Vietnam** — GDP, dân số, lao động 2020–2025
- **Bộ TT&TT** — Chỉ số chuyển đổi số DTI 2024
- **World Bank / ADB** — TFP, FDI, năng suất lao động
- **MOLISA** — Cơ cấu lao động theo ngành 2024

---

## 👥 Nhóm thực hiện
*[Điền tên thành viên nhóm tại đây]*

---
*AIDEOM-VN © 2025 — Đồ án môn Kinh tế số & AI*
=======
# AIDEOM-VN
>>>>>>> d310e83136cb24e0a5ae33de0c994e88a56034b0

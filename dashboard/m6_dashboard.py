"""
Module M6 — Dashboard ra quyết định (Streamlit)
================================================
Tích hợp outputs của M1–M5 thành giao diện trực quan 4 tab:
  Tab 1: Tổng quan — GDP dự báo, bản đồ sẵn sàng số
  Tab 2: Phân bổ ngân sách — ma trận vùng × hạng mục
  Tab 3: So sánh kịch bản — 5 kịch bản × 4 chỉ tiêu
  Tab 4: Cảnh báo rủi ro — cyber, môi trường, phụ thuộc

Chạy: streamlit run m6_dashboard.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

from modules.m1_forecast import forecast_all_scenarios, SCENARIO_PARAMS, load_macro
from modules.m2_readiness import assess_regions, assess_sectors, get_digital_gap_index
from modules.m3_allocation import optimize_static, compare_scenarios_static
from modules.m4_labor import compare_scenarios_labor, simulate_labor
from modules.m5_risk import compute_risk_scores, risk_radar_data, monte_carlo_risk

# ── Cấu hình trang ──────────────────────────────────────────────
st.set_page_config(
    page_title="AIDEOM-VN Dashboard",
    page_icon="🇻🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

SCENARIO_COLORS = {
    "S1": "#607D8B", "S2": "#1976D2", "S3": "#E53935",
    "S4": "#43A047", "S5": "#7B1FA2"
}
SCENARIO_LABELS = {
    "S1": "S1 · Truyền thống", "S2": "S2 · Số hóa nhanh",
    "S3": "S3 · AI dẫn dắt",  "S4": "S4 · Bao trùm số",
    "S5": "S5 · Tối ưu cân bằng"
}

# ── Sidebar ──────────────────────────────────────────────────────
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Flag_of_Vietnam.svg/200px-Flag_of_Vietnam.svg.png", width=80)
st.sidebar.title("AIDEOM-VN")
st.sidebar.caption("AI-driven Economic Optimization Model for Vietnam")
st.sidebar.divider()

selected_scenario = st.sidebar.selectbox(
    "Chọn kịch bản phân tích:",
    options=list(SCENARIO_LABELS.keys()),
    format_func=lambda x: SCENARIO_LABELS[x],
    index=4
)
horizon = st.sidebar.slider("Tầm nhìn dự báo (năm):", 3, 10, 5)
budget  = st.sidebar.number_input("Ngân sách (tỷ VND):", 60_000, 300_000, 120_000, 10_000)

st.sidebar.divider()
st.sidebar.info("📚 Dữ liệu: Vietnam GSO, MOLISA, MIC 2020–2025")
st.sidebar.info("⚙️ Model: Cobb-Douglas + NSGA-II + TOPSIS + Markov Chain")

# ── Tiêu đề chính ───────────────────────────────────────────────
st.title("🇻🇳 AIDEOM-VN — Hệ thống Tối ưu hoá Phát triển Kinh tế Số Việt Nam")
st.caption(f"Kịch bản đang xem: **{SCENARIO_LABELS[selected_scenario]}** · Ngân sách: **{budget:,} tỷ VND** · Tầm nhìn: **2026–{2025+horizon}**")
st.divider()

# ════════════════════════════════════════════════════════════════
# TAB LAYOUT
# ════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Tổng quan", "💰 Phân bổ ngân sách",
    "🔄 So sánh kịch bản", "⚠️ Cảnh báo rủi ro"
])

# ────────────────────────────────────────────────────────────────
# TAB 1: TỔNG QUAN
# ────────────────────────────────────────────────────────────────
with tab1:
    st.header("📊 Tổng quan kinh tế & Sẵn sàng số")

    with st.spinner("Đang tính toán..."):
        df_all  = forecast_all_scenarios(horizon)
        df_scen = df_all[df_all["scenario"] == selected_scenario]
        df_macro = load_macro()


    col1, col2, col3, col4 = st.columns(4)
    gdp_2030 = df_scen[df_scen["year"] == 2025 + horizon]["Y"].values[0] if not df_scen.empty else 0
    gdp_2025 = float(df_macro[df_macro["year"] == 2025]["GDP_trillion_VND"].iloc[0])
    growth_total = (gdp_2030 / gdp_2025 - 1) * 100
    cagr = ((gdp_2030 / gdp_2025) ** (1/horizon) - 1) * 100
    tfp_2030 = df_scen["A"].values[-1] if not df_scen.empty else 0

    col1.metric("GDP 2025 (thực)", f"{gdp_2025:,.0f} tỷ VND", "Năm gốc")
    col2.metric(f"GDP {2025+horizon} (dự báo)", f"{gdp_2030:,.0f} tỷ VND",
                f"+{growth_total:.1f}% so với 2025")
    col3.metric("CAGR dự báo", f"{cagr:.2f}%/năm",
                "Tốt" if cagr > 7 else "Trung bình")
    col4.metric("TFP cuối kỳ (A)", f"{tfp_2030:.4f}",
                f"{'Tăng' if tfp_2030 > df_scen['A'].values[0] else 'Giảm'}")

    st.divider()

    # Biểu đồ GDP dự báo tất cả kịch bản
    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.subheader("Dự báo GDP 2026–2030 theo kịch bản")
        fig_gdp = go.Figure()
        # Lịch sử
        fig_gdp.add_trace(go.Scatter(
            x=df_macro["year"], y=df_macro["GDP_trillion_VND"],
            name="Lịch sử 2020–2025", line=dict(color="#263238", width=3, dash="solid"),
            mode="lines+markers"
        ))
        # Dự báo theo kịch bản
        for s in ["S1","S2","S3","S4","S5"]:
            df_s = df_all[df_all["scenario"] == s]
            fig_gdp.add_trace(go.Scatter(
                x=df_s["year"], y=df_s["Y"],
                name=SCENARIO_LABELS[s],
                line=dict(color=SCENARIO_COLORS[s], width=2,
                          dash="solid" if s == selected_scenario else "dot"),
                mode="lines+markers",
                opacity=1.0 if s == selected_scenario else 0.45
            ))
        fig_gdp.add_vline(x=2025.5, line_dash="dash", line_color="gray",
                          annotation_text="Bắt đầu dự báo")
        fig_gdp.update_layout(
            xaxis_title="Năm", yaxis_title="Nghìn tỷ VND",
            legend=dict(orientation="h", y=-0.2), height=380,
            hovermode="x unified"
        )
        st.plotly_chart(fig_gdp, use_container_width=True)

    with col_r:
        st.subheader("Tăng trưởng TFP theo kịch bản")
        fig_tfp = px.bar(
            df_all.groupby("scenario").last().reset_index(),
            x="scenario", y="A",
            color="scenario",
            color_discrete_map=SCENARIO_COLORS,
            labels={"A": "TFP cuối kỳ", "scenario": "Kịch bản"},
            text_auto=".4f"
        )
        fig_tfp.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig_tfp, use_container_width=True)

    st.divider()

    # Digital Readiness Map
    st.subheader("Bản đồ Sẵn sàng Số — 6 Vùng kinh tế")
    with st.spinner("Tính TOPSIS..."):
        df_regions, w_dict = assess_regions()
        df_gap = get_digital_gap_index()

    col_m, col_s = st.columns([2, 1])
    with col_m:
        fig_reg = px.bar(
            df_regions.sort_values("rank"),
            x="topsis_score", y="region_name_en",
            orientation="h",
            color="topsis_score",
            color_continuous_scale="RdYlGn",
            labels={"topsis_score": "Điểm TOPSIS", "region_name_en": "Vùng"},
            text_auto=".3f"
        )
        fig_reg.update_layout(height=320, coloraxis_showscale=False)
        st.plotly_chart(fig_reg, use_container_width=True)

    with col_s:
        st.markdown("**Phân loại mức sẵn sàng số:**")
        for _, row in df_regions.sort_values("rank").iterrows():
            cat = str(row["digital_readiness_category"])
            icon = {"Rất cao":"🟢","Cao":"🟡","Trung bình":"🟠","Thấp":"🔴"}.get(cat, "⚪")
            st.write(f"{icon} **{row['region_name_en']}** — {cat} ({row['topsis_score']:.3f})")

# ────────────────────────────────────────────────────────────────
# TAB 2: PHÂN BỔ NGÂN SÁCH
# ────────────────────────────────────────────────────────────────
with tab2:
    st.header("💰 Tối ưu phân bổ ngân sách")

    with st.spinner(f"Đang tối ưu hóa {selected_scenario}..."):
        X_opt, gdp_val, info = optimize_static(selected_scenario, budget)

    st.success(f"✅ Tối ưu hóa {'' if info['converged'] else 'chưa '}hội tụ · GDP contribution: **{gdp_val:,.1f} tỷ VND**")

    INVEST_TYPES = ["Hạ tầng (I)", "Dữ liệu (D)", "AI", "Nhân lực (H)"]
    REGIONS_VN   = ["Trung du MN phía Bắc","Đồng bằng sông Hồng","BTB + DH Trung Bộ",
                    "Tây Nguyên","Đông Nam Bộ","ĐB sông Cửu Long"]

    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.subheader("Ma trận phân bổ (tỷ VND)")
        df_alloc = pd.DataFrame(X_opt, index=REGIONS_VN, columns=INVEST_TYPES)
        fig_heat = px.imshow(
            df_alloc,
            color_continuous_scale="Blues",
            labels=dict(color="Tỷ VND"),
            aspect="auto", text_auto=".0f"
        )
        fig_heat.update_layout(height=340)
        st.plotly_chart(fig_heat, use_container_width=True)

    with col_r:
        st.subheader("Cơ cấu đầu tư theo hạng mục")
        totals = X_opt.sum(axis=0)
        fig_pie = px.pie(
            values=totals, names=INVEST_TYPES,
            color_discrete_sequence=["#1565C0","#43A047","#E53935","#7B1FA2"],
            hole=0.45
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(height=340, showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Stacked bar vùng
    st.subheader("Phân bổ ngân sách theo vùng (stacked)")
    df_long = pd.DataFrame(X_opt, index=REGIONS_VN, columns=INVEST_TYPES)
    df_long = df_long.reset_index().melt(id_vars="index", var_name="Hạng mục", value_name="Ngân sách")
    df_long.columns = ["Vùng", "Hạng mục", "Ngân sách (tỷ VND)"]
    fig_stack = px.bar(
        df_long, x="Vùng", y="Ngân sách (tỷ VND)", color="Hạng mục",
        color_discrete_sequence=["#1565C0","#43A047","#E53935","#7B1FA2"],
        barmode="stack"
    )
    fig_stack.update_layout(height=360, xaxis_tickangle=-20)
    st.plotly_chart(fig_stack, use_container_width=True)

    with st.expander("📋 Xem bảng chi tiết"):
        st.dataframe(info["alloc_table"].style.format("{:.1f}").background_gradient("Blues"), use_container_width=True)

# ────────────────────────────────────────────────────────────────
# TAB 3: SO SÁNH KỊCH BẢN
# ────────────────────────────────────────────────────────────────
with tab3:
    st.header("🔄 So sánh 5 kịch bản chính sách")

    with st.spinner("Đang so sánh các kịch bản..."):
        df_gdp_comp   = compare_scenarios_static(budget)
        df_labor_comp = compare_scenarios_labor()
        df_risk_comp  = risk_radar_data()
        df_macro_comp = forecast_all_scenarios(horizon)

    labels = {"S1":"Truyền thống","S2":"Số hóa nhanh","S3":"AI dẫn dắt",
              "S4":"Bao trùm số","S5":"Tối ưu cân bằng"}

    # Bảng tổng hợp 2030
    gdp_2030_all = df_macro_comp[df_macro_comp["year"] == 2025+horizon].set_index("scenario")["Y"]
    summary_df = pd.DataFrame({
        "Kịch bản": [labels[s] for s in ["S1","S2","S3","S4","S5"]],
        "GDP 2030 (nghìn tỷ)": [f"{gdp_2030_all.get(s, 0):,.0f}" for s in ["S1","S2","S3","S4","S5"]],
        "GDP Contribution": [f"{df_gdp_comp[df_gdp_comp['scenario']==s]['gdp_contribution'].values[0]:,.0f}" for s in ["S1","S2","S3","S4","S5"]],
        "NetJob 2030 (nghìn)": [f"{df_labor_comp[df_labor_comp['scenario']==s]['net_balance_2030'].values[0]/1000:+,.0f}" for s in ["S1","S2","S3","S4","S5"]],
        "Rủi ro tổng hợp": [f"{df_risk_comp[df_risk_comp['scenario']==s]['composite'].values[0]:.3f}" for s in ["S1","S2","S3","S4","S5"]],
    })
    st.subheader("Bảng tổng hợp kết quả 2030")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("GDP dự báo theo kịch bản")
        fig_comp = px.line(
            df_macro_comp, x="year", y="Y", color="scenario",
            color_discrete_map=SCENARIO_COLORS,
            labels={"Y":"GDP (nghìn tỷ VND)","year":"Năm","scenario":"Kịch bản"},
            line_dash="scenario"
        )
        fig_comp.update_layout(height=360, hovermode="x unified")
        st.plotly_chart(fig_comp, use_container_width=True)

    with col_r:
        st.subheader("Việc làm ròng 2030 (nghìn người)")
        df_labor_bar = df_labor_comp.copy()
        df_labor_bar["net_k"] = df_labor_bar["net_balance_2030"] / 1000
        df_labor_bar["color"] = df_labor_bar["net_k"].apply(lambda x: "#43A047" if x > 0 else "#E53935")
        fig_job = go.Figure(go.Bar(
            x=df_labor_bar["label"],
            y=df_labor_bar["net_k"],
            marker_color=df_labor_bar["color"],
            text=df_labor_bar["net_k"].round(0),
            textposition="outside"
        ))
        fig_job.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_job.update_layout(height=360, yaxis_title="NetJob (nghìn người)")
        st.plotly_chart(fig_job, use_container_width=True)

    # Radar chart so sánh kịch bản
    st.subheader("Biểu đồ Radar — Đánh giá đa chiều 5 kịch bản")
    categories = ["GDP Growth", "Digital Equity", "AI Adoption", "Human Capital", "Risk Control"]

    fig_radar = go.Figure()
    radar_values = {
        "S1": [0.45, 0.30, 0.20, 0.25, 0.80],
        "S2": [0.70, 0.60, 0.55, 0.50, 0.55],
        "S3": [0.80, 0.45, 0.90, 0.45, 0.30],
        "S4": [0.55, 0.90, 0.35, 0.85, 0.70],
        "S5": [0.75, 0.72, 0.70, 0.72, 0.65],
    }
    for s, vals in radar_values.items():
        fig_radar.add_trace(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=categories + [categories[0]],
            name=SCENARIO_LABELS[s],
            line_color=SCENARIO_COLORS[s],
            fill="toself" if s == selected_scenario else "none",
            opacity=1.0 if s == selected_scenario else 0.55,
            line_width=3 if s == selected_scenario else 1.5
        ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True, height=420
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# ────────────────────────────────────────────────────────────────
# TAB 4: CẢNH BÁO RỦI RO
# ────────────────────────────────────────────────────────────────
with tab4:
    st.header("⚠️ Đánh giá & Cảnh báo rủi ro")

    with st.spinner("Đang phân tích rủi ro..."):
        df_risk = compute_risk_scores(selected_scenario, budget)
        df_risk_all = risk_radar_data()

    # Cảnh báo nổi bật
    high_risk = df_risk[df_risk["composite_risk"] > 0.5]
    if not high_risk.empty:
        for _, row in high_risk.iterrows():
            st.warning(f"**{row['alert_level']} {row['region']}**: rủi ro tổng hợp = {row['composite_risk']:.3f}")
    else:
        st.success("✅ Không có vùng nào vượt ngưỡng rủi ro cao trong kịch bản này.")

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader(f"Rủi ro theo vùng — {SCENARIO_LABELS[selected_scenario]}")
        fig_risk = px.bar(
            df_risk, x="region", y=["cyber_risk","env_risk","depend_risk"],
            barmode="group",
            color_discrete_sequence=["#E53935","#FF9800","#1565C0"],
            labels={"value":"Điểm rủi ro","variable":"Loại rủi ro"},
        )
        fig_risk.update_layout(height=360, xaxis_tickangle=-25, legend_title="Loại rủi ro")
        st.plotly_chart(fig_risk, use_container_width=True)

    with col_r:
        st.subheader("Rủi ro tổng hợp — So sánh kịch bản")
        fig_risk_comp = px.bar(
            df_risk_all, x="label", y="composite",
            color="scenario", color_discrete_map=SCENARIO_COLORS,
            text_auto=".3f",
            labels={"composite":"Rủi ro tổng hợp","label":"Kịch bản"}
        )
        fig_risk_comp.add_hline(y=0.5, line_dash="dash", line_color="red",
                                 annotation_text="Ngưỡng cảnh báo")
        fig_risk_comp.update_layout(height=360, showlegend=False)
        st.plotly_chart(fig_risk_comp, use_container_width=True)

    # Monte Carlo
    st.subheader("🎲 Phân tích Monte Carlo — Phân phối rủi ro (5,000 mô phỏng)")
    with st.spinner("Chạy Monte Carlo..."):
        mc_result = monte_carlo_risk(selected_scenario, n_sim=5000, budget=budget)

    mc_df = pd.DataFrame(mc_result).T
    mc_df.index.name = "Vùng"
    mc_df = mc_df.reset_index()

    fig_mc = px.bar(
        mc_df, x="Vùng", y=["mean","VaR_95","CVaR_95"],
        barmode="group",
        color_discrete_sequence=["#1976D2","#FF9800","#E53935"],
        labels={"value":"Điểm rủi ro","variable":"Chỉ số"}
    )
    fig_mc.update_layout(height=360, xaxis_tickangle=-20)
    st.plotly_chart(fig_mc, use_container_width=True)

    with st.expander("📋 Chi tiết Monte Carlo"):
        st.dataframe(mc_df.set_index("Vùng").style.format("{:.4f}").background_gradient("Reds"),
                     use_container_width=True)

    # Khuyến nghị chính sách
    st.divider()
    st.subheader("💡 Khuyến nghị chính sách tự động")
    risk_level = df_risk["composite_risk"].mean()
    if risk_level < 0.3:
        st.success("🟢 **Mức rủi ro thấp**: Có thể đẩy nhanh tốc độ số hóa và tăng đầu tư AI. Ưu tiên mở rộng quy mô.")
    elif risk_level < 0.5:
        st.info("🟡 **Mức rủi ro trung bình**: Cân nhắc tăng đầu tư nhân lực số song song với AI để giảm thiểu rủi ro an ninh dữ liệu.")
    elif risk_level < 0.65:
        st.warning("🟠 **Mức rủi ro cao**: Nên ưu tiên đào tạo nhân lực bảo mật và ban hành khung pháp lý AI trước khi mở rộng đầu tư.")
    else:
        st.error("🔴 **Mức rủi ro nguy hiểm**: Cần kiểm soát phụ thuộc công nghệ nước ngoài và tăng cường đầu tư an ninh mạng ngay lập tức.")

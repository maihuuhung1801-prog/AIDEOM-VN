"""
Unit Tests — AIDEOM-VN (pytest)
================================
Chạy: pytest tests/test_modules.py -v
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))

import pytest
import numpy as np
import pandas as pd


# ══════════════════════════════════════════════════════════════════
# M1 — FORECAST TESTS
# ══════════════════════════════════════════════════════════════════
class TestM1Forecast:
    def setup_method(self):
        from m1_forecast import forecast, forecast_all_scenarios, calibrate_tfp, load_macro
        self.forecast = forecast
        self.forecast_all = forecast_all_scenarios
        self.calibrate_tfp = calibrate_tfp
        self.load_macro = load_macro

    def test_load_macro_shape(self):
        df = self.load_macro()
        assert len(df) == 6, "Phải có 6 năm dữ liệu (2020-2025)"
        assert "GDP_trillion_VND" in df.columns

    def test_calibrate_tfp_positive(self):
        df = self.load_macro()
        A0 = self.calibrate_tfp(df)
        assert A0 > 0, "TFP A0 phải dương"
        assert A0 < 100, "TFP A0 không nên quá lớn"

    def test_forecast_returns_correct_years(self):
        df = self.forecast("S5", horizon=5)
        assert list(df["year"]) == list(range(2026, 2031))

    def test_forecast_gdp_positive_growth(self):
        df = self.forecast("S5", horizon=5)
        assert (df["Y"] > 0).all(), "GDP phải dương"
        assert df["growth_pct"].mean() > 0, "Tăng trưởng trung bình phải dương"

    def test_all_scenarios_forecast(self):
        df = self.forecast_all(horizon=5)
        assert df["scenario"].nunique() == 5, "Phải có đủ 5 kịch bản"

    @pytest.mark.parametrize("scenario", ["S1","S2","S3","S4","S5"])
    def test_each_scenario_valid(self, scenario):
        df = self.forecast(scenario, horizon=5)
        assert len(df) == 5
        assert (df["Y"] > 0).all()


# ══════════════════════════════════════════════════════════════════
# M2 — READINESS TESTS
# ══════════════════════════════════════════════════════════════════
class TestM2Readiness:
    def setup_method(self):
        from m2_readiness import assess_regions, assess_sectors, entropy_weights, topsis, get_digital_gap_index
        self.assess_regions = assess_regions
        self.assess_sectors = assess_sectors
        self.entropy_weights = entropy_weights
        self.topsis = topsis
        self.get_gap = get_digital_gap_index

    def test_entropy_weights_sum_to_one(self):
        matrix = np.random.rand(6, 5)
        w = self.entropy_weights(matrix)
        assert abs(w.sum() - 1.0) < 1e-6, "Trọng số entropy phải tổng = 1"

    def test_topsis_scores_in_01(self):
        matrix = np.random.rand(6, 4) * 100
        weights = np.array([0.25, 0.25, 0.25, 0.25])
        benefit = np.array([True, True, False, True])
        scores = self.topsis(matrix, weights, benefit)
        assert (scores >= 0).all() and (scores <= 1).all(), "Điểm TOPSIS phải trong [0,1]"

    def test_assess_regions_has_6_rows(self):
        df, _ = self.assess_regions()
        assert len(df) == 6

    def test_assess_regions_rank_unique(self):
        df, _ = self.assess_regions()
        assert df["rank"].nunique() == 6, "Xếp hạng phải duy nhất"

    def test_assess_sectors_has_10_rows(self):
        df = self.assess_sectors()
        assert len(df) == 10

    def test_digital_gap_nonneg(self):
        df = self.get_gap()
        assert (df["digital_gap"] >= 0).all()


# ══════════════════════════════════════════════════════════════════
# M3 — ALLOCATION TESTS
# ══════════════════════════════════════════════════════════════════
class TestM3Allocation:
    def setup_method(self):
        from m3_allocation import optimize_static, compare_scenarios_static
        self.optimize = optimize_static
        self.compare  = compare_scenarios_static

    def test_optimize_returns_correct_shape(self):
        X, gdp, info = self.optimize("S5", budget=120_000)
        assert X.shape == (6, 4), "Ma trận phân bổ phải là 6×4"

    def test_optimize_budget_not_exceeded(self):
        budget = 120_000
        X, _, _ = self.optimize("S5", budget=budget)
        assert X.sum() <= budget * 1.01, "Tổng đầu tư không được vượt ngân sách (+1% dung sai)"

    def test_optimize_all_nonneg(self):
        X, _, _ = self.optimize("S5")
        assert (X >= -1e-6).all(), "Tất cả giá trị phân bổ phải không âm"

    def test_gdp_contribution_positive(self):
        _, gdp, _ = self.optimize("S5")
        assert gdp > 0, "GDP contribution phải dương"

    @pytest.mark.parametrize("scenario", ["S1", "S3", "S5"])
    def test_scenarios_s1_s3_s5(self, scenario):
        X, gdp, info = self.optimize(scenario, budget=120_000)
        assert X.shape == (6, 4)
        assert gdp > 0
        assert "alloc_table" in info


# ══════════════════════════════════════════════════════════════════
# M4 — LABOR TESTS
# ══════════════════════════════════════════════════════════════════
class TestM4Labor:
    def setup_method(self):
        from m4_labor import simulate_labor, national_netjob_summary, compare_scenarios_labor
        self.simulate = simulate_labor
        self.summary  = national_netjob_summary
        self.compare  = compare_scenarios_labor

    def test_simulate_returns_50_rows(self):
        df = self.simulate("S5", T=5)
        assert len(df) == 50, "10 ngành × 5 năm = 50 rows"

    def test_labor_nonneg(self):
        df = self.simulate("S5")
        assert (df["labor_million"] >= 0).all()

    def test_summary_has_5_years(self):
        df = self.summary("S5")
        assert len(df) == 5

    def test_compare_has_5_scenarios(self):
        df = self.compare()
        assert len(df) == 5

    def test_ai_scenario_has_more_job_loss(self):
        """S3 (AI dẫn dắt) phải có job loss nhiều hơn S4 (Bao trùm)."""
        df = self.compare()
        lost_s3 = df[df["scenario"]=="S3"]["net_lost_2030"].values[0]
        lost_s4 = df[df["scenario"]=="S4"]["net_lost_2030"].values[0]
        assert lost_s3 > lost_s4, "S3 AI scenario phải mất việc nhiều hơn S4"


# ══════════════════════════════════════════════════════════════════
# M5 — RISK TESTS
# ══════════════════════════════════════════════════════════════════
class TestM5Risk:
    def setup_method(self):
        from m5_risk import compute_risk_scores, risk_radar_data, monte_carlo_risk
        self.compute  = compute_risk_scores
        self.radar    = risk_radar_data
        self.mc       = monte_carlo_risk

    def test_compute_returns_6_rows(self):
        df = self.compute("S5")
        assert len(df) == 6

    def test_risk_scores_in_01(self):
        df = self.compute("S5")
        for col in ["cyber_risk","env_risk","depend_risk","composite_risk"]:
            assert (df[col] >= 0).all() and (df[col] <= 1).all(), f"{col} phải trong [0,1]"

    def test_radar_has_5_scenarios(self):
        df = self.radar()
        assert len(df) == 5

    def test_s3_higher_risk_than_s4(self):
        """S3 (AI dẫn dắt) phải có cyber_risk > S4 (Bao trùm số)."""
        df = self.radar()
        r_s3 = df[df["scenario"]=="S3"]["cyber_risk"].values[0]
        r_s4 = df[df["scenario"]=="S4"]["cyber_risk"].values[0]
        assert r_s3 > r_s4

    def test_monte_carlo_returns_all_regions(self):
        mc = self.mc("S5", n_sim=100)
        assert len(mc) == 6

    def test_monte_carlo_var_geq_mean(self):
        """VaR_95 phải ≥ mean."""
        mc = self.mc("S5", n_sim=200)
        for region, stats in mc.items():
            assert stats["VaR_95"] >= stats["mean"], f"{region}: VaR95 < mean"


# ══════════════════════════════════════════════════════════════════
# INTEGRATION TEST
# ══════════════════════════════════════════════════════════════════
class TestIntegration:
    """Kiểm tra pipeline M1→M5 cho 3 kịch bản S1, S3, S5."""

    @pytest.mark.parametrize("scenario", ["S1", "S3", "S5"])
    def test_full_pipeline(self, scenario):
        from m1_forecast  import forecast
        from m2_readiness import assess_regions
        from m3_allocation import optimize_static
        from m4_labor     import national_netjob_summary
        from m5_risk      import compute_risk_scores

        df_gdp  = forecast(scenario, horizon=5)
        df_r, _ = assess_regions()
        X, gdp, info = optimize_static(scenario, budget=120_000)
        df_lbr  = national_netjob_summary(scenario)
        df_risk = compute_risk_scores(scenario)

        assert not df_gdp.empty
        assert not df_r.empty
        assert gdp > 0
        assert not df_lbr.empty
        assert not df_risk.empty


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

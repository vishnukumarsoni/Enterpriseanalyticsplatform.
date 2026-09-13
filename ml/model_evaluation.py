"""
Model Evaluation Summary
=========================
Reads the artifacts produced by churn_model.py and forecasting.py and prints/
saves a consolidated model performance report.
"""
import os
import pandas as pd

REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "reports")


def main():
    print("=" * 60)
    print("CHURN MODEL COMPARISON")
    print("=" * 60)
    churn_cmp = pd.read_csv(os.path.join(REPORT_DIR, "churn_model_comparison.csv"))
    print(churn_cmp.to_string(index=False))

    print("\n" + "=" * 60)
    print("FORECAST BACKTEST METRICS (30-day holdout)")
    print("=" * 60)
    fc_metrics = pd.read_csv(os.path.join(REPORT_DIR, "forecast_backtest_metrics.csv"))
    print(fc_metrics.to_string(index=False))

    summary_path = os.path.join(REPORT_DIR, "model_evaluation_summary.txt")
    with open(summary_path, "w") as f:
        f.write("CHURN MODEL COMPARISON\n")
        f.write(churn_cmp.to_string(index=False))
        f.write("\n\nFORECAST BACKTEST METRICS (30-day holdout)\n")
        f.write(fc_metrics.to_string(index=False))
    print(f"\nSummary written to {summary_path}")


if __name__ == "__main__":
    main()

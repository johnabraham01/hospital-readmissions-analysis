"""
Hospital Readmissions Analysis
Loads the CSV into an in-memory SQLite database, runs every query in
sql/analysis_queries.sql, prints the results, and saves charts to images/.

Run:  python analysis.py
Needs: pandas, matplotlib
"""
import re
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# 1. Load and clean ------------------------------------------------------
df = pd.read_csv("data/hospital_readmissions_data.csv", na_values=["Not Available"])
df = df.rename(columns={
    "Facility Name": "facility_name",
    "Facility ID": "facility_id",
    "State": "state",
    "Measure Name": "measure_name",
    "Number of Discharges": "discharges",
    "Excess Readmission Ratio": "excess_ratio",
    "Predicted Readmission Rate": "predicted_rate",
    "Expected Readmission Rate": "expected_rate",
    "Number of Readmissions": "readmissions",
})
# "READM-30-HIP-KNEE-HRRP" -> "HIP-KNEE"
df["condition"] = df["measure_name"].str.replace("READM-30-", "").str.replace("-HRRP", "")

conn = sqlite3.connect(":memory:")
df.to_sql("readmissions", conn, index=False)

# 2. Run the SQL file ----------------------------------------------------
sql_text = open("sql/analysis_queries.sql").read()
blocks = re.split(r"\n(?=-- Q\d+\.)", sql_text)
results = {}
for block in blocks:
    title = re.search(r"-- (Q\d+\..*)", block)
    if not title:
        continue
    query = "\n".join(l for l in block.splitlines() if not l.strip().startswith("--"))
    result = pd.read_sql_query(query, conn)
    results[title.group(1)[:2].strip(".")] = result
    print(f"\n=== {title.group(1)} ===")
    print(result.to_string(index=False))

# 3. Charts --------------------------------------------------------------
plt.rcParams.update({"figure.dpi": 120, "axes.spines.top": False, "axes.spines.right": False})

# Chart 1: average excess ratio by condition
q2 = results["Q2"]
fig, ax = plt.subplots(figsize=(7, 4))
colors = ["#c0392b" if v > 1 else "#2e86c1" for v in q2.avg_excess_ratio]
ax.bar(q2.condition, q2.avg_excess_ratio, color=colors)
ax.axhline(1.0, color="black", linestyle="--", linewidth=1, label="Benchmark (1.0)")
ax.set_ylim(0.9, 1.1)
ax.set_title("Average Excess Readmission Ratio by Condition")
ax.set_ylabel("Excess readmission ratio")
for i, v in enumerate(q2.avg_excess_ratio):
    ax.text(i, v + 0.004, f"{v:.3f}", ha="center")
ax.legend()
plt.tight_layout(); plt.savefig("images/ratio_by_condition.png"); plt.close()

# Chart 2: ratio vs volume (priority matrix)
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.scatter(q2.total_discharges, q2.avg_excess_ratio, s=200, color="#2e86c1")
for _, r in q2.iterrows():
    ax.annotate(r.condition, (r.total_discharges, r.avg_excess_ratio),
                xytext=(8, 6), textcoords="offset points")
ax.axhline(1.0, color="grey", linestyle="--", linewidth=1)
ax.margins(x=0.12, y=0.15)
ax.set_title("Priority Matrix: Performance vs Volume")
ax.set_xlabel("Total discharges"); ax.set_ylabel("Average excess ratio")
plt.tight_layout(); plt.savefig("images/priority_matrix.png"); plt.close()

# Chart 3: worst 10 hospitals
q4 = results["Q4"].sort_values("avg_excess_ratio")
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.barh(q4.facility_name, q4.avg_excess_ratio, color="#c0392b")
ax.axvline(1.0, color="black", linestyle="--", linewidth=1)
ax.set_xlim(0.95, 1.15)
ax.set_title("10 Worst-Performing Hospitals (avg excess ratio)")
plt.tight_layout(); plt.savefig("images/worst_hospitals.png"); plt.close()

print("\nCharts saved to images/")

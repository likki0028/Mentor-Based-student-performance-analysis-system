import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import joblib

# ==============================
# 1. LOAD EXTERNAL DATASET
# ==============================

df = pd.read_csv("H:\mini project\mentor_student_system\external_dataset\student+performance (1)\student\student-mat.csv", sep=";")

# ==============================
# 2. SELECT ACADEMIC FEATURES
# ==============================

df = df[["absences", "G1", "G2", "G3", "failures"]]

# ==============================
# 3. FEATURE ENGINEERING
# ==============================

# Attendance (%)
df["attendance"] = 100 - (df["absences"] / df["absences"].max()) * 100

# Internal marks (out of 40)
df["internal_marks"] = ((df["G1"] + df["G2"]) / 2) * 2

# Previous CGPA (0–10)
df["previous_cgpa"] = (df["G3"] / 20) * 10

# Backlogs
df["backlogs"] = df["failures"]

# ==============================
# 4. FINAL FEATURE SET
# ==============================

X = df[["attendance", "internal_marks", "previous_cgpa", "backlogs"]]

# ==============================
# 5. SCALE FEATURES
# ==============================

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ==============================
# 6. K-MEANS (k = 2)
# ==============================

kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
clusters = kmeans.fit_predict(X_scaled)

df["cluster"] = clusters

# ==============================
# 7. SILHOUETTE SCORE
# ==============================

sil_score = silhouette_score(X_scaled, clusters)
print("Silhouette Score (k=2):", round(sil_score, 3))

# ==============================
# 8. CLUSTER SUMMARY
# ==============================

cluster_summary = df.groupby("cluster")[[
    "attendance",
    "internal_marks",
    "previous_cgpa",
    "backlogs"
]].mean()

# Risk score to decide which cluster is At-Risk
cluster_summary["risk_score"] = (
    cluster_summary["attendance"]
    + cluster_summary["internal_marks"]
    + cluster_summary["previous_cgpa"]
    - cluster_summary["backlogs"] * 10
)

ordered_clusters = cluster_summary["risk_score"].sort_values().index.tolist()

risk_mapping = {
    ordered_clusters[0]: "At-Risk",
    ordered_clusters[1]: "Safe",
}

df["risk_category"] = df["cluster"].map(risk_mapping)

print("\nCluster Summary:")
print(cluster_summary)

# ==============================
# 9. PCA FOR 2D VISUALIZATION
# ==============================

pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

df["PC1"] = X_pca[:, 0]
df["PC2"] = X_pca[:, 1]

# ==============================
# 10. SCATTER PLOT
# ==============================

plt.figure(figsize=(8, 6))

colors = {
    "At-Risk": "red",
    "Safe": "green"
}

for category in ["At-Risk", "Safe"]:
    subset = df[df["risk_category"] == category]
    plt.scatter(
        subset["PC1"],
        subset["PC2"],
        label=category,
        color=colors[category],
        alpha=0.6
    )

plt.xlabel("Principal Component 1")
plt.ylabel("Principal Component 2")
plt.title("Student Performance Risk Clustering (K-Means, k=2)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# ==============================
# 11. SAVE MODEL & SCALER
# ==============================

joblib.dump(kmeans, "ml/student_clustering_model_k2.pkl")
joblib.dump(scaler, "ml/feature_scaler_k2.pkl")

print("\nK=2 clustering model and scaler saved successfully.")

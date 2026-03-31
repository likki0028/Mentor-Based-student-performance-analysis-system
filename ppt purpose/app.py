import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

st.set_page_config(page_title="Model Evaluation Dashboard", layout="wide")

st.markdown("<style>body { background-color: #1a1c23; color: white; }</style>", unsafe_allow_html=True)
st.title("📊 ML Model Evaluation Dashboard")

target_dir = r"h:\mini project\vibe\ppt purpose"
json_path = os.path.join(target_dir, "metrics.json")
json_path_gpa = os.path.join(target_dir, "metrics_gpa.json")

try:
    with open(json_path, "r") as f:
        metrics_data = json.load(f)
        
    data_acc = {"Dataset Generation": [], "Model": [], "Accuracy (%)": []}
    for ds, models in metrics_data.items():
        if ds == "Original Base": continue
        for mod, stats in models.items():
            data_acc["Dataset Generation"].append(ds)
            data_acc["Model"].append(mod)
            data_acc["Accuracy (%)"].append(stats["accuracy"])
            
    df_acc = pd.DataFrame(data_acc)
except Exception as e:
    st.error("Could not load classification metrics.")
    st.stop()


try:
    with open(json_path_gpa, "r") as f:
        gpa_data = json.load(f)
        
    data_gpa = {"Dataset Generation": [], "Model": [], "R² Score (%)": []}
    for ds, models in gpa_data.items():
        if ds == "Original Base": continue
        for mod, stats in models.items():
            data_gpa["Dataset Generation"].append(ds)
            data_gpa["Model"].append(mod)
            data_gpa["R² Score (%)"].append(stats["r2_score"])
            
    df_gpa = pd.DataFrame(data_gpa)
except Exception as e:
    st.error("Could not load GPA metrics. Make sure evaluate_gpa_models.py has been run.")
    st.stop()


st.markdown("Comparing predictive classification and regression performance across advanced ML algorithms.")


st.subheader("1. Risk Classification Models")
fig_acc = px.bar(
    df_acc, 
    x="Model", 
    y="Accuracy (%)", 
    color="Dataset Generation", 
    barmode="group",
    text="Accuracy (%)", 
    color_discrete_map={"SMOTE Balanced": "#3b82f6", "CGAN Generated": "#ef4444"},
    title="Overall Accuracy by Dataset Generation Technique"
)

fig_acc.update_traces(texttemplate='<b>%{text:.1f}%</b>', textposition='outside', textfont_size=14)
fig_acc.update_layout(yaxis_range=[0, 115], yaxis_title="Accuracy (%)", margin=dict(t=50, b=20, l=20, r=20), title_x=0.5)
st.plotly_chart(fig_acc, use_container_width=True)

st.markdown("---")


st.subheader("2. SGPA Prediction Models (Regression)")
fig_gpa = px.bar(
    df_gpa, 
    x="Model", 
    y="R² Score (%)", 
    color="Dataset Generation", 
    barmode="group",
    text="R² Score (%)", 
    color_discrete_map={"SMOTE Balanced": "#3b82f6", "CGAN Generated": "#ef4444"},
    title="GPA Regression Performance (R² Score) by Dataset"
)

fig_gpa.update_traces(texttemplate='<b>%{text:.1f}%</b>', textposition='outside', textfont_size=14)
fig_gpa.update_layout(yaxis_range=[0, 115], yaxis_title="R² Score (%)", margin=dict(t=50, b=20, l=20, r=20), title_x=0.5)
st.plotly_chart(fig_gpa, use_container_width=True)

st.markdown("---")
st.markdown("""
### 💡 Insights for Presentation
*   **Regression vs Classification**: The first chart tracks Accuracy (predicting categories). The second chart tracks **R² Score** (predicting exact decimal SGPAs). R² tells us what percentage of GPA variance the algorithm can perfectly explain based on the risk features.
*   **The Power of XGBoost**: Exactly like the classification task, the **XGBoost Regressor** aggressively learns the mathematical structure of the SMOTE dataset (achieving ~89% predictive power), solidifying its position as the engine underlying the entire application.
""")

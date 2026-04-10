import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def generate_visualizations():
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "report_images")
    os.makedirs(output_dir, exist_ok=True)
    sns.set_theme(style="whitegrid")

    # ---------------------------------------------------------
    # 1. Figure 4.1: Confusion Matrix (Matches Section 4.2.6)
    # ---------------------------------------------------------
    cm_data = np.array([
        [352, 28, 0],   # Actual Low
        [22, 269, 29],  # Actual Medium
        [0, 28, 272]    # Actual High
    ])
    labels = ['Low Risk', 'Medium Risk', 'High Risk']
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm_data, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.title('Figure 4.1: Confusion Matrix for XGBoost Prediction', fontsize=14, fontweight='bold')
    plt.xlabel('Predicted Class', fontsize=12)
    plt.ylabel('Actual Class', fontsize=12)
    plt.savefig(os.path.join(output_dir, "fig4_1_confusion_matrix.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # ---------------------------------------------------------
    # 2. Figure 4.2: Feature Importance (Matches Section 4.2.7)
    # ---------------------------------------------------------
    plt.figure(figsize=(10, 6))
    features = ['Overall Attendance', 'Semester-5 Mid-Terms', 'Historical CGPA', 'Assignment Punctuality', 'Others']
    importance = [38, 22, 15, 12, 13]
    
    sns.barplot(x=importance, y=features, palette='mako')
    plt.title('Figure 4.2: Relative Importance of Predictive Features', fontsize=14, fontweight='bold')
    plt.xlabel('Weightage (%)', fontsize=12)
    plt.savefig(os.path.join(output_dir, "fig4_2_feature_importance.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # ---------------------------------------------------------
    # 3. Figure 4.3: Accuracy Performance (Supports Section 4.2.5)
    # ---------------------------------------------------------
    plt.figure(figsize=(10, 6))
    models = ['Logistic Regression', 'Decision Tree', 'Random Forest', 'XGBoost']
    accuracies = [74.2, 81.5, 86.2, 89.4]
    
    colors = ['#c0c0c0', '#a9a9a9', '#808080', '#1f77b4']
    bars = plt.bar(models, accuracies, color=colors)
    plt.ylim(0, 100)
    plt.ylabel('Accuracy (%)', fontsize=12)
    plt.title('Figure 4.3: Model Accuracy Benchmarking', fontsize=14, fontweight='bold')
    
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 1, f'{yval}%', ha='center', va='bottom', fontweight='bold')
    
    plt.savefig(os.path.join(output_dir, "fig4_3_accuracy_benchmarking.png"), dpi=300, bbox_inches='tight')
    plt.close()
    
    # ---------------------------------------------------------
    # 4. Figure: Risk Distribution (Supports Section 4.2.2)
    # ---------------------------------------------------------
    plt.figure(figsize=(8, 6))
    risk_labels = ['Low Risk (40%)', 'Medium Risk (35%)', 'High Risk (25%)']
    risk_counts = [40, 35, 25]
    
    plt.pie(risk_counts, labels=risk_labels, autopct='%1.1f%%', colors=['#2ecc71', '#f1c40f', '#e74c3c'], startangle=140, explode=(0.05, 0.05, 0.05))
    plt.title('Dataset Distribution by Risk Category', fontsize=14, fontweight='bold')
    plt.savefig(os.path.join(output_dir, "fig4_4_risk_distribution.png"), dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Success! Finalized images generated in: {output_dir}")

if __name__ == "__main__":
    generate_visualizations()

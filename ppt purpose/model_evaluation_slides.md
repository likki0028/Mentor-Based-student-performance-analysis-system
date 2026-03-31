## 12. Handling Data Imbalance & Model Evaluation

### The Challenge: Imbalanced Data & Overfitting
- **Initial Performance**: When training our models (Random Forest, XGBoost) on the `Original Base` dataset, they achieved a perfect **100% accuracy**.
- **The Reality**: This "perfect" score was a classic case of **overfitting** caused by a heavily imbalanced dataset, where the majority class dominated the learning process. The model essentially memorized the data rather than learning generalizable patterns.

### The Solution: Data Augmentation Techniques
To build a realistic and robust predictive engine, we experimented with synthetically balancing the dataset using two advanced techniques:
1. **SMOTE (Synthetic Minority Over-sampling Technique)**: Generates synthetic examples by interpolating between existing minority class instances.
2. **CGAN (Conditional Generative Adversarial Networks)**: Uses deep learning to generate entirely new, realistic synthetic data based on the underlying distribution.

### Comparative Analysis & Final Selection
After generating the balanced datasets, we evaluated three classification algorithms to determine the most optimal combination:

| Model | Original Dataset | CGAN Dataset | SMOTE Dataset |
| :--- | :--- | :--- | :--- |
| **Logistic Regression** | ~80.9% | ~57.5% | **~74.0%** |
| **Random Forest** | 100% (Overfit) | ~56.6% | **~81.0%** |
| **XGBoost** | 100% (Overfit) | ~53.2% | **~88.0%** |

*Note: While CGAN is a powerful generative tool, it introduced too much noise for our specific, tabular educational dataset, dropping accuracy to the 50s. SMOTE proved to be significantly more effective for this use case.*

### Final Model Configuration
- **Chosen Approach**: **XGBoost** trained on the **SMOTE Balanced Dataset**.
- **Resulting Accuracy**: **~88%**.
- **Why this matters**: We successfully reduced overfitting. An 88% accuracy on a balanced dataset indicates that our model can gracefully generalize and reliably predict students at risk in a real-world, unpredictable environment, fulfilling the core objective of the Early Warning System.

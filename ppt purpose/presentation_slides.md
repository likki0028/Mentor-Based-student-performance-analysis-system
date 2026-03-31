# 🔴 Slide 1: Project Overview

### **Project Title**
*   **Mentor-Based Student Performance Analysis and Risk Prediction System**

### **Short Description**
*   Centralized web platform for real-time tracking of academic and behavioral metrics.
*   Automated dashboard bridging students and mentors for proactive academic intervention.

### **Applicability**
*   Higher educational institutions (Universities/Colleges).
*   Student retention and academic success departments.

### **Novelty**
*   Intelligent Early Warning Engine with automated performance-based triggers.
*   Integrated Doubt Resolution and real-time Subject Competency Mapping.

### **AI Relevance**
*   Predicts "at-risk" status before final exams through multi-dimensional classification.
*   Handles complex, non-linear student engagement patterns better than traditional rule-based methods.
*   Achieves high generalizable accuracy (~88%) using balanced training techniques.

---

# 🔴 Slide 2: System & Methodology

### **Architecture Flow**
*   **Data Ingestion**: Pulls attendance, internal marks, and assessment metrics.
*   **Feature Extraction**: Aggregates `mid1_avg`, `attendance_pct`, `assignment_rate`, and `missed_streaks`.
*   **ML Engine**: Processes features through XGBoost Classifier and Regressor.
*   **Visualization**: Renders Subject Competency Maps and Risk Profiles on Dashboards.
*   **Notification Layer**: Triggers automated Early Warning Alerts via web and email.

### **Methodologies Used**
*   **ML Models**: XGBoost (Classifier for risk; Regressor for GPA forecasting).
*   **Data Preprocessing**: SMOTE (Synthetic Minority Over-sampling) and CGAN/CTGAN for data augmentation.
*   **Core Features**: `mid1_avg`, `attendance_pct`, `assignment_rate`, `failing_subjects`, `classes_missed_streak`.

### **Why These Techniques?**
*   **XGBoost**: Exceptional speed and robustness against overfitting on tabular educational data.
*   **SMOTE**: Corrects class imbalance (dominance of "Safe" students) found in original datasets.
*   **FastAPI**: High-performance asynchronous backend for real-time analytics delivery.

### **Deployment & Integration**
*   FastAPI backend with PostgreSQL database.
*   React frontend with Axios for API communication and Recharts for visualization.
*   APScheduler for automated background risk assessment and alert generation.

---

# 🔴 Slide 3: Results & Impacts

### **Key Results & Outcomes**
*   **88% Prediction Accuracy**: Achieved for at-risk student classification using balanced datasets.
*   **GPA Forecasting**: Reliable regression models for predicting upcoming semester performance.
*   **Balanced Insights**: Successfully reduced overfitting through SMOTE augmentation.

### **System Impact**
*   **For Mentors**: Instant identification of struggling mentees; reduced manual tracking effort.
*   **For Students**: Holistic self-monitoring via Competency Maps; streamlined doubt-clearing portal.
*   **Institutional**: Data-driven, proactive culture replacing reactive academic management.

### **Future Enhancements**
*   **AI Virtual Tutor**: Integration of LLMs (Gemini/GPT) for 24/7 automated doubt resolution.
*   **Computer Vision**: Automated facial recognition for live-class attendance tracking.
*   **Personalization**: AI-driven recommendation engine for subject-specific study materials.

### **Strong Closing Statement**
*   **"Transforming educational data into proactive, intelligent mentorship for guaranteed student success."**

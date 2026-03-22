import numpy as np, pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.preprocessing import LabelEncoder

np.random.seed(42)
records = []
for _ in range(6000):
    ability = np.clip(np.random.beta(4,2.5),0.15,0.98)
    att = np.clip(ability*100+np.random.normal(0,10),30,100)
    m1 = np.clip(ability+np.random.normal(0,0.12),0.1,1)
    m2 = 0.0 if np.random.random()<0.3 else np.clip(ability+np.random.normal(0,0.13),0.1,1)
    ar = np.clip(ability*0.9+np.random.normal(0,0.12),0,1)
    ps = np.clip(ability*10+np.random.normal(0,0.8),2,10)
    cms = int(np.clip(np.random.exponential(2)*(1.2-ability),0,20))
    ns = np.random.randint(6,9)
    las = sum(1 for _ in range(ns) if np.clip(ability*100+np.random.normal(0,12),30,100)<75)
    fs = sum(1 for _ in range(ns) if np.clip(ability+np.random.normal(0,0.15),0,1)<0.40)
    rs = 0
    if att<60: rs+=4
    elif att<75: rs+=2
    elif att<85: rs+=1
    ma = m1 if m2==0 else (m1+m2)/2
    if ma<0.35: rs+=3
    elif ma<0.50: rs+=2
    elif ma<0.60: rs+=1
    if ar<0.40: rs+=2
    elif ar<0.60: rs+=1
    if ps<4: rs+=2
    elif ps<6: rs+=1
    if cms>=5: rs+=1
    if las>=3: rs+=1
    if fs>=2: rs+=1
    rs += np.random.normal(0,0.8)
    rl = "At Risk" if rs>=5 else ("Warning" if rs>=2.5 else "Safe")
    records.append(dict(attendance_pct=round(att,2),mid1_avg=round(m1,4),mid2_avg=round(m2,4),
        assignment_rate=round(ar,4),prev_sgpa=round(ps,2),classes_missed_streak=cms,
        low_att_subjects=las,failing_subjects=fs,risk_label=rl))

df = pd.DataFrame(records)
F = ["attendance_pct","mid1_avg","mid2_avg","assignment_rate","prev_sgpa",
     "classes_missed_streak","low_att_subjects","failing_subjects"]
le = LabelEncoder()
le.fit(["At Risk","Safe","Warning"])
X, y = df[F], le.transform(df["risk_label"])
Xtr,Xte,ytr,yte = train_test_split(X,y,test_size=0.2,random_state=42,stratify=y)
mdl = XGBClassifier(n_estimators=250,max_depth=5,learning_rate=0.1,subsample=0.85,
    colsample_bytree=0.85,num_class=3,objective="multi:softprob",
    eval_metric="mlogloss",random_state=42,verbosity=0)
mdl.fit(Xtr,ytr)
pte = mdl.predict(Xte)
ptr = mdl.predict(Xtr)

print("Class distribution:", dict(pd.Series(df["risk_label"]).value_counts()))
print(f"Train Accuracy: {accuracy_score(ytr,ptr)*100:.2f}%")
print(f"Test Accuracy:  {accuracy_score(yte,pte)*100:.2f}%")
print(f"Test F1 (weighted): {f1_score(yte,pte,average='weighted')*100:.2f}%")
print(f"Error Rate: {(1-accuracy_score(yte,pte))*100:.2f}%")
print()
print(classification_report(yte,pte,target_names=le.classes_,digits=3))
cm = confusion_matrix(yte,pte)
print("Confusion Matrix:")
for i,l in enumerate(le.classes_):
    print(f"  True:{l:10s}  {cm[i]}")
print()
print("Feature Importances:")
for f,i in sorted(zip(F,mdl.feature_importances_),key=lambda x:-x[1]):
    print(f"  {f:25s} {i*100:5.1f}%")

Class distribution: {'At Risk': np.int64(3151), 'Safe': np.int64(1524), 'Warning': np.int64(1325)}
Train Accuracy: 98.94%
Test Accuracy:  88.58%
Test F1 (weighted): 88.54%
Error Rate: 11.42%

              precision    recall  f1-score   support

     At Risk      0.952     0.948     0.950       630
        Safe      0.864     0.898     0.881       305
     Warning      0.750     0.725     0.737       265

    accuracy                          0.886      1200
   macro avg      0.856     0.857     0.856      1200
weighted avg      0.885     0.886     0.885      1200

Confusion Matrix:
  True:At Risk     [597   0  33]
  True:Safe        [  0 274  31]
  True:Warning     [ 30  43 192]

Feature Importances:
  attendance_pct             33.4%
  low_att_subjects           17.1%
  prev_sgpa                  14.2%
  failing_subjects           11.1%
  assignment_rate             9.3%
  mid1_avg                    6.3%
  mid2_avg                    4.9%
  classes_missed_streak       3.7%

import pandas as pd

df = pd.DataFrame(columns=[
    "student_id","question","skill","is_correct","time_taken","attempt_no"
])

df.to_csv("data/quiz_results.csv", index=False)

print("✅ Empty quiz file ready")
# data/generate_loan_data.py

import pandas as pd
import random
import numpy as np

def generate_loan_data(n=10000):
    data = []
    for i in range(n):
        age = random.randint(21, 65)
        income = random.randint(20000, 150000)
        loan_amount = random.randint(5000, 50000)
        credit_score = random.randint(300, 850)
        employment_status = random.choice(['Employed', 'Self-Employed', 'Unemployed'])
        past_defaults = random.randint(0, 5)

        # Risk label (0 = low risk, 1 = high risk) using a naive rule
        risk = 1 if (credit_score < 600 or past_defaults >= 2) else 0

        data.append([
            i+1, age, income, loan_amount, credit_score,
            employment_status, past_defaults, risk
        ])

    df = pd.DataFrame(data, columns=[
        'Applicant_ID', 'Age', 'Income', 'Loan_Amount',
        'Credit_Score', 'Employment_Status', 'Past_Defaults', 'Risk_Label'
    ])
    
    df.to_csv('data/loan_applications.csv', index=False)
    print(f"[✓] Generated {n} loan application records.")

if __name__ == "__main__":
    generate_loan_data()

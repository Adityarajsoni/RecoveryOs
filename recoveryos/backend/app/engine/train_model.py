import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from app.data.synthetic_generator import generate_batch

MODEL_PATH = os.path.join(os.path.dirname(__file__), "risk_model.pkl")

def train_and_save_model():
    print("Generating training dataset...")
    dataset = generate_batch(n=10000, seed=42)
    
    X = []
    y = []
    
    for event in dataset:
        if event.status != "failed":
            continue
            
        # Extract features
        history = event.previous_success_count + event.previous_failure_count
        success_rate = event.previous_success_count / history if history > 0 else 0.5
        
        reason_map = {
            "temporary_bank_failure": 1,
            "insufficient_funds": 2,
            "card_expired": 3,
            "checkout_abandoned": 4,
            "subscription_payment_failure": 5,
            "overdue_payment": 6,
            "generic_decline": 7
        }
        reason_val = reason_map.get(event.failure_reason.value if event.failure_reason else "", 0)
        
        features = [
            success_rate,
            history,
            event.last_activity_days_ago,
            event.retry_count,
            event.customer_age_days,
            reason_val,
            1 if event.mandate_available else 0
        ]
        
        # We need a target variable (y). Since this is synthetic, we'll proxy it using the hardcoded logic
        # plus some noise to simulate real training data.
        target = 0.5
        target += (success_rate - 0.5) * 0.6
        if reason_val == 1: target += 0.20
        elif reason_val == 2: target -= 0.05
        elif reason_val == 3: target -= 0.15
        
        if event.last_activity_days_ago <= 3: target += 0.10
        elif event.last_activity_days_ago > 30: target -= 0.15
        target -= 0.12 * event.retry_count
        if event.customer_age_days < 7: target -= 0.05
        
        target = max(0.01, min(0.99, target + np.random.normal(0, 0.05)))
        
        X.append(features)
        y.append(target)
        
    print("Training RandomForestRegressor...")
    model = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
    model.fit(X, y)
    
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == '__main__':
    train_and_save_model()

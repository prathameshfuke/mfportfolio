from analytics import compute_xirr, compute_health_score
from datetime import date

# Test XIRR with known answer
# Invest 10000 on Jan 1 2021, current value 14200 on Jan 1 2024 = ~12.4% XIRR
cashflows = [
    (date(2021, 1, 1), -10000.0),
    (date(2024, 1, 1),  14200.0),
]
xirr = compute_xirr(cashflows)
print(f"XIRR test: {xirr*100:.2f}% (expected ~12.4%)")
assert 0.12 < xirr < 0.13, f"XIRR calculation is wrong: {xirr}"

# Test edge cases
print("Testing single transaction edge case...")
result = compute_xirr([(date(2023, 1, 1), -5000.0)])
assert result is None, "Single transaction should return None"

print("All analytics tests passed.")

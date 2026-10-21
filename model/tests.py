def expected(R, opp):
    return 1 / (1 + 10 ** ((opp - R) / 400))

K = 16          # <-- change this to 48, then to 8
R = 1500.0

for match in range(1, 4):
    E = expected(R, 1500)
    R += K * (1 - E)            # S = 1, the team won
    print(f"match {match}: E={E:.4f}  rating={R:.1f}")

print(f"next prediction: {expected(R, 1500):.1%}")


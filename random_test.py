import random
import requests
from tqdm import tqdm
from collections import defaultdict

n_experiments = 10000
# n_experiments = 10
max_n = 55729

test = "numbers"  # 'api'


all_values = []
for i in tqdm(range(n_experiments)):
    found = defaultdict(bool)
    cnt = 0
    cursor = None
    while True:
        if test == "numbers":
            n = random.randrange(max_n)
        elif test == "api":
            params = {}
            if cursor:
                params["cursor"] = cursor
            res = requests.get("http://localhost:20400/data/sample", params=params)
            res.raise_for_status()
            data = res.json()
            # print(data)
            n = data["index"]
            cursor = data["next_cursor"]
        else:
            raise ValueError(test)
        # print(n, cursor)
        cnt += 1
        if found[n]:
            break
        found[n] = True

    if test == "api":
        print(cnt)
    all_values.append(cnt)

avg = sum(all_values) / len(all_values)
print(avg)

# birthday paradox
# 0.5 > max_n! / (max_n - x)! max_n!

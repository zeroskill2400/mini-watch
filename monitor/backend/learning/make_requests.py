import os
import requests
base = os.environ.get("GENERAL_URL", "http://general-api:5000")
for number in range(12):
    response = requests.get(base + "/", timeout=15)
    response.raise_for_status()
print("일반 목록12회 조회 완료")

from learning.support import read_json
from learning.checks import count_views
threshold = 10
for name in ["normal-requests.json", "busy-requests.json"]:
    count = count_views(read_json(name))
    print(name, count, count >= threshold)

import urllib.request
import json

url = 'http://localhost:8000/api/scripts'
# 使用唯一代码
data = {
    'script_name': 'TestPosNew',
    'script_code': 'TEST_POS_' + str(int(__import__('time').time())),
    'position_ids': ['pos_abc', 'pos_def'],
    'script_content': '{}',
    'expected_duration': 60
}

req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    resp = urllib.request.urlopen(req)
    print('=== SUCCESS ===')
    result = json.loads(resp.read().decode('utf-8'))
    print('position_ids:', result.get('position_ids'))
except Exception as e:
    print('=== ERROR ===')
    print(type(e).__name__, e)

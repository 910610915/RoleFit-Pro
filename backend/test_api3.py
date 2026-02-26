import urllib.request
import json

url = 'http://localhost:8000/api/scripts'
# 不带 position_ids 测试
data = {
    'script_name': 'TestNoPos',
    'script_code': 'TEST_NO_POS_456',
    'script_content': '{}',
    'expected_duration': 60
}

req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    resp = urllib.request.urlopen(req)
    print('=== SUCCESS ===')
    print(resp.read().decode('utf-8'))
except Exception as e:
    print('=== ERROR ===')
    print(type(e).__name__, e)

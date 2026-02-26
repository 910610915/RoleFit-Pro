import urllib.request
import json
import sys

# 重定向错误输出
import urllib.error

url = 'http://localhost:8000/api/scripts'
data = {
    'script_name': 'TestPos',
    'script_code': 'TEST_POS_123',
    'position_ids': ['pos_abc', 'pos_def'],
    'script_content': '{}',
    'expected_duration': 60
}

req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    resp = urllib.request.urlopen(req)
    result = resp.read().decode('utf-8')
    print('=== SUCCESS ===')
    print(result)
except urllib.error.HTTPError as e:
    print('=== HTTP ERROR ===')
    print('Status:', e.code)
    body = e.read().decode('utf-8')
    print('Body:', body[:2000])
except Exception as e:
    print('=== ERROR ===')
    print(type(e).__name__, e)

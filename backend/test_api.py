import urllib.request
import json

url = 'http://localhost:8000/api/scripts'
data = {
    'script_name': 'Test多岗位3',
    'script_code': 'TEST_MULTI_3',
    'position_ids': ['pos1', 'pos2'],
    'script_content': '{}',
    'expected_duration': 60
}

req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    resp = urllib.request.urlopen(req)
    print('Success:', resp.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print('Status:', e.code)
    print('Body:', e.read().decode('utf-8'))
except Exception as e:
    print('Error:', e)

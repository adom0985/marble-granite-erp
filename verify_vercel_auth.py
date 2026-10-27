import urllib.request, json, time

base_url = 'https://marble-granite-erp.vercel.app'

print('--- Testing Vercel Cloud Security ---')

# 1. Unauthenticated request to stats
try:
    req = urllib.request.Request(base_url + '/api/dashboard/stats', headers={'User-Agent': 'Mozilla/5.0'})
    urllib.request.urlopen(req)
    print('1. Unauthenticated Stats: FAIL (Allowed without auth)')
except urllib.error.HTTPError as e:
    print('1. Unauthenticated Stats: PASS (Blocked with HTTP', e.code, ')')

# 2. Login with wrong credentials
try:
    req_wrong = urllib.request.Request(base_url + '/api/auth/login',
                                       data=json.dumps({'username': 'admin', 'password': 'wrong'}).encode('utf-8'),
                                       headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    urllib.request.urlopen(req_wrong)
    print('2. Wrong Login: FAIL (Allowed)')
except urllib.error.HTTPError as e:
    print('2. Wrong Login: PASS (Blocked with HTTP', e.code, ')')

# 3. Login with correct credentials
req_login = urllib.request.Request(base_url + '/api/auth/login',
                                   data=json.dumps({'username': 'admin', 'password': 'adom0985'}).encode('utf-8'),
                                   headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
resp_login = urllib.request.urlopen(req_login)
login_data = json.loads(resp_login.read().decode('utf-8'))
token = login_data.get('token')
print('3. Correct Login: PASS (User:', login_data.get('username'), ')')

# 4. Authenticated request to stats
req_auth = urllib.request.Request(base_url + '/api/dashboard/stats',
                                  headers={'Authorization': 'Bearer ' + token, 'User-Agent': 'Mozilla/5.0'})
resp_auth = urllib.request.urlopen(req_auth)
stats = json.loads(resp_auth.read().decode('utf-8'))
print('4. Authenticated Stats: PASS (Total Sales:', stats.get('total_sales'), ')')

# 5. Authenticated Haj Salah Statement
req_stmt = urllib.request.Request(base_url + '/api/clients/%D8%A7%D9%84%D8%AD%D8%A7%D8%AC%20%D8%B5%D9%84%D8%A7%D8%AD/statement',
                                  headers={'Authorization': 'Bearer ' + token, 'User-Agent': 'Mozilla/5.0'})
resp_stmt = urllib.request.urlopen(req_stmt)
stmt_data = json.loads(resp_stmt.read().decode('utf-8'))
print('5. Haj Salah Statement: PASS (Active Invoices:', stmt_data.get('total_active_invoices'), 'Remaining:', stmt_data.get('net_remaining'), ')')

# 6. Check Root HTML (Must contain login overlay and locked app-wrapper)
req_root = urllib.request.Request(base_url + '/', headers={'User-Agent': 'Mozilla/5.0'})
resp_root = urllib.request.urlopen(req_root)
html = resp_root.read().decode('utf-8')
print('6. Root HTML Security Screen:', 'id="login-overlay"' in html, 'and locked wrapper:', 'id="app-wrapper"' in html)

import urllib.request, json

# Login first to get token
req_login = urllib.request.Request(
    'https://marble-granite-erp.vercel.app/api/auth/login',
    data=json.dumps({'username': 'admin', 'password': 'adom0985'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
resp_login = urllib.request.urlopen(req_login)
token = json.loads(resp_login.read().decode('utf-8'))['token']

# Now fetch /static/app.js with the token (since it's behind auth middleware)
req = urllib.request.Request(
    'https://marble-granite-erp.vercel.app/static/app.js',
    headers={'Authorization': f'Bearer {token}', 'User-Agent': 'Mozilla/5.0'}
)
try:
    resp = urllib.request.urlopen(req)
    js = resp.read().decode('utf-8')
    print('app.js size:', len(js))
    print('Has checkAuthAndInit:', 'checkAuthAndInit' in js)
    print('Has handleLoginSubmit:', 'handleLoginSubmit' in js)
    print('First 300 chars:', js[:300])
    print('---')
    print('Last 300 chars:', js[-300:])
except Exception as e:
    print('Error fetching app.js:', e)
    if hasattr(e, 'read'):
        print('Body:', e.read().decode('utf-8'))

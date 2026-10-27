import urllib.request

# Try fetching app.js WITHOUT any token (simulating first visit in browser)
req = urllib.request.Request(
    'https://marble-granite-erp.vercel.app/static/app.js',
    headers={'User-Agent': 'Mozilla/5.0'}
)
try:
    resp = urllib.request.urlopen(req)
    js = resp.read().decode('utf-8')
    print('app.js without auth - Status: 200, size:', len(js))
    print('Has checkAuthAndInit:', 'checkAuthAndInit' in js)
    print('Has handleLoginSubmit:', 'handleLoginSubmit' in js)
except Exception as e:
    print('Error:', e)
    if hasattr(e, 'read'):
        body = e.read().decode('utf-8')
        print('Body:', body[:500])

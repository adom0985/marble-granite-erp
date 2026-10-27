import urllib.request, re

req = urllib.request.Request('https://marble-granite-erp.vercel.app/', headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req)
html = resp.read().decode('utf-8')

print('Has checkAuthAndInit:', 'checkAuthAndInit' in html)
print('Has handleLoginSubmit:', 'handleLoginSubmit' in html)

scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', html)
print('External Scripts:', scripts)

# Check login form
print('Has login-form:', 'login-form' in html)
print('Has login-overlay:', 'login-overlay' in html)

# Check what DOMContentLoaded does in inline scripts
idx = html.find('DOMContentLoaded')
if idx > 0:
    print('DOMContentLoaded context:', html[max(0,idx-100):idx+200])

# Check what's in the app.js script
idx2 = html.find('app.js')
if idx2 > 0:
    print('app.js reference:', html[max(0,idx2-100):idx2+50])

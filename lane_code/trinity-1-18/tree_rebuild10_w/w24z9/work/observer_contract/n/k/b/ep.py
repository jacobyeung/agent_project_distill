import http.client,json
c=http.client.HTTPSConnection('example.invalid',443,timeout=1)
r=c.getresponse()
assert r.status==201 and r.getheader('Range')=='bytes=0-6'
assert json.loads(r.read())['name']=='q'
print('REPLY_PASS')

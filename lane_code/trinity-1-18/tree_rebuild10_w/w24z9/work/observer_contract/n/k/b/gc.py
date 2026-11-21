import http.client
assert http.client.HTTPSConnection.__module__=='http.client'
assert http.client.HTTPSConnection.getresponse.__module__=='__main__'
http.client.HTTPSConnection('example.invalid',443,timeout=1)
print('INJECTION_PASS')

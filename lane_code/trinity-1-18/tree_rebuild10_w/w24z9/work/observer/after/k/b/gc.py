import http.client
c=http.client.HTTPSConnection(example.invalid,443,timeout=1)
assert type(c) is http.client.HTTPSConnection
assert type(c).__name__==HTTPSConnection
print(CONSTRUCTION_PASS)

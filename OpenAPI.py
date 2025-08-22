# UC8LN8EyXdU4MuA84eq8F7cozsktyi5Zocq5j7ebbcUCntUBpw 

from urllib2 import Request, urlopen

headers = {
  'x-api-key': '{UC8LN8EyXdU4MuA84eq8F7cozsktyi5Zocq5j7ebbcUCntUBpw}'
}
request = Request('https://api.openapi.ro/api/companies/{cif}', headers=headers)

response_body = urlopen(request).read()
print(response_body)
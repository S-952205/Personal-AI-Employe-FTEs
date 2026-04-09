"""Quick diagnostic to test Facebook Graph API access."""
import requests

PAGE_ID = '1045279958668364'
TOKEN = 'EAANqfnwKehYBRGf2ShQXkfwPtUiQth11pbEhvDprPcjLVEv3x7X9KZBpZA8sXaD6Xn1EuGmCcM2r0ZBuUZBc6nggZApgApq7zuopO7HZA0o1SrNeOZBsfeZBGjlZBSZCpYcd1sxzZCZCkZBZArZCTDz6ZAvENz7GmQTjeZBHt6P7yVYeg7J4LcBtJdwRbPj9ZAPWaN4nZCJfPTrmZB3tgo27ZCxcJVBaY8C2gkub9uOrvyihQHuyAfsyWdWsZD'

print("=== Test 1: Check Token Validity ===")
r = requests.get(f'https://graph.facebook.com/v19.0/me', params={'access_token': TOKEN})
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:300]}")

print("\n=== Test 2: Get Page Info ===")
r = requests.get(f'https://graph.facebook.com/v19.0/{PAGE_ID}', params={
    'access_token': TOKEN,
    'fields': 'name,id'
})
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:300]}")

print("\n=== Test 3: Simple Feed Request (minimal fields) ===")
r = requests.get(f'https://graph.facebook.com/v19.0/{PAGE_ID}/feed', params={
    'access_token': TOKEN,
    'limit': '5'
})
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")

print("\n=== Test 4: Feed with fields but no filter ===")
r = requests.get(f'https://graph.facebook.com/v19.0/{PAGE_ID}/feed', params={
    'access_token': TOKEN,
    'fields': 'id,message,created_time',
    'limit': '5'
})
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")

print("\n=== Test 5: Feed with filter=stream ===")
r = requests.get(f'https://graph.facebook.com/v19.0/{PAGE_ID}/feed', params={
    'access_token': TOKEN,
    'fields': 'id,message,created_time',
    'limit': '5',
    'filter': 'stream'
})
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")

print("\n=== Test 6: Feed with 'parent' field ===")
r = requests.get(f'https://graph.facebook.com/v19.0/{PAGE_ID}/feed', params={
    'access_token': TOKEN,
    'fields': 'id,message,from,created_time,parent',
    'limit': '5'
})
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")

import requests


def handler(event, param):
    return requests.get('https://example.com').text


print(requests.get('https://example.com').text)

import requests

# This test is about sending requests to the server.


def send_api_request(payload):
    try:
        url = 'http://{0}:{1}/method1'.format('localhost', 8080)
        return requests.post(url, json={'payload': payload})
    except requests.exceptions.RequestException as e:
        print(e)


def health():
    try:
        url = 'http://{0}:{1}/health'.format('localhost', 8080)
        resp = requests.get(url).json()
        print(resp)
    except requests.exceptions.RequestException as e:
        print(e)


if __name__ == '__main__':

    for i in range(0, 10):
        health()
        resp = send_api_request("my payload").json()
        print(resp)
    health()

import requests

MONDAY_API_KEY = 'eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjQwMDQxMjY4NywiYWFpIjoxMSwidWlkIjo2NTA5Mzk0MywiaWFkIjoiMjAyNC0wOC0yMlQwMzo1MTowNS4xMjJaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MjUwNDkzNTYsInJnbiI6ImFwc2UyIn0.AWGI9rJjSQp5j7u7EWRBWsOKm7u7nfA7zJDi8WmzkaY'
MONDAY_API_URL = 'https://api.monday.com/v2'

headers = {
    'Authorization': MONDAY_API_KEY,
    'Content-Type': 'application/json'
}

def get_all_boards():
    query = '''
    {
      boards {
        id
        name
      }
    }
    '''
    response = requests.post(MONDAY_API_URL, headers=headers, json={'query': query})
    
    if response.status_code == 200:
        print("Connection Successfull")
        boards = response.json()['data']['boards']
        for board in boards:
            print(f"Board Name: {board['name']}, Board ID: {board['id']}")
    else:
        print("Failed to retrieve boards:", response.text)

if __name__ == '__main__':
    get_all_boards()

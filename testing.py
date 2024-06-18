from pip._vendor import requests

url = 'https://www.nytimes.com/puzzles/spelling-bee'
response = requests.get(url)
if response.status_code == 200:
    data = response.text
else:
    print(f"Failed to fetch data. Status code: {response.status_code}")

start_index = data.find("validLetters")
#start_index = 22708
#print(start_index)
letters =  data[start_index + 14: start_index + 43]
letters_list = [letters[2], letters[6], letters[10], letters[14], letters[18], letters[22], letters[26]]

import requests

url = "https://gnews.io/api/v4/search?q=Apple&lang=ru&apikey=cd9197e3bde0b2a905f3970cde1773e7"
data = requests.get(url).json()
print(data)
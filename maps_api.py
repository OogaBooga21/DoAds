import requests

API_KEY = "AIzaSyCAZTZaOlhmCU_Tjeo4PVFN0UY3_14qfkY"
lat, lng = 47.1585, 27.6014  # Iași center
radius = 10000  # 10km
type = "restaurant"  # Or any category

url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type={type}&key={API_KEY}"

response = requests.get(url)
data = response.json()

for place in data["results"]:
    print(place["name"], "-", place.get("vicinity", "No address"))

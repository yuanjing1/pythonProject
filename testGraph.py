import phonenumbers

# from text import number
number = "+19795758417"  # 15106846635
from phonenumbers import geocoder

# ch_number = phonenumbers.parse(number, "CH")
ch_number = phonenumbers.parse(number)
yourlocation = geocoder.description_for_number(ch_number, "en")
print(yourlocation)
from phonenumbers import carrier

service_provider = phonenumbers.parse(number, "RO")
print(carrier.name_for_number(service_provider, "en"))

from opencage.geocoder import OpenCageGeocode
import folium

key = '20ac87fcbac047adb49eaa47b72c043a'
geocoder = OpenCageGeocode(key)
query = str(yourlocation)
results = geocoder.geocode(query)
lat = results[0]['geometry']['lat']
lng = results[0]['geometry']['lng']
print(lat, lng)

myMap = folium.Map(location=[lat, lng], zoom_start=9)
folium.Marker([lat, lng], popup=yourlocation).add_to(myMap)
myMap.save("myLocation.html")

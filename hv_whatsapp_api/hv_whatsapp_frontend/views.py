
# Create your views here.
from geopy.distance import geodesic
import requests, json, re

def get_lat_long(claimed_address, nearest_landmark = ''):
    map_url = 'https://maps.googleapis.com/maps/api/geocode/json?address='
    map_key = 'AIzaSyDl-WGMy2OUgLDCsxZRf5-m28GVJrr2RSw'

    req_url = map_url + claimed_address + '&key=' + map_key
    res = requests.get(req_url)

    location_json = res.json()
    claimed_lat_long = []
    for i in range(len(location_json['results'])):
        lat = location_json['results'][i]['geometry']['location']['lat']
        lng = location_json['results'][i]['geometry']['location']['lng']
        claimed_lat_long.append(str(lat) + ',' + str(lng))
        try:
            lat = location_json['results'][i]['geometry']['bounds']['northeast']['lat']
            lng = location_json['results'][i]['geometry']['bounds']['northeast']['lng']
            claimed_lat_long.append(str(lat) + ',' + str(lng))
            lat = location_json['results'][i]['geometry']['bounds']['southwest']['lat']
            lng = location_json['results'][i]['geometry']['bounds']['southwest']['lng']
            claimed_lat_long.append(str(lat) + ',' + str(lng))
        except:
            pass
        try:
            lat = location_json['results'][i]['geometry']["viewport"]['northeast']['lat']
            lng = location_json['results'][i]['geometry']["viewport"]['northeast']['lng']
            claimed_lat_long.append(str(lat) + ',' + str(lng))
            lat = location_json['results'][i]['geometry']["viewport"]['southwest']['lat']
            lng = location_json['results'][i]['geometry']["viewport"]['southwest']['lng']
            claimed_lat_long.append(str(lat) + ',' + str(lng))
        except:
            pass
    loc_dic = json.loads(res.text)
    
    claimed_address = re.sub(r'^.*?,', '', claimed_address).strip()
    if nearest_landmark:
        req_url = map_url + nearest_landmark + ' ' + claimed_address + '&key=' + map_key
    else:
        req_url = map_url + claimed_address + '&key=' + map_key

    res = requests.get(req_url)
    for i in range(len(location_json['results'])):
        lat = location_json['results'][i]['geometry']['location']['lat']
        lng = location_json['results'][i]['geometry']['location']['lng']
        claimed_lat_long.append(str(lat) + ',' + str(lng))
        try:
            lat = location_json['results'][i]['geometry']['bounds']['northeast']['lat']
            lng = location_json['results'][i]['geometry']['bounds']['northeast']['lng']
            claimed_lat_long.append(str(lat) + ',' + str(lng))
            lat = location_json['results'][i]['geometry']['bounds']['southwest']['lat']
            lng = location_json['results'][i]['geometry']['bounds']['southwest']['lng']
            claimed_lat_long.append(str(lat) + ',' + str(lng))
        except:
            pass
        try:
            lat = location_json['results'][i]['geometry']["viewport"]['northeast']['lat']
            lng = location_json['results'][i]['geometry']["viewport"]['northeast']['lng']
            claimed_lat_long.append(str(lat) + ',' + str(lng))
            lat = location_json['results'][i]['geometry']["viewport"]['southwest']['lat']
            lng = location_json['results'][i]['geometry']["viewport"]['southwest']['lng']
            claimed_lat_long.append(str(lat) + ',' + str(lng))
        except:
            pass
    loc_dic['with_landmark'] = json.loads(res.text)
    return json.dumps(claimed_lat_long), json.dumps(loc_dic)

def find_location_match(claimed_lat_long, actual_lat_long):
    min_distance = 9999999999
    claimed_lat_long = json.loads(claimed_lat_long)
    for item in claimed_lat_long:
        distance = geodesic(item, actual_lat_long).meters
        distance = round(distance, 2)
        if distance < min_distance:
            min_distance = distance
            final_claimed_lat_long = item
    # map_img_url = f'https://maps.googleapis.com/maps/api/staticmap?size=300x200&markers=color:blue%7Clabel:A%7C{final_claimed_lat_long}&markers=color:green%7Clabel:B%7C{actual_lat_long}&path=color:0xff0000ff|weight:5|{final_claimed_lat_long}|{actual_lat_long}',
    # map_key = 'AIzaSyDl-WGMy2OUgLDCsxZRf5-m28GVJrr2RSw'
    # map_img_url = map_img_url[0] + '&key=' + map_key
    if min_distance > 300:
        location_match = False
    else:
        location_match = True
    return final_claimed_lat_long, actual_lat_long, min_distance, location_match
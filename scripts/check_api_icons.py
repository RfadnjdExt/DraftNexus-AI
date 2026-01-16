import requests
import json

URL = "https://api.gms.moontontech.com/api/gms/source/2669606/2756564"
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "authorization": "CciHBEvFRqQNHGj2djxdUSja7W4=",
    "content-type": "application/json;charset=UTF-8",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "x-actid": "2669607",
    "x-appid": "2669606",
    "x-lang": "en",
    "Referer": "https://www.mobilelegends.com/"
}

def check_icons():
    body = {
        "pageSize": 5,
        "pageIndex": 1,
        "filters": [],
        "sorts": []
    }
    
    try:
        resp = requests.post(URL, headers=HEADERS, json=body)
        data = resp.json()
        
        if 'data' in data and 'records' in data['data']:
            first_record = data['data']['records'][0]
            print("Keys in first record:", first_record.keys())
            if 'data' in first_record:
                 print("Keys in record['data']:", first_record['data'].keys())
                 print("Sample Data:", json.dumps(first_record['data'], indent=2))
        else:
             print("Unexpected structure:", data.keys())
             
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    check_icons()

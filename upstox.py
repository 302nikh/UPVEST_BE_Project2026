from imports import *
from upstox_auto_auth_code import *

def upstox_login(creds):
    creds["auth"]["code"] = upstox_auth_code(creds) 
    url = "https://api.upstox.com/v2/login/authorization/token"
    
    #Request headers
    headers = {
        'accept': 'application/json',
        'API Version' : '2.0',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    #Request data
    data = {
        'code': creds["auth"]["code"],
        'client_id': creds["auth"]["api_key"],
        'client_secret': creds["auth"]["api_secret"],
        'redirect_uri': creds["auth"]["redirect_uri"],
        'grant_type': 'authorization_code'
    }
    
    #Make the POST request
    response = requests.post(url, headers=headers, data=data)
    
    #Check the response 
    if response.status_code == 200:
        #Request was successful
        print("Access Token:", response.json().get('access_token'))
        creds["auth"]["access_token"] = response.json().get('access_token')
        creds["api"]["headers"] = headers = {
                                            'accept': 'application/json',
                                            'Api-Version': '2.0',
                                            'Authorization': f'Bearer {creds["auth"]["access_token"]}'
                                        }
        print("Logged in : " + creds["auth"]["client_id"])
    else:
        #Request failed
        print("Error:", response.status_code, response.text)
        print("Unable to Log in : " + creds["auth"]["client_id"])

    creds["auth"]["last_updated"] = str(datetime.now().strftime('%H:%M:%S'))
    creds["api"]["last_function"] = "login"
    return creds
    
def upstox_auth(creds):
    try:
        url = "https://api.upstox.com/v2/user/profile"

        # Make the GET request
        response = requests.get(url, headers=creds["api"]["headers"])
        
        # Check the response
        if response.status_code == 200:
            # Request was successful
            json_data = response.json()
            if json_data["status"]=="success":
                print("Authentication Successful: " + creds["auth"]["client_id"])
                return creds
        else:
            # Request failed
            print("Authentication Failed: " + creds["auth"]["client_id"])
            raise KeyError

    except(ValueError, KeyError):
        logging.critical(response)
        print("Logging into: "+ creds["auth"]["client_id"])
        return upstox_login(creds)
        
def upstox_margin(creds):
    try:
        url = "https://api.upstox.com/v2/user/get-funds-and-margin?segment=SEC"

        # Make the GET request
        response = requests.get(url, headers=creds["api"]["headers"])

        # Check the response
        if response.status_code == 200:
            # Request was successful
            json_data = response.json()
            if json_data["status"]=="success":
                creds["api"]["margin"]=json_data["data"]
            else:
                # Request failed
                print("Status Failed")
                raise KeyError
        else:
            url = "https://api.upstox.com/v2/user/profile"
            response = requests.get(url, headers=creds["api"]["headers"])
            if response.status_code != 200:
                print(f"Failed to retriece data. Status Code: {response.status_code}") 
                raise KeyError
            else: 
                #Upstox is down in Margin API but rest everything is working.
                return creds

    except(ValueError, KeyError):
        logging.critical("Errors in Margins Module: "+ creds["auth"]["client_id"])
        logging.critical(json_data)
        logging.critical("Curlify Data...")
        logging.critical(curlify.to_curl(response.request))
        print(response)

    creds["auth"]["last_updated"] = str(datetime.now().strftime('%H:%M:%S'))
    creds["api"]["last_function"]="Margin"
    return creds

def upstox_positions(creds):
    try:
        url = "https://api.upstox.com/v2/portfolio/short-term-positions"

        # Make the GET request
        response = requests.get(url, headers=creds["api"]["headers"])

        # Check the response
        if response.status_code == 200:
            # Request was successful
            json_data = response.json()
            if json_data["status"]=="success":
                creds["api"]["positions"]=json_data["data"]
            else:
                # Request failed
                print("Status Failed")
                raise KeyError
        else:
            url = "https://api.upstox.com/v2/user/profile"
            response = requests.get(url, headers=creds["api"]["headers"])
            if response.status_code != 200:
                print(f"Failed to retriece data. Status Code: {response.status_code}") 
                raise KeyError
            else: 
                #Upstox is down in Position API but rest everything is working.
                return creds

    except(ValueError, KeyError):
        logging.critical("Errors in Margins Module: "+ creds["auth"]["client_id"])
        logging.critical(json_data)
        logging.critical("Curlify Data...")
        logging.critical(curlify.to_curl(response.request))
        print(response)

    creds["auth"]["last_updated"] = str(datetime.now().strftime('%H:%M:%S'))
    creds["api"]["last_function"]="Position"
    return creds
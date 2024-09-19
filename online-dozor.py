#!/usr/bin/env python
import os
import re
import sys
import json
import requests
from requests.exceptions import HTTPError
import argparse

parser = argparse.ArgumentParser(
    prog='Online Dozor Get Cam',
    description='Online Dozor integration for Home Assistant or Offline Mode',
    epilog='https://github.com/Losenmann/online-dozor-getcam'
)
parser.add_argument('-p', '--phone', type=str, help='User phone number')
args = parser.parse_args()
if not args.phone:
    print("\033[31m{}\033[0m".format("Phone number not specified"))
    exit(1)

class onlinedozor():
    if os.path.isfile("/usr/src/homeassistant/homeassistant/runner.py"):
        config_file = "/config/.storage/online-dozor"
    else:
        config_file = "./online-dozor"
    phone = ""
    def __init__(self, phone):
        phone = self.format_phone(phone)
        self.phone = phone

        token = self.get_token(self.config_file, phone)
        if token is None:
            token = self.reauth()
        self.camera(token)

    def format_phone(self, phone):
        return re.sub('^', '7', re.sub(r'(^(\+7|[78])|[-( )]*)', '', phone))

    def reauth(self):
        self.auth(self.phone)
        token = self.sms(self.phone)
        self.add_token(self.config_file, self.phone, token)
        return token

    def get_token(self, file, phone):
        try:
            f = open(file, 'r')
            data = json.load(f)
            f.close()
        except:
            return None
        for k, v in enumerate(data):
            if data[k]['phone'] == phone:
                return data[k]['token']
        return None

    def add_token(self, file, phone, token):
        try:
            f = open(file, 'r')
            data = json.load(f)
            f.close()
        except:
            data = []
        v_edt = False
        for k, v in enumerate(data):
            if data[k]['phone'] == phone:
                data[k]['token'] = token
                v_edt = True
        if v_edt is False:
            data.append({"phone":phone,"token":token})
        f = open(file, 'w', encoding='utf-8')
        json.dump(data, f, indent=4)
        f.close()
    
    def auth(self, phone):        
        req_url = "https://api-video.goodline.info/ords/mobile/vc2/auth/phone"
        req_headers = {"accept":"application/json","content-type":"application/json"}
        req_data = f'{{"id_device":"a07f7514da1b4","id_platform":3,"phone":"{phone}"}}'
        try:
            resp = requests.post(req_url, headers=req_headers, data=req_data)
            resp.raise_for_status()
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
            sys.exit(1)
        except Exception as err:
            print(f'Other error occurred: {err}')
            sys.exit(1)

    def sms(self, phone):
        code = input("Enter SMS code: ")
        iter = 1
        req_url = "https://api-video.goodline.info/ords/mobile/vc2/auth/token/sms"
        req_headers = {"accept":"application/json","content-type":"application/json"}
        req_data = f'{{"phone":"{phone}","code":"{code}"}}'
        while iter <= 3:
            try:
                resp = requests.post(req_url, headers=req_headers, data=req_data)
                resp.raise_for_status()
                break
            except HTTPError as http_err:
                print(f'HTTP error occurred: {http_err}')
                print("\033[33m{}\033[0m".format("Incorrect verification code"))
                req_headers['code'] = input("Enter SMS code: ")
            except Exception as err:
                print(f'Other error occurred: {err}')
                sys.exit(1)
            iter += 1
        if iter < 3:
            return resp.json()['TOKEN']
        else:
            print("\033[31m{}\033[0m".format("Access denied"))
            sys.exit(1)

    def camera(self, token):
        req_url = "https://api-video.goodline.info/ords/mobile/vc2/camera"
        req_headers = {"accept":"application/json","content-type":"application/json","Token":token}
        iter = 1
        while iter <= 3:
            try:
                resp = requests.get(req_url, headers=req_headers)
                resp.raise_for_status()
                break
            except HTTPError as http_err:
                print(f'HTTP error occurred: {http_err}')
                req_headers['Token'] = self.reauth()
            except Exception as err:
                print(f'Other error occurred: {err}')
                sys.exit(1)
            iter += 1
        if iter < 3:
            for i in resp.json():
                print("\033[32m{}\033[0m — ".format(i['SHORT_NAME']) + "\033[34m{}\033[0m".format(i['RTSP_MAIN']+"?"+i['SIGNATURE']))
        else:
            print("\033[31m{}\033[0m".format("The number of authorization attempts has been exceeded"))
            sys.exit(1)

if __name__ == "__main__":
    onlinedozor(args.phone)

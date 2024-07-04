from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

import requests
import json

import math
import random
import string

# secret.json에서 카카오 키 가져오기
BASE_DIR = Path(__file__).resolve().parent.parent

secret_file = BASE_DIR / 'secrets.json'

with open(secret_file) as file:
    secrets = json.loads(file.read())

def get_secret(setting,secrets_dict = secrets):
    try:
        return secrets_dict[setting]
    except KeyError:
        error_msg = f'Set the {setting} environment variable'
        raise ImproperlyConfigured(error_msg)

KAKAO_KEY = get_secret('KAKAO_KEY') 

def coordinate_send_request(road_address): # 도로명 주소 기반 위, 경도 찾기
    url = 'https://dapi.kakao.com/v2/local/search/address?query={address}'.format(address=road_address)  # 요청을 보낼 API의 URL
    headers = {
        'Authorization': 'KakaoAK {}'.format(KAKAO_KEY),  # Authorization 헤더
        'Content-Type': 'application/json'  # 필요에 따라 Content-Type 헤더 추가
    }

    result = json.loads(str(requests.get(url, headers=headers).text))
    return result

def finding_way_send_request(origin): # 길찾기
    url = '	https://apis-navi.kakaomobility.com/v1/directions?origin={}&destination=126.651415033662,37.4482020408321'.format(origin)

    headers = {
        'Authorization': 'KakaoAK {}'.format(KAKAO_KEY),  # Authorization 헤더
        'Content-Type': 'application/json'  # 필요에 따라 Content-Type 헤더 추가
    }

    result = json.loads(str(requests.get(url, headers=headers).text))
    return result

def finding_road_send_request(long, lat): # 위, 경도 기반 도로명 주소 찾기
    url = 'https://dapi.kakao.com/v2/local/geo/coord2address?x={x}&y={y}'.format(x=long, y=lat)  # 요청을 보낼 API의 URL
    headers = {
        'Authorization': 'KakaoAK {}'.format(KAKAO_KEY),  # Authorization 헤더
        'Content-Type': 'application/json'  # 필요에 따라 Content-Type 헤더 추가
    }

    result = json.loads(str(requests.get(url, headers=headers).text))
    return result


def generate_random_location(lat, lon, radius):
    # 지구의 반지름 (킬로미터)
    R = 6371.0

    # 반경 내 랜덤 거리 (미터)
    random_distance = random.uniform(0, radius)
    
    # 랜덤 각도 (라디안)
    random_angle = random.uniform(0, 2 * math.pi)

    # 중심 좌표를 라디안으로 변환
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)

    # 새로운 좌표 계산
    new_lat_rad = math.asin(math.sin(lat_rad) * math.cos(random_distance / R) +
                            math.cos(lat_rad) * math.sin(random_distance / R) * math.cos(random_angle))
    new_lon_rad = lon_rad + math.atan2(math.sin(random_angle) * math.sin(random_distance / R) * math.cos(lat_rad),
                                       math.cos(random_distance / R) - math.sin(lat_rad) * math.sin(new_lat_rad))

    # 라디안 좌표를 다시 도 단위로 변환
    new_lat = math.degrees(new_lat_rad)
    new_lon = math.degrees(new_lon_rad)

    return new_lat, new_lon

def generate_license_number(): # 자동차 번호판 랜덤 생성
    # 숫자 2자리 또는 3자리 생성
    num_digits = random.choice([2, 3])
    digits = ''.join(random.choices(string.digits, k=num_digits))
    
    # 한글 문자 생성
    hangul = chr(random.choice(range(0xAC00, 0xD7A3)))

    # 숫자 4자리 생성
    last_digits = ''.join(random.choices(string.digits, k=4))

    license_number = f"{digits}{hangul}{last_digits}"
    return license_number
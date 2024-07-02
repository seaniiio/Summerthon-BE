from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.http import JsonResponse, HttpResponse

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

import requests
import json
from .models import *
from .serializer import *

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

@swagger_auto_schema(
        method="POST", 
        tags=["회원 api"],
        operation_summary="회원가입", 
        request_body=UserRegisterSerializer
)
@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = UserRegisterSerializer(data = request.data)

    if serializer.is_valid():
        serializer.save()
        return Response({'status':'201','message': 'All data added successfully'}, status=201)
    return Response({'status':'400','message':serializer.errors}, status=400)

@swagger_auto_schema(
        method="POST", 
        tags=["회원 api"],
        operation_summary="로그인", 
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_login_id': openapi.Schema(type=openapi.TYPE_STRING, description='User login ID'),
                'user_pwd': openapi.Schema(type=openapi.TYPE_STRING, description='User password'),
            }
        ),
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):

    user_login_id = request.data.get('user_login_id')
    user_pwd = request.data.get('user_pwd')

    user = User.objects.get(user_login_id = user_login_id)

    if user.check_password(user_pwd):
        token = RefreshToken.for_user(user)
        refresh_token = str(token)
        access_token = str(token.access_token)

        return Response({'status':'200', 'refresh_token': refresh_token,
                        'access_token': access_token, }, status=status.HTTP_200_OK)
    
    return Response({'status':'401', 'message': '아이디 또는 비밀번호가 일치하지 않습니다.'}, status=status.HTTP_401_UNAUTHORIZED)

@swagger_auto_schema(
        method="POST", 
        tags=["택시 api"],
        operation_summary="택시 생성", 
        request_body=TaxiSerializer
)
@api_view(['POST'])
@permission_classes([AllowAny])
def new_taxi(request):
    serializer = TaxiSerializer(data = request.data)

    if serializer.is_valid():
        serializer.save()
        return Response({'status':'201','message': 'All data added successfully'}, status=201)
    return Response({'status':'400','message':serializer.errors}, status=400)


# 도로명주소 -> 위,경도 변환 api
@swagger_auto_schema(
    method="POST", 
    tags=["주소 api"],
    operation_summary="위도, 경도 변환", 
    request_body = RoadAddressSerializer
)
@api_view(['POST'])
@permission_classes([AllowAny])
def coordinate(request):
    #road_address = request.data.get('road_address')
    serializer = RoadAddressSerializer(data = request.data)
    # api 호출

    if serializer.is_valid():
        road_address = serializer.data['road_address']

        url = 'https://dapi.kakao.com/v2/local/search/address?query={address}'.format(address=road_address)  # 요청을 보낼 API의 URL
        headers = {
            'Authorization': 'KakaoAK {}'.format(KAKAO_KEY),  # Authorization 헤더
            'Content-Type': 'application/json'  # 필요에 따라 Content-Type 헤더 추가
        }

        result = json.loads(str(requests.get(url, headers=headers).text))
        return Response({"road_address":road_address, "latitude":result["documents"][0]['y'], "longitude":result["documents"][0]['x']}, status=201)
    return Response({'status':'400','message':serializer.errors}, status=400)
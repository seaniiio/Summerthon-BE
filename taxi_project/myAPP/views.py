from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import *
from .serializer import *
from .utils import coordinate_send_request

################################################################
# api 1 : 회원가입 

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

################################################################


################################################################
# api 2 : 로그인 

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

################################################################


################################################################
# api 3 : 택시 생성

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

################################################################


################################################################
# api 4 : 도로명주소 -> 위,경도 변환 api
@swagger_auto_schema(
    method="POST", 
    tags=["주소 api"],
    operation_summary="위도, 경도 변환", 
    request_body = RoadAddressSerializer
)
@api_view(['POST'])
@permission_classes([AllowAny])
def coordinate(request):
    serializer = RoadAddressSerializer(data = request.data)
    # api 호출

    if serializer.is_valid():
        road_address = serializer.data['road_address']
        result = coordinate_send_request(road_address)
        return Response({"road_address":road_address, "latitude":result["documents"][0]['y'], "longitude":result["documents"][0]['x']}, status=201)
    return Response({'status':'400','message':serializer.errors}, status=400)

################################################################


################################################################
# api 5 : 회원 정보 조회

@api_view(['GET'])
@permission_classes([AllowAny])
def user_info(request, user_login_id):
    try:
        user = User.objects.get(user_login_id=user_login_id)
    except User.DoesnotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    #user serializer
    user_serializer = UserInfoSerializer(user)

#대표 보호자 정보 받아오기 (이름, 연락처)
    represent_protector = Protector.objects.get(user_id=user, is_represent_protector=True)
    represent_protector_serializer = ProtectorRegisterSerializer(represent_protector)

#대표 주소 정보 받아오기 (도로명주소)
    represent_address=Address.objects.get(user_id=user, is_represent_address=True)


    return Response({
        "user": user_serializer.data,
        "represent_protector": represent_protector_serializer.data,
        "represent_address": represent_address.road_address
    }, status=status.HTTP_200_OK)


################################################################
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
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='User password'),
            }
        ),
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):

    user_login_id = request.data.get('user_login_id')
    password = request.data.get('password')

    user = authenticate(user_login_id=user_login_id, password=password)

    if user is None:
        return Response({'status':'401', 'message': '아이디 또는 비밀번호가 일치하지 않습니다.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    token = RefreshToken.for_user(user)
    update_last_login(None, user)

    return Response({'status':'200', 'refresh_token': str(token),
                    'access_token': str(token.access_token), }, status=status.HTTP_200_OK)


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
# api 5 : 회원 정보 get api

@swagger_auto_schema(
    method="GET", 
    tags=["회원 api"],
    operation_summary="회원 정보 get", 
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info(request):
    
    user = request.user
    if user is None:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    #user serializer
    user_serializer = UserInfoSerializer(user)

#대표 보호자 정보 받아오기 (이름, 연락처)
    represent_protector = Protector.objects.get(user_id=user.id, is_represent_protector=True)
    represent_protector_serializer = ProtectorRegisterSerializer(represent_protector)

#대표 주소 정보 받아오기 (도로명주소)
    represent_address=Address.objects.get(user_id=user, is_represent_address=True)


    return Response({
        "user": user_serializer.data,
        "represent_protector": represent_protector_serializer.data,
        "represent_address": represent_address.road_address
    }, status=status.HTTP_200_OK)

################################################################

################################################################
# api 6 : 주소 목록 get api

@swagger_auto_schema(
    method="GET", 
    tags=["주소 api"],
    operation_summary="저장한 주소 get", 
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def addresses(request):
    user = request.user
    if user is None:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    addresses = Address.objects.filter(user_id=user.id)
    serializer = AddressInfoSerializer(addresses, many=True)
    return Response({"addresses": serializer.data})


################################################################


################################################################
# api 7 : 긴급 호출 메일 전송

@swagger_auto_schema(
    method="GET", 
    tags=["회원 api"],
    operation_summary="긴급 호출 api", 
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def urgent_call(request):
    user = request.user
    
    try:
        # 대표 보호자 정보 받아오기 (이름, 연락처, 이메일)
        represent_protector = Protector.objects.get(user_id=user, is_represent_protector=True)
        represent_protector_email = represent_protector.protector_email  # 보호자의 이메일 주소
        
        # 긴급 호출 내용 작성
        subject = 'SAFE-T 긴급 호출 알림'
        message = f'SAFE-T로부터의 긴급 알림입니다. \n{user.user_name}님의 보호자 {represent_protector.protector_name}님께 긴급 호출이 발생했습니다. \n즉시 연락해주시기 바랍니다.'
        from_email = 'SafeT@gmail.com'  # 발신자 이메일 주소
        
        # 이메일 전송
        send_mail(
            subject,
            message,
            from_email,
            [represent_protector_email],
            fail_silently=False,
        )
        
        return Response({'status': '200', 'message': '긴급 호출 이메일이 성공적으로 전송되었습니다.'}, status=status.HTTP_200_OK)
    except Protector.DoesNotExist:
        return Response({"error": "대표 보호자를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
################################################################

################################################################
# api 8 : 주소지 추가 api 
 
@swagger_auto_schema(
    method="POST", 
    tags=["회원 api"],
    operation_summary="주소지 추가 api", 
    request_body = AddressAddSerializer,
    manual_parameters=[
        openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer 토큰", type=openapi.TYPE_STRING),
    ]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def new_address(request):
    user_id = request.user.id
    data = request.data

    data['user_id'] = user_id
    latitude_and_longitude = coordinate_send_request(data["road_address"])
    data['latitude'] = round(float(latitude_and_longitude["documents"][0]['y']), 6)
    data['longitude'] = round(float(latitude_and_longitude["documents"][0]['x']), 6)

    serializer = AddressSerializer(data = request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'status':'200'}, status=status.HTTP_200_OK)
    return Response({'status':'400','message':serializer.errors}, status=400)

################################################################

    
################################################################
# api 9 : 보호자 추가 api 

@swagger_auto_schema(
    method="POST", 
    tags=["회원 api"],
    operation_summary="보호자 추가 api", 
    request_body = ProtectorAddSerializer
)
@api_view(['POST'])
def new_protector(request):
    user_id = request.user.id 
    data = request.data

    data['user_id'] = user_id

    serializer = ProtectorSerializer(data = request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'status':'200'}, status=status.HTTP_200_OK)
    return Response({'status':'400','message':serializer.errors}, status=400)
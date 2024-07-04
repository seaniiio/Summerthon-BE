from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail, EmailMultiAlternatives

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import base64
from email.mime.image import MIMEImage

from .models import *
from .serializer import *
from .utils import *

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
@authentication_classes([JWTAuthentication])
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
@authentication_classes([JWTAuthentication])
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
@authentication_classes([JWTAuthentication])
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
@authentication_classes([JWTAuthentication])
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

        with open('image/location.png', 'rb') as img_file:
            img_data_1 = img_file.read()
        
        with open('image/app_logo.png', 'rb') as img_file:
            img_data_2 = img_file.read()
        
        # 이메일 전송
        email = EmailMultiAlternatives(
            subject,
            message,
            from_email,
            [represent_protector_email]
        )
        
        # HTML 본문 작성
        html_content = f"""
        <img src="cid:app_logo" width="10%" alt="logo">
        <h3>SAFE-T로부터의 긴급 알림입니다.</h3>
        <p>{user.user_name}님의 보호자 {represent_protector.protector_name}님께 긴급 호출이 발생했습니다.</p>
        <p>즉시 연락해주시기 바랍니다.</p>
        <p>긴급 호출을 전송한 사용자의 현재 위치입니다:</p>
        <img src="cid:location_map" alt="Map">
        """
        email.attach_alternative(html_content, "text/html")

        image1 = MIMEImage(img_data_1)
        image2 = MIMEImage(img_data_2)
        image1.add_header('Content-ID', '<location_map>')
        image2.add_header('Content-ID', '<app_logo>')
        email.attach(image1)
        email.attach(image2)

        email.send()
        
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
@authentication_classes([JWTAuthentication])
def new_address(request):
    user_id = request.user.id
    data = request.data

    data['user_id'] = user_id
    latitude_and_longitude = coordinate_send_request(data["road_address"])

    if latitude_and_longitude["meta"]["total_count"] == 0:
        return Response({'status':'400','message':"도로명 주소가 유효하지 않습니다."}, status=400)

    # 회원이 저장한 같은 이름의 주소지가 있는지 검사
    address_name = request.data.get('address_name') # address_name은 nullable이기 때문에 우선 data에 address_name이 존재하는지 검사
    if address_name:
        taxis = Address.objects.filter(user_id=user_id, address_name=address_name)
        if taxis.exists():
            return Response({'status':'409','message':'중복된 이름의 주소가 이미 저장되어 있습니다.'}, status=409)

    # 회원이 저장한 같은 도로명 주소가 있는지 검사
    taxis = Address.objects.filter(user_id=user_id, road_address=data.get("road_address"))
    if taxis.exists():
        return Response({'status':'409','message':'중복된 도로명주소가 이미 저장되어 있습니다.'}, status=409)

    data['latitude'] = round(float(latitude_and_longitude["documents"][0]['y']), 6)
    data['longitude'] = round(float(latitude_and_longitude["documents"][0]['x']), 6)

    serializer = AddressSerializer(data = request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'address':serializer.data, 'status':'200'}, status=status.HTTP_200_OK)
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
@authentication_classes([JWTAuthentication])
@api_view(['POST'])
def new_protector(request):
    user_id = request.user.id 
    data = request.data

    data['user_id'] = user_id

    # 회원이 저장한 같은 이름의 보호자가 있는지 검사
    protector_name = request.data.get('protector_name') # address_name은 nullable이기 때문에 우선 data에 address_name이 존재하는지 검사
    protectors = Protector.objects.filter(user_id=user_id, protector_name=protector_name)
    if protectors.exists():
        return Response({'status':'409','message':'중복된 이름의 보호자가 이미 저장되어 있습니다.'}, status=409)

    serializer = ProtectorSerializer(data = request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'protector':serializer.data, 'status':'200'}, status=status.HTTP_200_OK)
    return Response({'status':'400','message':serializer.errors}, status=400)

################################################################

################################################################
# api 10 : 택시 목록 조회 api

@swagger_auto_schema(
    method="GET", 
    tags=["택시 api"],
    operation_summary="택시 목록 get", 
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
def taxies(request):
    user = request.user
    if user is None:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    taxis = Taxi.objects.all()
    serializer = TaxiSerializer(taxis, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

################################################################
# api 11 : 가까운 택시 조회 api

def nearby_taxi(request):
    user = request.user
    if user is None:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    taxis = Taxi.objects.all()
    origin_list = []

    for taxi in taxis:
        origin_str = f"{str(taxi.longitude)},{str(taxi.latitude)}"
        origin_list.append((taxi.id, origin_str))
    
    distance_list = []
    for origin in origin_list:
        print("출발지:", origin[1])
        result = finding_way_send_request(origin[1])

        if result["routes"][0]["result_code"] == 0: # 길찾기 성공한 경우에만
            distance = result["routes"][0]["summary"]["distance"] # 예상 거리
            fair = result["routes"][0]["summary"]["fare"]['taxi'] # 예상 요금
            duration = result["routes"][0]["summary"]["duration"] # 예상 시간

            distance_list.append((origin[0], distance, fair, duration)) # (택시 id, 거리, 요금, 시간)

    print("distance_list:", distance_list)
    
    # sort
    distance_list.sort(key = lambda x : x[1])
    print("distance_list:", distance_list)

    nearby_taxi_id = distance_list[0][0]
    nearby_taxi = Taxi.objects.get(id = nearby_taxi_id)

    serializer = TaxiSerializer(nearby_taxi)

    return Response({"taxi": serializer.data, "distance":distance_list[0][1], "fair":distance_list[0][2], "duration":distance_list[0][3]}, status=status.HTTP_200_OK)
    
    ################################################################

    ################################################################
    # api 12 : 택시 호출 api

    # 인하대 근처의 주소 중, 랜덤하게 3개의 택시 생성 후 return (가장 가까운 taxi는 표기)

@swagger_auto_schema(
    method="POST", 
    tags=["택시 api"],
    operation_summary="출발지 근처 3개의 택시 get", 
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'destination_address': openapi.Schema(type=openapi.TYPE_STRING, description='User login ID'),
        }
    )
)
@api_view(['POST'])
def call_taxi(request):
    user = request.user
    destination_address = request.data.get('destination_address')
    if user is None:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    # 기존에 존재하던 택시 데이터 삭제
    Taxi.objects.all().delete()

    # 저장한 인하대 위, 경도
    center_lat = 37.4482020408321
    center_lon = 126.651415033662
    radius_km = 1.0  # 반경 1KM

    for i in range(1,4): # 3대의 택시 생성
        # 랜덤 데이터 생성
        driver_name = '운전자' + str(i)
        license_number = generate_license_number()
        driver_phone = "010-0000-0000"
        acceptance = 1

        new_lat, new_lon = generate_random_location(center_lat, center_lon, radius_km)

        taxi_data = {
            "driver_name" : driver_name,
            "license_number" : license_number,
            "driver_phone" : driver_phone,
            "acceptance" : acceptance,
            "latitude" : str(new_lat),
            "longitude" : str(new_lon)
        }
        
        # 그에 대한 택시 생성
        serializer = TaxiSerializer(data = taxi_data)
        if serializer.is_valid():
            print("taxi 생성")
            serializer.save()
        else:
            return Response(serializer.errors, status=400)
    
    taxis = Taxi.objects.all()
    print("taxis:", taxis)
    origin_list = []

    for taxi in taxis:
        origin_str = f"{str(taxi.longitude)},{str(taxi.latitude)}"
        origin_list.append((taxi.id, origin_str))
    
    distance_list = []
    for origin in origin_list:
        print("출발지:", origin[1])
        result = finding_way_send_request(origin[1])

        if result["routes"][0]["result_code"] == 0: # 길찾기 성공한 경우에만
            distance = result["routes"][0]["summary"]["distance"] # 예상 거리
            fair = result["routes"][0]["summary"]["fare"]['taxi'] # 예상 요금
            duration = result["routes"][0]["summary"]["duration"] # 예상 시간

            distance_list.append((origin[0], distance, fair, duration)) # (택시 id, 거리, 요금, 시간)

    # distance 기준으로 sort
    distance_list.sort(key = lambda x : x[1])

    return_data = []

    for i in range(3):
        taxi_id = distance_list[i][0]
        taxi = Taxi.objects.get(id = taxi_id)
        serializer = TaxiSerializer(taxi)
        print(serializer.data)
        return_data.append(serializer.data)

    # 출발지부터 도착지까지의 비용
    # destination의 위, 경도
    dest_coordinate = coordinate_send_request(destination_address)
    dest_long, dest_lat = dest_coordinate["documents"][0]['x'], dest_coordinate["documents"][0]['y']
    dest_str = f"{str(dest_long)},{str(dest_lat)}"
    from_origin_to_dest = finding_way_send_request(dest_str)

    total_fair = from_origin_to_dest["routes"][0]["summary"]["fare"]['taxi']

    return Response({"taxi": return_data, "fair":total_fair, "duration":distance_list[0][3]}, status=status.HTTP_200_OK)
        

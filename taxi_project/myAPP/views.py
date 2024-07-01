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

from .models import *
from .serializer import *

@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):

    user_data = request.data.get('user')
    protector_data = request.data.get('protector')
    address_data = request.data.get('address')

    # User 데이터 저장
    user_serializer = UserSerializer(data=user_data)
    if user_serializer.is_valid():
        user = user_serializer.save()
        user.set_password(request.data.get('password'))
        user.save()
    else:
        return Response({'status':'400','message':user_serializer.errors}, status=400)

    # Protector 데이터 저장 (유저와 연결)
    protector_data['user_id'] = user.id  # 유저 ID를 연결
    protector_serializer = ProtectorSerializer(data=protector_data)
    if protector_serializer.is_valid():
        protector_serializer.save()
    else:
        return Response({'status':'400','message':protector_serializer.errors}, status=400)

    # Address 데이터 저장 (유저와 연결)

    #지금 이렇게 작성해두긴 했는데, 위도, 경도는 입력받은 도로명주소로 지도 api 호출해서 리턴받은 후 작성해야될듯. 
    
    address_data['user_id'] = user.id  # 유저 ID를 연결
    address_serializer = AddressSerializer(data=address_data)
    if address_serializer.is_valid():
        address_serializer.save()
    else:
        return Response({'status':'400','message':address_serializer.errors}, status=400)

    return Response({'status':'201','message': 'All data added successfully'}, status=201)


from rest_framework import serializers
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class ProtectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Protector
        fields = '__all__'

class ProtectorAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = Protector
        fields = ['protector_name', 'protector_email']

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'

class AddressAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['road_address', 'detail_address']


class ProtectorRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Protector
        fields = ['protector_name', 'protector_email', 'is_represent_protector']

class AddressRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['address_name', 'road_address', 'detail_address', 'is_represent_address']

class AddressInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['address_name', 'road_address', 'latitude', 'longitude']

class UserRegisterSerializer(serializers.Serializer):
    user = UserSerializer()
    protector = ProtectorRegisterSerializer()
    address = AddressRegisterSerializer()

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        protector_data = validated_data.pop('protector')
        address_data = validated_data.pop('address')

        user = User.objects.create(**user_data)
        user.set_password(user_data['password'])
        user.save()

        Protector.objects.create(user_id=user, **protector_data)
        Address.objects.create(user_id=user, **address_data)
       
        return user


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('user_name', 'user_age', 'user_gender')
        
class TaxiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Taxi
        fields = '__all__'

class RoadAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ('road_address', )
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.auth.hashers import make_password, check_password

class User(models.Model) : 
    # default : (null=False, blank=False)

    # 자동으로 설정되는 id랑 헷갈릴까봐 일단 변수 이름을 user_login_id로 설정했음!
    user_login_id = models.CharField(max_length=15, unique=True)
    user_pwd = models.CharField(max_length=20)
    user_name = models.CharField(max_length=5)
    #나이 범위 제한 1~100
    user_age = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)]) 

    gender_choices=[
        ('M', '남자'),
        ('F', '여자')
    ]
    user_gender = models.CharField(max_length=1, choices=gender_choices)
    #정규식으로 유효성 검사
    user_phone = models.CharField(
        max_length=13,
        validators=[RegexValidator(regex=r'^010-\d{4}-\d{4}$', message='올바른 연락처 형식이 아닙니다.')]
    )

    def set_password(self, raw_password):
        self.user_pwd = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.user_pwd)

    def __str__(self):
        return self.user_name


class Protector(models.Model) :
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="protectors", verbose_name="User") 
    protector_name = models.CharField(max_length=10, null=True, blank=True)

    ###########################################
    #알림 전송 테스트 할 땐 이메일로 변경 필요.
    protector_phone = models.CharField(
        max_length=13,
        validators=[RegexValidator(regex=r'^010-\d{4}-\d{4}$', message='올바른 연락처 형식이 아닙니다.')]
    )
    ############################################

    is_represent_protector = models.BooleanField(default=False)



    def save(self, *args, **kwargs):
        #보호자 default 이름을 보호자1, 보호자2, 보호자3 ... 과 같이 설정하는 함수
        if not self.protector_name:
            protector_count = Protector.objects.filter(user_id=self.user_id).count() + 1
            self.protector_name = f'보호자 {protector_count}'
        super().save(*args, **kwargs)

        # 최초 등록된 보호자를 대표로 설정
        if Protector.objects.filter(user_id=self.user_id, is_represent_protector=True).count() == 0:
            self.is_represent_protector = True
            self.save(update_fields=['is_represent_protector'])
        elif self.is_represent_protector:
            Protector.objects.filter(user_id=self.user_id, is_represent_protector=True).exclude(id=self.id).update(is_represent_protector=False)

    def __str__(self) : 
        return self.protector_name

class Address(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses", verbose_name="User")
    address_name = models.CharField(max_length=10, null=True, blank=True)
    #프론트에서 입력받은 도로명주소 저장
    road_address = models.CharField(max_length=200, null=True)
    #상세주소
    detail_address = models.CharField(max_length=200, null=True, blank=True)
    #위도. decimal(10,6)
    latitude = models.DecimalField(max_digits=10, decimal_places=6)
    #경도. decimal(10,6)
    longitude = models.DecimalField(max_digits=10, decimal_places=6)

    is_represent_address = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.address_name:
            address_count = Address.objects.filter(user_id=self.user_id).count() + 1
            self.address_name = f'주소지 {address_count}'
        
        super().save(*args, **kwargs)

        if Address.objects.filter(user_id=self.user_id, is_represent_address=True).count() == 0:
            self.is_represent_address = True
            self.save(update_fields=['is_represent_address'])
        elif self.is_represent_address:
            Address.objects.filter(user_id=self.user_id, is_represent_address=True).exclude(id=self.id).update(is_represent_address=False)

    def __str__(self):
        return self.address_name

class Taxi(models.Model):
    license_number = models.CharField(max_length=10)
    # 택시 위도 - 고정
    latitude = models.DecimalField(max_digits=10, decimal_places=6)
    # 택시 경도 - 고정
    longitude = models.DecimalField(max_digits=10, decimal_places=6)
    driver_name = models.CharField(max_length=5)
    driver_phone = models.CharField(
        max_length=13,
        validators=[RegexValidator(regex=r'^010-\d{4}-\d{4}$', message='올바른 연락처 형식이 아닙니다.')]
    )
    acceptance = models.IntegerField(default = 0)

    def __str__(self):
        return self.license_number
# 서버 실행 방법

## 1. 가상환경 설정

### 가상환경 생성

python3 -m venv hackenv

### 가상환경 실행

source hackenv/bin/activate

### 가상환경에 requirements.txt 목록 설치(requirements.txt 존재하는 경로에서 명령어 입력)

pip install -r requirements.txt

## 2. 장고 서버 실행

### manage.py 존재하는 경로에서 아래의 명령어 입력

python manage.py runserver

## 3. swagger로 데이터 입출력 확인

http://localhost:8000/swagger/ 접속 후 테스트

# swagger 테스트 방법

## 1. 테스트용 회원 생성

## 2. 로그인 후 access_token 복사

## 3. authorize버튼 클릭 후, Bearer + access_token 입력

ex) Bearer ewieufowi~

## 4. 인증 필요한 api 테스트

## Team members

1. 김정대
2. 권오준
3. 이윤혁

## Purpose

떠오르는 아이디어가 있지만 도면이나 그림으로 바로 나타내기 어려운 사람이 손쉽게 모델링하여 확인할 수 있도록 함

## High Level Design

- 스케치한 도면과 키워드를 입력
    - 도면과 키워드에 따라 새로운 이미지 생성
- 생성된 이미지를 객체만 추출하여 3D 모델링
- 추가로 음악 키워드 입력시 원하는 분위기에 맞는 BGM 생성

![Untitled](https://prod-files-secure.s3.us-west-2.amazonaws.com/c08abce7-a3c3-4a9f-ae00-a86e9d3f60f8/616a4f3c-bc77-4a42-9c41-d0fc52c5d815/Untitled.jpeg)

## Github link

https://github.com/jd6286/SH2GH

## Prerequite

```python
python3 -m venv sh2gh
source sh2gh/bin/activate
git clone https://github.com/GaParmar/img2img-turbo.git
# Install requirements
pip3 install -U pip
pip3 install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
```

## Model Excute

```python
python main.py
```

## Result
- 실행 화면

![Untitled](/home/ubuntu/Downloads/output(1).png)

- 입력 이미지
    
    ![Untitled](https://prod-files-secure.s3.us-west-2.amazonaws.com/c08abce7-a3c3-4a9f-ae00-a86e9d3f60f8/6225bf4a-ef12-4051-acd2-725e5afa376a/8d83ad79-74a7-474c-bee7-d14106c38209.png)
    

- 출력 파일
    
    ![Untitled](https://prod-files-secure.s3.us-west-2.amazonaws.com/c08abce7-a3c3-4a9f-ae00-a86e9d3f60f8/91b1f3ae-6959-4e0c-9e7e-1d7d46785565/Untitled.png)

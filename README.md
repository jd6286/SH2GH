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

![image](https://github.com/user-attachments/assets/bd288edd-efe8-4819-b841-4c0b7b2d068d)


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
- GUI

![image](https://github.com/user-attachments/assets/5857b45f-1c38-4090-904e-bf8af0ba18ee)

- 원본 이미지

![image](https://github.com/user-attachments/assets/20e3fcba-eff1-4cfe-b76f-9e63b6c566a5)


- 3D 이미지
  
![image](https://github.com/user-attachments/assets/0d078229-147f-41ff-9161-6c8dcd1f5da2)


## Demo

https://drive.google.com/file/d/12uHbnKXtz3ksCBNqbf-WtNpigkmD6zYF/view


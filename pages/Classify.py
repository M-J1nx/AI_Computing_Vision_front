import streamlit as st
import cv2
import os
import random
import shutil
import time
import json
import numpy as np
import boto3  # AWS SDK
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from torchvision import transforms
from PIL import Image
import io
import base64


# Streamlit 페이지 설정
st.set_page_config(page_title="NG/OK Classification", layout="centered", page_icon="🔍")


# SNS 클라이언트 초기화
def initialize_sns_client():
    """
    AWS SNS 클라이언트를 초기화합니다.
    """
    try:
        sns_client = boto3.client('sns', region_name='us-east-1')  # AWS 리전 설정
        return sns_client
    except (NoCredentialsError, PartialCredentialsError) as e:
        st.error("AWS 인증 정보가 유효하지 않습니다. AWS CLI를 통해 인증 정보를 설정하세요.")
        return None
    

def send_sns_message(topic_arn, subject, message):
    """
    AWS SNS를 사용해 메시지를 전송하는 함수
    - topic_arn: SNS Topic ARN
    - subject: 메시지 제목
    - message: 메시지 본문
    """
    try:
        sns_client = boto3.client("sns")
        response = sns_client.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        print(f"SNS 메시지가 성공적으로 전송되었습니다. Message ID: {response['MessageId']}")
    except NoCredentialsError:
        print("AWS 자격 증명이 설정되지 않았습니다.")
    except PartialCredentialsError:
        print("AWS 자격 증명이 불완전합니다.")
    except Exception as e:
        print(f"SNS 메시지 전송 중 오류 발생: {e}")



# 엔드포인트 호출 시민리얼리션
def call_sagemaker_model(endpoint_name, frames):
    """
    SageMaker 엔드포인트 호출
    - endpoint_name: SageMaker 엔드포인트 이름
    - frames: 이미지 파일 경로 리스트
    """
    sagemaker_runtime = boto3.client('sagemaker-runtime', region_name='us-east-1')
    results = []
    
    for frame in frames:
        # 이미지 파일을 Base64로 인코딩
        with open(frame, "rb") as image_file:
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

        # JSON 페이로드 생성
        payload = {
            "image": image_base64
        }

        try:
            # SageMaker 엔드포인트 호출
            response = sagemaker_runtime.invoke_endpoint(
                EndpointName=endpoint_name,
                ContentType="application/json",
                Body=json.dumps(payload)
            )
            result = json.loads(response["Body"].read().decode("utf-8"))
            results.append({"frame": frame, "prediction": result["prediction"], "confidence": result["confidence"]})
        except Exception as e:
            print(f"SageMaker 엔드포인트 호출 중 오류 발생: {e}")
            results.append({"frame": frame, "prediction": "Error", "confidence": 0})
    
    return results





def input_fn(request_body, request_content_type):
    """
    SageMaker 엔드포인트가 호출되었을 때 입력 데이터를 처리하는 함수입니다.
    - request_body: 요청 본문 데이터
    - request_content_type: 요청 데이터의 MIME 타입
    """
    if request_content_type == "application/x-image":
        image = Image.open(io.BytesIO(request_body))

        # 이미지 전처리 정의
        transform = transforms.Compose([
            transforms.Resize((224, 224)),  # 모델 입력 크기로 조정
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        return transform(image).unsqueeze(0)
    else:
        raise ValueError(f"지원되지 않는 콘텐츠 타입입니다: {request_content_type}")



# dynamodb에 최종 결과 업로드
def upload_to_dynamodb_from_session_state(table_name, data):
    """
    Streamlit 세션 상태에서 DynamoDB로 데이터를 업로드하는 함수.
    - table_name: DynamoDB 테이블 이름
    - data: 업로드할 데이터 (Python 리스트)
    """
    try:
        dynamodb_client = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb_client.Table(table_name)

        for item in data:
            # 최종 결과를 0 (OK) 또는 1 (NG)으로 변환
            final_result_numeric = 1 if item["final_result"] == "NG" else 0

            # DynamoDB에 저장할 데이터 형태로 변환
            table.put_item(Item={
                "product_id": int(item["product_id"]),  # Partition Key로 사용
                "final_result": final_result_numeric,
                "frames": json.dumps(item["frames"])  # 리스트를 JSON 문자열로 변환
            })

        print("DynamoDB에 데이터가 성공적으로 업로드되었습니다.")
        st.success("DynamoDB에 데이터가 업로드되었습니다!")
    except Exception as e:
        print(f"DynamoDB 업로드 중 오류 발생: {e}")
        st.error(f"DynamoDB 업로드 중 오류 발생: {e}")



# 타이틀과 설명
st.title("숙명 다이캐스팅 OK/NG 분류")

# 영상 업로드 UI
uploaded_file = st.file_uploader("테스트 영상 선택", type=["mp4", "avi", "mov"])
info_placeholder = st.empty() #수정된 부분: 문구 표시 카는
info_placeholder2 = st.empty() #수정된 부분: 프레임 개수
progress_bar = st.progress(0) #수정된 부분: 로딩바


def manage_frames_folder(folder_name="temp_frame"):
    """
    프레임 폴더를 관리하는 함수.
    - 폴더가 없으면 생성.
    - 폴더가 있으면 삭제 후 새로 생성.
    """
    if os.path.exists(folder_name):
        print(f"기존 폴더 '{folder_name}'가 존재합니다. 삭제 중...")
        shutil.rmtree(folder_name)  # 기존 폴더 삭제
    print(f"새 폴더 '{folder_name}' 생성 중...")
    os.makedirs(folder_name)  # 새 폴더 생성
    return folder_name



def extract_frames(video_path, folder_name="temp_frame", threshold=20, brightness_threshold=240):
    """
    화면이 변할 때마다 프레임을 저장하는 함수.
    - "출력중" 화면(빈 화면)을 제거합니다.
    - 첫 번째 프레임은 무조건 저장합니다.
    """
    # 프레임 폴더 관리
    frames_folder = manage_frames_folder(folder_name)

    cap = cv2.VideoCapture(video_path)
    prev_frame = None
    frames = []
    global product_count
    count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 그레이스케일 변환 (밝기 계산용)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 밝기 평균 계산 (빈 화면 감지)
        mean_brightness = np.mean(gray_frame)
        if mean_brightness > brightness_threshold:
            # 빈 화면("촬영 중")으로 간주하고 건너뜀
            continue

        # 첫 번째 프레임은 무조건 저장
        if prev_frame is None:
            frame_filename = os.path.join(frames_folder, f"frame_{count}.jpg")
            cv2.imwrite(frame_filename, frame)
            frames.append(frame_filename)
            count += 1
        else:
            # 이전 프레임과 비교하여 변화 감지
            if prev_frame.shape == gray_frame.shape:  # 크기 확인
                diff = cv2.absdiff(prev_frame, gray_frame)
                diff_mean = diff.mean()

                if diff_mean > threshold:  # 변화량이 임계값 초과 시 저장
                    frame_filename = os.path.join(frames_folder, f"frame_{count}.jpg")
                    cv2.imwrite(frame_filename, frame)
                    frames.append(frame_filename)
                    count += 1
            else:
                print("프레임 크기가 일치하지 않아 비교를 건너뜁니다.")

        # 이전 프레임 업데이트
        prev_frame = gray_frame

    product_count = count
    cap.release()
    print(f"총 {len(frames)}개의 프레임이 저장되었습니다.")
    return frames






# 제품별 결과 종합
def aggregate_results(mock_results, frames_per_product=5):
    """
    5개의 각도 이미지 결과를 종합하여 제품의 최종 NG/OK를 판단합니다.
    """
    if os.path.exists("database.txt"):
        with open('database.txt', 'r') as file:
            m = int(file.read().strip())
    else:
        with open('database.txt', 'w') as file:
            file.write("1")
        m = 0

    aggregated_results = []
    num_products = len(mock_results) // frames_per_product

    for i in range(num_products):
        progress_bar.progress(0.5 + 0.5*((i+1)/num_products))
        product_frames = mock_results[i * frames_per_product:(i + 1) * frames_per_product]
        product_result = {
            "product_id": m + 1, #db에서 가져온 m
            "frames": product_frames,
            "final_result": any(frame["prediction"] == 1 for frame in product_frames)
        }
        m += 1
        aggregated_results.append(product_result)
    #m업로드

    with open('database.txt', 'w') as file:
        file.write(str(m))

    return aggregated_results



def save_results_to_json(results, file_path="results.json"):
    """
    판정 결과를 JSON 파일로 저장합니다.
    """
    try:
        # JSON 직렬화 가능 형태로 변환
        json_serializable_results = [
            {
                "product_id": product["product_id"],
                "final_result": "NG" if product["final_result"] else "OK",
                "frames": [
                    {"frame_path": frame["frame"], "prediction": "NG" if frame["prediction"] else "OK"}
                    for frame in product["frames"]
                ]
            }
            for product in results
        ]
        with open(file_path, "w") as f:
            json.dump(json_serializable_results, f, indent=4)
        print(f"JSON 결과가 '{file_path}'에 성공적으로 저장되었습니다.")
    except Exception as e:
        print(f"JSON 저장 중 오류 발생: {e}")




# 영상 처리 및 결과 표시
if uploaded_file is not None:
    # 업로드된 영상을 로컴에 저장
    video_path = os.path.join("temp_video.mp4")
    with open(video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # 영상 미리보기
    st.video(video_path)

    if st.button("시작 버튼 "):
        try:
            # Step 0: SNS로 "테스트 시작" 메시지 전송
            topic_arn = "arn:aws:sns:us-east-1:730335373015:smwu-cv-08-test"
            send_sns_message(
                topic_arn,
                subject="테스트 시작 알림",
                message="테스트가 시작되었습니다. 업로드된 영상에 대한 검사가 진행 중입니다."
            )

            global aggregated_results
            # Step 1: 프레임 추적
            info_placeholder.info("프레임 추적 중")
            frames = extract_frames(video_path)
            info_placeholder.empty() #수정된 부분: 문구 업데이트화
            info_placeholder2.info(f"총 {len(frames)}개의 프레임이 추작되었습니다.")
            print("1단계끝")

            # Step 2: 엔드포인트 호출 (배치 처리)
            info_placeholder.info("모델 호출 중")
            batch_results = call_sagemaker_model('die-casting-endpoint',frames)  # 배치 결과 호출
            if batch_results is None:
                st.error("모델 호출 중 오류가 발생했습니다.")
                # return

            # 프레임별 결과 매핑
            mock_results = [
                {"frame": frames[i], "prediction": 1 if result["class"] == "NG" else 0}
                for i, result in enumerate(batch_results)
            ]

            info_placeholder.empty()
            print("2단계 끝")

            # Step 3: 제품별 결과 종합 및 Session State 저장
            info_placeholder.info("결과 종합 중")
            aggregated_results = aggregate_results(mock_results)
            st.session_state["aggregated_results"] = aggregated_results  # 결과를 Session State에 저장
            info_placeholder.empty()
            print("3단계끝")

            # Step 4: 결과 표시
            if "aggregated_results" in st.session_state:
                for product in st.session_state["aggregated_results"]:
                    st.subheader(f"제품 ID: {product['product_id']}")
                    st.write(f"최종 결과: {'❌ NG (불량)' if product['final_result'] else '✅ OK (양품)'}")
                    for frame in product["frames"]:
                        st.write(f"  - 프레임 {frame['frame']} 예측: {'❌ NG' if frame['prediction'] else '✅ OK'}")
                info_placeholder2.empty()
            else:
                st.warning("결과가 없습니다. '시작 버튼'을 눌러 테스트를 실행하세요.")


            # Step 5: 폴더 삭제
            # shutil.rmtree("temp_frame")
            print("5단계끝")
            
        except Exception as e:
            st.error(f"오류 발생: {e}")
    

    if st.button("테스트 종료 및 결과 알림"):
        try:
            if "aggregated_results" in st.session_state and st.session_state["aggregated_results"]:
                # # JSON 파일 저장
                save_results_to_json(st.session_state["aggregated_results"], "results.json")

                # DynamoDB로 업로드
                table_name = "NG_OK_Results"
                upload_to_dynamodb_from_session_state('smwu-cv8', st.session_state["aggregated_results"])

                # 최종 결과 요약
                total_products = len(st.session_state["aggregated_results"])
                ng_products = sum(1 for product in st.session_state["aggregated_results"] if product["final_result"])

                # SNS로 "테스트 종료" 메시지 전송
                topic_arn = "arn:aws:sns:us-east-1:730335373015:smwu-cv-08-test"
                message = (
                    f"테스트가 완료되었습니다.\n"
                    f"검사된 총 제품 수: {total_products}\n"
                    f"불량(NG)으로 판정된 제품 수: {ng_products}\n"
                )
                send_sns_message(
                    topic_arn,
                    subject="테스트 종료 알림",
                    message=message
                )

                st.success("결과 알림이 SNS로 전송되었습니다!")
            else:
                st.warning("먼저 '시작 버튼'을 눌러 결과를 생성하세요.")
        except Exception as e:
            st.error(f"SNS 메시지 전송 중 오류 발생: {e}")



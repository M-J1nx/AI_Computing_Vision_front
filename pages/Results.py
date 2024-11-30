import streamlit as st
import boto3

# AWS 클라이언트 설정 (자격 증명은 환경 변수나 AWS 설정 파일을 사용)
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')

# DynamoDB 테이블 및 S3 버킷 이름
table_name = 'ProductsResults_jj'
bucket_name = 'sagemaker-us-east-1-730335373015'
folder_name = 'temp_frame_test_f/'  # S3 버킷 내 폴더 경로 (마지막에 슬래시 포함)

# DynamoDB에서 데이터 가져오기
def fetch_data_from_dynamodb():
    table = dynamodb.Table(table_name)
    response = table.scan()
    items = response['Items']

    list_final_1 = []
    list_final_0 = []

    # S3 URL 생성 함수
    def get_s3_url(frame_path):
        full_path = f"{folder_name}{frame_path}"  # 폴더 경로 포함
        return s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': full_path},
            ExpiresIn=3600  # URL 만료 시간 (초)
        )
    
    # 데이터 파싱
    for item in items:
        product_id = item["product_id"]
        final_result = item["final_result"]
        frames = []
        for frame in item["frames"]:
            if isinstance(frame, str):
                frame_path = frame
                prediction = None  # prediction 데이터가 없는 경우
            elif "frame_path" in frame and "prediction" in frame:
                frame_path = frame["frame_path"]
                prediction = int(frame["prediction"])
            else:
                st.write(f"Unexpected frame format: {frame}")
                continue

            frames.append({
                "frame_path": frame_path,
                "prediction": prediction,
                "url": get_s3_url(frame_path)
            })
        
        parsed_item = {
            "product_id": product_id,
            "final_result": final_result,
            "frames": frames
        }
        if final_result == 1:
            list_final_1.append(parsed_item)
        else:
            list_final_0.append(parsed_item)
    
    # 정렬: product_id 기준으로 오름차순 정렬
    list_final_1 = sorted(list_final_1, key=lambda x: x["product_id"])
    list_final_0 = sorted(list_final_0, key=lambda x: x["product_id"])
    
    return list_final_1, list_final_0

# DynamoDB 업데이트 함수
def update_dynamodb_final_result(product_id, new_final_result):
    """DynamoDB에서 final_result 값을 업데이트"""
    table = dynamodb.Table(table_name)
    try:
        table.update_item(
            Key={
                "product_id": product_id  # Partition Key만 제공
            },
            UpdateExpression="SET final_result = :val",  # 일반 속성 업데이트
            ExpressionAttributeValues={
                ":val": new_final_result  # 새로운 final_result 값
            }
        )
        st.success(f"Product ID {product_id}의 final_result가 {new_final_result}로 업데이트되었습니다.")
    except Exception as e:
        st.error(f"Error updating item: {e}")

# 페이지 내용
st.title("📊 분석 결과")

# 데이터 가져오기
list_final_1, list_final_0 = fetch_data_from_dynamodb()

# 화면 전환 버튼
col1, col2 = st.columns(2)
with col1:
    if st.button("🔴 NG 리스트 보기"):
        st.session_state.current_view = "NG"
with col2:
    if st.button("🟢 OK 리스트 보기"):
        st.session_state.current_view = "OK"

# 초기 화면 설정
if "current_view" not in st.session_state:
    st.session_state.current_view = "NG"  # 기본 화면은 NG 리스트

# NG 리스트 화면
if st.session_state.current_view == "NG":
    st.header("🔴 NG 리스트")
    for item in list_final_1:
        st.subheader(f"물품 ID: {item['product_id']}")
        if st.button(f"수정 (OK로 변경)", key=f"ng_{item['product_id']}"):
            new_result = 0  # NG에서 OK로 변경
            update_dynamodb_final_result(item['product_id'], new_result)
            st.session_state.updated = True  # 업데이트 상태 저장

        # 5개 이미지를 가로로 표시
        cols = st.columns(5)
        for i, frame in enumerate(item["frames"]):
            with cols[i]:
                st.image(frame["url"], use_container_width=True)
                if frame["prediction"] == 1:
                    st.markdown(
                        f"<span style='color:red;'>NG</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown("OK")

# OK 리스트 화면
elif st.session_state.current_view == "OK":
    st.header("🟢 OK 리스트")
    for item in list_final_0:
        st.subheader(f"물품 ID: {item['product_id']}")
        if st.button(f"수정 (NG로 변경)", key=f"ok_{item['product_id']}"):
            new_result = 1  # OK에서 NG로 변경
            update_dynamodb_final_result(item['product_id'], new_result)
            st.session_state.updated = True  # 업데이트 상태 저장

        # 5개 이미지를 가로로 표시
        cols = st.columns(5)
        for i, frame in enumerate(item["frames"]):
            with cols[i]:
                st.image(frame["url"], use_container_width=True)
                if frame["prediction"] == 1:
                    st.markdown(
                        f"<span style='color:red;'>NG</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown("OK")

# 업데이트 후 데이터 재로드
if st.session_state.get("updated", False):
    st.session_state.updated = False
    st.experimental_set_query_params(refresh="true")
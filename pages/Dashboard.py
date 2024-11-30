import streamlit as st
import boto3
import matplotlib.pyplot as plt
import os

# AWS DynamoDB 클라이언트 설정 (자격 증명은 환경 변수나 AWS 설정 파일을 사용)
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# DynamoDB 테이블 이름
table_name = 'ProductsResults_jj'

# DynamoDB 데이터 가져오기 함수
def fetch_ng_ok_ratios():
    """
    DynamoDB에서 NG와 OK 데이터를 가져와 비율 계산
    """
    table = dynamodb.Table(table_name)
    response = table.scan()
    items = response['Items']

    # NG와 OK 개수 계산
    ng_count = sum(1 for item in items if item["final_result"] == 1)
    ok_count = sum(1 for item in items if item["final_result"] == 0)

    return ng_count, ok_count

# NG/OK 비율 시각화 함수
def visualize_ng_ok_ratios(ng_count, ok_count):
    """
    NG와 OK 비율을 원형 차트로 시각화
    """
    labels = ['NG', 'OK']
    sizes = [ng_count, ok_count]

    fig, ax = plt.subplots()
    ax.pie(
        sizes,
        labels=labels,
        autopct=lambda p: f"{p:.1f}%\n({int(p * sum(sizes) / 100)})",
        startangle=90,
        colors=['red', 'green']
    )
    ax.axis('equal')  # 원형 비율 유지
    st.pyplot(fig)

# 페이지 내용
st.title("📊 NG/OK 비율 대시보드")

# DynamoDB 데이터 가져오기
try:
    ng_count, ok_count = fetch_ng_ok_ratios()
except Exception as e:
    st.error(f"데이터를 가져오는 중 오류 발생: {e}")
else:
    # 데이터 시각화
    st.subheader("🔍 NG/OK 비율")
    visualize_ng_ok_ratios(ng_count, ok_count)

    # 추가 정보 표시
    total_count = ng_count + ok_count
    st.write(f"총 제품 수: **{total_count}**")
    st.write(f"🔴 NG: **{ng_count}**")
    st.write(f"🟢 OK: **{ok_count}**")
# 
import streamlit as st

# 페이지 설정
st.set_page_config(page_title="SM-Diecasting Application", layout="wide")


# 페이지 제목
st.title("SM-Diecasting Application")


# 시연 영상 업로드 및 재생
st.video("/Users/raeyoung/Desktop/AWS 컴퓨터 비전 /화면 기록 2024-11-30 오전 6.41.54.mov")  # 여기에 영상 URL 또는 로컬 경로 입력


# Classification 섹션
st.markdown("### How to use this application:")
st.markdown("""
<div style="background-color:#f9f9f9; padding:15px; border-radius:10px; margin-bottom:20px;">
    <h3 style="color:#4CAF50;">📂 Classification</h3>
    <ol>
        <li>검사할 동영상을 업로드 하세요.</li>
        <li>애플리케이션이 불량품을 검출해줄 것입니다.</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# Results 섹션
st.markdown("""
<div style="background-color:#eaf4fc; padding:15px; border-radius:10px; margin-bottom:20px;">
    <h3 style="color:#2196F3;">📊 Results</h3>
    <ol>
        <li>제품의 검사 결과를 확인하세요.</li>
        <li>검사 결과를 수정할 수 있습니다.</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# Dashboard 섹션
st.markdown("""
<div style="background-color:#fffbe6; padding:15px; border-radius:10px; margin-bottom:20px;">
    <h3 style="color:#FFC107;">📈 Dashboard</h3>
    <ol>
        <li>최종 결과를 확인하세요.</li>
        <li>검사 결과를 한눈에 시각화하였습니다.</li>
    </ol>
</div>
""", unsafe_allow_html=True)

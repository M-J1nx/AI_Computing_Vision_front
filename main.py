import streamlit as st
from moviepy import VideoFileClip
import tempfile
import os

# Set the page layout
st.set_page_config(layout="wide")

# Sidebar
with st.sidebar:
    st.header("MENU")

# 전체 레이아웃을 만들기 위해 컨테이너를 사용합니다.
col1, col2 = st.columns([1, 2])
i = 0

# 기본 영상 길이 (초 단위)
video_duration = 600  # 업로드 전 기본값: 10분

# Column 1 - 영상 선택 및 표시
with col1:
    st.markdown("<style>div.stFileUploader { width: 300px !important; height: 300px !important; }</style>", unsafe_allow_html=True)
    video_file = st.file_uploader("영상 선택", type="mp4", label_visibility='visible')
    
    video_placeholder = st.empty()  # 빈 공간 생성
    
    if video_file is not None:
        # 업로드된 파일을 임시로 저장
        with open("temp_video.mp4", "wb") as f:
            f.write(video_file.read())
        
        # moviepy를 사용해 영상 길이 가져오기
        try:
            clip = VideoFileClip("temp_video.mp4")
            video_duration = int(clip.duration)  # 영상 길이 (초 단위)
            clip.close()
        except Exception as e:
            st.error("영상 정보를 불러오는 중 문제가 발생했습니다.")
        
    st.markdown("""
    <div style='display: flex; justify-content: center; align-items: center;'>
        <span style='background-color: green; height:150px; width:250px; color: white; text-align: center; justify-content: center; font-size: 90px; font-weight: bold;'>NG</span>
        <span style='background-color: red; height:150px; width:250px; color: white; text-align: center; justify-content: center; font-size: 90px; font-weight: bold;'>OK</span>
    </div>
    """, unsafe_allow_html=True)
    st.progress(i)  # Placeholder for progress bar

# Column 2 - Settings
with col2:
    st.markdown("""
    <div style='font-size: 30px; font-weight: bold; margin-bottom: 500px;'>불량:</div>
    """, unsafe_allow_html=True)

    time_range = st.slider(
        label="(초)",
        min_value=0,
        max_value=video_duration,  # Example: maximum of 10 minutes (600 seconds)
        value=(0, min(60, video_duration)),
    )
    st.write("테스트 구간: 시작 {}초 - 종료 {}초".format(time_range[0], time_range[1]))
    start_button = st.button("\u25B6\ufe0f")
    if start_button:
        # 영상 표시
        video_placeholder.video(video_file, format='video/mp4', start_time=time_range[0])
        st.markdown("<style>div.stVideo > video { width: 300px !important; height: 300px !important; }</style>", unsafe_allow_html=True)

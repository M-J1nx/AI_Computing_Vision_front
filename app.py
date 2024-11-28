import streamlit as st

# Streamlit 페이지 설정
st.set_page_config(page_title="다이캐스팅 품질 검사 시스템", layout="wide")

# 사이드바 기본 안내 메시지
st.sidebar.success("왼쪽 메뉴에서 페이지를 선택하세요.")

# 홈화면 또는 첫 진입 시 보여줄 내용
st.title("다이캐스팅 품질 검사 시스템")
st.write("""
    이 애플리케이션은 다이캐스팅 부품의 품질을 검사하고 데이터를 시각화하는 시스템입니다.  
    사이드바 메뉴를 사용하여 각 페이지로 이동하세요.
""")

import streamlit as st
import requests
from moviepy.editor import VideoFileClip
import os
import urllib.parse

# 페이지 기본 설정 (와이드 모드 및 귀여운 타이틀)
st.set_page_config(page_title="먼작귀 플레이어 & 짤 메이커", layout="wide", page_icon="🎬")

st.title("🎬 먼작귀 전용 플레이어 & 고화질 GIF 메이커 🐹")

# -----------------------------------------------------------------------------
# [옵션 1] Supabase를 안 쓸 경우: R2 퍼블릭 URL 하위에 파일명이 규칙적일 때 자동 생성
# [옵션 2] Supabase를 쓸 경우: DB에서 타이틀과 URL 목록을 select()로 긁어오면 끝!
# -----------------------------------------------------------------------------
R2_PUBLIC_URL = "https://pub-decfccfe3ea6499a9d98ac3dcf96ef70.r2.dev" # 👈 오구님의 R2 퍼블릭 주소 입력

# 하드코딩 대신 기존에 쓰시던 1화~199화 리스트를 파이썬 딕셔너리로 자동 빌드합니다.
# (만약 Supabase를 쓴다면 이 부분이 `supabase.table("videos").select("*")`로 대체되어 편해집니다!)
raw_episodes = [
    "먼작귀 1화_단단한 푸딩, 핫케이크",
    "먼작귀 2화_스핑크스, 실물이다",
    "먼작귀 3화_맛나 오징어, 스튜파이",
    "먼작귀 4화_브로콜리, 피자만두",
    "먼작귀 5화_까리메라, 까르메라",
    # ... 필요한 에피소드 이름들을 쭉 나열하거나 R2에서 리스트를 API로 받아와도 됩니다.
]

# 한글 파일명 깨짐 방지를 위해 URL 인코딩 처리하며 플레이리스트 조립
playlist = []
for idx, name in enumerate(raw_episodes):
    encoded_file = urllib.parse.quote(f"{name}.mp4")
    playlist.append({
        "id": idx,
        "name": name,
        "url": f"{R2_PUBLIC_URL}/{encoded_file}"
    })

# -----------------------------------------------------------------------------
# 레이아웃 분할 (왼쪽: 비디오 플레이어 & 짤방 메이커 / 오른쪽: 사이드바 플레이리스트)
# -----------------------------------------------------------------------------
col_main, col_list = st.columns([2.5, 1])

with col_list:
    st.subheader("📋 에피소드 목록")
    # 검색 기능
    search_keyword = st.text_input("🔍 에피소드 검색", placeholder="검색어를 입력하세요...")
    
    filtered_playlist = [
        vid for vid in playlist if search_keyword.lower() in vid["name"].lower()
    ] if search_keyword else playlist

    # 드롭다운 또는 라디오 버튼으로 영상 선택
    video_names = [vid["name"] for vid in filtered_playlist]
    
    if video_names:
        selected_name = st.radio("상영관 선택", video_names, label_visibility="collapsed")
        # 선택된 영상 오브젝트 추출
        selected_video = next(vid for vid in filtered_playlist if vid["name"] == selected_name)
    else:
        st.write("검색 결과가 없습니다 😭")
        selected_video = playlist[0] if playlist else None

with col_main:
    if selected_video:
        st.subheader(f"🎥 현재 재생 중: {selected_video['name']}")
        
        # 1. ⚡ 영상 플레이어 렌더링 (CORS 걱정 없음)
        st.video(selected_video["url"])
        
        st.write("---")
        
        # 2. ⚡ GIF 짤 추출기 스페이스
        st.subheader("🔥 고화질 GIF 짤방 생성기")
        st.caption("위 플레이어에서 원하는 구간의 초(second)를 확인한 후 입력해 주세요.")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            start_time = st.number_input("시작 시간 (초)", min_value=0.0, value=0.0, step=0.1)
        with c2:
            end_time = st.number_input("종료 시간 (초)", min_value=0.0, value=2.0, step=0.1)
        with c3:
            gif_fps = st.slider("부드러움 (FPS)", min_value=5, max_value=20, value=12, step=1)
            
        if st.button("🚀 이 구간 짤로 찌기!", use_container_width=True):
            if start_time >= end_time:
                st.error("종료 시간이 시작 시간보다 커야 합니다! (우사기 호통 💢)")
            elif (end_time - start_time) > 10.0:
                st.warning("무료 서버 과부하 방지를 위해 짤방은 최대 10초까지만 잘라낼 수 있습니다.")
            else:
                with st.spinner("백엔드 엔진에서 고화질 인코딩 중... 잠시만 기다려주세요 ⚙️"):
                    try:
                        # MoviePy로 R2 스트리밍 주소에서 필요한 부분만 싹둑 자르기
                        clip = VideoFileClip(selected_video["url"]).subclip(start_time, end_time)
                        
                        # 해상도를 절반으로 줄여 용량 최적화 (가로 비율 유지)
                        clip_resized = clip.resize(0.5)
                        
                        output_filename = "temp_preview.gif"
                        # GIF 변환 파일 쓰기
                        clip_resized.write_gif(output_filename, fps=gif_fps, logger=None)
                        clip.close()
                        
                        # 화면에 완성된 GIF 출력
                        st.success("짜잔! 고화질 짤방이 완성되었습니다!")
                        st.image(output_filename)
                        
                        # 다운로드 버튼 생성
                        with open(output_filename, "rb") as file:
                            st.download_button(
                                label="💾 내 컴퓨터에 짤방 저장하기",
                                data=file,
                                file_name=f"gif_{selected_video['id']}.gif",
                                mime="image/gif",
                                use_container_width=True
                            )
                        
                        # 서버 임시 파일 청소
                        if os.path.exists(output_filename):
                            os.remove(output_filename)
                            
                    except Exception as e:
                        st.error(f"인코딩 실패 😭 에러 원인: {e}")
    else:
        st.info("등록된 비디오 데이터가 없습니다.")
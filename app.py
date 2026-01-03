import streamlit as st
import yt_dlp
import random
import copy
import json
from urllib.parse import urlparse, parse_qs
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="유튜브 이상형 월드컵", layout="wide", initial_sidebar_state="expanded")

# --- 스타일 커스텀 (CSS) ---
st.markdown("""
    <style>
    /* 페이지 상단 여백 조정 */
    .block-container {
        padding-top: 3.5rem !important; 
        padding-bottom: 5rem !important;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
    }
    .select-btn {
        height: 3em;
        font-size: 20px;
        font-weight: bold;
        background-color: #ff4b4b;
        color: white !important;
        border: none;
    }
    .vs-text {
        text-align: center;
        font-size: 50px;
        font-weight: bold;
        color: red;
        margin-top: 10px; 
    }
    .result-card {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 5px;
        border-left: 5px solid #ff4b4b;
    }
    .like-card {
        background-color: #fff0f0; 
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 5px;
        border: 1px solid #ffcccc;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 상태 초기화 ---
if 'playlist_data' not in st.session_state: st.session_state.playlist_data = []
if 'current_round_list' not in st.session_state: st.session_state.current_round_list = []
if 'next_round_list' not in st.session_state: st.session_state.next_round_list = []
if 'game_started' not in st.session_state: st.session_state.game_started = False
if 'winner' not in st.session_state: st.session_state.winner = None
if 'current_pair' not in st.session_state: st.session_state.current_pair = []
if 'bye_video' not in st.session_state: st.session_state.bye_video = None
if 'match_history' not in st.session_state: st.session_state.match_history = []
if 'liked_videos' not in st.session_state: st.session_state.liked_videos = []
if 'history_stack' not in st.session_state: st.session_state.history_stack = []
if 'balloons_shown' not in st.session_state: st.session_state.balloons_shown = False

# --- 함수 정의 ---
@st.cache_data(show_spinner=False)
def fetch_playlist(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    if 'list' in query_params:
        playlist_id = query_params['list'][0]
        target_url = f"https://www.youtube.com/playlist?list={playlist_id}"
    else:
        target_url = url

    ydl_opts = {'extract_flat': True, 'quiet': True, 'ignoreerrors': True}
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(target_url, download=False)
        if 'entries' in info: return list(info['entries'])
        return [info]

def reset_game():
    st.session_state.game_started = False
    st.session_state.winner = None
    st.session_state.playlist_data = []
    st.session_state.current_round_list = []
    st.session_state.next_round_list = []
    st.session_state.current_pair = []
    st.session_state.bye_video = None
    st.session_state.match_history = []
    st.session_state.liked_videos = []
    st.session_state.history_stack = []
    st.session_state.balloons_shown = False

def toggle_like(video):
    liked_ids = [v['id'] for v in st.session_state.liked_videos]
    if video['id'] in liked_ids:
        st.session_state.liked_videos = [v for v in st.session_state.liked_videos if v['id'] != video['id']]
    else:
        st.session_state.liked_videos.append(video)

def save_current_state():
    state_snapshot = {
        'current_round_list': copy.deepcopy(st.session_state.current_round_list),
        'next_round_list': copy.deepcopy(st.session_state.next_round_list),
        'current_pair': copy.deepcopy(st.session_state.current_pair),
        'bye_video': copy.deepcopy(st.session_state.bye_video),
        'match_history': copy.deepcopy(st.session_state.match_history),
        'winner': st.session_state.winner,
        'balloons_shown': st.session_state.balloons_shown
    }
    st.session_state.history_stack.append(state_snapshot)

def undo_last_action():
    if st.session_state.history_stack:
        prev_state = st.session_state.history_stack.pop()
        st.session_state.current_round_list = prev_state['current_round_list']
        st.session_state.next_round_list = prev_state['next_round_list']
        st.session_state.current_pair = prev_state['current_pair']
        st.session_state.bye_video = prev_state['bye_video']
        st.session_state.match_history = prev_state['match_history']
        st.session_state.winner = prev_state['winner']
        st.session_state.balloons_shown = prev_state.get('balloons_shown', False)
        st.rerun()

def check_round_end():
    if not st.session_state.current_round_list and not st.session_state.current_pair and not st.session_state.bye_video:
        if len(st.session_state.next_round_list) == 1:
            st.session_state.winner = st.session_state.next_round_list[0]
        else:
            st.session_state.current_round_list = st.session_state.next_round_list
            st.session_state.next_round_list = []
            random.shuffle(st.session_state.current_round_list)

def select_winner(choice_idx):
    save_current_state()
    pair = st.session_state.current_pair
    winner = pair[choice_idx]
    loser = pair[1 - choice_idx]
    
    total_participants = (len(st.session_state.next_round_list) * 2) + len(st.session_state.current_pair) + len(st.session_state.current_round_list)
    if st.session_state.bye_video: total_participants += 1
    
    round_name = "결승전" if total_participants <= 2 else f"{total_participants}강"
    
    st.session_state.match_history.append({'round': round_name, 'winner': winner['title'], 'loser': loser['title']})
    st.session_state.next_round_list.append(winner)
    st.session_state.current_pair = []
    
    check_round_end()
    st.rerun()

def confirm_bye():
    if st.session_state.bye_video:
        save_current_state()
        st.session_state.next_round_list.append(st.session_state.bye_video)
        st.session_state.bye_video = None
        check_round_end()
        st.rerun()

def find_video_by_title(title):
    for vid in st.session_state.playlist_data:
        if vid['title'] == title: return vid
    return None

def get_game_state_json():
    data = {
        'playlist_data': st.session_state.playlist_data,
        'current_round_list': st.session_state.current_round_list,
        'next_round_list': st.session_state.next_round_list,
        'game_started': st.session_state.game_started,
        'winner': st.session_state.winner,
        'current_pair': st.session_state.current_pair,
        'bye_video': st.session_state.bye_video,
        'match_history': st.session_state.match_history,
        'liked_videos': st.session_state.liked_videos,
        'history_stack': st.session_state.history_stack,
        'balloons_shown': st.session_state.balloons_shown
    }
    return json.dumps(data, ensure_ascii=False, indent=2)

def load_game_state(uploaded_file):
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            st.session_state.playlist_data = data.get('playlist_data', [])
            st.session_state.current_round_list = data.get('current_round_list', [])
            st.session_state.next_round_list = data.get('next_round_list', [])
            st.session_state.game_started = data.get('game_started', False)
            st.session_state.winner = data.get('winner', None)
            st.session_state.current_pair = data.get('current_pair', [])
            st.session_state.bye_video = data.get('bye_video', None)
            st.session_state.match_history = data.get('match_history', [])
            st.session_state.liked_videos = data.get('liked_videos', [])
            st.session_state.history_stack = data.get('history_stack', [])
            st.session_state.balloons_shown = data.get('balloons_shown', False)
            return True
        except Exception as e:
            st.error(f"파일 불러오기 실패: {e}")
            return False
    return False

# --- 사이드바 ---
with st.sidebar:
    st.header("💾 게임 데이터 관리")
    st.caption("게임 상태를 저장하거나 불러올 수 있습니다.")
    
    if st.session_state.game_started:
        json_str = get_game_state_json()
        st.download_button("📥 현재 상태 파일로 저장", json_str, "worldcup_save.json", "application/json")
    
    st.divider()
    uploaded_file = st.file_uploader("📤 저장된 파일 불러오기", type=['json'])
    if uploaded_file and st.button("파일 적용하여 이어하기"):
        if load_game_state(uploaded_file): st.success("게임을 불러왔습니다!"); st.rerun()

    st.divider()
    st.link_button("🐞 버그 제보 및 건의함", "https://forms.gle/rDxwu5rUzYuGMCJM7")

# --- 메인 화면 로직 ---
if not st.session_state.game_started:
    st.title("🎵 유튜브 플레이리스트 이상형 월드컵")
    st.write("") # 여백
    st.info("유튜브 영상 링크(list 포함)나 플레이리스트 링크를 넣으세요.")
    url = st.text_input("링크 입력", placeholder="https://www.youtube.com/watch?v=...&list=...")
    
    if st.button("게임 시작하기", use_container_width=True):
        if url:
            with st.spinner("플레이리스트 목록을 가져오는 중..."):
                try:
                    raw_data = fetch_playlist(url)
                    videos = []
                    for v in raw_data:
                        if v and v.get('title') and v.get('title') != '[Deleted video]':
                            videos.append({'title': v.get('title'), 'url': f"https://www.youtube.com/watch?v={v.get('id')}", 'id': v.get('id')})
                    
                    if len(videos) < 2:
                        st.error(f"재생 가능한 영상이 부족합니다. (추출된 영상: {len(videos)}개)")
                    else:
                        random.shuffle(videos)
                        st.session_state.playlist_data = videos
                        st.session_state.current_round_list = videos[:]
                        st.session_state.game_started = True
                        st.rerun()
                except Exception as e: st.error(f"오류가 발생했습니다: {e}")
        else: st.warning("URL을 입력해주세요.")

elif st.session_state.winner:
    if not st.session_state.balloons_shown:
        st.balloons()
        st.session_state.balloons_shown = True

    st.title("👑 최종 우승! 👑")
    winner = st.session_state.winner
    
    # --- 순위 산정 ---
    reversed_history = list(reversed(st.session_state.match_history))
    unique_rounds = []
    for match in reversed_history:
        if match['round'] not in unique_rounds: unique_rounds.append(match['round'])
    
    st.write("#### 🎖️ 전체 순위 (클릭하여 영상 보기)")
    
    with st.expander(f"{winner['title']}", expanded=True):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2: st.video(winner['url'])
    
    current_start_rank = 2
    for r_idx, r_name in enumerate(unique_rounds):
        losers_in_round = [find_video_by_title(match['loser']) for match in reversed_history if match['round'] == r_name]
        losers_in_round = [l for l in losers_in_round if l]
        
        count = len(losers_in_round)
        if count == 0: continue
        end_rank = current_start_rank + count - 1
        
        if current_start_rank == end_rank:
            rank_str = f"{current_start_rank}위"
        else:
            rank_str = f"{current_start_rank}~{end_rank}위"

        if r_idx == 0: rank_title = "🥈 2위 (준우승)"
        elif r_idx == 1 and r_name == "4강": rank_title = "🥉 3~4위 (Top 4)"
        else:
            if r_idx == len(unique_rounds) - 1: rank_title = f"🏅 {rank_str} ({r_name})"
            else: rank_title = f"🏅 {rank_str} ({r_name} 진출)"
        
        st.markdown("---")
        st.caption(f"**{rank_title}**")
        for vid in losers_in_round:
            with st.expander(f"{vid['title']}"):
                c1, c2, c3 = st.columns([1, 2, 1])
                with c2: st.video(vid['url'])
        current_start_rank += count

    st.divider()
    if st.session_state.history_stack and st.button("↩️ 결과 취소하고 결승전으로 돌아가기"): undo_last_action()

    st.divider()
    st.subheader("❤️ 내가 찜한 노래들")
    if st.session_state.liked_videos:
        st.write("")
        cols = st.columns(3)
        for idx, vid in enumerate(st.session_state.liked_videos):
            with cols[idx % 3]:
                st.markdown(f"<div class='like-card'><b>{vid['title']}</b><br><a href='{vid['url']}' target='_blank'>유튜브에서 보기</a></div>", unsafe_allow_html=True)
    else:
        st.caption("아직 찜한 노래가 없습니다.")
    
    st.divider()
    st.subheader("📜 대진 기록")
    for match in reversed(st.session_state.match_history):
        st.markdown(f"<div class='result-card'><small>{match['round']}</small><br><span style='color:red; font-weight:bold;'>🏆 {match['winner']}</span> vs <span style='color:gray; text-decoration:line-through;'>{match['loser']}</span></div>", unsafe_allow_html=True)
    
    if st.button("다시 하기"): reset_game(); st.rerun()

else:
    # --- 게임 진행 화면 ---
    if not st.session_state.current_pair and not st.session_state.bye_video:
         if len(st.session_state.current_round_list) >= 2:
            v1 = st.session_state.current_round_list.pop(); v2 = st.session_state.current_round_list.pop()
            st.session_state.current_pair = [v1, v2]
         elif len(st.session_state.current_round_list) == 1:
            st.session_state.bye_video = st.session_state.current_round_list.pop()
    
    if st.session_state.bye_video:
        st.subheader(f"🎉 부전승")
        b_vid = st.session_state.bye_video
        col_l, col_c, col_r = st.columns([2, 3, 2]) 
        with col_c:
            st.video(b_vid['url'])
            st.markdown(f"<h3 style='text-align:center;'>{b_vid['title']}</h3>", unsafe_allow_html=True)
            is_liked = b_vid['id'] in [v['id'] for v in st.session_state.liked_videos]
            if st.button("❤️ 좋아요 취소" if is_liked else "🤍 좋아요", key=f"like_bye_{b_vid['id']}", use_container_width=True):
                toggle_like(b_vid); st.rerun()
            st.write("") 
            if st.button("🚀 다음 라운드로 진출하기", type="primary", use_container_width=True): confirm_bye()
        st.divider()
        if st.session_state.history_stack:
            _, c_center, _ = st.columns([5, 2, 5]) 
            with c_center:
                if st.button("↩️ 무르기", use_container_width=True):
                    undo_last_action()

    elif st.session_state.current_pair:
        participants_in_next = len(st.session_state.next_round_list)
        participants_current = len(st.session_state.current_round_list) + len(st.session_state.current_pair)
        if st.session_state.bye_video: participants_current += 1
        total_participants_in_round = (participants_in_next * 2) + participants_current
        total_matches = total_participants_in_round // 2
        current_match_seq = participants_in_next + 1
        round_name = "결승전" if total_participants_in_round <= 2 else f"{total_participants_in_round}강"
        
        if round_name == "결승전": st.subheader(f"⚔️ {round_name}")
        else: st.subheader(f"⚔️ {round_name} ({current_match_seq}/{total_matches})") 
        
        col1, col2, col3 = st.columns([1, 0.3, 1])
        pair = st.session_state.current_pair
        liked_ids = [v['id'] for v in st.session_state.liked_videos]

        with col1:
            st.video(pair[0]['url'])
            st.write(f"**{pair[0]['title']}**")
            if st.button("❤️ 좋아요 취소" if pair[0]['id'] in liked_ids else "🤍 좋아요", key=f"like_{pair[0]['id']}"):
                toggle_like(pair[0]); st.rerun()
            if st.button("👈 이 노래 선택", key="btn_select_1", type="primary"): select_winner(0)
            
        with col2:
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            
            if st.button("🎲 리롤", key="reroll_btn", use_container_width=True, help="남은 대진을 다시 섞습니다"):
                pool = st.session_state.current_round_list + st.session_state.current_pair
                random.shuffle(pool)
                st.session_state.current_round_list = pool
                if len(st.session_state.current_round_list) >= 2:
                    v1 = st.session_state.current_round_list.pop()
                    v2 = st.session_state.current_round_list.pop()
                    st.session_state.current_pair = [v1, v2]
                st.rerun()

            st.markdown('<div class="vs-text">VS</div>', unsafe_allow_html=True)
            
            st.write("")
            st.write("")

            if st.session_state.history_stack:
                if st.button("↩️ 무르기", key="undo_match", use_container_width=True): 
                    undo_last_action()
            
        with col3:
            st.video(pair[1]['url'])
            st.write(f"**{pair[1]['title']}**")
            if st.button("❤️ 좋아요 취소" if pair[1]['id'] in liked_ids else "🤍 좋아요", key=f"like_{pair[1]['id']}"):
                toggle_like(pair[1]); st.rerun()
            if st.button("이 노래 선택 👉", key="btn_select_2", type="primary"): select_winner(1)
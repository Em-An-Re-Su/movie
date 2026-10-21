# main.py
# KOBIS 일별 박스오피스 대시보드
# 초보자도 수정하기 쉽도록 기능별로 주석을 달았습니다.

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import hashlib

import requests
import pandas as pd
import streamlit as st
import plotly.express as px

# -----------------------------
# 1. 기본 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="CINÉ / DAILY BOX OFFICE",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

SEOUL = ZoneInfo("Asia/Seoul")
TODAY_KR = datetime.now(SEOUL).date()
YESTERDAY_KR = TODAY_KR - timedelta(days=1)

API_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)

# -----------------------------
# 2. 디자인: 기하학적 모더니즘
# -----------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    :root {
        --ink: #171717;
        --paper: #f3f0e8;
        --red: #ef493c;
        --blue: #315ee8;
        --yellow: #f4c94b;
        --line: rgba(23,23,23,.18);
    }
    .stApp {
        background:
          radial-gradient(circle at 88% 7%, rgba(244,201,75,.22), transparent 21rem),
          radial-gradient(circle at 8% 28%, rgba(49,94,232,.10), transparent 23rem),
          #f3f0e8;
        color: var(--ink);
        font-family: 'Space Grotesk', sans-serif;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] {
        background: #e9e4d8;
        border-right: 1px solid var(--line);
    }
    .block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 1500px; }
    .eyebrow {
        font-family: 'DM Mono', monospace; text-transform: uppercase;
        letter-spacing: .16em; font-size: .72rem; font-weight: 500;
    }
    .hero {
        position: relative; overflow: hidden; border: 2px solid var(--ink);
        border-radius: 4px; padding: clamp(1.5rem, 4vw, 3.5rem);
        background: #f8f5ed; min-height: 245px;
        box-shadow: 8px 8px 0 var(--ink);
        margin: .5rem 0 2rem 0;
    }
    .hero h1 {
        font-size: clamp(2.4rem, 6vw, 5.7rem); line-height: .9;
        letter-spacing: -.075em; margin: .9rem 0 1rem 0; font-weight: 700;
        max-width: 760px;
    }
    .hero p { max-width: 600px; font-size: 1rem; margin-bottom: 0; }
    .geo {
        position: absolute; pointer-events: none; right: 4%; top: 12%;
        width: 220px; height: 180px; transform: rotate(-8deg);
    }
    .geo .circle { position:absolute; width:125px;height:125px;border-radius:50%;
        background:var(--red);right:0;top:0;border:2px solid var(--ink); }
    .geo .tri { position:absolute; width:0;height:0;border-left:72px solid transparent;
        border-right:72px solid transparent;border-bottom:128px solid var(--blue);
        left:0;bottom:0;transform:rotate(18deg);filter: drop-shadow(3px 3px 0 var(--ink)); }
    .geo .square { position:absolute;width:70px;height:70px;background:var(--yellow);
        border:2px solid var(--ink);left:78px;top:53px;transform:rotate(23deg); }
    .section-title {
        font-size: 1.25rem; font-weight: 700; letter-spacing: -.04em;
        border-bottom: 2px solid var(--ink); padding-bottom: .55rem; margin: 1.5rem 0 1rem;
    }
    .metric-card {
        border: 2px solid var(--ink); padding: 1.15rem 1.25rem;
        min-height: 145px; box-shadow: 5px 5px 0 var(--ink);
        transition: transform .18s ease, box-shadow .18s ease;
        animation: rise .45s ease both;
    }
    .metric-card:hover { transform: translate(-2px,-3px); box-shadow: 8px 8px 0 var(--ink); }
    .metric-card .label { font-family:'DM Mono',monospace;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase; }
    .metric-card .value { font-size:clamp(1.8rem,3vw,3rem);font-weight:700;letter-spacing:-.07em;margin-top:.55rem;line-height:1; }
    .metric-card .sub { font-size:.8rem; margin-top:.7rem; opacity:.75; }
    .film-panel {
        border: 2px solid var(--ink); padding: 1.4rem; min-height: 220px;
        box-shadow: 6px 6px 0 var(--ink); position:relative; overflow:hidden;
        transition: transform .2s ease;
    }
    .film-panel:hover { transform: translateY(-3px); }
    .film-title { font-size: clamp(1.8rem,4vw,3.5rem); line-height:1; letter-spacing:-.07em;
        font-weight:700; max-width:75%; overflow-wrap:anywhere; }
    .film-orbit { position:absolute; right:-24px; bottom:-48px; width:180px;height:180px;
        border:2px solid var(--ink);border-radius:50%;opacity:.9; }
    .film-orbit:before { content:'';position:absolute;width:105px;height:105px;left:-32px;top:10px;
        background:rgba(255,255,255,.25);border:2px solid var(--ink);transform:rotate(25deg); }
    div.stButton > button {
        border:2px solid var(--ink); border-radius:2px; font-weight:700;
        transition: transform .15s ease, box-shadow .15s ease;
    }
    div.stButton > button:hover { transform:translate(-2px,-2px); box-shadow:4px 4px 0 var(--ink); }
    [data-testid="stDataFrame"] { border:1px solid var(--line); }
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
        border-color: var(--ink);
    }
    @keyframes rise { from { opacity:0; transform:translateY(12px); } to {opacity:1;transform:translateY(0);} }
    @media (max-width: 700px) {
        .geo { opacity:.22; right:-45px; top:20px; transform:scale(.75) rotate(-8deg); }
        .hero { padding:1.4rem; }
        .hero h1 { max-width:95%; }
    }
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { animation:none !important; transition:none !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# 3. 도우미 함수
# -----------------------------
def format_number(value):
    """숫자를 천 단위 쉼표가 있는 문자열로 바꿉니다."""
    try:
        return f"{int(float(value)):,}"
    except (TypeError, ValueError):
        return "0"


def format_date(raw_date):
    """API의 YYYY-MM-DD 날짜를 읽기 좋은 형태로 바꿉니다."""
    if not raw_date:
        return "정보 없음"
    try:
        return datetime.strptime(raw_date, "%Y-%m-%d").strftime("%Y.%m.%d")
    except ValueError:
        return str(raw_date)


def get_palette(movie_name):
    """영화 제목에 따라 일관된 색상 조합을 선택합니다.
    KOBIS 일별 박스오피스 API에는 포스터 색이나 장르가 없으므로,
    실제 포스터 분석이 아니라 제목 기반의 추상적 디자인 테마입니다.
    """
    palettes = [
        ("#ef493c", "#f8f5ed", "#f4c94b"),
        ("#315ee8", "#f4f0e7", "#f2c84b"),
        ("#f4c94b", "#202020", "#ef493c"),
        ("#d9d5f2", "#202020", "#ef493c"),
        ("#1f6c5c", "#f7f0df", "#e9b7a6"),
        ("#e9b7a6", "#242424", "#f4c94b"),
    ]
    digest = hashlib.sha256(str(movie_name).encode("utf-8")).hexdigest()
    return palettes[int(digest[:8], 16) % len(palettes)]


def fetch_box_office(target_date):
    """KOBIS API에 날짜와 비밀 금고의 인증키를 전달합니다."""
    api_key = st.secrets.get("KOBIS_KEY", "")
    if not api_key:
        raise RuntimeError(
            "인증키를 찾을 수 없습니다. Streamlit Cloud의 앱 설정 → Secrets에 "
            'KOBIS_KEY = "발급받은_인증키" 형식으로 등록했는지 확인해 주세요.'
        )

    params = {
        "key": api_key,
        "targetDt": target_date.strftime("%Y%m%d"),
    }
    try:
        response = requests.get(API_URL, params=params, timeout=20)
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.Timeout as exc:
        raise RuntimeError("KOBIS 서버 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            "KOBIS API에 연결하지 못했습니다. 인터넷 연결, API 주소, KOBIS 서비스 상태를 확인해 주세요."
        ) from exc
    except ValueError as exc:
        raise RuntimeError("KOBIS 응답을 JSON으로 읽지 못했습니다. 잠시 후 다시 시도해 주세요.") from exc

    # 인증키가 틀려도 HTTP 상태코드가 200일 수 있어 faultInfo를 따로 확인합니다.
    if payload.get("faultInfo"):
        fault = payload["faultInfo"]
        message = fault.get("message", "KOBIS에서 오류를 반환했습니다.")
        code = fault.get("errorCode", "오류 코드 없음")
        raise RuntimeError(
            f"KOBIS API 오류({code}): {message} "
            "인증키가 정확한지, API 이용 신청 및 접근 권한이 유효한지 확인해 주세요."
        )

    result = payload.get("boxOfficeResult")
    if not isinstance(result, dict):
        raise RuntimeError(
            "응답에 boxOfficeResult가 없습니다. API 응답 형식이나 인증키 상태를 확인해 주세요."
        )

    return result.get("dailyBoxOfficeList", [])


# -----------------------------
# 4. 상단 헤더
# -----------------------------
st.markdown(
    f"""
    <div class="hero">
      <div class="eyebrow">KOBIS DATA / DAILY REPORT · {YESTERDAY_KR:%Y.%m.%d} 기준 최신 조회 가능일</div>
      <div class="geo"><div class="circle"></div><div class="tri"></div><div class="square"></div></div>
      <h1>THE DAILY<br>BOX OFFICE.</h1>
      <p>매일의 관객 흐름을 읽는 영화 데이터 아카이브. 숫자는 선명하게, 화면은 영화처럼.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# 5. 날짜 선택
# -----------------------------
with st.sidebar:
    st.markdown('<div class="eyebrow">01 / DATE SELECT</div>', unsafe_allow_html=True)
    st.title("조회 날짜")
    selected_date = st.date_input(
        "박스오피스 날짜",
        value=YESTERDAY_KR,
        min_value=date(2004, 1, 1),
        max_value=YESTERDAY_KR,
        help="한국 시간 기준 오늘보다 늦은 날짜는 선택할 수 없습니다.",
    )
    st.caption(f"한국 시간 기준 오늘: {TODAY_KR:%Y.%m.%d}")
    st.caption("오늘의 박스오피스는 집계 전일 수 있어 어제까지 조회할 수 있습니다.")
    refresh = st.button("↻ 데이터 다시 불러오기", use_container_width=True)

if selected_date > YESTERDAY_KR:
    st.error("오늘 이후 날짜는 조회할 수 없습니다. 어제 또는 그 이전 날짜를 선택해 주세요.")
    st.stop()

if refresh:
    st.cache_data.clear()

# 선택한 날짜별 결과를 짧게 캐시하여 불필요한 API 호출을 줄입니다.
@st.cache_data(ttl=900, show_spinner=False)
def cached_fetch(target_date):
    return fetch_box_office(target_date)

st.markdown(
    f'<div class="eyebrow">02 / DAILY REPORT &nbsp;·&nbsp; {selected_date:%Y.%m.%d}</div>',
    unsafe_allow_html=True,
)

try:
    with st.spinner("KOBIS에서 일별 박스오피스 데이터를 가져오는 중입니다..."):
        movies = cached_fetch(selected_date)
except Exception as error:
    st.error("박스오피스 데이터를 불러오지 못했습니다.")
    st.markdown("**확인할 사항**")
    st.markdown(
        "- Streamlit Cloud의 **Settings → Secrets**에 `KOBIS_KEY`가 등록되어 있는지 확인하세요.\n"
        "- 인증키 앞뒤에 불필요한 공백이 없고, KOBIS Open API 이용 신청이 유효한지 확인하세요.\n"
        "- 잠시 후 다시 시도하거나 KOBIS API 서비스 상태를 확인하세요."
    )
    st.code(str(error))
    st.stop()

if not movies:
    st.warning(
        f"**{selected_date:%Y년 %m월 %d일} — 그날은 아직 집계 전입니다.**\n\n"
        "해당 날짜의 영화 목록이 비어 있습니다. 날짜를 하루 이전으로 바꾸거나, "
        "KOBIS에서 해당 날짜의 집계 데이터가 공개되었는지 확인해 주세요."
    )
    st.stop()

# API 숫자 값은 문자열로 오므로 표와 그래프를 위해 숫자로 변환합니다.
df = pd.DataFrame(movies)
required_columns = ["rank", "rankInten", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]
for column in required_columns:
    if column not in df.columns:
        df[column] = ""

for column in ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt", "showCnt"]:
    if column in df.columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0).astype(int)

df["rank"] = df["rank"].astype(int)
df["movieNm"] = df["movieNm"].fillna("제목 정보 없음").astype(str)
df["openDt"] = df["openDt"].fillna("").astype(str)

# -----------------------------
# 6. 1위 영화와 지표 카드
# -----------------------------
leader = df.sort_values("rank").iloc[0]
leader_name = str(leader["movieNm"])
leader_bg, leader_fg, leader_accent = get_palette(leader_name)

st.markdown('<div class="section-title">TODAY\'S LEADER / 1위 영화</div>', unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="film-panel" style="background:{leader_bg};color:{leader_fg};">
      <div class="eyebrow">RANK NO. 01 &nbsp; / &nbsp; {selected_date:%Y.%m.%d}</div>
      <div class="film-title">{leader_name}</div>
      <div style="margin-top:1rem;font-family:'DM Mono',monospace;font-size:.78rem;">
        개봉일 {format_date(leader['openDt'])}
        &nbsp; / &nbsp; 누적 관객 {format_number(leader['audiAcc'])}명
      </div>
      <div class="film-orbit" style="background:{leader_accent};"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

m1, m2, m3 = st.columns(3)
metrics = [
    (m1, "DAILY AUDIENCE", format_number(leader["audiCnt"]), "오늘 하루 관객수", "#ef493c", "#171717"),
    (m2, "TOTAL AUDIENCE", format_number(leader["audiAcc"]), "누적 관객수", "#f4c94b", "#171717"),
    (m3, "SCREENS", format_number(leader["scrnCnt"]), "스크린 수", "#315ee8", "#ffffff"),
]
for col, label, value, sub, bg, fg in metrics:
    with col:
        st.markdown(
            f"""
            <div class="metric-card" style="background:{bg};color:{fg};">
              <div class="label">{label}</div>
              <div class="value">{value}</div>
              <div class="sub">{sub}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# -----------------------------
# 7. 관객수 상위 5편 막대그래프
# -----------------------------
st.markdown('<div class="section-title">AUDIENCE RACE / 관객수 TOP 5</div>', unsafe_allow_html=True)
top5 = df.sort_values("audiCnt", ascending=False).head(5).copy()
top5["관객수"] = top5["audiCnt"]
top5["영화명"] = top5.apply(
    lambda row: f"{'🏆 ' if row['audiAcc'] > 1_000_000 else ''}{row['movieNm']}",
    axis=1,
)
chart = px.bar(
    top5.sort_values("관객수", ascending=True),
    x="관객수",
    y="영화명",
    orientation="h",
    text="관객수",
    color="관객수",
    color_continuous_scale=["#315ee8", "#ef493c", "#f4c94b"],
    labels={"관객수": "일일 관객수", "영화명": ""},
)
chart.update_traces(texttemplate="%{text:,.0f}명", textposition="outside", cliponaxis=False)
chart.update_layout(
    height=360,
    margin=dict(l=8, r=45, t=12, b=8),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Space Grotesk, sans-serif", color="#171717"),
    showlegend=False,
    coloraxis_showscale=False,
    xaxis=dict(showgrid=True, gridcolor="rgba(23,23,23,.12)", zeroline=False),
    yaxis=dict(showgrid=False),
)
st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})

# -----------------------------
# 8. 전체 순위표
# -----------------------------
st.markdown('<div class="section-title">FULL RANKING / 전체 순위</div>', unsafe_allow_html=True)
st.caption("🔺 빨간색은 전일 대비 순위 상승, 🔻 파란색은 순위 하락입니다. 🏆는 누적 관객 100만 명 초과를 뜻합니다.")

def rank_change(value):
    """rankInten은 양수면 순위 상승, 음수면 순위 하락입니다."""
    value = int(value)
    if value > 0:
        return f"🔺 +{value}"
    if value < 0:
        return f"🔻 {value}"
    return "— 0"

display_df = df.sort_values("rank").copy()
display_df["순위"] = display_df["rank"].map(lambda value: f"{value}위")
display_df["순위 변동"] = display_df["rankInten"].map(rank_change)
display_df["영화명"] = display_df.apply(
    lambda row: f"{'🏆 ' if row['audiAcc'] > 1_000_000 else ''}{row['movieNm']}",
    axis=1,
)
display_df["개봉일"] = display_df["openDt"].map(format_date)
display_df["관객수"] = display_df["audiCnt"].map(format_number)
display_df["누적관객"] = display_df["audiAcc"].map(format_number)
display_df["스크린수"] = display_df["scrnCnt"].map(format_number)

table_df = display_df[["순위", "순위 변동", "영화명", "개봉일", "관객수", "누적관객", "스크린수"]]
st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "순위": st.column_config.TextColumn("순위", width="small"),
        "순위 변동": st.column_config.TextColumn("전일 대비", width="medium"),
        "영화명": st.column_config.TextColumn("영화명", width="large"),
        "개봉일": st.column_config.TextColumn("개봉일", width="medium"),
        "관객수": st.column_config.TextColumn("관객수(명)", width="medium"),
        "누적관객": st.column_config.TextColumn("누적관객(명)", width="medium"),
        "스크린수": st.column_config.TextColumn("스크린 수", width="small"),
    },
)

# -----------------------------
# 9. 영화 선택 인터랙션
# -----------------------------
st.markdown('<div class="section-title">FOCUS ON A FILM / 영화 들여다보기</div>', unsafe_allow_html=True)
movie_names = df.sort_values("rank")["movieNm"].tolist()
selected_movie = st.selectbox("영화를 선택하면 상세 지표와 색상 테마가 바뀝니다.", movie_names)
chosen = df.loc[df["movieNm"] == selected_movie].iloc[0]
focus_bg, focus_fg, focus_accent = get_palette(selected_movie)

left, right = st.columns([1.3, 1])
with left:
    st.markdown(
        f"""
        <div class="film-panel" style="background:{focus_bg};color:{focus_fg};">
          <div class="eyebrow">SELECTED FILM / RANK {int(chosen['rank']):02d}</div>
          <div class="film-title">{'🏆 ' if chosen['audiAcc'] > 1_000_000 else ''}{selected_movie}</div>
          <div style="margin-top:1rem;font-family:'DM Mono',monospace;font-size:.8rem;">
            개봉일 {format_date(chosen['openDt'])}
          </div>
          <div class="film-orbit" style="background:{focus_accent};"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with right:
    st.markdown("#### 선택한 영화의 기록")
    st.metric("박스오피스 순위", f"{int(chosen['rank'])}위")
    st.metric("일일 관객수", f"{format_number(chosen['audiCnt'])}명")
    st.metric("누적 관객수", f"{format_number(chosen['audiAcc'])}명")
    st.metric("스크린 수", f"{format_number(chosen['scrnCnt'])}개")
    delta = int(chosen["rankInten"])
    if delta > 0:
        st.markdown(f"**전일 대비:** 🔺 빨간 위 화살표 · {delta}계단 상승")
    elif delta < 0:
        st.markdown(f"**전일 대비:** 🔻 파란 아래 화살표 · {abs(delta)}계단 하락")
    else:
        st.markdown("**전일 대비:** 순위 변동 없음")

st.markdown("---")
st.markdown(
    '<div class="eyebrow">DATA SOURCE / KOBIS OPEN API · VISUAL THEME GENERATED FROM MOVIE TITLE</div>',
    unsafe_allow_html=True,
)
st.caption(
    "참고: 제공된 KOBIS 일별 박스오피스 응답에는 포스터 이미지·포스터 색상·장르 정보가 포함되지 않습니다. "
    "따라서 배경 테마는 실제 포스터나 장르를 분석한 결과가 아니라 영화 제목에 따라 정해지는 추상적인 색상 디자인입니다."
)

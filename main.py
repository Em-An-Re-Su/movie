
# main.py
# KOBIS 일별 박스오피스 + 영화 장면 애니메이션
# 초보자를 위해 기능별로 주석을 달았습니다.

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from html import escape
import hashlib

import requests
import pandas as pd
import plotly.express as px
import streamlit as st


# =========================================================
# 1. 기본 설정
# =========================================================

st.set_page_config(
    page_title="CINÉ | DAILY BOX OFFICE",
    page_icon="🎬",
    layout="wide",
)

SEOUL = ZoneInfo("Asia/Seoul")
TODAY = datetime.now(SEOUL).date()
YESTERDAY = TODAY - timedelta(days=1)

API_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)

# 실제 캐릭터 이미지가 있다면 영화 제목과 이미지 URL을 등록하세요.
# 이미지 URL은 공개적으로 접근 가능한 이미지 파일이어야 합니다.
# KOBIS API 자체는 포스터나 캐릭터 이미지를 제공하지 않습니다.
MOVIE_SCENES = {
    # 예시:
    # "영화 제목": {
    #     "images": [
    #         "https://example.com/character1.png",
    #         "https://example.com/character2.png",
    #     ],
    #     "emojis": ["🦸", "🦹"],
    #     "caption": "영화 장면 설명",
    # },
}


# =========================================================
# 2. 화면 디자인 및 애니메이션 CSS
# =========================================================

st.markdown(
    """
    <style>
    @import url(
      'https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500'
      '&family=Space+Grotesk:wght@400;500;600;700&display=swap'
    );

    :root {
        --ink: #191919;
        --paper: #f3f0e8;
        --red: #ef493c;
        --blue: #315ee8;
        --yellow: #f4c94b;
    }

    .stApp {
        background:
            radial-gradient(circle at 90% 5%,
                rgba(244,201,75,.22), transparent 22rem),
            radial-gradient(circle at 5% 35%,
                rgba(49,94,232,.10), transparent 25rem),
            var(--paper);
        color: var(--ink);
        font-family: 'Space Grotesk', sans-serif;
    }

    [data-testid="stSidebar"] {
        background: #e8e2d6;
        border-right: 1px solid #c9c3b8;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    .eyebrow {
        font-family: 'DM Mono', monospace;
        font-size: .72rem;
        letter-spacing: .14em;
        text-transform: uppercase;
    }

    .hero {
        position: relative;
        overflow: hidden;
        background: #faf7ef;
        border: 2px solid var(--ink);
        box-shadow: 7px 7px 0 var(--ink);
        padding: clamp(1.5rem, 4vw, 3.5rem);
        margin-bottom: 2rem;
    }

    .hero h1 {
        font-size: clamp(2.5rem, 6vw, 5.5rem);
        letter-spacing: -.075em;
        line-height: .92;
        margin: 1rem 0;
    }

    .hero-shape {
        position: absolute;
        right: 8%;
        top: 15%;
        width: 100px;
        height: 100px;
        background: var(--red);
        border: 2px solid var(--ink);
        border-radius: 50%;
        animation: floatShape 5s ease-in-out infinite;
    }

    .hero-shape::after {
        content: '';
        position: absolute;
        width: 65px;
        height: 65px;
        left: -35px;
        top: 55px;
        background: var(--yellow);
        border: 2px solid var(--ink);
        transform: rotate(25deg);
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: -.04em;
        border-bottom: 2px solid var(--ink);
        padding-bottom: .6rem;
        margin: 1.8rem 0 1rem;
    }

    .metric-card {
        border: 2px solid var(--ink);
        padding: 1.2rem;
        min-height: 135px;
        box-shadow: 5px 5px 0 var(--ink);
        animation: appear .45s ease both;
        transition: transform .2s ease;
    }

    .metric-card:hover {
        transform: translateY(-4px);
    }

    .metric-label {
        font-family: 'DM Mono', monospace;
        font-size: .72rem;
        letter-spacing: .08em;
    }

    .metric-value {
        font-size: clamp(1.8rem, 3vw, 2.8rem);
        font-weight: 700;
        letter-spacing: -.06em;
        margin-top: .7rem;
        overflow-wrap: anywhere;
    }

    /* 영화 장면 재생 영역 */
    .cinema {
        position: relative;
        overflow: hidden;
        min-height: 330px;
        padding: 1.5rem;
        border: 2px solid #171717;
        box-shadow: 7px 7px 0 #171717;
        isolation: isolate;
    }

    .cinema::before {
        content: '';
        position: absolute;
        inset: 0;
        z-index: -2;
        background:
            radial-gradient(circle at 50% 110%,
                var(--accent), transparent 45%),
            linear-gradient(135deg, var(--bg), var(--fg));
    }

    /* 영화관의 빛과 화면 질감 */
    .cinema::after {
        content: '';
        position: absolute;
        inset: 0;
        z-index: -1;
        pointer-events: none;
        background: repeating-linear-gradient(
            0deg,
            transparent 0px,
            transparent 3px,
            rgba(0,0,0,.045) 4px
        );
    }

    .cinema-header {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        font-family: 'DM Mono', monospace;
        font-size: .72rem;
        letter-spacing: .1em;
    }

    .scene-title {
        font-size: clamp(2rem, 5vw, 4rem);
        font-weight: 700;
        line-height: 1;
        letter-spacing: -.07em;
        margin-top: 1.3rem;
        overflow-wrap: anywhere;
        max-width: 95%;
    }

    .scene-stage {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: clamp(1rem, 5vw, 4rem);
        height: 150px;
        overflow: hidden;
    }

    .character {
        display: flex;
        align-items: center;
        justify-content: center;
        width: clamp(72px, 12vw, 120px);
        height: clamp(72px, 12vw, 120px);
        font-size: clamp(3rem, 8vw, 6rem);
        filter: drop-shadow(4px 6px 0 rgba(0,0,0,.18));
        animation: characterMove 3.2s ease-in-out infinite;
        will-change: transform;
    }

    .character:nth-child(2) {
        animation-delay: -.8s;
    }

    .character:nth-child(3) {
        animation-delay: -1.6s;
    }

    .character img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        filter: drop-shadow(4px 6px 0 rgba(0,0,0,.18));
    }

    .paused .character,
    .paused .scene-shape,
    .paused .film-light {
        animation-play-state: paused !important;
    }

    .scene-shape {
        position: absolute;
        z-index: -1;
        width: 90px;
        height: 90px;
        right: 8%;
        bottom: 14%;
        border: 2px solid var(--fg);
        background: var(--accent);
        transform: rotate(25deg);
        animation: rotateShape 9s linear infinite;
        opacity: .8;
    }

    .film-light {
        position: absolute;
        width: 200px;
        height: 450px;
        top: -70px;
        left: -230px;
        background: rgba(255,255,255,.18);
        transform: rotate(25deg);
        animation: lightSweep 6s ease-in-out infinite;
        pointer-events: none;
    }

    .scene-caption {
        font-family: 'DM Mono', monospace;
        font-size: .75rem;
        margin-top: .7rem;
    }

    @keyframes characterMove {
        0%, 100% { transform: translateY(8px) rotate(-5deg) scale(.96); }
        25% { transform: translateY(-16px) rotate(3deg) scale(1.03); }
        50% { transform: translateY(0) rotate(6deg) scale(1); }
        75% { transform: translateY(-8px) rotate(-2deg) scale(1.02); }
    }

    @keyframes rotateShape {
        from { transform: rotate(0deg) translateY(0); }
        50% { transform: rotate(180deg) translateY(-18px); }
        to { transform: rotate(360deg) translateY(0); }
    }

    @keyframes lightSweep {
        0% { left: -230px; }
        70%, 100% { left: 120%; }
    }

    @keyframes floatShape {
        0%, 100% { transform: translateY(0) rotate(0deg); }
        50% { transform: translateY(20px) rotate(20deg); }
    }

    @keyframes appear {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }

    div.stButton > button {
        border: 2px solid var(--ink);
        border-radius: 2px;
        font-weight: 700;
        transition: transform .15s ease, box-shadow .15s ease;
    }

    div.stButton > button:hover {
        transform: translate(-2px, -2px);
        box-shadow: 4px 4px 0 var(--ink);
    }

    @media (max-width: 650px) {
        .hero-shape { opacity: .25; right: -10px; }
        .cinema { padding: 1rem; min-height: 300px; }
        .scene-stage { gap: .6rem; }
    }

    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation: none !important;
            transition: none !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 3. 공통 함수
# =========================================================

def number_text(value):
    """숫자에 천 단위 쉼표를 붙입니다."""
    try:
        return f"{int(float(value)):,}"
    except (TypeError, ValueError):
        return "0"


def date_text(value):
    """개봉일을 보기 좋은 날짜로 바꿉니다."""
    try:
        return datetime.strptime(
            str(value), "%Y-%m-%d"
        ).strftime("%Y.%m.%d")
    except (TypeError, ValueError):
        return "정보 없음"


def palette(movie_name):
    """영화 제목마다 일정한 추상 색상 테마를 선택합니다."""
    themes = [
        ("#ef493c", "#faf5e9", "#f4c94b"),
        ("#315ee8", "#f6f0e5", "#ef493c"),
        ("#f4c94b", "#202020", "#ef493c"),
        ("#d9d5f2", "#202020", "#ef493c"),
        ("#1f6c5c", "#f7f0df", "#e9b7a6"),
        ("#e9b7a6", "#242424", "#f4c94b"),
    ]
    code = hashlib.sha256(
        str(movie_name).encode("utf-8")
    ).hexdigest()
    return themes[int(code[:8], 16) % len(themes)]


def get_api_key():
    """인증키는 코드에 쓰지 않고 Streamlit Secrets에서 읽습니다."""
    try:
        key = st.secrets.get("KOBIS_KEY", "")
    except Exception:
        key = ""

    if not key:
        raise RuntimeError(
            "KOBIS_KEY를 찾을 수 없습니다. "
            "Streamlit Cloud의 Settings → Secrets에 "
            'KOBIS_KEY = "발급받은_인증키"를 등록하세요.'
        )
    return key


@st.cache_data(ttl=900, show_spinner=False)
def load_box_office(target_date):
    """선택 날짜의 박스오피스를 API에서 가져옵니다."""
    params = {
        "key": get_api_key(),
        "targetDt": target_date.strftime("%Y%m%d"),
    }

    try:
        response = requests.get(
            API_URL, params=params, timeout=20
        )
        response.raise_for_status()
        payload = response.json()
    except requests.Timeout as exc:
        raise RuntimeError(
            "KOBIS 응답 시간이 초과되었습니다. 잠시 후 다시 시도하세요."
        ) from exc
    except requests.RequestException as exc:
        raise RuntimeError(
            "KOBIS 서버에 연결하지 못했습니다. "
            "네트워크와 API 서비스 상태를 확인하세요."
        ) from exc
    except ValueError as exc:
        raise RuntimeError(
            "API 응답을 JSON으로 읽지 못했습니다."
        ) from exc

    # 인증키 오류는 HTTP 200이어도 faultInfo로 올 수 있습니다.
    if payload.get("faultInfo"):
        info = payload["faultInfo"]
        raise RuntimeError(
            f"KOBIS API 오류: {info.get('message', '알 수 없는 오류')}. "
            "인증키와 API 이용 권한을 확인하세요."
        )

    result = payload.get("boxOfficeResult")
    if not isinstance(result, dict):
        raise RuntimeError(
            "boxOfficeResult가 없습니다. 인증키와 API 응답을 확인하세요."
        )

    return result.get("dailyBoxOfficeList", [])


def rank_arrow(value):
    """양수는 순위 상승, 음수는 순위 하락입니다."""
    value = int(value)
    if value > 0:
        return f"🔺 +{value}"
    if value < 0:
        return f"🔽 {value}"
    return "— 0"


def scene_html(movie_name, rank, opened, playing):
    """영화 장면 영역을 HTML로 만듭니다."""
    bg, fg, accent = palette(movie_name)
    scene = MOVIE_SCENES.get(movie_name, {})

    # 등록한 캐릭터 이미지가 있으면 이미지를 표시합니다.
    image_urls = scene.get("images", [])
    emojis = scene.get("emojis", ["🦸", "🌟", "🎭"])
    emojis = (emojis + ["✨", "🎬", "⭐"])[:3]

    characters = []
    for i in range(min(3, max(len(image_urls), len(emojis)))):
        if i < len(image_urls):
            # 이미지 URL은 설정자가 직접 등록한 주소입니다.
            url = escape(str(image_urls[i]), quote=True)
            characters.append(
                f'<div class="character">'
                f'<img src="{url}" alt="영화 캐릭터"></div>'
            )
        else:
            characters.append(
                f'<div class="character">{escape(str(emojis[i]))}</div>'
            )

    motion_class = "" if playing else "paused"
    title = escape(str(movie_name))
    caption = escape(
        str(scene.get("caption", "A MOMENT FROM THE MOVIE"))
    )
    status = "▶ PLAYING" if playing else "Ⅱ PAUSED"

    return f"""
    <div class="cinema {motion_class}"
         style="--bg:{bg};--fg:{fg};--accent:{accent};color:{fg};">
      <div class="film-light"></div>
      <div class="scene-shape"></div>
      <div class="cinema-header">
        <span>CINÉ / SCENE PREVIEW</span>
        <span>{status}</span>
      </div>
      <div class="scene-title">{title}</div>
      <div class="scene-stage">
        {''.join(characters)}
      </div>
      <div class="scene-caption">
        RANK {int(rank):02d} &nbsp; · &nbsp; RELEASE {escape(str(opened))}
        <br>{caption}
      </div>
    </div>
    """


# =========================================================
# 4. 페이지 헤더
# =========================================================

st.markdown(
    f"""
    <div class="hero">
      <div class="hero-shape"></div>
      <div class="eyebrow">
        KOBIS DATA / DAILY REPORT · 최대 조회 가능일 {YESTERDAY:%Y.%m.%d}
      </div>
      <h1>THE DAILY<br>BOX OFFICE.</h1>
      <p>영화의 기록을 읽고, 움직이는 장면으로 감상하는 박스오피스 아카이브.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 5. 날짜 선택 및 API 호출
# =========================================================

with st.sidebar:
    st.markdown("### 01 / 날짜 선택")

    selected_date = st.date_input(
        "조회할 날짜",
        value=YESTERDAY,
        min_value=date(2004, 1, 1),
        max_value=YESTERDAY,
        help="한국 시간 기준 어제까지 선택할 수 있습니다.",
    )

    st.caption(f"한국 시간 오늘: {TODAY:%Y.%m.%d}")

    if st.button("↻ 데이터 새로고침", use_container_width=True):
        load_box_office.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("### 02 / 장면 설정")
    playing = st.toggle("애니메이션 재생", value=True)
    st.caption("재생을 끄면 캐릭터와 도형의 움직임이 멈춥니다.")

if selected_date > YESTERDAY:
    st.error("오늘 이후 날짜는 조회할 수 없습니다.")
    st.stop()

st.markdown(
    f'<div class="eyebrow">DAILY REPORT / {selected_date:%Y.%m.%d}</div>',
    unsafe_allow_html=True,
)

try:
    with st.spinner("박스오피스 데이터를 불러오는 중입니다..."):
        movies = load_box_office(selected_date)
except Exception as error:
    st.error("박스오피스 데이터를 불러오지 못했습니다.")
    st.markdown(
        """
        **다음 사항을 확인해 주세요.**
        - Streamlit Cloud의 Settings → Secrets에 `KOBIS_KEY`가 등록되어 있는지
        - 인증키가 정확하고 KOBIS API 이용 권한이 유효한지
        - 네트워크와 KOBIS API 서비스가 정상인지
        """
    )
    st.code(str(error))
    st.stop()

if not movies:
    st.warning(
        f"**{selected_date:%Y년 %m월 %d일}: 그날은 아직 집계 전입니다.**\n\n"
        "영화 목록이 비어 있습니다. 다른 날짜를 선택하거나 "
        "KOBIS의 해당 날짜 집계 여부를 확인해 주세요."
    )
    st.stop()


# =========================================================
# 6. 데이터 정리
# =========================================================

df = pd.DataFrame(movies)

required = [
    "rank", "rankInten", "movieNm", "openDt",
    "audiCnt", "audiAcc", "scrnCnt",
]
for col in required:
    if col not in df.columns:
        df[col] = ""

for col in ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]:
    df[col] = pd.to_numeric(
        df[col], errors="coerce"
    ).fillna(0).astype(int)

df["movieNm"] = df["movieNm"].fillna("제목 정보 없음").astype(str)
df["openDt"] = df["openDt"].fillna("").astype(str)
df = df.sort_values("rank").reset_index(drop=True)


# =========================================================
# 7. 1위 영화 카드
# =========================================================

leader = df.iloc[0]
leader_name = leader["movieNm"]
bg, fg, accent = palette(leader_name)

st.markdown(
    '<div class="section-title">DAY’S LEADER / 1위 영화</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="metric-card" style="background:{bg};color:{fg};">
      <div class="metric-label">RANK NO. 01</div>
      <div class="metric-value">{escape(leader_name)}</div>
      <div>개봉일 {date_text(leader['openDt'])}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

a, b, c = st.columns(3)
cards = [
    (a, "DAILY AUDIENCE", leader["audiCnt"], "#ef493c", "#191919"),
    (b, "TOTAL AUDIENCE", leader["audiAcc"], "#f4c94b", "#191919"),
    (c, "SCREENS", leader["scrnCnt"], "#315ee8", "#ffffff"),
]

for col, label, value, color, text_color in cards:
    with col:
        st.markdown(
            f"""
            <div class="metric-card"
                 style="background:{color};color:{text_color};">
              <div class="metric-label">{label}</div>
              <div class="metric-value">{number_text(value)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# 8. 관객수 TOP 5 그래프
# =========================================================

st.markdown(
    '<div class="section-title">AUDIENCE RACE / 관객수 TOP 5</div>',
    unsafe_allow_html=True,
)

top5 = df.nlargest(5, "audiCnt").copy()
top5["영화명"] = top5.apply(
    lambda r: ("🏆 " if r["audiAcc"] > 1_000_000 else "")
    + r["movieNm"],
    axis=1,
)

fig = px.bar(
    top5.sort_values("audiCnt"),
    x="audiCnt",
    y="영화명",
    orientation="h",
    text="audiCnt",
    color="audiCnt",
    color_continuous_scale=["#315ee8", "#ef493c", "#f4c94b"],
    labels={"audiCnt": "일일 관객수", "영화명": ""},
)

fig.update_traces(
    texttemplate="%{text:,.0f}명",
    textposition="outside",
    cliponaxis=False,
)
fig.update_layout(
    height=350,
    margin=dict(l=8, r=45, t=10, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#191919"),
    showlegend=False,
    coloraxis_showscale=False,
)

st.plotly_chart(
    fig, use_container_width=True,
    config={"displayModeBar": False},
)


# =========================================================
# 9. 전체 순위표
# =========================================================

st.markdown(
    '<div class="section-title">FULL RANKING / 전체 순위</div>',
    unsafe_allow_html=True,
)

st.caption(
    "🔺 빨간 위쪽 기호: 순위 상승 · "
    "🔽 파란 아래쪽 기호: 순위 하락 · "
    "🏆 누적 관객 100만 명 초과"
)

table = df.copy()
table["순위"] = table["rank"].map(lambda x: f"{x}위")
table["전일 대비"] = table["rankInten"].map(rank_arrow)
table["영화명"] = table.apply(
    lambda r: ("🏆 " if r["audiAcc"] > 1_000_000 else "")
    + r["movieNm"],
    axis=1,
)
table["개봉일"] = table["openDt"].map(date_text)
table["관객수"] = table["audiCnt"].map(number_text)
table["누적관객"] = table["audiAcc"].map(number_text)
table["스크린 수"] = table["scrnCnt"].map(number_text)

st.dataframe(
    table[
        [
            "순위", "전일 대비", "영화명", "개봉일",
            "관객수", "누적관객", "스크린 수",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# 10. 영화 선택 및 장면 애니메이션
# =========================================================

st.markdown(
    '<div class="section-title">SCENE PREVIEW / 영화 장면 감상</div>',
    unsafe_allow_html=True,
)

movie_names = df["movieNm"].tolist()
selected_movie = st.selectbox(
    "장면을 감상할 영화를 선택하세요.",
    movie_names,
    key="selected_movie",
)

chosen = df.loc[df["movieNm"] == selected_movie].iloc[0]

# 선택한 영화의 장면을 다시 렌더링합니다.
st.markdown(
    scene_html(
        movie_name=selected_movie,
        rank=chosen["rank"],
        opened=date_text(chosen["openDt"]),
        playing=playing,
    ),
    unsafe_allow_html=True,
)

if selected_movie not in MOVIE_SCENES:
    st.info(
        "현재 영화에는 실제 캐릭터 이미지가 등록되어 있지 않아 "
        "추상적인 캐릭터 애니메이션을 표시하고 있습니다. "
        "실제 이미지를 사용하려면 코드 위쪽의 MOVIE_SCENES에 "
        "이미지 주소를 추가하세요."
    )

left, right = st.columns(2)
with left:
    st.metric("일일 관객수", f"{number_text(chosen['audiCnt'])}명")
    st.metric("누적 관객수", f"{number_text(chosen['audiAcc'])}명")
with right:
    st.metric("박스오피스 순위", f"{chosen['rank']}위")
    st.metric("스크린 수", f"{number_text(chosen['scrnCnt'])}개")

if chosen["rankInten"] > 0:
    st.markdown(f"전일 대비 🔺 **{chosen['rankInten']}계단 상승**")
elif chosen["rankInten"] < 0:
    st.markdown(f"전일 대비 🔽 **{abs(chosen['rankInten'])}계단 하락**")
else:
    st.markdown("전일 대비 순위 변동 없음")


# =========================================================
# 11. 데이터 출처
# =========================================================

st.markdown("---")
st.caption(
    "DATA SOURCE: KOBIS OPEN API. "
    "영화별 실제 포스터와 캐릭터 이미지는 별도 이미지 URL을 등록해야 합니다. "
    "애니메이션은 HTML/CSS 기반이며 실제 영화 영상을 재생하는 기능은 아닙니다."
)

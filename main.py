
import io
import os
import tempfile
from datetime import date, timedelta

import imageio.v2 as imageio
import numpy as np
import pandas as pd
import requests
import streamlit as st
import plotly.express as px
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# --------------------------------------------------
# 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="CINEMA LAB",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE = "https://image.tmdb.org/t/p/"
KOBIS_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)

try:
    TMDB_KEY = st.secrets.get("TMDB_API_KEY", "")
    KOBIS_KEY = st.secrets.get("KOBIS_KEY", "")
except Exception:
    TMDB_KEY = os.getenv("TMDB_API_KEY", "")
    KOBIS_KEY = os.getenv("KOBIS_KEY", "")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Playfair+Display:wght@500;600;700&display=swap');

.stApp {
    background:
      radial-gradient(ellipse at 15% 0%, #202c40 0%, transparent 38%),
      linear-gradient(140deg, #080b12 0%, #101522 55%, #090b10 100%);
    color: #f3f3f3;
}
.block-container {max-width: 1400px; padding-top: 2rem;}
h1, h2, h3 {font-family: 'Playfair Display', Georgia, serif;}
p, label, div, span {font-family: 'DM Sans', sans-serif;}
.hero {
    padding: 32px 0 25px;
    border-bottom: 1px solid #343a49;
    margin-bottom: 25px;
}
.eyebrow {
    color: #c6a86b;
    letter-spacing: .22em;
    font-size: 12px;
    font-weight: 700;
}
.hero-title {font-size: clamp(38px, 6vw, 72px); line-height: 1.0; margin: 10px 0;}
.subtle {color: #9da7b8;}
.metric-card {
    background: linear-gradient(135deg, #1c2432, #111722);
    border: 1px solid #30394a;
    border-radius: 15px;
    padding: 18px;
    min-height: 105px;
}
.metric-label {font-size: 12px; color: #a6b0c0;}
.metric-value {font-size: 25px; font-weight: 700; margin-top: 9px;}
.section-label {
    color: #c6a86b; letter-spacing: .15em;
    font-size: 12px; font-weight: 700;
}
div[data-testid="stDataFrame"] {border: 1px solid #30394a; border-radius: 12px;}
.stButton > button {
    border-radius: 10px; border: 1px solid #bda16c;
    background: #c6a86b; color: #10131a; font-weight: 700;
}
.stButton > button:hover {background: #e0c78e; color: #10131a;}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# API / 데이터 함수
# --------------------------------------------------
def tmdb_get(endpoint, params=None):
    if not TMDB_KEY:
        raise RuntimeError(
            "TMDB_API_KEY가 설정되지 않았습니다. "
            "Streamlit Cloud의 Settings → Secrets에서 등록하세요."
        )
    p = dict(params or {})
    p["api_key"] = TMDB_KEY
    p.setdefault("language", "ko-KR")
    r = requests.get(
        f"{TMDB_BASE}/{endpoint.lstrip('/')}",
        params=p,
        timeout=25,
    )
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and data.get("success") is False:
        raise RuntimeError(data.get("status_message", "TMDB API 오류"))
    return data


def get_image(url, timeout=25):
    if not url:
        return None
    try:
        r = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "CinemaLab/1.0"},
        )
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content)).convert("RGB")
        return im
    except Exception:
        return None


def tmdb_image(path, size="w780"):
    if not path:
        return None
    return f"{TMDB_IMAGE}{size}{path}"


def search_movies(query):
    data = tmdb_get(
        "search/movie",
        {"query": query, "include_adult": "false", "page": 1},
    )
    return data.get("results", [])


def get_movie_cast(movie_id):
    data = tmdb_get(f"movie/{movie_id}/credits")
    cast = []
    for person in data.get("cast", []):
        if person.get("profile_path"):
            cast.append({
                "name": person.get("name", "Unknown"),
                "character": person.get("character", ""),
                "profile": tmdb_image(person["profile_path"], "w500"),
            })
        if len(cast) >= 8:
            break
    return cast


def get_font(size, bold=False):
    candidates = []
    if bold:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
            "C:/Windows/Fonts/malgunbd.ttf",
        ]
    candidates += [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/malgun.ttf",
    ]
    for path in candidates:
        try:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def cover_crop(image, width, height, zoom=1.0, focus_x=0.5, focus_y=0.5):
    """이미지를 화면 비율에 맞춰 자르고 줌/패닝을 적용한다."""
    if image is None:
        return Image.new("RGB", (width, height), (15, 19, 29))

    image = image.convert("RGB")
    iw, ih = image.size
    scale = max(width / iw, height / ih) * zoom
    nw, nh = max(width, int(iw * scale)), max(height, int(ih * scale))
    image = image.resize((nw, nh), Image.Resampling.LANCZOS)

    max_x = max(0, nw - width)
    max_y = max(0, nh - height)
    left = int(max_x * min(1, max(0, focus_x)))
    top = int(max_y * min(1, max(0, focus_y)))
    return image.crop((left, top, left + width, top + height))


def rounded_portrait(image, size, radius=18):
    image = image.convert("RGB").resize(size, Image.Resampling.LANCZOS)
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size[0] - 1, size[1] - 1),
        radius=radius,
        fill=255,
    )
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.paste(image.convert("RGBA"), (0, 0), mask)
    return out


def generate_movie_video(movie, cast, duration=10, fps=18):
    """
    TMDB 배경 이미지와 출연진 프로필 이미지를 조합해 MP4를 생성한다.
    배경 줌, 패닝, 인물 카드 이동, 빛/그레인 효과, 타이틀 연출을 사용한다.
    """
    width, height = 960, 540
    total_frames = duration * fps

    backdrop = get_image(tmdb_image(movie.get("backdrop_path"), "w1280"))
    if backdrop is None:
        backdrop = get_image(tmdb_image(movie.get("poster_path"), "w780"))

    if backdrop is None:
        raise RuntimeError(
            "이 영화의 배경/포스터 이미지를 불러오지 못했습니다. "
            "다른 영화로 다시 시도해 주세요."
        )

    # 출연진 이미지 내려받기
    portraits = []
    for actor in cast[:5]:
        im = get_image(actor.get("profile"))
        if im is not None:
            portraits.append((actor, im))

    if not portraits:
        raise RuntimeError(
            "출연진 프로필 이미지를 불러오지 못했습니다. "
            "TMDB에서 이미지가 제공되는 영화인지 확인해 주세요."
        )

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    output_path = tmp.name
    tmp.close()

    title = movie.get("title") or movie.get("original_title") or "Untitled"
    original_title = movie.get("original_title") or ""
    year = (movie.get("release_date") or "")[:4]

    title_font = get_font(38, bold=True)
    small_font = get_font(18)
    name_font = get_font(17, bold=True)
    role_font = get_font(13)

    # 초당 fps 프레임으로 MP4 영상 인코딩
    with imageio.get_writer(
        output_path,
        fps=fps,
        codec="libx264",
        quality=7,
        macro_block_size=16,
        pixelformat="yuv420p",
    ) as writer:
        for frame_no in range(total_frames):
            t = frame_no / max(1, total_frames - 1)
            phase = frame_no / fps

            # 카메라가 배경을 천천히 확대하며 좌우로 이동
            zoom = 1.02 + 0.15 * t
            focus_x = 0.25 + 0.5 * (0.5 + 0.5 * np.sin(phase * 0.32))
            focus_y = 0.35 + 0.2 * (0.5 + 0.5 * np.sin(phase * 0.22))
            frame = cover_crop(
                backdrop, width, height, zoom, focus_x, focus_y
            ).convert("RGBA")

            # 어두운 색조와 하단 그라데이션을 합성
            shade = Image.new("RGBA", (width, height), (5, 9, 18, 95))
            frame = Image.alpha_composite(frame, shade)
            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            for y in range(height // 2, height):
                alpha = int(5 + 130 * ((y - height / 2) / (height / 2)))
                od.line((0, y, width, y), fill=(3, 5, 10, alpha))
            frame = Image.alpha_composite(frame, overlay)

            draw = ImageDraw.Draw(frame)

            # 위쪽 작은 영화 정보
            draw.text(
                (38, 28), "C I N E M A   L A B",
                font=small_font, fill=(231, 204, 146, 255)
            )
            if year:
                draw.text(
                    (width - 90, 30), year,
                    font=small_font, fill=(240, 240, 240, 220)
                )

            # 제목을 영상 중간부터 천천히 나타내기
            title_alpha = int(255 * min(1, max(0, t * 4)))
            title_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            td = ImageDraw.Draw(title_layer)
            td.text(
                (40, 365), title,
                font=title_font, fill=(255, 255, 255, title_alpha),
                stroke_width=1, stroke_fill=(0, 0, 0, title_alpha),
            )
            if original_title and original_title != title:
                td.text(
                    (43, 415), original_title[:70],
                    font=small_font, fill=(225, 225, 225, title_alpha),
                )
            frame = Image.alpha_composite(frame, title_layer)
            draw = ImageDraw.Draw(frame)
            
            # 출연진 이미지를 화면 좌우로 순차적으로 이동시킨다.
            card_w, card_h = 150, 205
            visible_start = 0.13
            visible_end = 0.80
            if visible_start <= t <= visible_end:
                local_t = (t - visible_start) / (visible_end - visible_start)
                max_cards = min(4, len(portraits))
                for idx in range(max_cards):
                    actor, portrait = portraits[idx]
                    # 카드가 시간차를 두고 등장
                    stagger = idx * 0.13
                    progress = min(1.0, max(0.0, (local_t - stagger) * 2.5))
                    if progress <= 0:
                        continue

                    x_target = 38 + idx * (card_w + 20)
                    x = int(x_target + (1 - progress) * (idx % 2 * 70 - 35))
                    y = 85 + int(10 * np.sin(phase * 1.2 + idx))
                    card = rounded_portrait(portrait, (card_w, card_h))

                    # 부드러운 그림자
                    shadow = Image.new("RGBA", (card_w + 20, card_h + 20), (0, 0, 0, 0))
                    sd = ImageDraw.Draw(shadow)
                    sd.rounded_rectangle(
                        (8, 8, card_w + 10, card_h + 10),
                        radius=20, fill=(0, 0, 0, 150)
                    )
                    shadow = shadow.filter(ImageFilter.GaussianBlur(8))
                    frame.alpha_composite(shadow, (x - 10, y - 6))
                    frame.alpha_composite(card, (x, y))

                    draw = ImageDraw.Draw(frame)
                    label_y = y + card_h + 8
                    name = actor.get("name", "")[:22]
                    role = actor.get("character", "")[:22]
                    draw.text(
                        (x + 2, label_y), name,
                        font=name_font, fill=(255, 255, 255, 245)
                    )
                    if role:
                        draw.text(
                            (x + 2, label_y + 25), role,
                            font=role_font, fill=(220, 215, 205, 230)
                        )

            # 움직이는 빛줄기
            light = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            ld = ImageDraw.Draw(light)
            sweep_x = int((phase * 115) % (width + 300)) - 150
            ld.polygon(
                [
                    (sweep_x, 0),
                    (sweep_x + 32, 0),
                    (sweep_x - 80, height),
                    (sweep_x - 112, height),
                ],
                fill=(255, 232, 190, 17),
            )
            frame = Image.alpha_composite(frame, light)

            # 얇은 프레임과 영화 필름 느낌의 상/하단 바
            draw = ImageDraw.Draw(frame)
            draw.rectangle((15, 15, width - 16, height - 16),
                           outline=(255, 255, 255, 45), width=1)
            draw.rectangle((0, 0, width, 12), fill=(0, 0, 0, 180))
            draw.rectangle((0, height - 12, width, height),
                           fill=(0, 0, 0, 180))

            # 미세한 필름 그레인
            rgb = np.array(frame.convert("RGB"), dtype=np.int16)
            rng = np.random.default_rng(frame_no)
            noise = rng.normal(0, 2.0, (height, width, 1))
            rgb = np.clip(rgb + noise, 0, 255).astype(np.uint8)
            writer.append_data(rgb)

    with open(output_path, "rb") as f:
        video_bytes = f.read()

    try:
        os.remove(output_path)
    except OSError:
        pass

    return video_bytes


# --------------------------------------------------
# 헤더
# --------------------------------------------------
st.markdown("""
<div class="hero">
  <div class="eyebrow">FILM DISCOVERY · DAILY BOX OFFICE · MOTION DESIGN</div>
  <div class="hero-title">CINEMA LAB</div>
  <div class="subtle">
    영화 데이터를 살펴보고, 실제 영화 이미지로 나만의 시네마틱 영상을 만든다.
  </div>
</div>
""", unsafe_allow_html=True)


# --------------------------------------------------
# 사이드바
# --------------------------------------------------
with st.sidebar:
    st.markdown("## 🎬 Cinema Lab")
    st.caption("영화 탐색 및 영상 합성")
    page = st.radio(
        "메뉴",
        ["오늘의 박스오피스", "영화 이미지로 영상 만들기"],
    )
    st.divider()
    st.caption("영화 이미지 및 정보 출처: TMDB")
    st.caption("비상업적 이용 시에도 TMDB의 출처 표시 조건을 확인하세요.")


# --------------------------------------------------
# 페이지 1: KOBIS 박스오피스
# --------------------------------------------------
if page == "오늘의 박스오피스":
    st.markdown("## Daily Box Office")
    st.write("한국 영화관 일일 박스오피스 데이터를 확인한다.")

    latest_date = date.today() - timedelta(days=1)
    selected_date = st.date_input(
        "조회 날짜",
        value=latest_date,
        min_value=date(2004, 1, 1),
        max_value=latest_date,
    )

    if st.button("박스오피스 조회", use_container_width=True):
        if not KOBIS_KEY:
            st.error(
                "KOBIS_KEY가 없습니다. Streamlit Secrets에 "
                "KOBIS_KEY를 등록해 주세요."
            )
        else:
            try:
                response = requests.get(
                    KOBIS_URL,
                    params={
                        "key": KOBIS_KEY,
                        "targetDt": selected_date.strftime("%Y%m%d"),
                        "itemPerPage": 10,
                    },
                    timeout=20,
                )
                response.raise_for_status()
                payload = response.json()
                fault = payload.get("faultInfo")
                if fault:
                    st.error(
                        f"KOBIS API 오류: {fault.get('message', '요청 실패')}"
                    )
                else:
                    rows = payload.get("boxOfficeResult", {}).get(
                        "dailyBoxOfficeList", []
                    )
                    if not rows:
                        st.info("그날은 아직 집계 전이거나 조회 결과가 없습니다.")
                    else:
                        df = pd.DataFrame(rows)
                        for col in [
                            "audiCnt", "audiAcc", "scrnCnt",
                            "rank", "rankInten",
                        ]:
                            if col in df:
                                df[col] = pd.to_numeric(
                                    df[col], errors="coerce"
                                ).fillna(0)

                        leader = df.iloc[0]
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.markdown(
                                f"""<div class="metric-card">
                                <div class="metric-label">오늘의 1위</div>
                                <div class="metric-value">{leader['movieNm']}</div>
                                </div>""",
                                unsafe_allow_html=True,
                            )
                        with c2:
                            st.markdown(
                                f"""<div class="metric-card">
                                <div class="metric-label">당일 관객 수</div>
                                <div class="metric-value">
                                {int(leader['audiCnt']):,}명</div></div>""",
                                unsafe_allow_html=True,
                            )
                        with c3:
                            st.markdown(
                                f"""<div class="metric-card">
                                <div class="metric-label">누적 관객 수</div>
                                <div class="metric-value">
                                {int(leader['audiAcc']):,}명</div></div>""",
                                unsafe_allow_html=True,
                            )

                        st.markdown("### 관객 수 TOP 10")
                        chart_df = df[["movieNm", "audiCnt"]].copy()
                        chart_df = chart_df.sort_values("audiCnt")
                        fig = px.bar(
                            chart_df,
                            x="audiCnt",
                            y="movieNm",
                            orientation="h",
                            labels={
                                "audiCnt": "당일 관객 수",
                                "movieNm": "영화",
                            },
                            text="audiCnt",
                        )
                        fig.update_traces(
                            marker_color="#c6a86b",
                            texttemplate="%{text:,.0f}",
                            textposition="outside",
                            cliponaxis=False,
                        )
                        fig.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            font_color="#eeeeee",
                            margin=dict(l=10, r=70, t=15, b=10),
                            xaxis=dict(showgrid=True, gridcolor="#30394a"),
                            yaxis=dict(showgrid=False),
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        st.markdown("### 전체 순위")
                        view = pd.DataFrame({
                            "순위": df["rank"].astype(int),
                            "전일 대비": df["rankInten"].apply(
                                lambda x: "NEW" if x == 0 and False
                                else (f"▲ {int(x)}" if x > 0
                                      else (f"▼ {abs(int(x))}" if x < 0
                                            else "—"))
                            ),
                            "영화 제목": df["movieNm"],
                            "당일 관객 수": df["audiCnt"].map(
                                lambda x: f"{int(x):,}"
                            ),
                            "누적 관객 수": df["audiAcc"].map(
                                lambda x: f"{int(x):,}"
                            ),
                            "상영관 수": df["scrnCnt"].astype(int),
                        })
                        st.dataframe(
                            view, hide_index=True, use_container_width=True
                        )
            except requests.RequestException as e:
                st.error(f"박스오피스 API 연결에 실패했습니다: {e}")
            except Exception as e:
                st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")


# --------------------------------------------------
# 페이지 2: 영화 이미지 기반 영상 생성
# --------------------------------------------------
else:
    st.markdown("## Make a Motion Scene")
    st.write(
        "영화 제목으로 검색한 뒤, 영화의 배경과 등장인물 이미지로 "
        "짧은 MP4 장면을 합성한다."
    )

    if not TMDB_KEY:
        st.warning(
            "TMDB_API_KEY가 설정되지 않았습니다. "
            "Settings → Secrets에 TMDB_API_KEY를 추가해 주세요."
        )

    query = st.text_input(
        "영화 제목",
        value="인터스텔라",
        placeholder="예: 인터스텔라, 기생충, Dune",
    )

    if st.button("영화 검색", use_container_width=True):
        if not TMDB_KEY:
            st.error("먼저 TMDB_API_KEY를 등록해 주세요.")
        elif not query.strip():
            st.warning("영화 제목을 입력해 주세요.")
        else:
            try:
                with st.spinner("영화 정보를 검색하고 있습니다..."):
                    results = search_movies(query.strip())
                st.session_state["movie_results"] = results
                st.session_state.pop("generated_video", None)
                if not results:
                    st.info("검색 결과가 없습니다. 다른 제목으로 시도해 주세요.")
            except Exception as e:
                st.error(f"영화 검색에 실패했습니다: {e}")

    results = st.session_state.get("movie_results", [])
    selected_movie = None

    if results:
        def movie_label(m):
            year = (m.get("release_date") or "")[:4]
            title = m.get("title") or m.get("original_title") or "제목 없음"
            original = m.get("original_title") or ""
            extra = f" / {original}" if original and original != title else ""
            return f"{title}{extra} ({year or '개봉 연도 미상'})"

        selected_index = st.selectbox(
            "영상으로 만들 영화 선택",
            options=list(range(len(results))),
            format_func=lambda i: movie_label(results[i]),
        )
        selected_movie = results[selected_index]

        left, right = st.columns([1, 2])
        with left:
            poster_url = tmdb_image(selected_movie.get("poster_path"), "w500")
            if poster_url:
                st.image(poster_url, use_container_width=True)
            else:
                st.info("포스터 이미지가 없습니다.")
        with right:
            st.markdown(f"### {selected_movie.get('title', '영화 제목')}")
            st.caption(selected_movie.get("original_title", ""))
            st.write(selected_movie.get("overview") or "등록된 줄거리가 없습니다.")
            st.write(
                f"개봉일: {selected_movie.get('release_date') or '정보 없음'}"
            )
            st.write(
                f"평점: {selected_movie.get('vote_average', 0)} / 10"
            )

        st.markdown("---")
        st.markdown("### 영상 연출 설정")
        col_a, col_b = st.columns(2)
        with col_a:
            duration = st.slider("영상 길이(초)", 6, 15, 10)
        with col_b:
            fps = st.select_slider(
                "영상 부드러움",
                options=[12, 15, 18, 24],
                value=18,
                format_func=lambda x: f"{x} FPS",
            )

        st.caption(
            "영상은 배경 줌/패닝, 출연진 이미지의 순차적 등장, "
            "타이틀과 빛 효과를 합성해 생성합니다."
        )

        if st.button("🎞️ MP4 영상 생성", use_container_width=True):
            try:
                with st.spinner(
                    "출연진 이미지를 내려받고 프레임을 합성하고 있습니다. "
                    "설정에 따라 잠시 걸릴 수 있습니다..."
                ):
                    cast = get_movie_cast(selected_movie["id"])
                    if not cast:
                        raise RuntimeError(
                            "출연진 프로필 이미지를 찾지 못했습니다."
                        )
                    video = generate_movie_video(
                        selected_movie, cast,
                        duration=duration, fps=fps,
                    )
                    st.session_state["generated_video"] = video
                    st.session_state["generated_title"] = (
                        selected_movie.get("title", "cinema_scene")
                    )
                    st.session_state["generated_cast"] = cast
            except Exception as e:
                st.error(f"영상 생성에 실패했습니다: {e}")

        video = st.session_state.get("generated_video")
        if video:
            st.markdown("### 생성된 시네마틱 영상")
            st.video(video, format="video/mp4")
            safe_title = "".join(
                c if c.isalnum() or c in "-_ " else "_"
                for c in st.session_state.get(
                    "generated_title", "cinema_scene"
                )
            ).strip().replace(" ", "_")
            st.download_button(
                "⬇️ MP4 영상 다운로드",
                data=video,
                file_name=f"{safe_title or 'cinema_scene'}.mp4",
                mime="video/mp4",
                use_container_width=True,
            )

            st.markdown("### 영상에 사용된 출연진 이미지")
            cast = st.session_state.get("generated_cast", [])
            cols = st.columns(min(4, max(1, len(cast))))
            for idx, person in enumerate(cast[:4]):
                with cols[idx % len(cols)]:
                    st.image(person["profile"], use_container_width=True)
                    st.caption(
                        f"**{person['name']}**\n\n"
                        f"{person.get('character') or ''}"
                    )

            st.caption(
                "영화 정보 및 이미지 출처: TMDB. "
                "TMDB API 사용 시 요구되는 출처 표시 및 이용 조건을 준수하세요."
            )

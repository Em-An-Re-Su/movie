
# -----------------------------
# 9. 영화 선택 + 자체 생성 시네마틱 장면
# -----------------------------
st.markdown(
    '<div class="section-title">FOCUS ON A FILM / 영화 들여다보기</div>',
    unsafe_allow_html=True,
)

movie_names = df.sort_values("rank")["movieNm"].tolist()
selected_movie = st.selectbox(
    "영화를 선택하면 상세 정보와 애니메이션 장면이 바뀝니다.",
    movie_names,
    key="cinematic_movie_select",
)

chosen = df.loc[df["movieNm"] == selected_movie].iloc[0]
focus_bg, focus_fg, focus_accent = get_palette(selected_movie)

# 영화 제목에 따라 장면의 분위기를 결정합니다.
# KOBIS 응답에 장르가 없으므로 제목의 단어를 바탕으로 추정하는 연출입니다.
title_lower = selected_movie.lower()

if any(word in title_lower for word in [
    "공포", "귀신", "악마", "살인", "저주", "호러", "horror", "devil"
]):
    mood = "horror"
    mood_label = "DARK / SUSPENSE"
elif any(word in title_lower for word in [
    "우주", "별", "은하", "로봇", "미래", "행성", "space", "star"
]):
    mood = "space"
    mood_label = "COSMIC / SCI-FI"
elif any(word in title_lower for word in [
    "사랑", "연애", "봄날", "첫사랑", "로맨스", "love", "heart"
]):
    mood = "romance"
    mood_label = "DREAM / ROMANCE"
elif any(word in title_lower for word in [
    "전쟁", "전투", "영웅", "군인", "전쟁", "war", "battle"
]):
    mood = "war"
    mood_label = "EPIC / DRAMA"
else:
    mood = "cinema"
    mood_label = "CINEMATIC / ABSTRACT"

# JSON 문자열로 안전하게 전달합니다.
film_title_js = json.dumps(selected_movie, ensure_ascii=False).replace("<", "\\u003c")
palette_js = json.dumps(
    {
        "background": focus_bg,
        "foreground": focus_fg,
        "accent": focus_accent,
        "mood": mood,
    },
    ensure_ascii=False,
)

scene_html = r"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { box-sizing: border-box; }
html, body {
    margin: 0; padding: 0; width: 100%; height: 100%;
    overflow: hidden; background: #101015;
    font-family: Arial, "Malgun Gothic", sans-serif;
}
.scene {
    width: 100%; height: 490px; position: relative; overflow: hidden;
    background: #101015; border: 2px solid #171717;
    isolation: isolate;
}
canvas {
    position: absolute; inset: 0; width: 100%; height: 100%;
    display: block;
}
.vignette {
    position: absolute; inset: 0; pointer-events: none;
    background:
      linear-gradient(0deg, rgba(0,0,0,.78), transparent 48%),
      radial-gradient(ellipse at center, transparent 25%, rgba(0,0,0,.55) 100%);
}
.topline {
    position: absolute; left: 22px; right: 22px; top: 18px;
    display: flex; justify-content: space-between; gap: 10px;
    color: rgba(255,255,255,.8); font: 10px monospace;
    letter-spacing: .17em; text-transform: uppercase;
}
.titlebox {
    position: absolute; left: 7%; right: 7%; bottom: 39px;
    color: #fff; pointer-events: none;
}
.kicker {
    font: 10px monospace; letter-spacing: .24em;
    text-transform: uppercase; margin-bottom: 12px;
    color: var(--accent, #f4c94b);
}
h2 {
    margin: 0; font-size: clamp(30px, 6vw, 62px);
    font-weight: 900; line-height: .98; letter-spacing: -.055em;
    text-shadow: 0 4px 30px rgba(0,0,0,.5);
    overflow-wrap: anywhere;
    animation: titleIn 1.2s cubic-bezier(.2,.7,.2,1) both;
}
.subtitle {
    margin-top: 14px; color: rgba(255,255,255,.76);
    font-size: 11px; letter-spacing: .12em;
}
.rec {
    position: absolute; top: 47px; left: 22px;
    color: #fff; font: 10px monospace; letter-spacing: .1em;
}
.dot {
    display: inline-block; width: 7px; height: 7px;
    background: #ef493c; border-radius: 50%; margin-right: 6px;
    animation: blink 1.4s infinite;
}
.corner {
    position: absolute; width: 24px; height: 24px;
    border-color: rgba(255,255,255,.7); border-style: solid;
}
.tl { top: 12px; left: 12px; border-width: 1px 0 0 1px; }
.tr { top: 12px; right: 12px; border-width: 1px 1px 0 0; }
.bl { bottom: 12px; left: 12px; border-width: 0 0 1px 1px; }
.br { bottom: 12px; right: 12px; border-width: 0 1px 1px 0; }
@keyframes titleIn {
    from { opacity: 0; transform: translateY(22px); filter: blur(8px); }
    to { opacity: 1; transform: translateY(0); filter: blur(0); }
}
@keyframes blink { 50% { opacity: .2; } }
@media (prefers-reduced-motion: reduce) {
    h2, .dot { animation: none; }
}
</style>
</head>
<body>
<div class="scene" id="scene">
    <canvas id="film"></canvas>
    <div class="vignette"></div>
    <div class="topline">
        <span>FRAME 001 / CINÉ LAB</span>
        <span id="moodLabel">CINEMATIC STUDY</span>
    </div>
    <div class="rec"><span class="dot"></span>SCENE IN MOTION</div>
    <div class="titlebox">
        <div class="kicker">A FILM EXPERIENCE</div>
        <h2 id="filmTitle"></h2>
        <div class="subtitle">LIGHT · DEPTH · MOVEMENT · ATMOSPHERE</div>
    </div>
    <div class="corner tl"></div><div class="corner tr"></div>
    <div class="corner bl"></div><div class="corner br"></div>
</div>

<script>
const filmTitle = __FILM_TITLE__;
const theme = __PALETTE__;
const canvas = document.getElementById("film");
const ctx = canvas.getContext("2d", { alpha: false });
const titleEl = document.getElementById("filmTitle");
const moodEl = document.getElementById("moodLabel");

titleEl.textContent = filmTitle;
moodEl.textContent = ({
    horror: "DARK / SUSPENSE",
    space: "COSMIC / SCI-FI",
    romance: "DREAM / ROMANCE",
    war: "EPIC / DRAMA",
    cinema: "CINEMATIC / ABSTRACT"
})[theme.mood] || "CINEMATIC";

let W = 900, H = 490, dpr = 1, t = 0;
let particles = [];
let stars = [];

function resize() {
    const rect = canvas.getBoundingClientRect();
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = Math.max(320, rect.width);
    H = Math.max(300, rect.height);
    canvas.width = Math.floor(W * dpr);
    canvas.height = Math.floor(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    stars = Array.from({length: 100}, () => ({
        x: Math.random() * W,
        y: Math.random() * H * .72,
        r: Math.random() * 1.6 + .2,
        p: Math.random() * Math.PI * 2
    }));
    particles = Array.from({length: 65}, () => ({
        x: Math.random() * W,
        y: Math.random() * H,
        r: Math.random() * 2.5 + .4,
        speed: Math.random() * .6 + .15,
        phase: Math.random() * 6.28
    }));
}
window.addEventListener("resize", resize);
resize();

function hexToRgb(hex) {
    const h = hex.replace("#", "");
    return [
        parseInt(h.slice(0, 2), 16),
        parseInt(h.slice(2, 4), 16),
        parseInt(h.slice(4, 6), 16)
    ];
}
const bgRGB = hexToRgb(theme.background);
const accentRGB = hexToRgb(theme.accent);

function rgba(rgb, a) {
    return `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a})`;
}
function line(x1, y1, x2, y2, color, width) {
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
}
function polygon(points, color) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(points[0][0], points[0][1]);
    for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i][0], points[i][1]);
    }
    ctx.closePath();
    ctx.fill();
}

function drawBackground(time) {
    const g = ctx.createLinearGradient(0, 0, W, H);
    g.addColorStop(0, theme.background);
    g.addColorStop(.48, "#20212b");
    g.addColorStop(1, "#08090e");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);

    // 천천히 움직이는 빛 덩어리와 카메라 패닝
    const drift = Math.sin(time * .22) * W * .09;
    const glow = ctx.createRadialGradient(
        W * .53 + drift, H * .32, 4,
        W * .53 + drift, H * .32, W * .68
    );
    glow.addColorStop(0, rgba(accentRGB, .30));
    glow.addColorStop(.45, rgba(bgRGB, .12));
    glow.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, W, H);

    // 먼 배경의 별 또는 비산 입자
    for (const s of stars) {
        const twinkle = .22 + .65 * (Math.sin(time * 1.3 + s.p) + 1) / 2;
        ctx.fillStyle = `rgba(255,255,255,${twinkle})`;
        ctx.beginPath();
        ctx.arc((s.x + drift * .15 + W) % W, s.y, s.r, 0, Math.PI * 2);
        ctx.fill();
    }

    if (theme.mood === "space") {
        // 성운과 행성
        const px = W * (.72 + .025 * Math.sin(time * .2));
        const py = H * .30;
        const planet = ctx.createRadialGradient(px - 22, py - 22, 3, px, py, H * .18);
        planet.addColorStop(0, "#fff2ce");
        planet.addColorStop(.25, theme.accent);
        planet.addColorStop(1, "#24243b");
        ctx.fillStyle = planet;
        ctx.beginPath();
        ctx.arc(px, py, H * .12, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = "rgba(255,255,255,.35)";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.ellipse(px, py, H * .20, H * .055, -.25, 0, Math.PI * 2);
        ctx.stroke();
    } else if (theme.mood === "horror") {
        // 달빛과 어두운 안개
        const mx = W * .76, my = H * .23;
        ctx.fillStyle = "rgba(220,225,255,.72)";
        ctx.beginPath();
        ctx.arc(mx, my, H * .065, 0, Math.PI * 2);
        ctx.fill();
        for (let i = 0; i < 5; i++) {
            const y = H * (.44 + i * .055);
            ctx.fillStyle = `rgba(170,180,210,${.025 + .015 * Math.sin(time + i)})`;
            ctx.fillRect(0, y + Math.sin(time + i) * 8, W, 32);
        }
    } else {
        // 기하학적 빛의 원
        ctx.save();
        ctx.translate(W * .76 + drift * .25, H * .30);
        ctx.rotate(time * .06);
        ctx.strokeStyle = rgba(accentRGB, .5);
        ctx.lineWidth = 1.2;
        for (let i = 0; i < 4; i++) {
            ctx.beginPath();
            ctx.ellipse(0, 0, H * (.10 + i * .045), H * (.035 + i * .018), i * .2, 0, Math.PI * 2);
            ctx.stroke();
        }
        ctx.restore();
    }

    // 여러 깊이의 산·도시 실루엣: 움직이는 시차 효과
    const shift = Math.sin(time * .12) * 10;
    polygon([
        [0,H*.59],[W*.12,H*.40],[W*.24,H*.58],[W*.39,H*.36],
        [W*.54,H*.59],[W*.68,H*.42],[W*.82,H*.58],[W,H*.43],[W,H],[0,H]
    ], theme.mood === "horror" ? "#161722" : "#171923");

    polygon([
        [0,H*.70],[W*.18,H*.55],[W*.31,H*.71],[W*.50,H*.51],
        [W*.68,H*.72],[W*.84,H*.55],[W,H*.68],[W,H],[0,H]
    ], "#101219");

    // 먼 도시의 창문
    for (let i = 0; i < 34; i++) {
        const x = ((i * 73 + shift * (i % 3 + 1)) % (W + 30));
        const baseY = H * (.64 + (i % 5) * .035);
        const bw = 7 + (i % 4) * 3;
        const bh = 20 + (i % 6) * 8;
        ctx.fillStyle = i % 4 === 0 ? rgba(accentRGB, .40) : "rgba(210,220,255,.12)";
        ctx.fillRect(x, baseY, bw, bh);
    }

    // 바닥 원근선
    const horizon = H * .72;
    ctx.strokeStyle = "rgba(255,255,255,.11)";
    ctx.lineWidth = 1;
    for (let i = -8; i <= 8; i++) {
        ctx.beginPath();
        ctx.moveTo(W / 2, horizon);
        ctx.lineTo(W / 2 + i * W * .18, H);
        ctx.stroke();
    }
    for (let i = 1; i <= 7; i++) {
        const y = horizon + i * i * H * .006;
        line(0, y, W, y, "rgba(255,255,255,.07)", 1);
    }
}

function drawCharacter(time) {
    // 실제 영화 캐릭터를 복제하는 대신 자체 생성한 인물 실루엣
    const walk = Math.sin(time * 3.2);
    const stride = Math.sin(time * 3.2) * H * .025;
    const bob = Math.abs(Math.sin(time * 3.2)) * 3;
    const x = W * (.50 + Math.sin(time * .18) * .10);
    const ground = H * .80;
    const scale = Math.min(W / 850, H / 440) * 1.25;

    ctx.save();
    ctx.translate(x, ground + bob);
    ctx.scale(scale, scale);

    // 바닥 그림자
    const shadow = ctx.createRadialGradient(0, 0, 4, 0, 0, 70);
    shadow.addColorStop(0, "rgba(0,0,0,.65)");
    shadow.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = shadow;
    ctx.beginPath();
    ctx.ellipse(0, 0, 70, 12, 0, 0, Math.PI * 2);
    ctx.fill();

    const silhouette = theme.mood === "romance" ? "#211b29" : "#090a0e";
    const edge = rgba(accentRGB, .65);

    // 다리 애니메이션
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    line(-8, -57, -13 + stride, -9, silhouette, 16);
    line(9, -57, 13 - stride, -9, silhouette, 16);
    line(-13 + stride, -9, -25 + stride, -3, silhouette, 10);
    line(13 - stride, -9, 24 - stride, -3, silhouette, 10);

    // 몸통과 어깨
    polygon([[-19,-112],[17,-112],[25,-65],[12,-54],[-14,-54],[-24,-67]], silhouette);
    line(-17, -105, -29 - walk * 5, -72, silhouette, 11);
    line(17, -105, 28 + walk * 5, -75, silhouette, 11);

    // 머리
    ctx.fillStyle = silhouette;
    ctx.beginPath();
    ctx.arc(0, -129, 16, 0, Math.PI * 2);
    ctx.fill();

    // 윤곽에 얇은 빛을 더해 실루엣의 입체감 연출
    line(16, -108, 20, -75, edge, 1.2);
    line(8, -55, 12, -22, edge, 1.2);

    // 장르별 보조 오브젝트
    if (theme.mood === "war") {
        line(-17, -103, -31, -89, edge, 2);
        line(-31, -89, -26, -76, silhouette, 7);
    } else if (theme.mood === "romance") {
        ctx.fillStyle = rgba(accentRGB, .9);
        ctx.beginPath();
        ctx.arc(28, -81, 4, 0, Math.PI * 2);
        ctx.fill();
    } else if (theme.mood === "space") {
        ctx.strokeStyle = edge;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(0, -128, 21, -.7, 2.1);
        ctx.stroke();
    }

    ctx.restore();
}

function drawParticles(time) {
    for (const p of particles) {
        p.y -= p.speed;
        p.x += Math.sin(time + p.phase) * .35;
        if (p.y < -10) {
            p.y = H + 10;
            p.x = Math.random() * W;
        }
        const alpha = .15 + .38 * (Math.sin(time * 1.4 + p.phase) + 1) / 2;
        ctx.fillStyle = rgba(accentRGB, alpha);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
    }
}

function drawLightSweep(time) {
    const x = ((time * 40) % (W + 300)) - 150;
    const beam = ctx.createLinearGradient(x - 120, 0, x + 120, 0);
    beam.addColorStop(0, "rgba(255,255,255,0)");
    beam.addColorStop(.5, "rgba(255,255,255,.045)");
    beam.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = beam;
    ctx.fillRect(0, 0, W, H);
}

function frame() {
    t += 1 / 60;
    ctx.clearRect(0, 0, W, H);

    // 느린 카메라 줌 인·아웃
    const zoom = 1.015 + Math.sin(t * .23) * .018;
    ctx.save();
    ctx.translate(W / 2, H / 2);
    ctx.scale(zoom, zoom);
    ctx.translate(-W / 2, -H / 2);

    drawBackground(t);
    drawParticles(t);
    drawCharacter(t);
    drawLightSweep(t);

    ctx.restore();

    // 필름 그레인
    for (let i = 0; i < 70; i++) {
        const x = Math.random() * W;
        const y = Math.random() * H;
        ctx.fillStyle = `rgba(255,255,255,${Math.random() * .045})`;
        ctx.fillRect(x, y, 1.5, 1.5);
    }

    requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
</script>
</body>
</html>
"""

scene_html = (
    scene_html
    .replace("__FILM_TITLE__", film_title_js)
    .replace("__PALETTE__", palette_js)
)

st.markdown(
    f"""
    <div class="eyebrow">03 / MOTION STUDY · {mood_label}</div>
    <p style="margin-top:.5rem;color:#555;">
      선택한 영화의 분위기를 바탕으로 배경·빛·인물 실루엣을 실시간 생성합니다.
      실제 영화 장면이나 공식 캐릭터를 가져오는 방식은 아닙니다.
    </p>
    """,
    unsafe_allow_html=True,
)

components.html(scene_html, height=510, scrolling=False)

# 선택 영화의 기존 정보 카드
st.markdown(
    '<div class="section-title">FILM DATA / 선택 영화의 기록</div>',
    unsafe_allow_html=True,
)

left, right = st.columns([1.3, 1])

with left:
    st.markdown(
        f"""
        <div class="film-panel" style="background:{focus_bg};color:{focus_fg};">
          <div class="eyebrow">SELECTED FILM / RANK {int(chosen['rank']):02d}</div>
          <div class="film-title">
            {'🏆 ' if chosen['audiAcc'] > 1_000_000 else ''}{selected_movie}
          </div>
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
    '<div class="eyebrow">DATA SOURCE / KOBIS OPEN API · GENERATED CINEMATIC VISUAL</div>',
    unsafe_allow_html=True,
)
st.caption(
    "박스오피스 수치는 KOBIS Open API에서 가져옵니다. "
    "움직이는 장면은 브라우저에서 생성한 시각 효과이며, 실제 영화 영상이나 캐릭터가 아닙니다."
)

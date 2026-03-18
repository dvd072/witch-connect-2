from flask import Flask, request, redirect, session, render_template_string, url_for
import os
import random
import datetime

from game_data import (
    cards,
    emotions,
    special_readings,
    cat_lines,
    cat_talks,
    resident_npc,
    rarity_label,
    forest_data,
)
from shared_store import load_shared_data, save_shared_data
from forest_system import (
    ensure_forest_state,
    reset_forest_run,
    consume_forest_energy,
    draw_forest_item,
    draw_forest_event,
    generate_forest_scene,
    resolve_forest_event,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "witch-connect-integrated-secret")


def add_to_collection(card_name):
    collection = session.get("collection", [])
    if card_name not in collection:
        collection.append(card_name)
        session["collection"] = collection
        session.modified = True


def weighted_draw():
    r = random.random()
    if r < 0.68:
        pool = [c for c in cards if c["rarity"] == "common"]
    elif r < 0.90:
        pool = [c for c in cards if c["rarity"] == "rare"]
    elif r < 0.985:
        pool = [c for c in cards if c["rarity"] == "epic"]
    else:
        pool = [c for c in cards if c["rarity"] == "legend"]
    return random.choice(pool)


def owned_card_draw():
    owned_names = session.get("collection", [])
    owned_cards = [c for c in cards if c["name"] in owned_names]

    if not owned_cards:
        return weighted_draw()

    rarity_groups = {
        "common": [c for c in owned_cards if c["rarity"] == "common"],
        "rare": [c for c in owned_cards if c["rarity"] == "rare"],
        "epic": [c for c in owned_cards if c["rarity"] == "epic"],
        "legend": [c for c in owned_cards if c["rarity"] == "legend"]
    }

    r = random.random()
    if r < 0.68 and rarity_groups["common"]:
        pool = rarity_groups["common"]
    elif r < 0.90 and rarity_groups["rare"]:
        pool = rarity_groups["rare"]
    elif r < 0.985 and rarity_groups["epic"]:
        pool = rarity_groups["epic"]
    elif rarity_groups["legend"]:
        pool = rarity_groups["legend"]
    else:
        pool = owned_cards

    return random.choice(pool)


def build_reading(card, emotion):
    base = random.choice(card["meanings"])
    emotion_line = {
        "외로움": "지금 당신은 연결과 이해를 바라고 있습니다.",
        "불안": "확실하지 않은 미래가 마음을 흔들고 있습니다.",
        "분노": "참아 온 감정이 강하게 움직이고 있습니다.",
        "희망": "아직 포기하지 않은 마음이 안쪽에서 버티고 있습니다.",
        "혼란": "지금은 결정보다 정리가 먼저일 수 있습니다.",
        "슬픔": "슬픔을 밀어내기보다 받아들이는 시간이 필요할 수 있습니다."
    }.get(emotion, "")
    special = special_readings.get((card["name"], emotion))
    return base, emotion_line, special


def find_question(question_id):
    for item in session.get("questions", []):
        if item["id"] == question_id:
            return item
    return None


def ensure_data():
    today = str(datetime.date.today())

    if "user_id" not in session:
        session["user_id"] = str(int(datetime.datetime.now().timestamp() * 1000)) + str(random.randint(1000, 9999))
    if "today_date" not in session:
        session["today_date"] = ""
    if "today_card" not in session:
        session["today_card"] = None
    if "collection" not in session:
        session["collection"] = []
    if "questions" not in session:
        session["questions"] = []
    if "feedbacks" not in session:
        session["feedbacks"] = []
    if "received_readings" not in session:
        session["received_readings"] = []
    if "letter_feedbacks" not in session:
        session["letter_feedbacks"] = []
    if "sent_letters_feedbacks" not in session:
        session["sent_letters_feedbacks"] = []
    if "runes" not in session:
        session["runes"] = 0
    if "cat_line" not in session:
        session["cat_line"] = random.choice(cat_lines)
    if "cat_today_line" not in session:
        session["cat_today_line"] = random.choice(cat_talks)
    if "resident_date" not in session:
        session["resident_date"] = ""
    if "resident_today" not in session:
        session["resident_today"] = None
    if "resident_history" not in session:
        session["resident_history"] = []
    if "login_reward_date" not in session:
        session["login_reward_date"] = ""

    if session["login_reward_date"] != today:
        session["runes"] = session.get("runes", 0) + 300
        session["login_reward_date"] = today
        session.modified = True

    if session["today_date"] != today:
        card = random.choice(cards)
        meaning = random.choice(card["meanings"])
        session["today_date"] = today
        session["today_card"] = {
            "name": card["name"],
            "keyword": card["keyword"],
            "rarity": rarity_label[card["rarity"]],
            "meaning": meaning
        }
        add_to_collection(card["name"])
        session["cat_line"] = random.choice(cat_lines)
        session["cat_today_line"] = random.choice(cat_talks)
        session.modified = True

    if session["resident_date"] != today:
        picked_problem = random.choice(resident_npc["problems"])
        picked_line = random.choice(resident_npc["lines"])

        session["resident_today"] = {
            "id": f"resident-{today}",
            "name": resident_npc["name"],
            "line": picked_line,
            "problem_title": picked_problem["title"],
            "problem_text": picked_problem["text"],
            "status": "pending",
            "card_name": "",
            "card_keyword": "",
            "card_rarity": "",
            "reading_base": "",
            "reading_emotion": "",
            "reading_special": "",
            "selected_slot": None,
            "reward_claimed": False
        }

        session["resident_date"] = today
        session.modified = True

    ensure_forest_state(session, today)


def page(title, body):
    return render_template_string(
        """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  <style>
    * { box-sizing: border-box; }
    :root {
      --bg: #0f0b1a;
      --panel: rgba(255,255,255,0.08);
      --panel-strong: rgba(255,255,255,0.12);
      --line: rgba(255,255,255,0.12);
      --text: #f5efff;
      --sub: #cbbce7;
      --accent: #9d7bff;
      --accent-2: #6de2ff;
      --gold: #f8d47a;
      --shadow: 0 16px 40px rgba(0,0,0,0.35);
    }

    html, body {
      margin: 0;
      background:
        radial-gradient(circle at top, #2a194f 0%, #171027 35%, #0f0b1a 100%);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      min-height: 100%;
    }

    body {
      padding-bottom: 96px;
    }

    .wrap {
      max-width: 760px;
      margin: 0 auto;
      padding: 20px 16px 110px;
    }

    .hero {
      background: linear-gradient(135deg, rgba(109,226,255,0.12), rgba(157,123,255,0.18));
      backdrop-filter: blur(12px);
      border: 1px solid var(--line);
      color: var(--text);
      border-radius: 28px;
      padding: 24px;
      box-shadow: var(--shadow);
      margin-bottom: 16px;
    }

    .hero h1, .hero h2 {
      margin: 0 0 8px;
      letter-spacing: -0.02em;
    }

    .sub {
      margin: 0;
      color: var(--sub);
      line-height: 1.55;
    }

    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      backdrop-filter: blur(14px);
      border-radius: 24px;
      padding: 18px;
      margin: 14px 0;
      box-shadow: var(--shadow);
    }

    .btn, button {
      display: inline-block;
      width: 100%;
      border: none;
      border-radius: 18px;
      padding: 14px 16px;
      background: linear-gradient(135deg, #7e59ef, #5ed7ff);
      color: white;
      text-align: center;
      text-decoration: none;
      font-size: 16px;
      font-weight: 700;
      cursor: pointer;
      margin-top: 10px;
      box-shadow: 0 10px 24px rgba(86, 135, 255, 0.28);
      transition: transform .15s ease, opacity .15s ease;
    }

    .btn:hover, button:hover {
      transform: translateY(-2px);
      opacity: .96;
    }

    .btn.secondary, button.secondary {
      background: rgba(255,255,255,0.08);
      color: var(--text);
      border: 1px solid var(--line);
      box-shadow: none;
    }

    .btn.ghost {
      background: rgba(255,255,255,0.04);
      color: var(--sub);
      border: 1px solid var(--line);
      box-shadow: none;
    }

    input, select, textarea {
      width: 100%;
      padding: 14px;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.07);
      color: var(--text);
      font-size: 16px;
      margin-top: 10px;
      outline: none;
    }

    textarea { min-height: 110px; resize: vertical; }
    option { color: black; }

    .pill {
      display: inline-block;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(157,123,255,0.18);
      color: #f0e8ff;
      font-size: 14px;
      margin-right: 8px;
      margin-bottom: 8px;
      border: 1px solid rgba(255,255,255,0.1);
    }

    .big {
      font-size: 30px;
      font-weight: 800;
      margin: 8px 0;
      letter-spacing: -0.03em;
    }

    .small {
      font-size: 14px;
      color: var(--sub);
    }

    .divider {
      height: 1px;
      background: var(--line);
      margin: 16px 0;
    }

    .grid6 {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }

    .tarot-back {
      border-radius: 22px;
      padding: 24px 14px;
      min-height: 140px;
      background:
        radial-gradient(circle at top, rgba(157,123,255,0.25), rgba(255,255,255,0.03)),
        linear-gradient(135deg, #241539, #3b245f 60%, #1d1232);
      color: white;
      font-weight: 700;
      border: 1px solid rgba(255,255,255,0.16);
      position: relative;
      overflow: hidden;
    }

    .tarot-back::before {
      content: "✦";
      position: absolute;
      top: 12px;
      left: 14px;
      opacity: .7;
      font-size: 18px;
    }

    .tarot-back::after {
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(120deg, transparent 30%, rgba(255,255,255,0.12), transparent 70%);
      transform: translateX(-120%);
      transition: transform .5s ease;
    }

    .tarot-back:hover::after {
      transform: translateX(120%);
    }

    .item {
      padding: 12px 0;
      border-bottom: 1px solid rgba(255,255,255,0.08);
    }

    .room-map {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    .room-node {
      min-height: 112px;
      padding: 16px;
      border-radius: 22px;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.1);
      box-shadow: var(--shadow);
      text-decoration: none;
      color: var(--text);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: transform .18s ease, background .18s ease;
    }

    .room-node:hover {
      transform: translateY(-3px) scale(1.01);
      background: rgba(255,255,255,0.1);
    }

    .room-node .icon {
      font-size: 28px;
      margin-bottom: 8px;
    }

    .room-node .title {
      font-size: 17px;
      font-weight: 700;
    }

    .room-node .desc {
      font-size: 13px;
      color: var(--sub);
      line-height: 1.45;
    }

    .splash {
      position: fixed;
      inset: 0;
      background: radial-gradient(circle at center, #2b1a54 0%, #120d1d 60%, #09070f 100%);
      z-index: 9999;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: opacity .5s ease, visibility .5s ease;
    }

    .splash.hidden {
      opacity: 0;
      visibility: hidden;
      pointer-events: none;
    }

    .splash-inner {
      text-align: center;
      padding: 24px;
    }

    .orb {
      font-size: 68px;
      filter: drop-shadow(0 0 18px rgba(109,226,255,0.6));
      animation: floatOrb 2.4s ease-in-out infinite;
    }

    .logo {
      font-size: 32px;
      font-weight: 800;
      margin-top: 16px;
      letter-spacing: -0.03em;
    }

    .tap {
      margin-top: 10px;
      color: var(--sub);
      font-size: 14px;
      letter-spacing: .08em;
      text-transform: uppercase;
    }

    @keyframes floatOrb {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-8px); }
    }

    .toast {
      position: fixed;
      left: 50%;
      bottom: 108px;
      transform: translateX(-50%) translateY(20px);
      background: rgba(15, 10, 25, 0.92);
      border: 1px solid rgba(255,255,255,0.12);
      color: white;
      padding: 12px 16px;
      border-radius: 16px;
      box-shadow: var(--shadow);
      opacity: 0;
      pointer-events: none;
      transition: .25s ease;
      z-index: 9998;
      font-size: 14px;
      min-width: 180px;
      text-align: center;
    }

    .toast.show {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }

    .bottom-nav {
      position: fixed;
      left: 50%;
      bottom: 14px;
      transform: translateX(-50%);
      width: min(740px, calc(100% - 20px));
      background: rgba(23,16,39,0.88);
      border: 1px solid rgba(255,255,255,0.1);
      backdrop-filter: blur(14px);
      border-radius: 24px;
      padding: 10px;
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 8px;
      box-shadow: var(--shadow);
      z-index: 1000;
    }

    .nav-link {
      text-decoration: none;
      color: var(--sub);
      font-size: 12px;
      text-align: center;
      padding: 8px 4px;
      border-radius: 16px;
      transition: .18s ease;
    }

    .nav-link:hover {
      background: rgba(255,255,255,0.08);
      color: white;
    }

    .nav-link .nav-icon {
      display: block;
      font-size: 18px;
      margin-bottom: 4px;
    }

    @media (max-width: 640px) {
      .room-map {
        grid-template-columns: 1fr;
      }
      .grid6 {
        grid-template-columns: repeat(2, 1fr);
      }
      .big {
        font-size: 26px;
      }
    }
  </style>
</head>
<body>
  <div id="splash" class="splash">
    <div class="splash-inner">
      <div class="orb">🔮</div>
      <div class="logo">Witch Connect</div>
      <div class="tap">Tap to Enter</div>
    </div>
  </div>

  <div class="wrap">
    {{ body|safe }}
  </div>

  <div id="toast" class="toast"></div>

  <nav class="bottom-nav">
    <a class="nav-link" href="/workroom"><span class="nav-icon">🕯️</span>작업실</a>
    <a class="nav-link" href="/book"><span class="nav-icon">📖</span>마법책</a>
    <a class="nav-link" href="/collection"><span class="nav-icon">🃏</span>도감</a>
    <a class="nav-link" href="/board"><span class="nav-icon">📝</span>광장</a>
    <a class="nav-link" href="/assistant"><span class="nav-icon">🐈‍⬛</span>조수</a>
  </nav>

  <script>
    (function() {
      const splash = document.getElementById("splash");
      const seen = sessionStorage.getItem("witchconnect_seen_splash");

      if (seen) {
        splash.classList.add("hidden");
      } else {
        splash.addEventListener("click", function() {
          sessionStorage.setItem("witchconnect_seen_splash", "1");
          splash.classList.add("hidden");
        });
      }

      const toastText = "{{ request.args.get('toast', '') }}";
      if (toastText) {
        const toast = document.getElementById("toast");
        toast.textContent = toastText;
        toast.classList.add("show");
        setTimeout(() => toast.classList.remove("show"), 2200);
      }

      document.querySelectorAll(".tarot-back").forEach(function(btn) {
        btn.addEventListener("click", function() {
          btn.style.transform = "scale(0.95) rotateY(180deg)";
          btn.style.transition = "transform .35s ease";
        });
      });
    })();
  </script>
</body>
</html>
        """,
        title=title,
        body=body
    )


@app.route("/")
def home():
    ensure_data()
    today_card = session.get("today_card", {})

    body = f"""
    <div class="hero">
      <h1>🔮 Witch Connect</h1>
    </div>

    <div class="card">
      <div class="small">오늘의 카드</div>
      <div class="big">{today_card.get('name', '')}</div>
      <div class="pill">{today_card.get('keyword', '')}</div>
      <div class="pill">{today_card.get('rarity', '')}</div>
      <p>{today_card.get('meaning', '')}</p>
    </div>

    <a class="btn" href="/workroom">작업실로 들어가기</a>
    <a class="btn secondary" href="/forest">사이프러스의 숲</a>
    """
    return page("Witch Connect", body)


@app.route("/workroom")
def workroom():
    ensure_data()
    shared = load_shared_data()

    pending = [q for q in session.get("questions", []) if q["status"] == "pending"]
    done = [q for q in session.get("questions", []) if q["status"] == "done"]
    resident_today = session.get("resident_today")

    my_user_id = session.get("user_id")
    open_letters = [
        l for l in shared.get("letters", [])
        if l["status"] == "open" and l.get("author_id") != my_user_id
    ]

    rune_count = session.get("runes", 0)
    resident_status = "상담 대기 중" if resident_today and resident_today["status"] == "pending" else "상담 완료"

    pending_html = ""
    if pending:
        for q in reversed(pending):
            pending_html += f"""
            <div class="item">
              <div class="small">대기 중인 점괘</div>
              <div>{q['question']}</div>
              <div class="pill">{q['emotion']}</div>
              <a class="btn" href="/reading/{q['id']}/draw">점괘 보러가기</a>
            </div>
            """
    else:
        pending_html = "<p class='small'>아직 대기 중인 점괘가 없어.</p>"

    recent_html = ""
    if done:
        for q in reversed(done[-3:]):
            recent_html += f"""
            <div class="item">
              <div class="small">최근 확인한 개인 점괘</div>
              <div>{q['question']}</div>
              <div class="pill">{q['emotion']}</div>
              <div class="pill">{q['card_name']}</div>
              <a class="btn ghost" href="/reading/{q['id']}/result">점괘 다시 보기</a>
            </div>
            """
    else:
        recent_html = "<p class='small'>아직 완료된 점괘가 없어.</p>"

    letters_html = ""
    if open_letters:
        for letter in reversed(open_letters[:5]):
            letters_html += f"""
            <div class="item">
              <div class="small">익명 유저의 편지</div>
              <div>{letter['text']}</div>
              <a class="btn" href="/letter/{letter['id']}/draw">작업실에서 확인하기</a>
            </div>
            """
    else:
        letters_html = "<p class='small'>지금은 열린 익명 편지가 없어. 친구가 먼저 편지를 남기면 여기서 볼 수 있어.</p>"

    resident_html = ""
    if resident_today:
        if resident_today["status"] == "pending":
            resident_html = f"""
            <div class="item">
              <div class="small">오늘의 주민</div>
              <div><strong>{resident_today['name']}</strong></div>
              <div class="pill">주민 NPC</div>
              <p>{resident_today['line']}</p>
              <div class="small">{resident_today['problem_title']}</div>
              <a class="btn" href="/resident">상담하러 가기</a>
            </div>
            """
        else:
            resident_html = f"""
            <div class="item">
              <div class="small">오늘의 주민</div>
              <div><strong>{resident_today['name']}</strong></div>
              <div class="pill">상담 완료</div>
              <div>{resident_today['problem_title']}</div>
              <a class="btn ghost" href="/resident/result">결과 다시 보기</a>
            </div>
            """

    body = f"""
    <div class="hero">
      <h2>🕯️ 작업실</h2>
      <p class="sub">오늘의 상태를 확인하고, 원하는 공간으로 이동해.</p>
    </div>

    <div class="card">
      <h3>오늘의 상태</h3>
      <div class="pill">보유 룬 {rune_count}</div>
      <div class="pill">열린 편지 {len(open_letters)}개</div>
      <div class="pill">메리벨 {resident_status}</div>
    </div>

    <div class="card">
      <h3>작업실 지도</h3>
      <div class="room-map">
        <a class="room-node" href="/question/new">
          <div>
            <div class="icon">🔮</div>
            <div class="title">내 점괘 보기</div>
          </div>
          <div class="desc">질문을 남기고 작업실에서 카드로 점괘를 확인한다.</div>
        </a>

        <a class="room-node" href="/letters/send">
          <div>
            <div class="icon">💌</div>
            <div class="title">편지함</div>
          </div>
          <div class="desc">익명 유저에게 편지를 남긴다.</div>
        </a>

        <a class="room-node" href="/letters/mine">
          <div>
            <div class="icon">📬</div>
            <div class="title">내 편지 상자</div>
          </div>
          <div class="desc">내가 보낸 익명 편지를 따로 확인한다.</div>
        </a>

        <a class="room-node" href="/resident">
          <div>
            <div class="icon">🪞</div>
            <div class="title">주민 의자</div>
          </div>
          <div class="desc">메리벨의 고민을 듣고 카드를 뽑아준다.</div>
        </a>

        <a class="room-node" href="/assistant">
          <div>
            <div class="icon">🐈‍⬛</div>
            <div class="title">고양이 자리</div>
          </div>
          <div class="desc">검은 고양이의 말과 힌트를 확인한다.</div>
        </a>

        <a class="room-node" href="/collection">
          <div>
            <div class="icon">🃏</div>
            <div class="title">도감 책장</div>
          </div>
          <div class="desc">카드 수집 현황과 가챠를 확인한다.</div>
        </a>

        <a class="room-node" href="/board">
          <div>
            <div class="icon">📝</div>
            <div class="title">광장 기록판</div>
          </div>
          <div class="desc">다른 사람의 글을 보고 답글을 남긴다.</div>
        </a>
      </div>
    </div>

    <div class="card">
      <h3>도착한 익명 편지</h3>
      {letters_html}
    </div>

    <div class="card">
      <h3>주민 NPC</h3>
      {resident_html}
    </div>

    <div class="card">
      <h3>대기 중인 내 점괘</h3>
      {pending_html}
    </div>

    <div class="card">
      <h3>최근 확인한 개인 점괘</h3>
      {recent_html}
    </div>

    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("작업실", body)


@app.route("/question/new", methods=["GET", "POST"])
def new_question():
    ensure_data()

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        emotion = request.form.get("emotion", "").strip()

        if question and emotion in emotions:
            question_id = str(int(datetime.datetime.now().timestamp() * 1000))
            questions = session.get("questions", [])
            questions.append({
                "id": question_id,
                "question": question,
                "emotion": emotion,
                "status": "pending",
                "card_name": "",
                "card_keyword": "",
                "card_rarity": "",
                "reading_base": "",
                "reading_emotion": "",
                "reading_special": "",
                "selected_slot": None,
                "feedback_choice": "",
                "feedback_text": ""
            })
            session["questions"] = questions
            session.modified = True
            return redirect("/workroom")

    options = "".join([f"<option value='{e}'>{e}</option>" for e in emotions])

    body = f"""
    <div class="hero">
      <h2>🔮 내 점괘 준비하기</h2>
      <p class="sub">질문을 남겨도 점괘는 바로 보이지 않아. 작업실에서 카드를 뽑아 확인하게 돼.</p>
    </div>

    <div class="card">
      <form method="post">
        <label>질문</label>
        <textarea name="question" placeholder="예: 요즘 인간관계가 너무 힘든데 어떻게 해야 할까?"></textarea>

        <label style="display:block; margin-top:12px;">현재 감정</label>
        <select name="emotion">
          {options}
        </select>

        <button type="submit">작업실에 점괘 보내기</button>
      </form>
    </div>

    <a class="btn secondary" href="/workroom">작업실로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("내 점괘 준비하기", body)


@app.route("/reading/<question_id>/draw", methods=["GET", "POST"])
def draw_room(question_id):
    ensure_data()
    item = find_question(question_id)
    if not item:
        return redirect("/workroom")

    if request.method == "POST":
        slot = request.form.get("slot")
        if item["status"] == "pending" and slot in ["1", "2", "3", "4", "5", "6"]:
            card = weighted_draw()
            add_to_collection(card["name"])

            base, emotion_line, special = build_reading(card, item["emotion"])

            item["status"] = "done"
            item["selected_slot"] = slot
            item["card_name"] = card["name"]
            item["card_keyword"] = card["keyword"]
            item["card_rarity"] = rarity_label[card["rarity"]]
            item["reading_base"] = base
            item["reading_emotion"] = emotion_line
            item["reading_special"] = special or ""

            session.modified = True
            return redirect(url_for("reading_result", question_id=question_id))

    cards_html = ""
    for i in range(1, 7):
        cards_html += f"""
        <form method="post">
          <input type="hidden" name="slot" value="{i}">
          <button class="tarot-back" type="submit">카드 {i}</button>
        </form>
        """

    body = f"""
    <div class="hero">
      <h2>🃏 작업실 카드 선택</h2>
      <p class="sub">카드 1~6 중 한 장을 골라 점괘를 확인하는 구조야.</p>
    </div>

    <div class="card">
      <div class="small">질문</div>
      <p>{item['question']}</p>
      <div class="pill">{item['emotion']}</div>
    </div>

    <div class="card">
      <h3>수정구 아래에 놓인 카드들</h3>
      <p class="small">카드 한 장을 눌러 점괘를 확인해.</p>
      <div class="grid6">
        {cards_html}
      </div>
    </div>

    <a class="btn secondary" href="/workroom">작업실로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("카드 선택", body)


@app.route("/reading/<question_id>/result", methods=["GET", "POST"])
def reading_result(question_id):
    ensure_data()
    item = find_question(question_id)
    if not item or item["status"] != "done":
        return redirect("/workroom")

    if request.method == "POST":
        choice = request.form.get("feedback_choice", "").strip()
        text = request.form.get("feedback_text", "").strip()

        item["feedback_choice"] = choice
        item["feedback_text"] = text

        feedbacks = session.get("feedbacks", [])
        exists = False
        for f in feedbacks:
            if f["question_id"] == question_id:
                f["choice"] = choice
                f["text"] = text
                exists = True
                break

        if not exists:
            feedbacks.append({
                "question_id": question_id,
                "question": item["question"],
                "card_name": item["card_name"],
                "choice": choice,
                "text": text
            })

        session["feedbacks"] = feedbacks
        session.modified = True
        return redirect("/book")

    special_html = ""
    if item["reading_special"]:
        special_html = f"""
        <div class="divider"></div>
        <div class="small">특수 해석</div>
        <p>{item['reading_special']}</p>
        """

    body = f"""
    <div class="hero">
      <h2>🔮 점괘 결과</h2>
      <p class="sub">해석을 확인하고 아래에 피드백을 남길 수 있어. 이 기록은 마법책으로 들어가.</p>
    </div>

    <div class="card">
      <div class="small">질문</div>
      <p>{item['question']}</p>
      <div class="pill">{item['emotion']}</div>

      <div class="divider"></div>

      <div class="small">뽑은 카드</div>
      <div class="big">{item['card_name']}</div>
      <div class="pill">{item['card_keyword']}</div>
      <div class="pill">{item['card_rarity']}</div>
      <div class="pill">선택한 카드 {item['selected_slot']}</div>

      <div class="divider"></div>

      <div class="small">해석</div>
      <p>{item['reading_base']}</p>
      <p>{item['reading_emotion']}</p>
      <p class="small">수정구가 카드의 흔적을 밝히고 있다.</p>
      {special_html}
    </div>

    <div class="card">
      <h3>점괘 피드백 남기기</h3>
      <form method="post">
        <label>이 점괘가 맞았나요?</label>
        <select name="feedback_choice">
          <option value="">선택</option>
          <option value="맞았어요">맞았어요</option>
          <option value="애매해요">애매해요</option>
          <option value="아닌 것 같아요">아닌 것 같아요</option>
        </select>

        <label style="display:block; margin-top:12px;">코멘트</label>
        <textarea name="feedback_text" placeholder="왜 그렇게 느꼈는지 적어 줘"></textarea>

        <button type="submit">피드백 저장하기</button>
      </form>
    </div>

    <a class="btn secondary" href="/workroom">작업실로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("점괘 결과", body)


@app.route("/letters/send", methods=["GET", "POST"])
def letters_send():
    ensure_data()

    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if text:
            shared = load_shared_data()
            letter_id = str(int(datetime.datetime.now().timestamp() * 1000))
            shared["letters"].append({
                "id": letter_id,
                "text": text,
                "status": "open",
                "created_at": str(datetime.datetime.now()),
                "author_id": session.get("user_id"),
                "answered_by": ""
            })
            save_shared_data(shared)
            return redirect("/workroom")

    body = """
    <div class="hero">
      <h2>📮 익명 편지 남기기</h2>
      <p class="sub">친구가 다른 브라우저에서 이 편지를 확인하고 점괘를 봐줄 수 있어.</p>
    </div>

    <div class="card">
      <form method="post">
        <label>익명 질문</label>
        <textarea name="text" placeholder="예: 내가 지금 놓치고 있는 감정은 뭘까?"></textarea>
        <button type="submit">편지 남기기</button>
      </form>
    </div>

    <a class="btn secondary" href="/workroom">작업실로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("익명 편지 남기기", body)


@app.route("/letters/mine")
def letters_mine():
    ensure_data()
    shared = load_shared_data()

    my_user_id = session.get("user_id")
    my_letters = [l for l in shared.get("letters", []) if l.get("author_id") == my_user_id]

    letters_html = ""
    if my_letters:
        for letter in reversed(my_letters):
            status_text = "답변 대기 중" if letter["status"] == "open" else "누군가 확인함"
            letters_html += f"""
            <div class="item">
              <div class="small">내가 보낸 익명 편지</div>
              <div>{letter['text']}</div>
              <div class="pill">{status_text}</div>
            </div>
            """
    else:
        letters_html = "<p class='small'>아직 보낸 익명 편지가 없어.</p>"

    body = f"""
    <div class="hero">
      <h2>📬 내 익명 편지</h2>
      <p class="sub">내가 보낸 편지를 따로 확인할 수 있어.</p>
    </div>

    <div class="card">
      {letters_html}
    </div>

    <a class="btn secondary" href="/workroom">작업실로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("내 익명 편지", body)


@app.route("/letter/<letter_id>/draw", methods=["GET", "POST"])
def letter_draw(letter_id):
    ensure_data()
    shared = load_shared_data()

    letter = None
    for item in shared.get("letters", []):
        if item["id"] == letter_id:
            letter = item
            break

    if not letter or letter["status"] != "open":
        return redirect("/workroom")

    if request.method == "POST":
        slot = request.form.get("slot")
        if slot in ["1", "2", "3", "4", "5", "6"]:
            card = weighted_draw()
            add_to_collection(card["name"])

            emotion = random.choice(emotions)
            base, emotion_line, special = build_reading(card, emotion)

            letter["status"] = "done"
            letter["answered_by"] = session.get("user_id")
            save_shared_data(shared)

            session["runes"] = session.get("runes", 0) + 100

            received = session.get("received_readings", [])
            received.append({
                "id": letter_id,
                "question": letter["text"],
                "emotion": emotion,
                "card_name": card["name"],
                "card_keyword": card["keyword"],
                "card_rarity": rarity_label[card["rarity"]],
                "reading_base": base,
                "reading_emotion": emotion_line,
                "reading_special": special or "",
                "selected_slot": slot
            })
            session["received_readings"] = received
            session.modified = True

            return redirect(url_for("letter_result", letter_id=letter_id, toast="+100 룬 획득"))

    cards_html = ""
    for i in range(1, 7):
        cards_html += f"""
        <form method="post">
          <input type="hidden" name="slot" value="{i}">
          <button class="tarot-back" type="submit">카드 {i}</button>
        </form>
        """

    body = f"""
    <div class="hero">
      <h2>💌 익명 편지 점괘</h2>
      <p class="sub">편지는 바로 열리지 않고, 작업실에서 카드를 골라 확인하게 돼.</p>
    </div>

    <div class="card">
      <div class="small">도착한 편지</div>
      <p>{letter['text']}</p>
    </div>

    <div class="card">
      <h3>익명 편지를 위한 카드 선택</h3>
      <p class="small">카드 한 장을 고르면 점괘가 열려.</p>
      <div class="grid6">
        {cards_html}
      </div>
    </div>

    <a class="btn secondary" href="/workroom">작업실로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("익명 편지 카드 선택", body)


@app.route("/letter/<letter_id>/result", methods=["GET", "POST"])
def letter_result(letter_id):
    ensure_data()

    letter_result_item = None
    for item in reversed(session.get("received_readings", [])):
        if item["id"] == letter_id:
            letter_result_item = item
            break

    if not letter_result_item:
        return redirect("/workroom")

    if request.method == "POST":
        choice = request.form.get("feedback_choice", "").strip()
        text = request.form.get("feedback_text", "").strip()

        feedbacks = session.get("letter_feedbacks", [])
        exists = False

        for f in feedbacks:
            if f["id"] == letter_id:
                f["choice"] = choice
                f["text"] = text
                exists = True
                break

        if not exists:
            feedbacks.append({
                "id": letter_id,
                "question": letter_result_item["question"],
                "card_name": letter_result_item["card_name"],
                "choice": choice,
                "text": text
            })

        session["letter_feedbacks"] = feedbacks
        session.modified = True
        return redirect(url_for("book", toast="편지 피드백 저장 완료"))

    special_html = ""
    if letter_result_item["reading_special"]:
        special_html = f"""
        <div class="divider"></div>
        <div class="small">특수 해석</div>
        <p>{letter_result_item['reading_special']}</p>
        """

    body = f"""
    <div class="hero">
      <h2>📨 편지 점괘 결과</h2>
      <p class="sub">익명 편지에 대한 점괘를 확인했어. 답변 완료 보상으로 100룬을 받았어.</p>
    </div>

    <div class="card">
      <div class="small">편지 내용</div>
      <p>{letter_result_item['question']}</p>

      <div class="divider"></div>

      <div class="small">뽑은 카드</div>
      <div class="big">{letter_result_item['card_name']}</div>
      <div class="pill">{letter_result_item['card_keyword']}</div>
      <div class="pill">{letter_result_item['card_rarity']}</div>
      <div class="pill">선택한 카드 {letter_result_item['selected_slot']}</div>

      <div class="divider"></div>

      <div class="small">해석</div>
      <p>{letter_result_item['reading_base']}</p>
      <p>{letter_result_item['reading_emotion']}</p>
      <p class="small">수정구가 카드의 흔적을 밝히고 있다.</p>
      {special_html}
    </div>

    <div class="card">
      <h3>편지 점괘 피드백</h3>
      <form method="post">
        <label>이 점괘가 어땠나요?</label>
        <select name="feedback_choice">
          <option value="">선택</option>
          <option value="맞았어요">맞았어요</option>
          <option value="애매해요">애매해요</option>
          <option value="아닌 것 같아요">아닌 것 같아요</option>
        </select>

        <label style="display:block; margin-top:12px;">코멘트</label>
        <textarea name="feedback_text" placeholder="이 편지 점괘에 대한 느낌을 적어 줘"></textarea>

        <button type="submit">피드백 저장하기</button>
      </form>
    </div>

    <div class="card">
      <div class="small">획득 보상</div>
      <div class="big">+100 룬</div>
      <p>현재 보유 룬: {session.get('runes', 0)}</p>
    </div>

    <a class="btn secondary" href="/workroom">작업실로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("편지 점괘 결과", body)


@app.route("/resident")
def resident():
    ensure_data()
    resident_today = session.get("resident_today")
    if not resident_today:
        return redirect("/workroom")

    body = f"""
    <div class="hero">
      <h2>🏠 주민 NPC</h2>
      <p class="sub">익명 유저와는 별개로, 작업실에 찾아오는 고정 주민이야.</p>
    </div>

    <div class="card">
      <div class="small">이름</div>
      <div class="big">{resident_today['name']}</div>
      <div class="pill">{resident_npc['personality']}</div>
      <p>{resident_today['line']}</p>
    </div>

    <div class="card">
      <div class="small">오늘의 고민</div>
      <div class="big">{resident_today['problem_title']}</div>
      <p>{resident_today['problem_text']}</p>
    </div>
    """

    if resident_today["status"] == "pending":
        body += '<a class="btn" href="/resident/draw">카드 뽑아주기</a>'
    else:
        body += '<a class="btn" href="/resident/result">결과 보기</a>'

    body += """
    <a class="btn secondary" href="/workroom">작업실로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("주민 NPC", body)


@app.route("/resident/draw", methods=["GET", "POST"])
def resident_draw():
    ensure_data()
    resident_today = session.get("resident_today")
    if not resident_today:
        return redirect("/workroom")

    if request.method == "POST":
        slot = request.form.get("slot")
        if resident_today["status"] == "pending" and slot in ["1", "2", "3", "4", "5", "6"]:
            card = owned_card_draw()
            add_to_collection(card["name"])

            emotion = random.choice(emotions)
            base, emotion_line, special = build_reading(card, emotion)

            resident_today["status"] = "done"
            resident_today["selected_slot"] = slot
            resident_today["card_name"] = card["name"]
            resident_today["card_keyword"] = card["keyword"]
            resident_today["card_rarity"] = rarity_label[card["rarity"]]
            resident_today["reading_base"] = base
            resident_today["reading_emotion"] = emotion_line
            resident_today["reading_special"] = special or ""

            if not resident_today["reward_claimed"]:
                session["runes"] = session.get("runes", 0) + 400
                resident_today["reward_claimed"] = True

            resident_history = session.get("resident_history", [])
            resident_history.append({
                "id": resident_today["id"],
                "name": resident_today["name"],
                "problem_title": resident_today["problem_title"],
                "problem_text": resident_today["problem_text"],
                "card_name": resident_today["card_name"],
                "card_keyword": resident_today["card_keyword"],
                "card_rarity": resident_today["card_rarity"],
                "reading_base": resident_today["reading_base"],
                "reading_emotion": resident_today["reading_emotion"],
                "reading_special": resident_today["reading_special"]
            })
            session["resident_history"] = resident_history
            session.modified = True

            return redirect(url_for("resident_result", toast="+400 룬 획득"))

    cards_html = ""
    for i in range(1, 7):
        cards_html += f"""
        <form method="post">
          <input type="hidden" name="slot" value="{i}">
          <button class="tarot-back" type="submit">카드 {i}</button>
        </form>
        """

    body = f"""
    <div class="hero">
      <h2>🃏 메리벨의 점괘</h2>
      <p class="sub">메리벨의 고민을 위해 카드 1~6 중 하나를 골라줘.</p>
    </div>

    <div class="card">
      <div class="small">메리벨의 고민</div>
      <div class="big">{resident_today['problem_title']}</div>
      <p>{resident_today['problem_text']}</p>
    </div>

    <div class="card">
      <h3>메리벨을 위한 카드 선택</h3>
      <p class="small">수정구 아래 카드 1~6 중 한 장을 골라 줘.</p>
      <div class="grid6">
        {cards_html}
      </div>
    </div>

    <a class="btn secondary" href="/resident">주민 NPC로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("메리벨 카드 선택", body)


@app.route("/resident/result")
def resident_result():
    ensure_data()
    resident_today = session.get("resident_today")
    if not resident_today or resident_today["status"] != "done":
        return redirect("/resident")

    special_html = ""
    if resident_today["reading_special"]:
        special_html = f"""
        <div class="divider"></div>
        <div class="small">특수 해석</div>
        <p>{resident_today['reading_special']}</p>
        """

    body = f"""
    <div class="hero">
      <h2>🌙 메리벨의 점괘 결과</h2>
      <p class="sub">오늘의 주민 상담이 완료됐어. 보상으로 400룬을 받았어.</p>
    </div>

    <div class="card">
      <div class="small">메리벨의 고민</div>
      <div class="big">{resident_today['problem_title']}</div>
      <p>{resident_today['problem_text']}</p>

      <div class="divider"></div>

      <div class="small">뽑은 카드</div>
      <div class="big">{resident_today['card_name']}</div>
      <div class="pill">{resident_today['card_keyword']}</div>
      <div class="pill">{resident_today['card_rarity']}</div>
      <div class="pill">선택한 카드 {resident_today['selected_slot']}</div>

      <div class="divider"></div>

      <div class="small">해석</div>
      <p>{resident_today['reading_base']}</p>
      <p>{resident_today['reading_emotion']}</p>
      <p class="small">수정구가 카드의 흔적을 밝히고 있다.</p>
      {special_html}
    </div>

    <div class="card">
      <div class="small">획득 보상</div>
      <div class="big">+400 룬</div>
      <p>현재 보유 룬: {session.get('runes', 0)}</p>
    </div>

    <a class="btn secondary" href="/workroom">작업실로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("메리벨 결과", body)


@app.route("/assistant")
def assistant():
    ensure_data()
    shared = load_shared_data()
    my_user_id = session.get("user_id")
    open_letters = [
        l for l in shared.get("letters", [])
        if l["status"] == "open" and l.get("author_id") != my_user_id
    ]

    resident_status = "상담 대기 중" if session.get("resident_today", {}).get("status") == "pending" else "상담 완료"

    body = f"""
    <div class="hero">
      <h2>🐈‍⬛ 검은 고양이</h2>
      <p class="sub">작업실을 지키는 조수야. 가끔은 카드보다 먼저 분위기를 읽는 것처럼 보여.</p>
    </div>

    <div class="card">
      <div class="small">오늘의 상태</div>
      <p>{session.get('cat_line', '')}</p>
    </div>

    <div class="card">
      <div class="small">고양이의 한마디</div>
      <p>{session.get('cat_today_line', '')}</p>
      <a class="btn" href="/cat/event">고양이에게 다가가기</a>
    </div>

    <div class="card">
      <div class="small">작업실 힌트</div>
      <p>현재 보유 룬: {session.get('runes', 0)} 룬</p>
      <p>하루 첫 접속 보상: 300룬</p>
      <p>열린 익명 편지: {len(open_letters)}개</p>
      <p>오늘의 주민 상태: {resident_status}</p>
    </div>

    <a class="btn secondary" href="/workroom">작업실로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("검은 고양이", body)


@app.route("/cat/event")
def cat_event():
    ensure_data()

    events = [
        {"text": "고양이가 네 손등에 얼굴을 비볐다. 작은 위로를 받은 기분이다.", "reward": 0},
        {"text": "고양이가 룬 하나를 어디선가 굴려왔다.", "reward": 30},
        {"text": "고양이가 카드 더미를 건드리며 희귀한 기운을 남긴 것 같다.", "reward": 50},
        {"text": "고양이가 아무 말 없이 네 옆에 앉아 있다. 오늘은 조용한 밤이다.", "reward": 0}
    ]

    picked = random.choice(events)
    reward = picked["reward"]

    if reward > 0:
        session["runes"] = session.get("runes", 0) + reward
        session.modified = True
        return redirect(url_for("assistant", toast=f"+{reward} 룬 · 고양이 이벤트"))

    return redirect(url_for("assistant", toast="고양이가 곁에 머물렀다"))


@app.route("/collection")
def collection():
    ensure_data()
    owned = session.get("collection", [])
    total = len(cards)

    collection_html = ""
    for card in cards:
        owned_mark = "보유" if card["name"] in owned else "미보유"
        owned_class = "" if card["name"] in owned else "small"
        collection_html += f"""
        <div class="item">
          <div><strong>{card['name']}</strong></div>
          <div class="pill">{card['keyword']}</div>
          <div class="pill">{rarity_label[card['rarity']]}</div>
          <div class="{owned_class}">{owned_mark}</div>
        </div>
        """

    body = f"""
    <div class="hero">
      <h2>🃏 카드 도감</h2>
      <p class="sub">오늘의 카드, 점괘, 가챠를 통해 카드를 수집하는 공간이야.</p>
    </div>

    <div class="card">
      <div class="small">수집 현황</div>
      <div class="big">{len(owned)} / {total}</div>
      <p>아직 모으지 못한 카드도 도감에서 확인할 수 있어.</p>
    </div>

    <div class="card">
      <h3>룬 가챠</h3>
      <p>가챠 1회 비용: 1000룬</p>
      <p>현재 보유 룬: {session.get('runes', 0)} 룬</p>
      <a class="btn" href="/gacha">1000룬 가챠 돌리기</a>
    </div>

    <div class="card">
      <h3>전체 카드 목록</h3>
      {collection_html}
    </div>

    <a class="btn secondary" href="/workroom">작업실로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("카드 도감", body)


@app.route("/gacha")
def gacha():
    ensure_data()
    current_runes = session.get("runes", 0)

    if current_runes < 1000:
        body = f"""
        <div class="hero">
          <h2>🎲 룬 가챠</h2>
          <p class="sub">룬이 부족해서 아직 가챠를 돌릴 수 없어.</p>
        </div>

        <div class="card">
          <p>현재 보유 룬: {current_runes} 룬</p>
          <p>필요한 룬: 1000 룬</p>
        </div>

        <a class="btn secondary" href="/collection">카드 도감으로</a>
        <a class="btn ghost" href="/">메인으로</a>
        """
        return page("가챠 실패", body)

    card = weighted_draw()
    session["runes"] = current_runes - 1000
    add_to_collection(card["name"])
    meaning = random.choice(card["meanings"])
    session.modified = True

    body = f"""
    <div class="hero">
      <h2>✨ 가챠 결과</h2>
      <p class="sub">룬 1000개를 사용해 카드를 한 장 획득했어.</p>
    </div>

    <div class="card">
      <div class="small">획득 카드</div>
      <div class="big">{card['name']}</div>
      <div class="pill">{card['keyword']}</div>
      <div class="pill">{rarity_label[card['rarity']]}</div>
      <p>{meaning}</p>
    </div>

    <div class="card">
      <div class="small">남은 룬</div>
      <div class="big">{session.get('runes', 0)} 룬</div>
    </div>

    <a class="btn secondary" href="/collection">카드 도감으로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("가챠 결과", body)


@app.route("/board")
def board():
    ensure_data()
    shared = load_shared_data()
    posts = shared.get("board_posts", [])

    posts_html = ""
    if posts:
        for post in reversed(posts):
            posts_html += f"""
            <div class="item">
              <div><strong>{post['title']}</strong></div>
              <div class="small">{post['content']}</div>
              <div class="pill">좋아요 {post['reactions']['like']}</div>
              <div class="pill">공감 {post['reactions']['empathy']}</div>
              <div class="pill">응원 {post['reactions']['cheer']}</div>
              <a class="btn ghost" href="/board/{post['id']}">글 보기</a>
            </div>
            """
    else:
        posts_html = "<p class='small'>아직 게시글이 없어.</p>"

    body = f"""
    <div class="hero">
      <h2>📝 게시판</h2>
      <p class="sub">오늘의 감정, 점괘 후기, 카드 이야기를 남길 수 있는 공간이야.</p>
    </div>

    <div class="card">
      <a class="btn" href="/board/new">글 쓰기</a>
    </div>

    <div class="card">
      <h3>게시글 목록</h3>
      {posts_html}
    </div>

    <a class="btn secondary" href="/workroom">작업실로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("게시판", body)


@app.route("/board/new", methods=["GET", "POST"])
def board_new():
    ensure_data()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        if title and content:
            shared = load_shared_data()
            post_id = str(int(datetime.datetime.now().timestamp() * 1000))
            shared["board_posts"].append({
                "id": post_id,
                "title": title,
                "content": content,
                "comments": [],
                "reactions": {"like": 0, "empathy": 0, "cheer": 0}
            })
            save_shared_data(shared)
            return redirect("/board")

    body = """
    <div class="hero">
      <h2>✍️ 게시글 작성</h2>
      <p class="sub">점괘 후기, 감정 기록, 카드 자랑 같은 글을 자유롭게 남길 수 있어.</p>
    </div>

    <div class="card">
      <form method="post">
        <label>제목</label>
        <input name="title" placeholder="예: 오늘 뽑은 카드가 너무 잘 맞았어">

        <label style="display:block; margin-top:12px;">내용</label>
        <textarea name="content" placeholder="자유롭게 적어 줘"></textarea>

        <button type="submit">글 올리기</button>
      </form>
    </div>

    <a class="btn secondary" href="/board">게시판으로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("글 쓰기", body)


@app.route("/board/<post_id>")
def board_post(post_id):
    ensure_data()
    shared = load_shared_data()

    post = None
    for item in shared.get("board_posts", []):
        if item["id"] == post_id:
            post = item
            break

    if not post:
        return redirect("/board")

    comments_html = ""
    if post["comments"]:
        for c in reversed(post["comments"]):
            comments_html += f"""
            <div class="item">
              <div class="small">답글</div>
              <div>{c}</div>
            </div>
            """
    else:
        comments_html = "<p class='small'>아직 답글이 없어.</p>"

    body = f"""
    <div class="hero">
      <h2>📌 게시글</h2>
      <p class="sub">리액션을 남기거나 답글을 달 수 있어.</p>
    </div>

    <div class="card">
      <div class="big">{post['title']}</div>
      <p>{post['content']}</p>

      <div class="divider"></div>

      <div class="pill">좋아요 {post['reactions']['like']}</div>
      <div class="pill">공감 {post['reactions']['empathy']}</div>
      <div class="pill">응원 {post['reactions']['cheer']}</div>

      <a class="btn" href="/board/{post_id}/react/like">좋아요</a>
      <a class="btn secondary" href="/board/{post_id}/react/empathy">공감</a>
      <a class="btn secondary" href="/board/{post_id}/react/cheer">응원</a>
    </div>

    <div class="card">
      <h3>답글</h3>
      {comments_html}
      <a class="btn" href="/board/{post_id}/comment">답글 달기</a>
    </div>

    <a class="btn secondary" href="/board">게시판으로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("게시글", body)


@app.route("/board/<post_id>/react/<kind>")
def board_react(post_id, kind):
    ensure_data()
    if kind not in ["like", "empathy", "cheer"]:
        return redirect(f"/board/{post_id}")

    shared = load_shared_data()
    for post in shared.get("board_posts", []):
        if post["id"] == post_id:
            post["reactions"][kind] += 1
            break
    save_shared_data(shared)
    return redirect(f"/board/{post_id}")


@app.route("/board/<post_id>/comment", methods=["GET", "POST"])
def board_comment(post_id):
    ensure_data()
    shared = load_shared_data()

    post = None
    for item in shared.get("board_posts", []):
        if item["id"] == post_id:
            post = item
            break

    if not post:
        return redirect("/board")

    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if text:
            post["comments"].append(text)
            save_shared_data(shared)
            return redirect(f"/board/{post_id}")

    body = f"""
    <div class="hero">
      <h2>💬 답글 달기</h2>
      <p class="sub">게시글에 짧은 답글을 남길 수 있어.</p>
    </div>

    <div class="card">
      <div class="small">원글</div>
      <div class="big">{post['title']}</div>
      <p>{post['content']}</p>
    </div>

    <div class="card">
      <form method="post">
        <label>답글</label>
        <textarea name="text" placeholder="답글을 적어 줘"></textarea>
        <button type="submit">답글 등록</button>
      </form>
    </div>

    <a class="btn secondary" href="/board/{post_id}">게시글로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("답글 달기", body)


@app.route("/book")
def book():
    ensure_data()
    today_card = session["today_card"]
    questions = session.get("questions", [])
    feedbacks = session.get("feedbacks", [])
    received_readings = session.get("received_readings", [])
    resident_history = session.get("resident_history", [])
    letter_feedbacks = session.get("letter_feedbacks", [])

    sent_html = ""
    sent_items = [q for q in questions if q["status"] == "done"]
    if sent_items:
        for q in reversed(sent_items):
            sent_html += f"""
            <div class="item">
              <div class="small">질문</div>
              <div>{q['question']}</div>
              <div class="pill">{q['emotion']}</div>
              <div class="pill">{q['card_name']}</div>
              <a class="btn ghost" href="/reading/{q['id']}/result">결과 보기</a>
            </div>
            """
    else:
        sent_html = "<p class='small'>아직 완료된 점괘가 없어.</p>"

    feedback_html = ""
    if feedbacks:
        for f in reversed(feedbacks):
            text_html = f"<p>{f['text']}</p>" if f["text"] else ""
            feedback_html += f"""
            <div class="item">
              <div>{f['question']}</div>
              <div class="pill">{f['card_name']}</div>
              <div class="pill">{f['choice'] or '선택 안 함'}</div>
              {text_html}
            </div>
            """
    else:
        feedback_html = "<p class='small'>아직 저장된 피드백이 없어.</p>"

    received_html = ""
    if received_readings:
        for r in reversed(received_readings):
            special = f"<p>{r['reading_special']}</p>" if r["reading_special"] else ""
            received_html += f"""
            <div class="item">
              <div class="small">받은 편지</div>
              <div>{r['question']}</div>
              <div class="pill">{r['emotion']}</div>
              <div class="pill">{r['card_name']}</div>
              <p>{r['reading_base']}</p>
              <p>{r['reading_emotion']}</p>
              {special}
            </div>
            """
    else:
        received_html = "<p class='small'>아직 받은 점괘가 없어.</p>"

    letter_feedback_html = ""
    if letter_feedbacks:
        for f in reversed(letter_feedbacks):
            text_html = f"<p>{f['text']}</p>" if f["text"] else ""
            letter_feedback_html += f"""
            <div class="item">
              <div class="small">편지 점괘 피드백</div>
              <div>{f['question']}</div>
              <div class="pill">{f['card_name']}</div>
              <div class="pill">{f['choice'] or '선택 안 함'}</div>
              {text_html}
            </div>
            """
    else:
        letter_feedback_html = "<p class='small'>아직 저장된 편지 피드백이 없어.</p>"

    resident_html = ""
    if resident_history:
        for r in reversed(resident_history):
            special = f"<p>{r['reading_special']}</p>" if r["reading_special"] else ""
            resident_html += f"""
            <div class="item">
              <div class="small">주민</div>
              <div><strong>{r['name']}</strong></div>
              <div>{r['problem_title']}</div>
              <div class="pill">{r['card_name']}</div>
              <p>{r['reading_base']}</p>
              <p>{r['reading_emotion']}</p>
              {special}
            </div>
            """
    else:
        resident_html = "<p class='small'>아직 주민 기록이 없어.</p>"

    body = f"""
    <div class="hero">
      <h2>📖 마법책</h2>
      <p class="sub">오늘의 카드, 내가 보낸 점괘, 받은 점괘, 피드백, 주민 기록을 모아 보는 공간이야.</p>
    </div>

    <div class="card">
      <div class="small">현재 재화</div>
      <div class="big">{session.get('runes', 0)} 룬</div>
    </div>

    <div class="card">
      <h3>오늘의 카드</h3>
      <div class="big">{today_card['name']}</div>
      <div class="pill">{today_card['keyword']}</div>
      <div class="pill">{today_card['rarity']}</div>
      <p>{today_card['meaning']}</p>
    </div>

    <div class="card">
      <h3>내가 보낸 점괘</h3>
      {sent_html}
    </div>

    <div class="card">
      <h3>받은 점괘</h3>
      {received_html}
    </div>

    <div class="card">
      <h3>점괘 피드백 기록</h3>
      {feedback_html}
    </div>

    <div class="card">
      <h3>편지 피드백 기록</h3>
      {letter_feedback_html}
    </div>

    <div class="card">
      <h3>주민 기록</h3>
      {resident_html}
    </div>

    <a class="btn secondary" href="/workroom">작업실로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("마법책", body)


@app.route("/forest")
def forest():
    ensure_data()

    inventory = session.get("forest_inventory", [])
    treasures = session.get("forest_treasures", [])
    energy = session.get("forest_energy", 10)
    max_energy = session.get("forest_max_energy", 10)
    depth = session.get("forest_depth", 0)

    if not session.get("forest_paths"):
        generate_forest_scene(session)

    inventory_html = ""
    if inventory:
        for item in reversed(inventory[-8:]):
            inventory_html += f"""
            <div class="item">
              <div><strong>{item['name']}</strong></div>
              <div class="pill">{item['rarity']}</div>
            </div>
            """
    else:
        inventory_html = "<p class='small'>아직 숲에서 얻은 재료가 없어.</p>"

    treasure_html = ""
    if treasures:
        for item in reversed(treasures):
            treasure_html += f"""
            <div class="item">
              <div><strong>{item['name']}</strong></div>
              <div class="pill">{item['rarity']}</div>
            </div>
            """
    else:
        treasure_html = "<p class='small'>아직 발견한 전리품이 없어.</p>"

    body = f"""
    <div class="hero">
      <h2>🌲 {forest_data['name']}</h2>
      <p class="sub">{forest_data['description']}</p>
    </div>

    <div class="card">
      <div class="pill">현재 깊이 {depth}</div>
      <div class="pill">행동력 {energy} / {max_energy}</div>
    </div>

    <div class="card">
      <h3>숲에서 얻을 수 있는 것</h3>
      <div class="pill">노멀 · 신선한 허브</div>
      <div class="pill">노멀 · 아름다운 꽃잎</div>
      <div class="pill">노멀 · 빛나는 원석</div>
      <div class="pill">레어 · 요정의 날개</div>
    </div>

    <div class="card">
      <h3>숲 입구</h3>
      <p>{session.get('forest_last_scene', '')}</p>
      <a class="btn" href="/forest/path">숲 안으로 들어간다</a>
      <a class="btn secondary" href="/forest/bag">숲 가방 보기</a>
    </div>

    <div class="card">
      <h3>최근 획득한 재료</h3>
      {inventory_html}
    </div>

    <div class="card">
      <h3>숲의 전리품</h3>
      {treasure_html}
    </div>

    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("사이프러스의 숲", body)


@app.route("/forest/path")
def forest_path():
    ensure_data()

    if session.get("forest_energy", 0) <= 0:
        return redirect(url_for("forest", toast="행동력이 부족해 더 깊게 들어갈 수 없다"))

    if not session.get("forest_paths"):
        generate_forest_scene(session)

    depth = session.get("forest_depth", 0)
    scene = session.get("forest_last_scene", "")
    paths = session.get("forest_paths", [])
    energy = session.get("forest_energy", 10)
    max_energy = session.get("forest_max_energy", 10)

    paths_html = ""
    for p in paths:
        paths_html += f"""
        <div class="item">
          <div class="small">{p['desc']}</div>
          <a class="btn" href="/forest/move/{p['key']}">{p['label']}</a>
        </div>
        """

    body = f"""
    <div class="hero">
      <h2>🌲 사이프러스의 숲</h2>
      <p class="sub">{forest_data['description']}</p>
    </div>

    <div class="card">
      <div class="pill">깊이 {depth}</div>
      <div class="pill">행동력 {energy} / {max_energy}</div>
      <p>{scene}</p>
    </div>

    <div class="card">
      <h3>어느 방향으로 갈까?</h3>
      {paths_html}
      <a class="btn secondary" href="/forest/return">숲에서 돌아간다</a>
    </div>

    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("사이프러스의 숲", body)


@app.route("/forest/move/<direction>")
def forest_move(direction):
    ensure_data()

    if direction not in ["left", "forward", "right"]:
        return redirect("/forest/path")

    if not consume_forest_energy(session, 1):
        return redirect(url_for("forest", toast="행동력이 부족하다"))

    session["forest_depth"] = session.get("forest_depth", 0) + 1

    session["forest_action_scene"] = {
        "text": session.get("forest_last_scene", ""),
        "direction": direction
    }

    generate_forest_scene(session)
    session.modified = True

    return redirect("/forest/action")


@app.route("/forest/action")
def forest_action():
    ensure_data()

    scene = session.get("forest_action_scene")
    if not scene:
        return redirect("/forest/path")

    energy = session.get("forest_energy", 10)
    max_energy = session.get("forest_max_energy", 10)
    depth = session.get("forest_depth", 0)

    body = f"""
    <div class="hero">
      <h2>🌲 사이프러스의 숲</h2>
      <p class="sub">{forest_data['description']}</p>
    </div>

    <div class="card">
      <div class="pill">깊이 {depth}</div>
      <div class="pill">행동력 {energy} / {max_energy}</div>
      <p>{scene['text']}</p>
    </div>

    <div class="card">
      <h3>어떻게 할까?</h3>

      <a class="btn" href="/forest/action/harvest">채집한다</a>
      <a class="btn secondary" href="/forest/action/search">주변을 조사한다</a>
      <a class="btn secondary" href="/forest/action/pass">지나간다</a>
      <a class="btn ghost" href="/forest/return">숲에서 돌아간다</a>
    </div>
    """

    return page("숲 탐험", body)


@app.route("/forest/action/harvest")
def forest_action_harvest():
    ensure_data()

    if not consume_forest_energy(session, 1):
        return redirect(url_for("forest", toast="행동력이 부족하다"))

    event = draw_forest_event(session, "harvest")

    if event:
        resolve_forest_event(session, event)
        session["forest_action_scene"] = None
        return redirect("/forest/event")

    found = draw_forest_item(session)

    inventory = session.get("forest_inventory", [])
    inventory.append({
        "name": found["name"],
        "rarity": "레어" if found["rarity"] == "rare" else "노멀"
    })

    session["forest_inventory"] = inventory
    session["forest_action_scene"] = None
    session.modified = True

    return redirect(url_for("forest_found", item_name=found["name"], rarity=found["rarity"]))


@app.route("/forest/action/search")
def forest_action_search():
    ensure_data()

    if not consume_forest_energy(session, 1):
        return redirect(url_for("forest", toast="행동력이 부족하다"))

    event = draw_forest_event(session, "search")

    if event:
        resolve_forest_event(session, event)
        session["forest_action_scene"] = None
        return redirect("/forest/event")

    found = draw_forest_item(session)

    inventory = session.get("forest_inventory", [])
    inventory.append({
        "name": found["name"],
        "rarity": "레어" if found["rarity"] == "rare" else "노멀"
    })

    session["forest_inventory"] = inventory
    session["forest_action_scene"] = None
    session.modified = True

    return redirect(url_for("forest_found", item_name=found["name"], rarity=found["rarity"]))


@app.route("/forest/action/pass")
def forest_action_pass():
    ensure_data()

    if not consume_forest_energy(session, 1):
        return redirect(url_for("forest", toast="행동력이 부족하다"))

    generate_forest_scene(session)
    session["forest_action_scene"] = None
    session.modified = True

    return redirect("/forest/path")


@app.route("/forest/found")
def forest_found():
    ensure_data()

    item_name = request.args.get("item_name", "")
    rarity = request.args.get("rarity", "normal")

    rarity_text = "레어" if rarity == "rare" else "노멀"

    body = f"""
    <div class="hero">
      <h2>✨ 숲에서 발견한 것</h2>
      <p class="sub">사이프러스의 숲을 걷던 중 무언가를 발견했다.</p>
    </div>

    <div class="card">
      <div class="small">획득 재료</div>
      <div class="big">{item_name}</div>
      <div class="pill">{rarity_text}</div>
    </div>

    <a class="btn" href="/forest/path">계속 탐험하기</a>
    <a class="btn secondary" href="/forest/return">숲에서 돌아간다</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("숲 발견", body)


@app.route("/forest/event")
def forest_event():
    ensure_data()

    event = session.get("forest_last_event")
    if not event:
        return redirect("/forest/path")

    rewards_html = ""
    for reward in event["rewards"]:
        rewards_html += f"""
        <div class="item">
          <div><strong>{reward['name']}</strong></div>
          <div class="pill">{reward['rarity']}</div>
        </div>
        """

    body = f"""
    <div class="hero">
      <h2>🌲 숲의 사건</h2>
      <p class="sub">사이프러스의 숲은 가끔 예상하지 못한 장면을 보여 준다.</p>
    </div>

    <div class="card">
      <div class="big">{event['title']}</div>
      <p>{event['description']}</p>
    </div>

    <div class="card">
      <h3>획득 / 발생</h3>
      {rewards_html}
    </div>

    <a class="btn" href="/forest/path">계속 탐험하기</a>
    <a class="btn secondary" href="/forest/return">숲에서 돌아간다</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("숲 이벤트", body)


@app.route("/forest/bag")
def forest_bag():
    ensure_data()

    inventory = session.get("forest_inventory", [])
    treasures = session.get("forest_treasures", [])

    item_counts = {}
    for item in inventory:
        key = item["name"]
        if key not in item_counts:
            item_counts[key] = {"count": 0, "rarity": item["rarity"]}
        item_counts[key]["count"] += 1

    items_html = ""
    if item_counts:
        for name, data in item_counts.items():
            items_html += f"""
            <div class="item">
              <div><strong>{name}</strong></div>
              <div class="pill">{data['rarity']}</div>
              <div class="small">x{data['count']}</div>
            </div>
            """
    else:
        items_html = "<p class='small'>아직 모은 재료가 없어.</p>"

    treasure_html = ""
    if treasures:
        for item in treasures:
            treasure_html += f"""
            <div class="item">
              <div><strong>{item['name']}</strong></div>
              <div class="pill">{item['rarity']}</div>
            </div>
            """
    else:
        treasure_html = "<p class='small'>아직 발견한 전리품이 없어.</p>"

    body = f"""
    <div class="hero">
      <h2>🎒 숲 가방</h2>
      <p class="sub">사이프러스의 숲에서 발견한 재료와 전리품을 정리해 둔 공간이다.</p>
    </div>

    <div class="card">
      <h3>재료</h3>
      {items_html}
    </div>

    <div class="card">
      <h3>전리품</h3>
      {treasure_html}
    </div>

    <a class="btn secondary" href="/forest">숲으로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("숲 가방", body)


@app.route("/forest/return")
def forest_return():
    ensure_data()
    reset_forest_run(session)
    return redirect(url_for("forest", toast="사이프러스의 숲에서 돌아왔다"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

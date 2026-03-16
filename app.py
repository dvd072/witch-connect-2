from flask import Flask, request, redirect, session, render_template_string
import os
import json
import random
import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "witch-connect-secret-key")

SHARED_FILE = "shared_data.json"

cards = [
    {
        "name": "광대",
        "keyword": "새로운 시작",
        "rarity": "common",
        "meanings": ["새로운 시작이 열립니다.", "가벼운 마음이 길을 열 수 있습니다.", "예상하지 못한 가능성이 다가옵니다."]
    },
    {
        "name": "마법사",
        "keyword": "의지와 능력",
        "rarity": "common",
        "meanings": ["당신에게는 시작할 힘이 있습니다.", "의지와 기술이 함께 움직일 때입니다.", "가능성은 이미 손안에 있습니다."]
    },
    {
        "name": "여사제",
        "keyword": "직감",
        "rarity": "common",
        "meanings": ["겉보다 안쪽의 신호를 보세요.", "직감이 중요한 답을 알고 있습니다.", "조용한 판단이 필요합니다."]
    },
    {
        "name": "여황제",
        "keyword": "감정의 풍요",
        "rarity": "common",
        "meanings": ["감정은 자라날 수 있습니다.", "돌봄과 안정이 필요합니다.", "관계 안에서 따뜻함이 생겨날 수 있습니다."]
    },
    {
        "name": "황제",
        "keyword": "안정과 통제",
        "rarity": "common",
        "meanings": ["흐트러진 것을 정리할 때입니다.", "안정은 스스로 만드는 것입니다.", "기준을 세우면 흔들림이 줄어듭니다."]
    },
    {
        "name": "교황",
        "keyword": "조언",
        "rarity": "common",
        "meanings": ["누군가의 지혜가 도움이 됩니다.", "기본으로 돌아가 보세요.", "정답보다 방향이 중요합니다."]
    },
    {
        "name": "연인",
        "keyword": "선택과 연결",
        "rarity": "rare",
        "meanings": ["관계는 선택 위에 놓입니다.", "마음이 가는 방향을 보세요.", "연결은 책임도 함께 가져옵니다."]
    },
    {
        "name": "전차",
        "keyword": "전진",
        "rarity": "rare",
        "meanings": ["주저하지 말고 밀고 나가세요.", "의지가 길을 만듭니다.", "갈등을 넘는 추진력이 필요합니다."]
    },
    {
        "name": "힘",
        "keyword": "내면의 힘",
        "rarity": "rare",
        "meanings": ["강함은 조용할 수도 있습니다.", "감정을 누르기보다 다스리세요.", "버티는 힘도 힘입니다."]
    },
    {
        "name": "은둔자",
        "keyword": "내면 탐색",
        "rarity": "rare",
        "meanings": ["혼자 생각할 시간이 필요합니다.", "답은 밖보다 안에 가까이 있습니다.", "서두르지 말고 천천히 보세요."]
    },
    {
        "name": "운명의 수레바퀴",
        "keyword": "변화",
        "rarity": "rare",
        "meanings": ["흐름이 바뀌고 있습니다.", "지금은 변화를 피하기 어렵습니다.", "운은 움직이는 쪽에 가까워집니다."]
    },
    {
        "name": "정의",
        "keyword": "균형",
        "rarity": "rare",
        "meanings": ["감정보다 판단이 필요한 순간입니다.", "균형을 되찾아야 합니다.", "지금의 선택은 결과를 남깁니다."]
    },
    {
        "name": "매달린 사람",
        "keyword": "멈춤과 관점",
        "rarity": "epic",
        "meanings": ["잠시 멈춰야 보이는 것이 있습니다.", "익숙한 시각을 바꿔 보세요.", "지금은 기다림에도 의미가 있습니다."]
    },
    {
        "name": "죽음",
        "keyword": "끝과 시작",
        "rarity": "epic",
        "meanings": ["끝은 다음 시작의 문입니다.", "변화는 이미 시작되었습니다.", "놓아야 새로 들어옵니다."]
    },
    {
        "name": "절제",
        "keyword": "조화",
        "rarity": "epic",
        "meanings": ["지금은 섞고 조절하는 시기입니다.", "과하지 않게 가야 합니다.", "느리지만 안정적인 흐름이 중요합니다."]
    },
    {
        "name": "악마",
        "keyword": "집착",
        "rarity": "epic",
        "meanings": ["당신을 붙잡는 감정을 보세요.", "불편한 끌림이 있을 수 있습니다.", "벗어나려면 먼저 자각이 필요합니다."]
    },
    {
        "name": "탑",
        "keyword": "붕괴와 충격",
        "rarity": "legend",
        "meanings": ["예상하지 못한 변화가 올 수 있습니다.", "무너지면서 진실이 드러납니다.", "불편하지만 필요한 흔들림일 수 있습니다."]
    },
    {
        "name": "별",
        "keyword": "희망과 치유",
        "rarity": "legend",
        "meanings": ["희망은 아직 꺼지지 않았습니다.", "천천히 회복될 수 있습니다.", "멀어 보여도 빛은 존재합니다."]
    },
    {
        "name": "달",
        "keyword": "불안과 혼란",
        "rarity": "legend",
        "meanings": ["모호한 감정이 커질 수 있습니다.", "지금은 모든 것이 선명하지 않을 수 있습니다.", "불안은 진실과 환상을 섞어 보이게 합니다."]
    },
    {
        "name": "태양",
        "keyword": "명확함과 기쁨",
        "rarity": "legend",
        "meanings": ["상황이 분명해질 가능성이 큽니다.", "따뜻한 흐름이 당신 쪽으로 옵니다.", "기쁨은 생각보다 가까이에 있습니다."]
    },
    {
        "name": "심판",
        "keyword": "각성",
        "rarity": "legend",
        "meanings": ["이제는 깨달아야 할 때입니다.", "과거를 정리하고 넘어갈 시기입니다.", "새로운 판단이 필요합니다."]
    },
    {
        "name": "세계",
        "keyword": "완성과 성취",
        "rarity": "legend",
        "meanings": ["하나의 흐름이 완성됩니다.", "도달해야 할 지점에 가까워졌습니다.", "마침내 정리되는 순간이 옵니다."]
    }
]

npc_letters = [
    "요즘 내가 너무 외로운데 이 감정이 언제 끝날까?",
    "사람 관계가 너무 힘들다. 내가 문제일까?",
    "내 선택이 맞는지 모르겠다.",
    "지금 버티는 게 맞는지 포기하는 게 맞는지 모르겠다.",
    "앞으로 나는 어떤 쪽으로 가야 할까?"
]

emotions = ["외로움", "불안", "분노", "희망", "혼란", "슬픔"]

special_readings = {
    ("달", "불안"): "지금의 불안은 현실보다 크게 느껴지고 있을 수 있습니다. 결론을 서두르지 않는 편이 좋습니다.",
    ("별", "슬픔"): "슬픔은 바로 사라지지 않아도, 회복은 이미 시작되었을 가능성이 큽니다.",
    ("탑", "분노"): "억눌러 온 감정이 무너지듯 터질 수 있습니다. 감정을 부정하지 말고 안전하게 흘려보내세요.",
    ("태양", "희망"): "지금 품고 있는 희망은 허상이 아닐 가능성이 큽니다. 밀고 나갈 가치가 있습니다.",
    ("은둔자", "혼란"): "혼란할수록 혼자 생각할 시간이 필요합니다. 답은 시끄러운 바깥보다 안쪽에 가깝습니다."
}

RARITY_ORDER = {
    "common": "일반",
    "rare": "희귀",
    "epic": "에픽",
    "legend": "전설"
}


def load_shared_data():
    if os.path.exists(SHARED_FILE):
        with open(SHARED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"letters": []}


def save_shared_data(data):
    with open(SHARED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ensure_user_data():
    today = str(datetime.date.today())

    if "collection" not in session:
        session["collection"] = []
    if "sent" not in session:
        session["sent"] = []
    if "received" not in session:
        session["received"] = []
    if "today_date" not in session:
        session["today_date"] = ""
    if "today_card" not in session:
        session["today_card"] = None

    if session["today_date"] != today:
        card = draw_card(mode="today")
        meaning = random.choice(card["meanings"])

        session["today_date"] = today
        session["today_card"] = {
            "name": card["name"],
            "keyword": card["keyword"],
            "meaning": meaning,
            "rarity": RARITY_ORDER[card["rarity"]]
        }

        add_to_collection(card["name"])
        session.modified = True


def add_to_collection(card_name):
    collection = session.get("collection", [])
    if card_name not in collection:
        collection.append(card_name)
        session["collection"] = collection
        session.modified = True


def draw_card(mode="normal"):
    if mode == "today":
        return random.choice(cards)

    r = random.random()
    if r < 0.55:
        pool = [c for c in cards if c["rarity"] == "common"]
    elif r < 0.82:
        pool = [c for c in cards if c["rarity"] == "rare"]
    elif r < 0.95:
        pool = [c for c in cards if c["rarity"] == "epic"]
    else:
        pool = [c for c in cards if c["rarity"] == "legend"]

    return random.choice(pool)


def build_reading(card, emotion):
    base = random.choice(card["meanings"])
    special = special_readings.get((card["name"], emotion))

    emotion_line = {
        "외로움": "지금 당신은 연결과 이해를 바라고 있습니다.",
        "불안": "확실하지 않은 미래가 마음을 흔들고 있습니다.",
        "분노": "참아 온 감정이 강하게 움직이고 있습니다.",
        "희망": "아직 포기하지 않은 마음이 안쪽에서 버티고 있습니다.",
        "혼란": "지금은 결정보다 정리가 먼저일 수 있습니다.",
        "슬픔": "슬픔을 밀어내기보다 받아들이는 시간이 필요할 수 있습니다."
    }.get(emotion, "")

    if special:
        return base, emotion_line, special
    return base, emotion_line, None


def page_layout(title, body_html):
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
    body {
      margin: 0;
      background: #f6f3ff;
      color: #1f1830;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .wrap {
      max-width: 720px;
      margin: 0 auto;
      padding: 24px 16px 56px;
    }
    .hero {
      background: linear-gradient(135deg, #2a194a, #5b3aa8);
      color: white;
      border-radius: 24px;
      padding: 24px;
      box-shadow: 0 16px 30px rgba(46, 24, 84, 0.18);
      margin-bottom: 18px;
    }
    .hero h1, .hero h2 {
      margin: 0 0 8px;
    }
    .sub {
      opacity: 0.9;
      line-height: 1.5;
      margin: 0;
    }
    .card {
      background: white;
      border-radius: 20px;
      padding: 18px;
      margin: 14px 0;
      box-shadow: 0 10px 24px rgba(34, 24, 64, 0.08);
    }
    .menu a, .btn, button {
      display: inline-block;
      width: 100%;
      text-align: center;
      text-decoration: none;
      border: none;
      border-radius: 16px;
      padding: 14px 16px;
      margin-top: 10px;
      background: #5b3aa8;
      color: white;
      font-size: 16px;
      cursor: pointer;
    }
    .btn.secondary, .menu a.secondary, button.secondary {
      background: #e9e3ff;
      color: #452a86;
    }
    input, select, textarea {
      width: 100%;
      padding: 14px;
      border-radius: 14px;
      border: 1px solid #d9cfff;
      font-size: 16px;
      margin-top: 10px;
      background: #fff;
    }
    textarea {
      min-height: 120px;
      resize: vertical;
    }
    .pill {
      display: inline-block;
      padding: 8px 12px;
      border-radius: 999px;
      background: #efe8ff;
      color: #5b3aa8;
      font-size: 14px;
      margin-right: 8px;
      margin-bottom: 8px;
    }
    .big {
      font-size: 28px;
      font-weight: 700;
      margin: 8px 0;
    }
    .muted {
      color: #6d6188;
    }
    .divider {
      height: 1px;
      background: #ece4ff;
      margin: 18px 0;
    }
    .list-item {
      padding: 12px 0;
      border-bottom: 1px solid #f0ebff;
    }
    .counter {
      font-size: 30px;
      font-weight: 800;
      color: #5b3aa8;
    }
    .small {
      font-size: 14px;
    }
  </style>
</head>
<body>
  <div class="wrap">
    {{ body|safe }}
  </div>
</body>
</html>
        """,
        title=title,
        body=body_html
    )


@app.route("/")
def home():
    ensure_user_data()
    today_card = session.get("today_card")

    body = f"""
    <div class="hero">
      <h1>🔮 Witch Connect</h1>
      <p class="sub">僕と契約して、魔法少女になってほしいんだ</p>
    </div>

    <div class="card">
      <div class="muted small">오늘의 카드</div>
      <div class="big">{today_card['name']}</div>
      <div class="pill">{today_card['keyword']}</div>
      <div class="pill">{today_card['rarity']}</div>
      <p>{today_card['meaning']}</p>
      <a class="btn secondary" href="/today">오늘의 카드 자세히 보기</a>
    </div>

    <div class="card menu">
      <a href="/tarot">타로 상담</a>
      <a href="/letters/read">익명 점괘 편지 읽기</a>
      <a href="/letters/send" class="secondary">익명 점괘 편지 보내기</a>
      <a href="/book" class="secondary">마법책</a>
      <a href="/collection" class="secondary">카드 도감</a>
    </div>
    """
    return page_layout("Witch Connect", body)


@app.route("/today")
def today():
    ensure_user_data()
    card = session.get("today_card")

    body = f"""
    <div class="hero">
      <h2>🃏 오늘의 카드</h2>
      <p class="sub">오늘의 점괘는?</p>
    </div>

    <div class="card">
      <div class="big">{card['name']}</div>
      <div class="pill">{card['keyword']}</div>
      <div class="pill">{card['rarity']}</div>
      <p>{card['meaning']}</p>
      <div class="divider"></div>
      <div class="muted small">수집 완료.</div>
    </div>

    <a class="btn secondary" href="/">메인으로</a>
    """
    return page_layout("오늘의 카드", body)


@app.route("/tarot", methods=["GET", "POST"])
def tarot():
    ensure_user_data()

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        emotion = request.form.get("emotion", "").strip()

        if not question or emotion not in emotions:
            return redirect("/tarot")

        card = draw_card()
        add_to_collection(card["name"])

        base, emotion_line, special = build_reading(card, emotion)

        sent = session.get("sent", [])
        sent.append({
            "question": question,
            "emotion": emotion,
            "card": card["name"],
            "keyword": card["keyword"],
            "rarity": RARITY_ORDER[card["rarity"]],
            "base": base,
            "special": special or ""
        })
        session["sent"] = sent
        session.modified = True

        special_html = f"""
        <div class="divider"></div>
        <div class="muted small">특수 해석</div>
        <p>{special}</p>
        """ if special else ""

        body = f"""
        <div class="hero">
          <h2>✨ 당신이 뽑은 카드</h2>
          <p class="sub">질문과 감정을 바탕으로 카드가 자동으로 뽑혔어.</p>
        </div>

        <div class="card">
          <div class="muted small">질문</div>
          <p>{question}</p>

          <div class="muted small">현재 감정</div>
          <div class="pill">{emotion}</div>

          <div class="divider"></div>

          <div class="big">{card['name']}</div>
          <div class="pill">{card['keyword']}</div>
          <div class="pill">{RARITY_ORDER[card['rarity']]}</div>

          <div class="divider"></div>
          <div class="muted small">해석</div>
          <p>{base}</p>
          <p>{emotion_line}</p>
          {special_html}
        </div>

        <a class="btn" href="/tarot">다시 상담하기</a>
        <a class="btn secondary" href="/book">마법책 보기</a>
        <a class="btn secondary" href="/collection">카드 도감 보기</a>
        """
        return page_layout("타로 결과", body)

    options = "".join([f'<option value="{e}">{e}</option>' for e in emotions])

    body = f"""
    <div class="hero">
      <h2>🔮 타로 상담</h2>
      <p class="sub">질문을 입력하고 감정을 고르면 카드가 자동으로 뽑혀.</p>
    </div>

    <div class="card">
      <form method="post">
        <label>질문</label>
        <input name="question" placeholder="예: 요즘 관계가 너무 힘든데 어떻게 해야 할까?">

        <label style="display:block; margin-top:12px;">감정</label>
        <select name="emotion">
          {options}
        </select>

        <button type="submit">카드 뽑기</button>
      </form>
    </div>

    <a class="btn secondary" href="/">메인으로</a>
    """
    return page_layout("타로 상담", body)


@app.route("/letters/send", methods=["GET", "POST"])
def letters_send():
    ensure_user_data()

    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if text:
            shared = load_shared_data()
            shared["letters"].append({
                "text": text,
                "created_at": str(datetime.datetime.now())
            })
            save_shared_data(shared)

        body = """
        <div class="hero">
          <h2>📩 편지가 남겨졌어</h2>
          <p class="sub">다른 누군가가 이 편지를 읽고 카드를 뽑게 돼.</p>
        </div>

        <a class="btn" href="/letters/read">익명 편지 읽으러 가기</a>
        <a class="btn secondary" href="/">메인으로</a>
        """
        return page_layout("편지 저장", body)

    body = """
    <div class="hero">
      <h2>📮 익명 점괘 편지 보내기</h2>
      <p class="sub">질문을 남기면 다른 누군가가 카드를 뽑아 보게 되는 구조.</p>
    </div>

    <div class="card">
      <form method="post">
        <label>익명 질문</label>
        <textarea name="text" placeholder="예: 내가 지금 놓치고 있는 감정은 뭘까?"></textarea>
        <button type="submit">편지 남기기</button>
      </form>
    </div>

    <a class="btn secondary" href="/">메인으로</a>
    """
    return page_layout("익명 편지 보내기", body)


@app.route("/letters/read")
def letters_read():
    ensure_user_data()

    shared = load_shared_data()
    queue = shared.get("letters", [])

    if queue:
        item = random.choice(queue)
        queue.remove(item)
        shared["letters"] = queue
        save_shared_data(shared)
        question = item["text"]
    else:
        question = random.choice(npc_letters)

    emotion = random.choice(emotions)
    card = draw_card()
    add_to_collection(card["name"])

    base, emotion_line, special = build_reading(card, emotion)

    received = session.get("received", [])
    received.append({
        "question": question,
        "emotion": emotion,
        "card": card["name"],
        "keyword": card["keyword"],
        "rarity": RARITY_ORDER[card["rarity"]],
        "base": base,
        "special": special or ""
    })
    session["received"] = received
    session.modified = True

    special_html = f"""
    <div class="divider"></div>
    <div class="muted small">특수 해석</div>
    <p>{special}</p>
    """ if special else ""

    body = f"""
    <div class="hero">
      <h2>💌 익명의 점괘 편지</h2>
      <p class="sub">편지를 읽고 카드가 자동으로 뽑혔어. 이 기록은 마법책의 ‘받은 점괘’에 저장돼.</p>
    </div>

    <div class="card">
      <div class="muted small">누군가의 질문</div>
      <p>{question}</p>

      <div class="muted small">감정 흐름</div>
      <div class="pill">{emotion}</div>

      <div class="divider"></div>

      <div class="big">{card['name']}</div>
      <div class="pill">{card['keyword']}</div>
      <div class="pill">{RARITY_ORDER[card['rarity']]}</div>

      <div class="divider"></div>
      <div class="muted small">해석</div>
      <p>{base}</p>
      <p>{emotion_line}</p>
      {special_html}
    </div>

    <a class="btn" href="/letters/read">다른 편지 읽기</a>
    <a class="btn secondary" href="/book">마법책 보기</a>
    """
    return page_layout("익명 편지 읽기", body)


@app.route("/book")
def book():
    ensure_user_data()
    today_card = session.get("today_card")
    sent = session.get("sent", [])
    received = session.get("received", [])

    sent_html = ""
    if sent:
        for item in reversed(sent):
            sent_html += f"""
            <div class="list-item">
              <div class="muted small">질문</div>
              <div>{item['question']}</div>
              <div class="pill">{item['emotion']}</div>
              <div class="pill">{item['card']}</div>
            </div>
            """
    else:
        sent_html = '<p class="muted">아직 보낸 점괘가 없어.</p>'

    received_html = ""
    if received:
        for item in reversed(received):
            received_html += f"""
            <div class="list-item">
              <div class="muted small">편지</div>
              <div>{item['question']}</div>
              <div class="pill">{item['emotion']}</div>
              <div class="pill">{item['card']}</div>
            </div>
            """
    else:
        received_html = '<p class="muted">아직 받은 점괘가 없어.</p>'

    body = f"""
    <div class="hero">
      <h2>📖 마법책</h2>
      <p class="sub">유저 감정 기록용 공간. 오늘의 카드, 내가 보낸 점괘, 받은 점괘를 모아 볼 수 있어.</p>
    </div>

    <div class="card">
      <div class="muted small">오늘의 카드</div>
      <div class="big">{today_card['name']}</div>
      <div class="pill">{today_card['keyword']}</div>
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

    <a class="btn secondary" href="/">메인으로</a>
    """
    return page_layout("마법책", body)


@app.route("/collection", methods=["GET", "POST"])
def collection():
    ensure_user_data()

    if request.method == "POST":
        card = draw_card()
        add_to_collection(card["name"])
        return redirect("/collection")

    owned = session.get("collection", [])
    all_names = [c["name"] for c in cards]

    card_list_html = ""
    for name in all_names:
        if name in owned:
            card_list_html += f'<div class="list-item">🃏 {name}</div>'
        else:
            card_list_html += f'<div class="list-item muted">🔒 {name}</div>'

    body = f"""
    <div class="hero">
      <h2>🃏 카드 도감</h2>
      <p class="sub">MVP에서는 22장 카드 수집. 오늘의 카드와 무료 가챠로 획득하는 구조.</p>
    </div>

    <div class="card">
      <div class="muted small">카드 도감</div>
      <div class="counter">{len(owned)} / {len(all_names)}</div>
      <form method="post">
        <button type="submit">무료 가챠</button>
      </form>
    </div>

    <div class="card">
      <h3>보유 카드</h3>
      {card_list_html}
    </div>

    <a class="btn secondary" href="/">메인으로</a>
    """
    return page_layout("카드 도감", body)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

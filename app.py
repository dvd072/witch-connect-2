from flask import Flask, request, redirect, session, render_template_string, url_for
import os
import json
import random
import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "witch-connect-integrated-secret")

SHARED_FILE = "shared_data.json"

cards = [
    {"name": "광대", "keyword": "새로운 시작", "rarity": "common", "meanings": ["새로운 시작이 가까워지고 있습니다.", "가벼운 마음이 길을 열 수 있습니다.", "예상하지 못한 가능성이 다가옵니다."]},
    {"name": "마법사", "keyword": "의지와 능력", "rarity": "common", "meanings": ["당신에게는 시작할 힘이 있습니다.", "의지와 기술이 함께 움직일 때입니다.", "가능성은 이미 손안에 있습니다."]},
    {"name": "여사제", "keyword": "직감", "rarity": "common", "meanings": ["겉보다 안쪽의 신호를 보세요.", "직감이 중요한 답을 알고 있습니다.", "조용한 판단이 필요합니다."]},
    {"name": "여황제", "keyword": "감정의 풍요", "rarity": "common", "meanings": ["감정은 자라날 수 있습니다.", "돌봄과 안정이 필요합니다.", "관계 안에서 따뜻함이 생겨날 수 있습니다."]},
    {"name": "황제", "keyword": "안정과 통제", "rarity": "common", "meanings": ["흐트러진 것을 정리할 때입니다.", "안정은 스스로 만드는 것입니다.", "기준을 세우면 흔들림이 줄어듭니다."]},
    {"name": "교황", "keyword": "조언", "rarity": "common", "meanings": ["누군가의 지혜가 도움이 됩니다.", "기본으로 돌아가 보세요.", "정답보다 방향이 중요합니다."]},
    {"name": "연인", "keyword": "선택과 연결", "rarity": "rare", "meanings": ["관계는 선택 위에 놓입니다.", "마음이 가는 방향을 보세요.", "연결은 책임도 함께 가져옵니다."]},
    {"name": "전차", "keyword": "전진", "rarity": "rare", "meanings": ["주저하지 말고 밀고 나가세요.", "의지가 길을 만듭니다.", "갈등을 넘는 추진력이 필요합니다."]},
    {"name": "힘", "keyword": "내면의 힘", "rarity": "rare", "meanings": ["강함은 조용할 수도 있습니다.", "감정을 누르기보다 다스리세요.", "버티는 힘도 힘입니다."]},
    {"name": "은둔자", "keyword": "내면 탐색", "rarity": "rare", "meanings": ["혼자 생각할 시간이 필요합니다.", "답은 밖보다 안에 가깝습니다.", "서두르지 말고 천천히 보세요."]},
    {"name": "운명의 수레바퀴", "keyword": "변화", "rarity": "rare", "meanings": ["흐름이 바뀌고 있습니다.", "지금은 변화를 피하기 어렵습니다.", "운은 움직이는 쪽에 가까워집니다."]},
    {"name": "정의", "keyword": "균형", "rarity": "rare", "meanings": ["감정보다 판단이 필요한 순간입니다.", "균형을 되찾아야 합니다.", "지금의 선택은 결과를 남깁니다."]},
    {"name": "매달린 사람", "keyword": "멈춤과 관점", "rarity": "epic", "meanings": ["잠시 멈춰야 보이는 것이 있습니다.", "익숙한 시각을 바꿔 보세요.", "지금은 기다림에도 의미가 있습니다."]},
    {"name": "죽음", "keyword": "끝과 시작", "rarity": "epic", "meanings": ["끝은 다음 시작의 문입니다.", "변화는 이미 시작되었습니다.", "놓아야 새로 들어옵니다."]},
    {"name": "절제", "keyword": "조화", "rarity": "epic", "meanings": ["지금은 섞고 조절하는 시기입니다.", "과하지 않게 가야 합니다.", "느리지만 안정적인 흐름이 중요합니다."]},
    {"name": "악마", "keyword": "집착", "rarity": "epic", "meanings": ["당신을 붙잡는 감정을 보세요.", "불편한 끌림이 있을 수 있습니다.", "벗어나려면 먼저 자각이 필요합니다."]},
    {"name": "탑", "keyword": "붕괴와 충격", "rarity": "legend", "meanings": ["예상하지 못한 변화가 올 수 있습니다.", "무너지면서 진실이 드러납니다.", "불편하지만 필요한 흔들림일 수 있습니다."]},
    {"name": "별", "keyword": "희망과 치유", "rarity": "legend", "meanings": ["희망은 아직 꺼지지 않았습니다.", "천천히 회복될 수 있습니다.", "멀어 보여도 빛은 존재합니다."]},
    {"name": "달", "keyword": "불안과 혼란", "rarity": "legend", "meanings": ["모호한 감정이 커질 수 있습니다.", "지금은 모든 것이 선명하지 않을 수 있습니다.", "불안은 진실과 환상을 섞어 보이게 합니다."]},
    {"name": "태양", "keyword": "명확함과 기쁨", "rarity": "legend", "meanings": ["상황이 분명해질 가능성이 큽니다.", "따뜻한 흐름이 당신 쪽으로 옵니다.", "기쁨은 생각보다 가까이에 있습니다."]},
    {"name": "심판", "keyword": "각성", "rarity": "legend", "meanings": ["이제는 깨달아야 할 때입니다.", "과거를 정리하고 넘어갈 시기입니다.", "새로운 판단이 필요합니다."]},
    {"name": "세계", "keyword": "완성과 성취", "rarity": "legend", "meanings": ["하나의 흐름이 완성됩니다.", "도달해야 할 지점에 가까워졌습니다.", "마침내 정리되는 순간이 옵니다."]}
]

emotions = ["외로움", "불안", "분노", "희망", "혼란", "슬픔"]

special_readings = {
    ("달", "불안"): "지금의 불안은 현실보다 크게 느껴지고 있을 수 있습니다. 결론을 서두르지 않는 편이 좋습니다.",
    ("별", "슬픔"): "슬픔은 바로 사라지지 않아도, 회복은 이미 시작되었을 가능성이 큽니다.",
    ("탑", "분노"): "억눌러 온 감정이 무너지듯 터질 수 있습니다. 감정을 부정하지 말고 안전하게 흘려보내세요.",
    ("태양", "희망"): "지금 품고 있는 희망은 허상이 아닐 가능성이 큽니다. 밀고 나갈 가치가 있습니다.",
    ("은둔자", "혼란"): "혼란할수록 혼자 생각할 시간이 필요합니다. 답은 시끄러운 바깥보다 안쪽에 가깝습니다."
}

cat_lines = [
    "검은 고양이가 조용히 촛불 옆에 앉아 있다.",
    "검은 고양이가 책장 위에서 꼬리를 흔들고 있다.",
    "검은 고양이가 네 쪽을 빤히 바라본다.",
    "검은 고양이가 작업실 문 앞에 웅크리고 있다.",
    "검은 고양이가 책 위에 올라와서 졸고 있다.",
    "검은 고양이가 앞발로 카드 더미를 살짝 밀었다.",
    "검은 고양이가 룬 주머니를 한 번 건드리고 지나갔다.",
    "검은 고양이가 메리벨 쪽을 바라보다가 다시 너를 본다."
]

cat_talks = [
    "고양이가 네 무릎 위에 앞발을 올리고 가만히 올려다본다.",
    "고양이가 카드 더미 옆에 앉아 꼬리를 천천히 흔든다.",
    "고양이가 오늘은 편지가 도착했는지 작업실 문 쪽을 바라본다.",
    "고양이가 작업실 안을 한 바퀴 돌고는 촛불 아래에 앉는다.",
    "고양이가 메리벨이 오늘도 왔다고 알고 있는 눈치다.",
    "고양이가 룬은 모아 둘수록 쓸 곳이 많다고 말하는 것만 같다.",
    "고양이가 도감에 빈 칸이 많다며 책장을 앞발로 톡 친다.",
    "고양이가 아무 말 없이 네 옆에 붙어 앉아 있다."
]

resident_npc = {
    "name": "메리벨",
    "personality": "상냥한 언니 느낌",
    "problems": [
        {
            "title": "남을 먼저 챙기는 습관",
            "text": "주변 사람들을 돌보는 데 익숙해서 정작 자기 감정이나 욕구는 뒤로 미뤄요. 어느 순간 ‘나는 뭘 원하는 거지?’라는 공허함이 들어요."
        },
        {
            "title": "강한 사람으로 보이는 부담",
            "text": "모두가 의지하다 보니 약한 모습을 보이기 어려워요. 울고 싶어도 참고 ‘언니니까 괜찮아’라고 넘기게 돼요."
        },
        {
            "title": "사람들에게 필요 없는 존재가 될까 봐 두려움",
            "text": "자신이 누군가에게 도움이 되지 못하면 가치가 사라지는 것 같다는 불안이 있어요."
        },
        {
            "title": "누군가에게는 솔직해지고 싶은 마음",
            "text": "항상 조언하는 위치에 있지만, 자신도 기대고 싶은 사람이 있었으면 좋겠다고 생각해요."
        },
        {
            "title": "선의를 오해받는 순간",
            "text": "도와주거나 간섭한 것이 ‘참견’이나 ‘위선’으로 보일 때 상처받아요. 그래도 다시 누군가를 돕게 되는 자신을 이해하지 못하겠어요."
        }
    ],
    "lines": [
        "괜찮아, 천천히 해도 돼. 내가 옆에 있을게.",
        "힘들면 말해도 돼. 혼자 버틸 필요 없어.",
        "응, 알아. 그래도 넌 꽤 잘하고 있어.",
        "내 걱정은 하지 마. 나는 원래 이런 거 잘 하거든.",
        "사람이 가끔 흔들리는 건 당연해. 그게 끝은 아니니까.",
        "…가끔은 나도 누가 괜찮다고 말해줬으면 좋겠네."
    ]
}

rarity_label = {
    "common": "일반",
    "rare": "희귀",
    "epic": "에픽",
    "legend": "전설"
}


def load_shared_data():
    if os.path.exists(SHARED_FILE):
        with open(SHARED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"letters": [], "board_posts": []}


def save_shared_data(data):
    with open(SHARED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_to_collection(card_name):
    collection = session.get("collection", [])
    if card_name not in collection:
        collection.append(card_name)
        session["collection"] = collection
        session.modified = True


def weighted_draw():
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
    body {
      margin: 0;
      background: #f7f3ff;
      color: #22183d;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .wrap {
      max-width: 760px;
      margin: 0 auto;
      padding: 20px 16px 56px;
    }
    .hero {
      background: linear-gradient(135deg, #2c184f, #6a47bd);
      color: white;
      border-radius: 24px;
      padding: 24px;
      box-shadow: 0 18px 34px rgba(54, 31, 100, 0.18);
      margin-bottom: 16px;
    }
    .hero h1, .hero h2 { margin: 0 0 8px; }
    .sub { margin: 0; opacity: .92; line-height: 1.55; }
    .card {
      background: white;
      border-radius: 20px;
      padding: 18px;
      margin: 14px 0;
      box-shadow: 0 10px 24px rgba(30, 20, 60, 0.08);
    }
    .btn, button {
      display: inline-block;
      width: 100%;
      border: none;
      border-radius: 16px;
      padding: 14px 16px;
      background: #6340b3;
      color: white;
      text-align: center;
      text-decoration: none;
      font-size: 16px;
      cursor: pointer;
      margin-top: 10px;
    }
    .btn.secondary, button.secondary {
      background: #eee7ff;
      color: #50308f;
    }
    .btn.ghost {
      background: #f8f5ff;
      color: #5d45a2;
      border: 1px solid #e3d8ff;
    }
    input, select, textarea {
      width: 100%;
      padding: 14px;
      border-radius: 14px;
      border: 1px solid #dccfff;
      background: white;
      font-size: 16px;
      margin-top: 10px;
    }
    textarea { min-height: 110px; resize: vertical; }
    .pill {
      display: inline-block;
      padding: 8px 12px;
      border-radius: 999px;
      background: #f0e9ff;
      color: #5b3fa8;
      font-size: 14px;
      margin-right: 8px;
      margin-bottom: 8px;
    }
    .big { font-size: 30px; font-weight: 800; margin: 8px 0; }
    .small { font-size: 14px; color: #6b6282; }
    .divider { height: 1px; background: #eee7ff; margin: 16px 0; }
    .grid6 {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;
    }
    .tarot-back {
      border-radius: 18px;
      padding: 24px 14px;
      min-height: 120px;
      background: linear-gradient(135deg, #251542, #49307e);
      color: white;
      font-weight: 700;
      border: 2px solid #8870d0;
    }
    .item {
      padding: 12px 0;
      border-bottom: 1px solid #f2edff;
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
        body=body
    )


@app.route("/")
def home():
    ensure_data()
    today_card = session["today_card"]

    shared = load_shared_data()
    open_letters = [l for l in shared.get("letters", []) if l["status"] == "open"]

    body = f"""
    <div class="hero">
      <h1>🌙 오늘의 카드</h1>
      <p class="sub">앱에 들어오면 오늘의 카드가 먼저 도착해. 진짜 메인 공간은 작업실이야.</p>
    </div>

    <div class="card">
      <div class="small">오늘의 카드</div>
      <div class="big">{today_card['name']}</div>
      <div class="pill">{today_card['keyword']}</div>
      <div class="pill">{today_card['rarity']}</div>
      <p>{today_card['meaning']}</p>
    </div>

    <div class="card">
      <div class="small">검은 고양이</div>
      <p>{session.get('cat_line', '')}</p>
    </div>

    <div class="card">
      <div class="small">오늘의 상태</div>
      <div class="pill">보유 룬 {session.get('runes', 0)}</div>
      <div class="pill">열린 익명 편지 {len(open_letters)}개</div>
    </div>

    <a class="btn" href="/workroom">작업실로 들어가기</a>
    <a class="btn secondary" href="/assistant">검은 고양이</a>
    <a class="btn secondary" href="/collection">카드 도감</a>
    <a class="btn secondary" href="/board">게시판</a>
    """
    return page("오늘의 카드", body)


@app.route("/workroom")
def workroom():
    ensure_data()
    shared = load_shared_data()

    pending = [q for q in session.get("questions", []) if q["status"] == "pending"]
    done = [q for q in session.get("questions", []) if q["status"] == "done"]
    resident_today = session.get("resident_today")

    open_letters = [l for l in shared.get("letters", []) if l["status"] == "open"]
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
      <p class="sub">질문을 남기고, 익명 편지를 확인하고, 주민의 고민을 봐줄 수 있는 메인 공간이야.</p>
    </div>

    <div class="card">
      <h3>오늘의 상태</h3>
      <div class="pill">보유 룬 {rune_count}</div>
      <div class="pill">열린 편지 {len(open_letters)}개</div>
      <div class="pill">메리벨 {resident_status}</div>
    </div>

    <div class="card">
      <h3>작업실 메뉴</h3>
      <a class="btn" href="/question/new">내 질문 남기기</a>
      <a class="btn secondary" href="/letters/send">익명 편지 남기기</a>
      <a class="btn secondary" href="/assistant">검은 고양이 조수</a>
      <a class="btn secondary" href="/collection">카드 도감 / 가챠</a>
      <a class="btn secondary" href="/board">광장 게시판</a>
      <a class="btn secondary" href="/book">마법책 기록</a>
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
      <h2>✍️ 질문 남기기</h2>
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
    return page("질문 남기기", body)


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
      <h3>카드를 골라 줘</h3>
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
                "created_at": str(datetime.datetime.now())
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

            return redirect(url_for("letter_result", letter_id=letter_id))

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
      <h3>카드를 골라 줘</h3>
      <div class="grid6">
        {cards_html}
      </div>
    </div>

    <a class="btn secondary" href="/workroom">작업실로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("익명 편지 카드 선택", body)


@app.route("/letter/<letter_id>/result")
def letter_result(letter_id):
    ensure_data()

    letter_result_item = None
    for item in reversed(session.get("received_readings", [])):
        if item["id"] == letter_id:
            letter_result_item = item
            break

    if not letter_result_item:
        return redirect("/workroom")

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
      {special_html}
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
            card = weighted_draw()
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

            return redirect("/resident/result")

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
      <h3>카드를 골라 줘</h3>
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
    open_letters = [l for l in shared.get("letters", []) if l["status"] == "open"]

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
      <h3>주민 기록</h3>
      {resident_html}
    </div>

    <a class="btn secondary" href="/workroom">작업실로</a>
    <a class="btn ghost" href="/">메인으로</a>
    """
    return page("마법책", body)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

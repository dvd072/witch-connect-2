import random
from game_data import forest_data, forest_events


def ensure_forest_state(session, today: str):
    if "forest_inventory" not in session:
        session["forest_inventory"] = []

    if "forest_treasures" not in session:
        session["forest_treasures"] = []

    if "forest_depth" not in session:
        session["forest_depth"] = 0

    if "forest_last_scene" not in session:
        session["forest_last_scene"] = ""

    if "forest_paths" not in session:
        session["forest_paths"] = []

    if "forest_action_scene" not in session:
        session["forest_action_scene"] = None

    if "forest_last_event" not in session:
        session["forest_last_event"] = None

    if "forest_energy" not in session:
        session["forest_energy"] = 10

    if "forest_max_energy" not in session:
        session["forest_max_energy"] = 10

    if "forest_date" not in session:
        session["forest_date"] = ""

    if session["forest_date"] != today:
        session["forest_depth"] = 0
        session["forest_last_scene"] = ""
        session["forest_paths"] = []
        session["forest_action_scene"] = None
        session["forest_last_event"] = None
        session["forest_energy"] = 10
        session["forest_max_energy"] = 10
        session["forest_date"] = today
        session.modified = True


def reset_forest_run(session):
    session["forest_depth"] = 0
    session["forest_last_scene"] = ""
    session["forest_paths"] = []
    session["forest_action_scene"] = None
    session["forest_last_event"] = None
    session.modified = True


def consume_forest_energy(session, amount=1):
    energy = session.get("forest_energy", 0)
    if energy < amount:
        return False

    session["forest_energy"] = energy - amount
    session.modified = True
    return True


def get_depth_rare_bonus(depth: int):
    if depth <= 1:
        return 0
    if depth == 2:
        return 3
    if depth == 3:
        return 6
    if depth == 4:
        return 10
    return 15


def draw_forest_item(session):
    depth = session.get("forest_depth", 0)
    rare_bonus = get_depth_rare_bonus(depth)

    adjusted_items = []
    for item in forest_data["items"]:
        if item["rarity"] == "rare":
            adjusted_items.append({
                "name": item["name"],
                "rarity": item["rarity"],
                "weight": item["weight"] + rare_bonus
            })
        else:
            adjusted_items.append(item)

    total_weight = sum(item["weight"] for item in adjusted_items)
    roll = random.randint(1, total_weight)

    current = 0
    for item in adjusted_items:
        current += item["weight"]
        if roll <= current:
            return item

    return adjusted_items[0]


def draw_forest_event(session, action_type="search"):
    depth = session.get("forest_depth", 0)

    base = 0
    if action_type == "harvest":
        base = 14
    elif action_type == "search":
        base = 40
    elif action_type == "pass":
        base = 0

    chance = min(base + depth * 4, 65)
    roll = random.randint(1, 100)

    if roll <= chance:
        return random.choice(forest_events)

    return None


def generate_forest_scene(session):
    depth = session.get("forest_depth", 0)

    scene_texts = [
        "사이프러스 나무들이 높게 뻗어 있고, 숲 전체에 옅은 신비로운 기운이 감돈다.",
        "축축한 흙 냄새와 함께 숲이 조용히 숨 쉬는 것처럼 느껴진다.",
        "숲 깊은 곳에서 희미한 빛이 흔들리는 것만 같다.",
        "잎사귀 사이로 스며드는 빛이 어둑한 숲 바닥을 희미하게 비춘다.",
        "바람이 스칠 때마다 숲이 무언가를 속삭이는 것처럼 들린다."
    ]

    left_texts = [
        "왼쪽 나무 사이로 풀잎이 흔들린다.",
        "왼쪽에서 옅은 향기가 흘러온다.",
        "왼쪽 덤불 아래로 반짝이는 것이 스친다.",
        "왼쪽에는 촉촉한 흙 냄새가 스며 있다."
    ]

    forward_texts = [
        "정면에는 안개 낀 오솔길이 이어진다.",
        "정면 길은 고요하지만 묘하게 깊어 보인다.",
        "정면 쪽으로 달빛이 희미하게 떨어지고 있다.",
        "정면의 나무 그림자들이 길게 늘어져 있다."
    ]

    right_texts = [
        "오른쪽에는 나무뿌리 사이로 어두운 길이 보인다.",
        "오른쪽에서 젖은 흙 냄새가 난다.",
        "오른쪽 가지 사이에서 바람이 낮게 울린다.",
        "오른쪽 수풀 뒤편에 뭔가 숨겨진 듯한 기분이 든다."
    ]

    if depth >= 3:
        scene_texts += [
            "숲은 점점 조용해지고, 발소리마저 이질적으로 울린다.",
            "사이프러스의 그림자가 길을 덮으며 방향 감각을 흐리게 만든다."
        ]

    paths = [
        {"key": "left", "label": "왼쪽으로 간다", "desc": random.choice(left_texts)},
        {"key": "forward", "label": "정면으로 간다", "desc": random.choice(forward_texts)},
        {"key": "right", "label": "오른쪽으로 간다", "desc": random.choice(right_texts)},
    ]

    session["forest_last_scene"] = random.choice(scene_texts)
    session["forest_paths"] = paths
    session.modified = True


def resolve_forest_event(session, event):
    inventory = session.get("forest_inventory", [])
    treasures = session.get("forest_treasures", [])

    result = {
        "title": event["title"],
        "description": event["description"],
        "rewards": []
    }

    if event["type"] == "bonus_harvest":
        bonus_pool = [
            {"name": "신선한 허브", "rarity": "노멀"},
            {"name": "아름다운 꽃잎", "rarity": "노멀"},
            {"name": "빛나는 원석", "rarity": "노멀"},
            {"name": "요정의 날개", "rarity": "레어"},
        ]

        for _ in range(5):
            picked = random.choices(
                bonus_pool,
                weights=[30, 30, 30, 5],
                k=1
            )[0]

            inventory.append({
                "name": picked["name"],
                "rarity": picked["rarity"]
            })
            result["rewards"].append(picked)

    elif event["type"] == "guaranteed_fairy":
        reward = {"name": "요정의 날개", "rarity": "레어"}
        inventory.append(reward)
        result["rewards"].append(reward)

    elif event["type"] == "marybelle_flower":
        reward = {"name": "아름다운 꽃잎", "rarity": "노멀"}
        inventory.append(reward)
        result["rewards"].append(reward)

    elif event["type"] == "cat_rescue_preview":
        result["rewards"].append({
            "name": "검은 고양이의 도움",
            "rarity": "이벤트"
        })

    elif event["type"] == "ritual_dagger":
        reward = {"name": "의식용 단검", "rarity": "전리품"}
        treasures.append(reward)
        result["rewards"].append(reward)

    session["forest_inventory"] = inventory
    session["forest_treasures"] = treasures
    session["forest_last_event"] = result
    session.modified = True

    return result

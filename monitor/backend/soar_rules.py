from history_ai import decide_with_ai


def decide_with_rule(history):
    if history["login_failure_count"] >= 3:
        return {"decision": "respond", "reason": "최근 이력에 로그인 실패가 3회 이상 있습니다."}
    return {"decision": "review", "reason": "최근 이력의 로그인 실패가 3회 미만입니다."}


def make_prompt():
    return "요청 횟수와 시간순서를 보고 판단하세요. 관찰 사실과 추정을 구분하고 근거 ID와 한계를 적으세요."


def decide(history):
    return decide_with_rule(history)


def choose_actions(decision):
    if decision == "respond":
        return ["notify", "create_ticket"]
    return ["notify", "create_ticket"]

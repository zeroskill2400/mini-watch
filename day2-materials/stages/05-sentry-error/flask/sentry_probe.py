import sentry_sdk

dsn = input("Sentry DSN: ").strip()
if not dsn:
    raise SystemExit("프로젝트의 DSN을 입력하세요.")

sentry_sdk.init(
    dsn=dsn,
    environment="local",
    send_default_pii=False,
    include_local_variables=False,
    enable_logs=False,
    traces_sample_rate=0.0,
)

try:
    raise ValueError("Day2 단독 오류 확인")
except ValueError as error:
    event_id = sentry_sdk.capture_exception(error)

sentry_sdk.flush(timeout=5)
print("보낼 오류의 ID:", event_id)
print("Sentry Issues에서 'Day2 단독 오류 확인'을 찾으세요.")

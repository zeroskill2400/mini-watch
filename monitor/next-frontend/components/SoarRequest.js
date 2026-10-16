import { PlaybookRun } from "./Playbook";

const STATE_LABELS = {
  awaiting_notification: "AI 알림 대기",
  notifying: "AI 알림 요청 중",
  awaiting_approval: "사람 승인 대기",
  approved: "실행 대기",
  executing: "제한 실행 중",
  restricted: "공지 저장 제한 중",
  verified: "정책 거절 403 확인",
  recovery_approved: "복구 실행 대기",
  recovering: "저장 허용 복구 중",
  restored: "저장 허용 · 200 확인 대기",
  completed: "정상 저장 200 확인 · 완료",
  completed_no_action: "기록만 남김 · 조치 없이 완료",
  rejected: "요청 거절 · 종료",
  cancelled: "승인 취소 · 종료",
  execution_error: "제한 실행 오류",
  recovery_error: "복구 실행 오류",
};

export function stateLabel(state) {
  return STATE_LABELS[state] || state;
}

export function displayTime(value) {
  if (!value) return "—";
  const timestamp = new Date(value);
  return Number.isNaN(timestamp.getTime()) ? value : timestamp.toLocaleString("ko-KR", { hour12: false });
}

function RawRecord({ title, record }) {
  if (!record) return null;
  return <details className="detection-raw soar-raw">
    <summary>{title}</summary>
    <pre>{JSON.stringify(record, null, 2)}</pre>
  </details>;
}

function Notification({ notification }) {
  if (!notification) return <p className="log-empty">아직 AI 요약 알림이 없습니다. 실제 API 응답이 있어야 승인을 요청할 수 있습니다.</p>;
  const result = notification.result;
  return <div className="soar-notification" id="soar-notification">
    <p className="detection-eyebrow">저장된 실제 AI 응답 · {notification.model} · {displayTime(notification.created_at)}</p>
    <h4>우선순위: {({ low: "낮음", medium: "중간", high: "높음" })[result.priority] || result.priority}</h4>
    <p>{result.summary}</p>
    <details className="detection-raw">
      <summary>추천과 근거 대조하기</summary>
      <h4>관찰한 내용</h4>
      <ul>{result.observations.map((item, index) => <li key={index}>{item}</li>)}</ul>
      <h4>사람이 확인할 항목</h4>
      <ul>{result.checks.map((item, index) => <li key={index}>{item}</li>)}</ul>
      <h4>단정하면 안 되는 점</h4>
      <ul>{result.cautions.map((item, index) => <li key={index}>{item}</li>)}</ul>
      <h4>AI가 인용한 근거 ID</h4>
      <ul>{result.evidence_ids.map(identifier => <li key={identifier}><code>{identifier}</code></li>)}</ul>
    </details>
    <RawRecord title="AI에 보낸 입력과 실제 응답 원문" record={notification} />
  </div>;
}

function Verification({ record, restored = false }) {
  if (!record) return null;
  if (record.status_code !== (restored ? 200 : 403) || record.expected_outcome !== (restored ? "save_succeeded" : "policy_denied")) {
    return <p className="error">저장 검증 기록의 상태와 결과가 맞지 않습니다. 성공으로 표시하지 않습니다.</p>;
  }
  return <div className="soar-verification">
    <strong>{restored ? "정상 저장 HTTP 200 확인" : "정책 거절 HTTP 403 확인"}</strong>
    <p>{restored
      ? "일반 사이트의 실제 공지 저장 기록을 확인했습니다. 저장 허용 복구는 이전 공지 내용으로 되돌리는 작업이 아닙니다."
      : "일반 사이트의 공지 저장이 이 제한 정책으로 거절된 원본을 확인했습니다. 로그인·입력·CSRF 오류의 403과 구분합니다."}</p>
    <RawRecord title={restored ? "정상 저장 200 원본 보기" : "정책 거절 403 원본 보기"} record={record} />
  </div>;
}

export default function SoarRequest({ request, rules, ai, busy, stale, onAction, recoveryOnly = false }) {
  const disabled = busy || stale;
  const hasNotification = Boolean(request.notification);
  const recordOnly = request.playbook_snapshot?.steps?.includes("record_only") === true;
  const caseRecord = request.case_snapshot;
  const canRecover = ["restricted", "verified", "execution_error"].includes(request.state);
  const canVerify = ["restricted", "restored"].includes(request.state);
  const stateGuides = {
    awaiting_notification: "요청을 만들었지만 아직 제한하지 않았습니다. 실제 AI 요약 알림을 만들고 근거와 대조하세요.",
    notifying: "실제 AI API 응답을 기다리고 있습니다. 알림 저장이 끝나기 전에는 승인하거나 실행하지 않습니다.",
    awaiting_approval: "알림을 읽고 사람이 승인하거나 거절합니다. AI는 승인하지 않으며 임의 조치를 실행하지 않습니다.",
    approved: rules.execute_approved
      ? "승인된 요청을 서버가 자동으로 처리합니다. 이 화면을 닫아도 처리는 계속됩니다."
      : "승인은 기록됐지만 EXECUTE_APPROVED=False라 실행하지 않습니다. True로 반영되면 준비된 서버가 이 요청을 자동으로 처리합니다.",
    executing: recordOnly ? "승인된 기록 단계를 처리 중입니다. 공지 저장 정책은 바꾸지 않습니다." : "승인된 공지 저장 제한을 실행 중입니다. 같은 요청에 다시 실행을 지시할 필요가 없습니다.",
    restricted: "일반 사이트에서 기존 내용과 다르게 공지를 저장해 보세요. 이후 저장 결과 확인을 눌러 실제 정책 거절 403을 연결합니다.",
    verified: "실제 정책 거절 403과 원본 불변을 확인했습니다. 사람이 복구를 승인하면 공지 저장을 다시 허용합니다.",
    recovery_approved: "복구 승인이 기록됐습니다. 서버가 공지 저장 허용을 자동으로 처리합니다. 복구는 자동 제한 설정이 꺼져 있어도 진행하는 안전 경로입니다.",
    recovering: "공지 저장을 다시 허용하는 중입니다. 공지 내용은 이전 버전으로 되돌리지 않습니다.",
    restored: "일반 사이트에서 서로 다른 내용으로 공지를 저장하고 저장 결과 확인을 누르세요. 실제 정상 저장 200을 연결해야 완료됩니다.",
    completed: request.verification
      ? "제한, 실제 정책 거절 403, 저장 허용 복구, 실제 정상 저장 200을 한 요청에서 확인했습니다."
      : "안전 복구 뒤 실제 정상 저장 200을 확인했습니다. 제한 당시의 정책 거절 403은 확인하지 않았습니다.",
    completed_no_action: "기록만 남기는 플레이북을 끝냈습니다. 공지 저장을 제한하지 않았으며 정책 거절 403과 복구 뒤 200 검증은 하지 않았습니다.",
    rejected: "사람이 요청을 거절했습니다. 이 요청은 제한을 실행하지 않으며 거절 기록은 남습니다.",
    cancelled: "실행 전 승인을 취소했습니다. 취소 기록은 남으며 이 요청으로 제한하지 않습니다.",
    execution_error: "제한 실행 결과를 확정하지 못했습니다. 아래 오류와 현재 정책을 확인하세요. 성공으로 표시하지 않습니다.",
    recovery_error: "복구 실행 결과를 확정하지 못했습니다. 아래 오류와 현재 정책을 확인하세요. 복구 완료로 표시하지 않습니다.",
  };

  return <section className="soar-request" aria-labelledby="soar-request-title" data-request-id={request.id}>
    <div className="detection-heading-row">
      <h3 id="soar-request-title">선택한 플레이북 실행 · 대응 요청</h3>
      <strong id="soar-request-state" className={`soar-state soar-state-${request.state}`}>{stateLabel(request.state)}</strong>
    </div>
    <p className="soar-request-id"><code>{request.id}</code></p>
    <dl className="soar-facts">
      <div><dt>{recordOnly ? "기록 대상" : "제한 대상"}</dt><dd><code>{caseRecord.server_id}</code> · <code>{caseRecord.target_path}</code>{recordOnly ? " · 정책 변경 없음" : "의 저장만"}</dd></div>
      <div><dt>인증된 계정</dt><dd>{caseRecord.username || "연결되지 않음"}</dd></div>
      <div><dt>요청에 연결한 실패</dt><dd>{request.failure_count}회 · 입력 이름이 같아도 동일인이라는 뜻은 아닙니다.</dd></div>
      <div><dt>요청 생성</dt><dd>{request.created_by} · {displayTime(request.created_at)}</dd></div>
    </dl>
    <p className="soar-guide" id="soar-request-guide">{recoveryOnly && ["awaiting_notification", "awaiting_approval", "approved"].includes(request.state) ? "이전 방식으로 저장된 상태입니다. 여기서는 새 알림이나 제한 승인을 시작하지 않습니다." : stateGuides[request.state]}</p>
    {request.last_error && <p className="error" role="alert">최근 실패: {typeof request.last_error === "string" ? request.last_error : JSON.stringify(request.last_error)}</p>}
    <RawRecord title="요청 생성 때의 사건과 원본 근거 보기" record={{ case: caseRecord, failure_evidence: request.failure_evidence }} />
    <PlaybookRun request={request} formatTime={displayTime} />

    <section className="soar-step" aria-labelledby="soar-inbox-title">
      <h4 id="soar-inbox-title">담당자 알림</h4>
      <Notification notification={request.notification} />
      {hasNotification && <p><a href="#soar-request-title">이 요청의 사건·근거 확인</a></p>}
      {request.notification_history?.length > 1 && <details className="detection-raw soar-raw">
        <summary>이전 AI 알림과 요청 문장 비교 · {request.notification_history.length - 1}건</summary>
        {request.notification_history.slice(0, -1).map(notification => <RawRecord key={notification.id} title={`${displayTime(notification.created_at)} · ${notification.model}`} record={notification} />)}
      </details>}
      {!recoveryOnly && ["awaiting_notification", "awaiting_approval"].includes(request.state) && <>
        <button id="soar-notify" onClick={() => onAction("notify", request.id)} disabled={disabled}>AI 요약 알림 만들기</button>
        {hasNotification && <p className="detection-small-note">다시 요청하면 새 실제 응답을 저장합니다. 실패하면 이전 응답을 그대로 두므로 저장 시각을 확인하세요.</p>}
        {!ai.available && <p className="error">AI 연결 미설정입니다. 요청하면 실제 미연결 오류를 표시하며 예시 답변으로 대신하지 않습니다.</p>}
      </>}
      <p className="detection-small-note">알림과 근거는 이 요청에 저장됩니다. 외부 Slack 발송이 아니며 AI 추천만으로 제한하지 않습니다.</p>
    </section>

    <section className="soar-step" aria-labelledby="soar-decision-title">
      <h4 id="soar-decision-title">사람 승인과 자동 실행</h4>
      {request.approval && <p>{recordOnly ? "기록 승인" : "제한 승인"}: <strong>{request.approval.operator}</strong> · {displayTime(request.approval.at)}</p>}
      <p>승인 대상: <code>{caseRecord.server_id}</code> · <code>{caseRecord.target_path}</code></p>
      <p>허용 조치: <strong>{recordOnly ? "기록만 남기기 · 정책 변경 없음" : "공지 저장 제한 / 저장 허용 복구"}</strong>. 로그인과 공지 읽기는 유지합니다.</p>
      {!recoveryOnly && <div className="actions">
        {request.state === "awaiting_approval" && <button id="soar-approve" className="soar-restrict" onClick={() => onAction("approve", request.id)} disabled={disabled || !hasNotification}>{recordOnly ? "기록 승인" : "제한 승인"}</button>}
        {request.state === "awaiting_approval" && <button id="soar-reject" onClick={() => onAction("reject", request.id)} disabled={disabled}>요청 거절</button>}
        {request.state === "approved" && <button id="soar-cancel" onClick={() => onAction("cancel", request.id)} disabled={disabled}>승인 취소</button>}
      </div>}
      {!recoveryOnly && request.state === "awaiting_approval" && <p className="detection-small-note">{recordOnly ? "기록 승인은 조치 없이 처리 기록만 남기는 승인입니다." : "제한 승인은 위 대상의 저장만 막는 승인입니다."} {rules.execute_approved ? "현재 자동 실행이 켜져 있어 승인 후 서버가 곧바로 처리합니다." : "현재 자동 실행이 꺼져 있어 승인 뒤 실행 대기 상태로 남습니다."}</p>}
      {request.restriction && <RawRecord title="제한 실행 기록 보기 · 중복 실행과 구분" record={request.restriction} />}
      {request.recovery && <RawRecord title="저장 허용 복구 실행 기록 보기" record={request.recovery} />}
      {(recoveryOnly ? request.state === "recovery_error" : ["execution_error", "recovery_error"].includes(request.state)) && <button id="soar-retry" onClick={() => onAction("retry", request.id)} disabled={disabled}>실패한 조치 다시 확인</button>}
    </section>

    {(canVerify || canRecover || request.verification || request.recovery_verification) && <section className="soar-step" aria-labelledby="soar-verify-title">
      <h4 id="soar-verify-title">실제 저장으로 효과 확인</h4>
      <p>일반 사이트에서 <strong>공지 저장</strong>을 먼저 누르고, 여기서 원본 기록을 확인합니다. 이 확인 버튼 자체가 공지를 저장하지는 않습니다.</p>
      <div className="actions">
        <a className="soar-link-button" href="http://localhost:8085/notice" target="_blank" rel="noopener noreferrer">일반 사이트 공지 열기</a>
        {canVerify && <button id="soar-verify" onClick={() => onAction("verify", request.id)} disabled={disabled}>저장 결과 확인</button>}
      </div>
      <Verification record={request.verification} />
      <Verification record={request.recovery_verification} restored />
      {canRecover && <div className="soar-recovery">
        <p>복구 대상도 위 공지 파일 하나입니다. <strong>저장을 다시 허용</strong>하며 공지 원문을 복원하지 않습니다.</p>
        <button id="soar-recover" onClick={() => onAction("recover", request.id)} disabled={disabled}>저장 허용 복구 승인</button>
        {request.state === "execution_error" && <p className="detection-small-note">서버에 이 요청의 실제 제한 기록이 있을 때만 복구합니다. 제한 기록이 없으면 오류를 표시합니다.</p>}
        {!request.verification && <p className="detection-small-note">아직 정책 거절 403을 확인하지 않았습니다. 수업에서는 먼저 저장 결과를 확인하세요.</p>}
      </div>}
    </section>}

    <section className="soar-step" aria-labelledby="soar-timeline-title">
      <h4 id="soar-timeline-title">요청 타임라인</h4>
      <ol id="soar-timeline" className="soar-timeline">
        {request.history.map((entry, index) => <li key={`${entry.at}-${entry.type}-${index}`} data-history-type={entry.type}>
          <div><strong>{entry.message}</strong><span>{entry.operator || "서버"}</span></div>
          <time dateTime={entry.at}>{displayTime(entry.at)}</time>
        </li>)}
      </ol>
      <p className="detection-small-note">새로고침은 기록 조회입니다. 요청 생성·승인·실행·검증은 서로 다른 기록으로 남습니다.</p>
    </section>
  </section>;
}

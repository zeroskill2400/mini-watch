import { displayTime } from "./SoarRequest";

const STAGES = [["extract", "URL 추출"], ["lookup", "정보 조회"], ["decide", "조건 판단"], ["plan", "대응 계획"], ["execute", "대응 실행"], ["record", "결과 알림"]];
const ACTIONS = { restrict_notice: "공지 저장 제한", notify: "담당자 알림 저장", create_ticket: "내부 티켓 생성" };
const STATES = { running: "실행 중", review_pending: "검토 대기", completed: "계획한 작업 완료", restricted: "공지 저장 제한 중", verified: "실제 정책 거절 403 확인", restored: "저장 허용 · 실제 200 확인 대기", completed_recovery: "저장 허용 복구 확인 완료", error: "실행 오류", recovery_error: "복구 오류", recovering: "복구 중" };
const STATUSES = { pending: "실행 전", running: "처리 중", succeeded: "완료", failed: "실패", skipped: "건너뜀" };

export function runLabel(state) {
  return STATES[state] || state || "결과 없음";
}

function branchLabel(value) {
  return value === "review" ? "review · 검토 대기" : value === "respond" ? "respond · 대응 경로" : "분기 미확인";
}

function actionLabel(value) {
  return ACTIONS[value] || value;
}

function ActionList({ values = [] }) {
  return values.length ? <ul className="light-action-list">{values.map(value => <li key={value}>{actionLabel(value)} <code>{value}</code></li>)}</ul> : <p>실행할 작업 없음</p>;
}

function Value({ label, children }) {
  return <div className="light-value"><span>{label}</span><div>{children}</div></div>;
}

function ActionResults({ actions = [] }) {
  return actions.length ? <ul className="light-action-results">{actions.map(action => <li key={action.id}>
    <div><strong>{actionLabel(action.id)}</strong><span className={`playbook-badge playbook-status-${action.status}`}>{STATUSES[action.status] || action.status}</span></div>
    {action.error && <p className="error">{action.error}</p>}
    {action.status === "succeeded" && action.id === "restrict_notice" && <p>{action.result?.blocked === true ? "공지 저장 제한이 적용됐습니다. 실제 저장 403은 별도로 확인합니다." : "제한 상태를 원본에서 확인하세요."}</p>}
    {action.status === "succeeded" && action.result?.message && <p>{action.result.message}</p>}
  </li>)}</ul> : <p>실행된 작업이 없습니다.</p>;
}

function StepValues({ step, run }) {
  const input = step.input || {};
  const output = step.output;
  if (step.status === "pending") return <p>아직 이 단계에 도달하지 않았습니다.</p>;
  if (step.id === "extract") return <>
    <Value label="입력 · 공지 문장"><p className="light-text">{input.text ?? "공지 내용을 확인하지 못했습니다."}</p></Value>
    <Value label="출력 · 추출한 URL"><code>{output?.url ?? "None · URL 없음"}</code></Value>
  </>;
  if (step.id === "lookup") return <>
    <Value label="입력 · URL"><code>{input.url ?? "None · URL 없음"}</code></Value>
    <Value label="출력 · 조회 점수"><strong className="light-score">{output?.score ?? "미확인"}</strong><span>{output?.score == null ? " · None을 안전 점수 0으로 바꾸지 않습니다." : " / 100"}</span><p>{output?.note || "조회 설명 없음"}</p></Value>
    <p className="detection-small-note">{output?.source || "수업용 로컬 CTI API"} · 준비된 연습 데이터이며 실제 외부 위협 평판이 아닙니다.</p>
  </>;
  if (step.id === "decide") return <>
    <Value label="입력 · 점수"><code>{input.score ?? "None · 미확인"}</code></Value>
    <Value label="출력 · 선택한 분기"><strong>{branchLabel(output?.branch)}</strong>{output?.guard && <p>{output.guard}</p>}</Value>
  </>;
  if (step.id === "plan") return <>
    <Value label="입력 · 분기"><strong>{branchLabel(input.branch)}</strong></Value>
    <Value label="출력 · 작업 목록"><ActionList values={output?.actions} /></Value>
    <Value label="출력 · 알림 문장"><p className="light-text">{output?.message || "작성된 문장 없음"}</p></Value>
  </>;
  if (step.id === "execute") return <>
    <Value label="입력 · 실행할 작업"><ActionList values={input.actions} /></Value>
    <Value label="출력 · 실제 처리 결과"><ActionResults actions={Array.isArray(output) ? output : run.actions} /></Value>
  </>;
  return <>
    <Value label="입력 · 처리한 분기"><strong>{branchLabel(output?.effective_branch || run.effective_branch)}</strong></Value>
    <Value label="출력 · 저장된 알림"><p className="light-text">{run.notification?.message || "이 실행에서 만든 알림이 없습니다."}</p></Value>
    <Value label="출력 · 내부 티켓">{run.ticket ? <><p className="light-text">{run.ticket.message}</p><p>티켓 상태: <strong>{run.ticket.status === "resolved" ? "해결됨" : run.ticket.status === "open" ? "열림" : run.ticket.status}</strong></p></> : <p>이 실행에서 만든 티켓이 없습니다.</p>}</Value>
    <p className="detection-small-note">감시 서비스 내부에 실제로 저장한 결과입니다. 외부 메신저 발송이나 외부 티켓 서비스 연동은 아닙니다.</p>
  </>;
}

function Verification({ record, restored = false }) {
  if (!record) return null;
  const valid = record.status_code === (restored ? 200 : 403) && record.expected_outcome === (restored ? "save_succeeded" : "policy_denied");
  return <p className={valid ? "message" : "error"}>{valid ? restored ? "실제 정상 저장 HTTP 200과 파일 변경을 확인했습니다." : "이 제한으로 거절된 실제 공지 저장 HTTP 403을 확인했습니다." : "저장 검증 기록이 기대 결과와 맞지 않습니다. 성공으로 표시하지 않습니다."}</p>;
}

export default function LightPlaybookRun({ run, stepId, onStep, onAction, busy, ai, recoveryOnly = false }) {
  const step = run.steps.find(record => record.id === stepId) || run.steps[0];
  const stageTitle = STAGES.find(([identifier]) => identifier === step?.id)?.[1];
  const canVerify = ["restricted", "restored"].includes(run.state);
  const canRecover = ["restricted", "verified", "error"].includes(run.state);
  const sourceNames = step?.id === "plan" ? ["choose_actions", "make_message"] : [step?.function_name];
  const sources = sourceNames.map(name => run.definition?.functions?.[name]).filter(Boolean);
  return <section className="light-run" id="legacy-url-run" data-run-id={run.id} aria-labelledby="legacy-url-run-title">
    <div className="detection-heading-row"><h3 id="legacy-url-run-title">실행 결과</h3><strong id="legacy-url-run-state" className="playbook-badge">{runLabel(run.state)}</strong></div>
    <p className="detection-small-note" id="legacy-url-run-trigger">{displayTime(run.created_at)} · {run.trigger?.type === "notice_file_change" ? "서버가 새 공지 변경을 감지해 자동으로 시작한 결과입니다. 시작 주체: system" : "이전 수동 시작 방식의 실행 기록입니다."}</p>
    <div className="light-facts"><span>URL <code id="legacy-url-url">{run.url || "없음"}</code></span><span>점수 <strong id="legacy-url-score">{run.score ?? "미확인"}</strong></span><span>분기 <strong id="legacy-url-branch">{run.branch || "미확인"}</strong></span></div>
    {run.approval && run.effective_branch !== run.branch && <p className="detection-small-note">함수의 분기는 그대로이며, 사람 승인 후 <strong>{run.effective_branch}</strong> 경로를 처리했습니다.</p>}
    <ol className="light-stage-nav" aria-label="실행 단계의 입력과 출력 보기">
      {STAGES.map(([identifier, title], index) => <li key={identifier}><button type="button" data-url-stage={identifier} aria-pressed={step?.id === identifier} aria-controls="legacy-url-step" onClick={() => onStep(identifier)}>{index + 1}. {title}</button></li>)}
    </ol>
    {step && <section className="light-step" id="legacy-url-step" aria-labelledby="legacy-url-step-title">
      <div className="detection-heading-row"><h4 id="legacy-url-step-title">{stageTitle}</h4><span className={`playbook-badge playbook-status-${step.status}`}>{STATUSES[step.status] || step.status}</span></div>
      <p className="light-function"><code>{step.function_name}()</code>{sources.length ? " · 학생 함수" : " · 준비된 연결"}</p>
      {step.error && <p className="error" role="alert">{step.error}</p>}
      <StepValues step={step} run={run} />
      {sources.length > 0 && <details className="detection-raw"><summary>이 실행에 사용한 학생 함수</summary>{sources.map((source, index) => <pre key={sourceNames[index]}>{source}</pre>)}</details>}
      <details className="detection-raw"><summary>이 단계 원본 보기</summary><pre>{JSON.stringify(step, null, 2)}</pre></details>
    </section>}
    {run.last_error && <p className="error" role="alert">최근 처리 오류: {run.last_error}</p>}
    {!recoveryOnly && run.state === "review_pending" && <details className="light-history light-followup"><summary>선택 · 검토 후 대응 승인</summary>
      <p>자동 제한하지 않았습니다. 아래 목록을 승인하면 이 실행에 고정된 대응 작업을 처리합니다.</p>
      <ActionList values={run.respond_plan} />
      {run.respond_plan?.includes("restrict_notice") && <p>제한 대상: <code>general-01 · /classroom-data/notice.txt</code>의 저장만. 로그인과 읽기는 유지합니다.</p>}
      <button id="legacy-url-approve" onClick={() => onAction("approve", run.id)} disabled={busy || !run.approve_allowed}>검토 후 대응 승인</button>
      {!run.approve_allowed && <p className="detection-small-note">조회 점수와 유효한 조회 결과가 없어 승인할 수 없습니다. 공지 내용과 조회 결과를 확인하세요.</p>}
    </details>}
    {(canVerify || canRecover || run.verification || run.recovery || run.recovery_verification || run.state === "recovery_error") && <div className="light-followup">
      <h4>실제 저장 확인과 복구</h4>
      {canVerify && <p>{run.state === "restricted" ? "일반 사이트에서 다른 내용으로 공지 저장을 시도한 뒤 실제 정책 거절 403을 확인하세요." : "일반 사이트에서 다른 내용으로 공지를 저장한 뒤 실제 정상 저장 200을 확인하세요."}</p>}
      <div className="actions">
        {canVerify && <button id="legacy-url-verify" onClick={() => onAction("verify", run.id)} disabled={busy}>실제 저장 결과 확인</button>}
        {canRecover && <button id="legacy-url-recover" onClick={() => onAction("recover", run.id)} disabled={busy}>저장 허용 복구 승인</button>}
      </div>
      {canRecover && <p className="detection-small-note">이 실행의 공지 저장 제한만 해제합니다. 이전 공지 내용으로 되돌리는 작업은 아닙니다.</p>}
      <Verification record={run.verification} /><Verification record={run.recovery_verification} restored />
      {run.recovery && !run.verification && <p className="detection-small-note">제한 당시의 실제 정책 거절 403은 확인하지 않았습니다.</p>}
    </div>}
    {(recoveryOnly ? run.state === "recovery_error" : ["error", "recovery_error"].includes(run.state)) && <button id="legacy-url-retry" onClick={() => onAction("retry", run.id)} disabled={busy}>실패한 작업 다시 확인</button>}
    {!recoveryOnly && <details className="light-history" id="legacy-url-ai"><summary>선택 · AI로 결과 요약하기</summary>
      <p>플레이북의 조회·분기·실행과 별개입니다. 실제 AI 응답만 저장하며 조치를 바꾸지 않습니다.</p>
      <button id="legacy-url-ai-summary" onClick={() => onAction("ai-summary", run.id)} disabled={busy || run.ai_running}>실제 AI 요약(선택)</button>
      {!ai?.available && <p className="detection-small-note">AI 연결 미설정입니다. 요청 시 미연결 오류가 나며 예시 응답으로 대신하지 않습니다.</p>}
      {run.ai_error && <p className="error">AI 요약 실패: {run.ai_error.message || "응답을 확인하지 못했습니다."}</p>}
      {run.ai_summary && <><p>저장된 실제 AI 응답 · {displayTime(run.ai_summary.at)}</p><p>{run.ai_summary.result?.summary || run.ai_summary.summary || "아래 원문에서 응답을 확인하세요."}</p><details className="detection-raw"><summary>AI 입력과 응답 원문</summary><pre>{JSON.stringify(run.ai_summary, null, 2)}</pre></details></>}
    </details>}
    <details className="detection-raw light-history"><summary>실행 원본과 작업 이력 보기</summary><pre>{JSON.stringify(run, null, 2)}</pre></details>
  </section>;
}

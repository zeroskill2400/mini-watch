import { displayTime } from "./SoarRequest";

const STATUS_LABELS = { pending: "분석 대기", running: "분석 중", succeeded: "응답 확인", unconfigured: "AI 미연결", failed: "분석 실패", insufficient: "근거 부족" };
const RISK_LABELS = { low: "낮음", medium: "중간", high: "높음", unknown: "판단 보류" };

function duration(value) {
  return typeof value === "number" ? value.toLocaleString("ko-KR", { maximumFractionDigits: 1 }) : "—";
}

export function decisionStatus(value) {
  return STATUS_LABELS[value] || value || "결과 없음";
}

export function branchName(value) {
  return value === "respond" ? "respond · 대응 경로" : value === "review" ? "review · 검토 대기" : "판단 전";
}

export function HistorySummary({ snapshot }) {
  if (!snapshot) return <p className="log-empty">요청 이력을 수집하는 중입니다.</p>;
  const window = snapshot.window || {};
  const limitations = (snapshot.quality?.limitations || []).filter(item => item !== snapshot.scope_note && item !== snapshot.identity_note);
  return <div className="history-summary">
    <dl className="history-counts">
      <div><dt>실제 요청</dt><dd id="history-request-count">{snapshot.request_count ?? "—"}<small>건</small></dd></div>
      <div><dt>논리 로그인 실패</dt><dd id="history-failure-count">{snapshot.login_failure_count ?? "—"}<small>회</small></dd></div>
      <div><dt>로그인 성공</dt><dd id="history-success-count">{snapshot.login_success_count ?? "—"}<small>회</small></dd></div>
      <div><dt>분당 요청</dt><dd>{snapshot.requests_per_minute ?? "—"}<small>건</small></dd></div>
    </dl>
    <p id="history-window">집계 시간: {displayTime(window.started_at)} ~ {displayTime(window.ended_at)}<br />요청한 창 {duration(window.requested_seconds)}초 · 실제 범위 {duration(window.effective_seconds)}초{window.clipped_to_logging_start ? " · 기록 시작 시점까지만 집계" : ""}</p>
    <p className="detection-small-note">{snapshot.scope_note}</p>
    <p className="detection-small-note">{snapshot.identity_note}</p>
    {snapshot.quality?.complete === false && <p className="error" role="alert">근거가 완전하지 않습니다. 일부 기록을 읽지 못한 상태를 안전하다고 판단하지 않습니다.</p>}
    {limitations.length > 0 && <ul className="detection-small-note">{limitations.map((item, index) => <li key={index}>{item}</li>)}</ul>}
  </div>;
}

export function HistoryTimeline({ snapshot }) {
  if (!snapshot) return null;
  const timeline = snapshot.timeline || [];
  const sample = snapshot.sample || {};
  return <details className="light-history" id="history-timeline">
    <summary>고정된 요청 이력 보기 · {sample.shown_count ?? timeline.length}건</summary>
    <p className="detection-small-note">출처 {snapshot.source || "app.jsonl"} · 전체 집계 {sample.total_count ?? snapshot.request_count}건 중 표시 {sample.shown_count ?? timeline.length}건. {sample.truncated ? `상세 표본은 최대 ${sample.limit}건이며 전체 횟수와 다릅니다.` : "실행 시 고정한 기록입니다."}</p>
    <div className="log-table-scroll" tabIndex={0} role="region" aria-label="고정된 요청 이력 표">
      <table className="log-table history-table"><thead><tr><th scope="col">시각</th><th scope="col">요청</th><th scope="col">상태</th><th scope="col">계정 기록</th><th scope="col">근거 ID</th></tr></thead><tbody>
        {timeline.map((event, index) => <tr key={`${event.event_id}-${index}`}><td>{displayTime(event.occurred_at)}</td><td><code>{event.method} {event.path}</code><br /><small>{event.event_type}</small></td><td>{event.status_code}</td><td>{event.authenticated_username ? `인증된 계정: ${event.authenticated_username}` : event.attempted_username ? `입력한 계정: ${event.attempted_username}` : "계정 근거 없음"}</td><td><code>{event.event_id || event.request_id || "없음"}</code></td></tr>)}
      </tbody></table>
    </div>
  </details>;
}

export function DecisionResult({ result, title }) {
  if (!result) return <div className="history-decision"><h4>{title}</h4><p>아직 판단 결과가 없습니다.</p></div>;
  return <div className="history-decision">
    <div className="detection-heading-row"><h4>{title}</h4><span className="playbook-badge">{decisionStatus(result.status)}</span></div>
    <p><strong>{branchName(result.decision)}</strong>{result.risk_level && <> · 검토 위험도 {RISK_LABELS[result.risk_level] || result.risk_level}</>}</p>
    <p>{result.reason || "판단 근거가 아직 없습니다."}</p>
    {result.mode === "fallback" && <p className="error">유효한 판단 성공 결과가 아닙니다. 자동 대응 대신 검토로 남겼습니다.</p>}
    {result.inferences?.length > 0 && <><h5>AI가 추론한 내용</h5><ul>{result.inferences.map((item, index) => <li key={index}>{item}</li>)}</ul></>}
    {result.evidence_ids?.length > 0 && <details className="detection-raw"><summary>판단에 인용한 근거 ID</summary><ul>{result.evidence_ids.map(identifier => <li key={identifier}><code>{identifier}</code></li>)}</ul></details>}
    {result.limitations?.length > 0 && <><h5>한계와 확인할 점</h5><ul>{result.limitations.map((item, index) => <li key={index}>{item}</li>)}</ul></>}
    {result.mode === "ai" && <p className="detection-small-note">AI 위험도 높음은 악성 행위 확정이 아닙니다. 기록과 추론을 구분해서 확인하세요.</p>}
  </div>;
}

export function HistoryComparison({ run, ai, busy, onAction }) {
  const comparisons = run.comparisons || [];
  const latest = comparisons[comparisons.length - 1];
  const running = comparisons.some(record => record.status === "running");
  const unfinished = ["running", "recovering"].includes(run.state);
  return <section className="history-comparison" id="history-ai-comparison" aria-labelledby="history-ai-title">
    <h3 id="history-ai-title">같은 이력 · 규칙과 AI 비교</h3>
    <p>이 실행에 고정한 실제 요청 이력으로 AI 판단만 비교합니다. 새 실행을 만들거나 분기·대응 작업을 바꾸지 않습니다.</p>
    <button id="history-compare-ai" onClick={() => onAction("compare-ai", run.id)} disabled={busy || running || unfinished || !run.history_snapshot}>같은 이력으로 AI 판단 비교</button>
    {unfinished && <p className="detection-small-note">현재 이력 판단이나 복구가 끝난 뒤 같은 이력 비교를 요청할 수 있습니다.</p>}
    {!ai?.available && <p className="detection-small-note">AI 연결 미설정입니다. 비교 요청 시 미연결 상태를 남기며 예시 응답으로 대신하지 않습니다.</p>}
    {latest && <>
      <p id="history-comparison-status" role="status">{decisionStatus(latest.status)} · {displayTime(latest.started_at)}{latest.status === "running" ? " · 화면은 결과를 조회하는 중입니다." : ""}</p>
      {latest.error && <p className="error" role="alert">{typeof latest.error === "string" ? latest.error : latest.error.message}</p>}
      <div className="history-compare-grid"><DecisionResult title="같은 입력의 규칙 판단" result={latest.rule_result || run.rule_result} /><DecisionResult title="같은 입력의 AI 판단" result={latest.ai_result} /></div>
      <details className="detection-raw"><summary>비교에 사용한 지시 문장</summary><p className="light-text">{latest.prompt}</p><p className="detection-small-note">미연결·실패 상태는 실제 AI 응답 성공을 뜻하지 않습니다.</p></details>
      <details className="detection-raw"><summary>비교 원본과 이전 비교 이력</summary><pre>{JSON.stringify(comparisons, null, 2)}</pre></details>
    </>}
  </section>;
}

"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { requestJson } from "../api/client";

function displayTime(value) {
  if (!value) return "—";
  const timestamp = new Date(value);
  if (Number.isNaN(timestamp.getTime())) return value;
  return timestamp.toLocaleString("ko-KR", { hour12: false });
}

function EvidenceList({ events }) {
  return <ol className="detection-evidence-list">
    {events.map(event => <li key={event.event_id} data-event-id={event.event_id}>
      <div className="detection-evidence-heading">
        <time dateTime={event.occurred_at}>{displayTime(event.occurred_at)}</time>
        <span className="http-status http-error">{event.status_code} · 로그인 실패</span>
      </div>
      <dl className="detection-evidence-fields">
        <div><dt>입력한 계정</dt><dd>{event.attempted_username}</dd></div>
        <div><dt>요청</dt><dd><code>{event.method} {event.path}</code></dd></div>
        <div><dt>근거 ID</dt><dd><code>{event.event_id}</code></dd></div>
      </dl>
      <details className="detection-raw">
        <summary>앱 원본 보기</summary>
        <pre>{typeof event.raw === "string" ? event.raw : JSON.stringify(event.raw, null, 2)}</pre>
      </details>
    </li>)}
  </ol>;
}

export default function DetectionClient() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const requestVersion = useRef(0);

  const fetchDetection = useCallback(async (version, start = false) => {
    try {
      const result = await requestJson(start ? "/api/detection/start" : "/api/detection", start ? "POST" : "GET");
      if (version !== requestVersion.current) return;
      setReport(result);
      setError("");
      setNotice(start ? "새 관찰을 시작했습니다. 기존 원본 로그는 삭제하지 않습니다." : "");
    } catch (requestError) {
      if (version !== requestVersion.current) return;
      setError(requestError.message);
    } finally {
      if (version === requestVersion.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const version = ++requestVersion.current;
    fetchDetection(version);
    return () => { requestVersion.current += 1; };
  }, [fetchDetection]);

  function loadDetection(start = false) {
    setLoading(true);
    setError("");
    setNotice("");
    fetchDetection(++requestVersion.current, start);
  }

  const observation = report?.observation;
  const alerts = report?.alerts || [];
  const counts = report?.counts || [];
  const threshold = report?.rule.threshold ?? 3;
  const windowSeconds = report?.rule.window_seconds ?? 60;

  return <section className="detection-panel" aria-labelledby="detection-heading" aria-busy={loading}>
    <div className="detection-heading-row">
      <div>
        <p className="detection-eyebrow">Day4 · 로그에서 경고로</p>
        <h2 id="detection-heading">반복 로그인 실패 탐지</h2>
      </div>
      <span className="detection-caution">수업용 기준 · 공격 확정 아님</span>
    </div>
    <p className="detection-intro">일반 사이트에서 비밀번호를 틀리게 입력하고, 실패가 반복될 때 어떤 기록이 경고의 근거가 되는지 확인합니다.</p>
    <p className="detection-rule" id="detection-rule">같은 입력 계정 · {windowSeconds}초 안에 · 로그인 실패 {threshold}회 이상</p>
    <ol className="detection-steps">
      <li><strong>새 관찰 시작</strong><span>이번 실습에서 발생시킬 요청만 따로 봅니다.</span></li>
      <li><strong>일반 사이트에서 로그인 실패</strong><span>같은 아이디로 비밀번호를 틀리게 입력합니다.</span></li>
      <li><strong>탐지 새로고침</strong><span>실패 횟수와 경고를 직접 불러옵니다.</span></li>
    </ol>
    <div className="detection-actions">
      <button id="detection-start" onClick={() => loadDetection(true)} disabled={loading}>새 관찰 시작</button>
      <button id="detection-refresh" className="refresh-logs" onClick={() => loadDetection()} disabled={loading}>탐지 새로고침</button>
      <a href="http://localhost:8083/login" target="_blank" rel="noopener noreferrer">일반 사이트 열기</a>
    </div>
    <p className="detection-manual-note">자동 갱신하지 않습니다. 일반 사이트를 조작한 뒤 <strong>탐지 새로고침</strong>을 누르세요.</p>
    <p id="detection-status" className="detection-status" role="status">{loading
      ? "탐지 결과를 불러오는 중입니다."
      : error
        ? "조회에 실패했습니다. 다시 새로고침하세요."
        : notice || (observation ? `관찰 시작: ${displayTime(observation.started_at)}` : "먼저 새 관찰 시작을 누르세요.")}</p>
    {error && <p role="alert" className="error">{error}{report ? " 아래는 마지막으로 정상 조회한 결과입니다." : ""}</p>}
    {observation && <>
      <div className="detection-results">
        <section className="detection-counts" aria-labelledby="detection-counts-heading">
          <h3 id="detection-counts-heading">최근 {windowSeconds}초 실패 횟수</h3>
          {counts.length === 0 ? <p id="detection-no-failures">집계된 로그인 실패가 없습니다.</p> : <ul>
            {counts.map(account => <li key={account.attempted_username} data-attempted-username={account.attempted_username}>
              <div><span className="detection-field-label">입력한 계정</span><strong>{account.attempted_username}</strong></div>
              <span className="detection-failure-count">{account.failure_count}회</span>
            </li>)}
          </ul>}
          <p className="detection-small-note">관찰 시작 이후의 앱 인증 실패만 셉니다. Nginx 기록은 더하지 않습니다.</p>
        </section>
        <section className={alerts.length ? "detection-summary has-alert" : "detection-summary"} aria-labelledby="detection-alert-count">
          <h3 id="detection-alert-count">{alerts.length ? `경고 ${alerts.length}건` : "경고 없음"}</h3>
          <p>{alerts.length
            ? "수업용 조건을 만족한 기록이 있습니다. 아래에서 실제 근거를 확인하세요."
            : `아직 같은 입력 계정의 실패가 ${windowSeconds}초 안에 ${threshold}회 모이지 않았습니다.`}</p>
          <p className="detection-small-note">경고는 이번 관찰 안에서 계정별로 한 번 남기며, 시간이 지나도 유지합니다. 다시 비교하려면 새 관찰을 시작하세요.</p>
        </section>
      </div>
      {alerts.length > 0 && <section className="detection-alert-list" aria-label="반복 로그인 실패 경고 목록">
        {alerts.map(alert => <article className="detection-alert" key={alert.id} data-alert-id={alert.id}>
          <div className="detection-alert-heading">
            <h3>{alert.attempted_username} 반복 로그인 실패</h3>
            <span>{alert.window_seconds}초 안에 {alert.failure_count}회</span>
          </div>
          <p>경고 발생: <time dateTime={alert.created_at}>{displayTime(alert.created_at)}</time></p>
          <details className="detection-evidence">
            <summary>근거 보기 · 앱 인증 기록 {alert.evidence.length}건</summary>
            <EvidenceList events={alert.evidence} />
          </details>
        </article>)}
      </section>}
      <p className="detection-small-note">마지막 조회: <time dateTime={report.evaluated_at}>{displayTime(report.evaluated_at)}</time>. 실패 횟수는 이 시각 기준입니다.</p>
    </>}
    {report?.invalid_line_count > 0 && <p className="error" role="alert">읽지 못한 앱 원본 {report.invalid_line_count}행이 있어 결과가 불완전할 수 있습니다.</p>}
    <p className="detection-footnote">입력한 계정은 로그인하려고 적은 이름이지, 실제 행동한 사람의 신원이 아닙니다. 경고가 떠도 비밀번호 입력 실수인지 추가 확인해야 합니다.</p>
  </section>;
}

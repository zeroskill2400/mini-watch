"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { requestJson } from "../api/client";
import SoarClient from "./SoarClient";
import LightPlaybookRun, { runLabel } from "./LightPlaybookRun";
import HistoryPlaybookRun from "./HistoryPlaybookRun";
import { displayTime } from "./SoarRequest";

function readStored(key) {
  try { return localStorage.getItem(key) || ""; } catch { return ""; }
}

function storeValue(key, value) {
  try { value ? localStorage.setItem(key, value) : localStorage.removeItem(key); } catch {}
}

function automaticRun(record) {
  return record.flow === "history-v1" && record.trigger?.type === "notice_file_change";
}

function errorMessage(value) {
  return typeof value === "string" ? value : value?.message || "";
}

export default function LightPlaybookClient({ username, observationId }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState("");
  const [comparingId, setComparingId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [stale, setStale] = useState(true);
  const [selectedId, setSelectedId] = useState("");
  const [stepId, setStepId] = useState("history");
  const [legacyOpen, setLegacyOpen] = useState(false);
  const [urlHistoryOpen, setUrlHistoryOpen] = useState(false);
  const [urlSelectedId, setUrlSelectedId] = useState("");
  const [urlStepId, setUrlStepId] = useState("extract");
  const selectedRef = useRef("");
  const fetchingRef = useRef(false);
  const mutatingRef = useRef(false);
  const comparingRef = useRef("");
  const versionRef = useRef(0);
  const storageKey = `day5-history-playbook-v1:${username}`;
  const urlStorageKey = `day5-url-playbook-v1:${username}`;

  const chooseRun = useCallback((identifier, stage) => {
    selectedRef.current = identifier;
    setSelectedId(identifier);
    storeValue(`${storageKey}:run`, identifier);
    if (stage) {
      setStepId(stage);
      storeValue(`${storageKey}:step`, stage);
    }
  }, [storageKey]);

  const refresh = useCallback(async () => {
    if (fetchingRef.current) return;
    fetchingRef.current = true;
    const version = ++versionRef.current;
    try {
      const result = await requestJson("/api/soar/playbook");
      if (version !== versionRef.current) return;
      setReport(result);
      setStale(false);
      setError(current => current.startsWith("조회 실패:") ? "" : current);
      const historyRuns = result.runs.filter(record => record.flow === "history-v1");
      if (!historyRuns.some(record => record.id === selectedRef.current)) {
        chooseRun(historyRuns[0]?.id || "", "history");
      } else setSelectedId(selectedRef.current);
    } catch (requestError) {
      if (version !== versionRef.current) return;
      setError(`조회 실패: ${requestError.message}`);
      setStale(true);
    } finally {
      fetchingRef.current = false;
      if (version === versionRef.current) setLoading(false);
    }
  }, [chooseRun]);

  useEffect(() => {
    selectedRef.current = readStored(`${storageKey}:run`);
    const kickoff = setTimeout(() => {
      setStepId(readStored(`${storageKey}:step`) || "history");
      setUrlSelectedId(readStored(`${urlStorageKey}:run`));
      setUrlStepId(readStored(`${urlStorageKey}:step`) || "extract");
      refresh();
    }, 0);
    const interval = setInterval(() => { if (!mutatingRef.current) refresh(); }, 3000);
    return () => {
      clearTimeout(kickoff);
      clearInterval(interval);
      versionRef.current += 1;
    };
  }, [refresh, storageKey, urlStorageKey, observationId]);

  function chooseStep(identifier) {
    setStepId(identifier);
    storeValue(`${storageKey}:step`, identifier);
  }

  async function performAction(action, identifier) {
    if (action === "compare-ai") {
      if (stale || comparingRef.current || report?.runs.find(item => item.id === identifier)?.flow !== "history-v1") return;
      comparingRef.current = identifier;
      setComparingId(identifier);
      setError("");
      setMessage("");
      try {
        await requestJson(`/api/soar/playbook/runs/${encodeURIComponent(identifier)}/compare-ai`, "POST", {});
        setMessage("같은 이력의 AI 비교 상태를 확인했습니다. 아래 상태와 근거를 읽어 보세요. 새 실행이나 대응 작업은 만들지 않습니다.");
      } catch (requestError) {
        setError(`AI 비교 요청 실패: ${requestError.status ? `HTTP ${requestError.status} · ` : ""}${requestError.message} 기존 실행의 분기와 대응은 바꾸지 않습니다.`);
      } finally {
        comparingRef.current = "";
        setComparingId("");
        await refresh();
      }
      return;
    }
    if (mutatingRef.current || stale) return;
    const record = report?.runs.find(item => item.id === identifier);
    if (record?.flow !== "history-v1" && (!["recover", "verify", "retry"].includes(action) || (action === "retry" && record?.state !== "recovery_error"))) return;
    mutatingRef.current = true;
    versionRef.current += 1;
    setPending(action);
    setError("");
    setMessage("");
    try {
      const result = await requestJson(`/api/soar/playbook/runs/${encodeURIComponent(identifier)}/${action}`, "POST", {});
      if (selectedRef.current === identifier) chooseRun(result.run.id, "record");
      setReport(current => ({ ...current, runs: current.runs.map(record => record.id === result.run.id ? result.run : record) }));
      setMessage("처리 결과를 다시 읽었습니다. 아래 결과와 현재 정책을 확인하세요.");
      await refresh();
    } catch (requestError) {
      setError(`${requestError.status ? `HTTP ${requestError.status} · ` : ""}${requestError.message} 이 오류는 실제 공지 저장의 정책 거절 403이 아닙니다.`);
      await refresh();
    } finally {
      mutatingRef.current = false;
      setPending("");
    }
  }

  const selected = report?.runs.find(record => record.id === selectedId);
  const historyRuns = (report?.runs || []).filter(record => record.flow === "history-v1");
  const urlRuns = (report?.runs || []).filter(record => record.flow !== "history-v1");
  const urlSelected = urlRuns.find(record => record.id === urlSelectedId) || urlRuns[0];
  const automaticRuns = (report?.runs || []).filter(automaticRun);
  const latest = automaticRuns[0];
  const newerCount = selected ? automaticRuns.filter(record => Date.parse(record.created_at) > Date.parse(selected.created_at)).length : automaticRuns.length;
  const automation = report?.automation;
  const automationStatus = !automation ? "자동 감지 상태 확인 불가" : !automation.enabled ? "자동 감지 꺼짐" : {
    watching: "새 공지 감지 대기",
    processing: "자동 처리 중",
    error: "자동 감지 오류",
    not_started: "자동 감지 시작 전",
  }[automation.status] || "자동 감지 상태 확인 불가";
  const latestFailure = automation?.latest_events?.find(record => record.status === "failed");
  const automationError = errorMessage(automation?.last_error) || errorMessage(latestFailure?.error);
  const busy = loading || Boolean(pending);

  return <section id="url-playbook" className="soar-panel light-playbook" aria-labelledby="url-playbook-title" aria-busy={busy}>
    <div className="detection-heading-row">
      <div><p className="detection-eyebrow">Day5 · 실제 이력으로 판단하는 SOAR</p><h2 id="url-playbook-title">요청 이력 플레이북</h2></div>
      <span className="detection-caution">AI 위험도 높음 ≠ 악성 확정</span>
    </div>
    <p>새 공지 변경을 감지하면 실제 요청 이력을 모아 판단하고, 정해 둔 작업과 결과 알림을 자동으로 처리합니다.</p>
    <div className="detection-actions">
      <button id="playbook-refresh" onClick={refresh} disabled={busy}>사건 새로고침</button>
      <button id="playbook-latest" className="refresh-logs" onClick={() => latest && chooseRun(latest.id, "history")} disabled={!latest}>최신 결과 보기</button>
      <a href="http://localhost:8085/notice" target="_blank" rel="noopener noreferrer">일반 사이트 공지 열기</a>
    </div>
    <p role="status" id="playbook-status" className="soar-status">{loading ? "사건을 불러오는 중입니다." : pending ? "선택한 작업을 처리 중입니다…" : comparingId ? "AI 비교 응답을 기다리는 중입니다. 조회와 다른 실행의 복구는 계속할 수 있습니다." : message}</p>
    {newerCount > 0 && <p id="playbook-new-results" role="status" className="light-notice">새 자동 실행 {newerCount}건 · 최신 결과 보기를 누르면 새 결과로 이동합니다. 현재 선택은 유지합니다.</p>}
    {error && <p className="error" role="alert" id="playbook-error">{error}</p>}
    {stale && report && <p className="error">마지막 조회 결과입니다. 다시 조회될 때까지 실행·변경 버튼을 잠급니다.</p>}
    {report?.definition.valid === false && <p className="error" role="alert" id="playbook-definition-error">{report.definition.error || "학생 코드의 함수를 확인하세요."} 새 자동 실행을 완료할 수 없습니다. 코드를 고친 뒤 공지를 새 내용으로 저장하세요. 기존 결과와 복구는 유지합니다.</p>}
    {report && <>
      <section className="light-input" aria-labelledby="playbook-input-title">
        <div className="detection-heading-row"><h3 id="playbook-input-title">자동 감지 상태</h3><strong id="playbook-automation-state" role="status">{automationStatus}</strong></div>
        <p>일반 사이트에서 공지를 새 내용으로 저장하세요. 앱 저장과 센서 기록이 연결되면 서버가 한 번 시작합니다. 감시 화면을 닫아도 처리는 계속됩니다.</p>
        {automation && <p className="detection-small-note" id="playbook-automation-detail">시작 주체: 서버 {automation.actor} · 마지막 확인: {displayTime(automation.last_poll_at)}</p>}
        {automationError && <p className="error" role="alert" id="playbook-automation-error">최근 자동 처리 오류: {automationError}{latestFailure?.run_id === null ? " 실행 결과를 만들지 못했습니다." : ""} 원인을 고친 뒤 공지를 새 내용으로 저장하세요.</p>}
        {!latest && <p className="log-empty" id="playbook-waiting">아직 자동 실행 결과가 없습니다. 일반 로그인 → 새 공지 저장 → 센서 도착을 기다리세요. 로그인 실패 3회나 별도 시작 버튼은 필요하지 않습니다.</p>}
        <p className="detection-small-note">최신 결과 보기는 저장된 결과를 선택할 뿐 새 실행을 만들지 않습니다.</p>
      </section>
      {selected && <HistoryPlaybookRun run={selected} stepId={stepId} onStep={chooseStep} onAction={performAction} busy={busy || stale} comparing={Boolean(comparingId)} ai={report.ai} />}
      {historyRuns.length > 0 && <details className="light-history" id="playbook-history"><summary>이전 이력 판단 실행 · {historyRuns.length}건</summary>
        <label htmlFor="playbook-run-select">결과를 비교할 실행
          <select id="playbook-run-select" value={selected?.id || ""} onChange={event => chooseRun(event.target.value, "history")} disabled={busy}>
            {historyRuns.map(record => <option key={record.id} value={record.id}>{displayTime(record.created_at)} · 실패 {record.history_snapshot?.login_failure_count ?? "—"}회 · {record.decision?.mode || "판단 중"} · {runLabel(record.state)}</option>)}
          </select>
        </label><p className="detection-small-note">코드를 바꿔도 이미 저장한 입력과 출력은 바뀌지 않습니다.</p>
      </details>}
      <p className="light-policy" id="playbook-policy">현재 공지 정책: <strong>{!report.policy?.available ? "확인 불가" : report.policy.blocked ? "저장 제한 중" : "저장 허용"}</strong> · 모든 실행에 공통인 현재 상태</p>
      <details className="detection-raw light-source"><summary>현재 학생 코드 보기</summary>
        <p><code>monitor/backend/soar_rules.py</code>의 짧은 판단 함수·지시 문장·작업 목록을 수정하고 Ctrl+S로 저장하세요. 일반 사이트에서 공지 제목에 숫자를 붙이거나 바꿔 다시 저장하면 다음 사건에 적용합니다. 코드 저장만으로 실행하지 않습니다.</p>
        {Object.entries(report.definition.functions || {}).map(([name, code]) => <pre key={name}>{code}</pre>)}
      </details>
      <p className="detection-small-note">화면은 3초마다 결과를 조회합니다. 조회와 새로고침은 실행을 시작하지 않습니다. 새 결과가 와도 선택한 실행과 단계는 유지합니다.</p>
      {urlRuns.length > 0 && <details className="light-history" id="legacy-url-history" onToggle={event => setUrlHistoryOpen(event.currentTarget.open)}><summary>이전 URL 플레이북 기록 · {urlRuns.length}건</summary>
        <p>이전 수업용 점수 방식의 기록입니다. 새 요청 이력 판단과 섞지 않고, 기존 원본 확인과 필요한 복구만 유지합니다.</p>
        <label htmlFor="legacy-url-select">확인할 이전 URL 실행<select id="legacy-url-select" value={urlSelected?.id || ""} onChange={event => { setUrlSelectedId(event.target.value); storeValue(`${urlStorageKey}:run`, event.target.value); }} disabled={busy}>{urlRuns.map(record => <option key={record.id} value={record.id}>{displayTime(record.created_at)} · {record.url || "URL 없음"} · {runLabel(record.state)}</option>)}</select></label>
        {urlHistoryOpen && urlSelected && <LightPlaybookRun run={urlSelected} stepId={urlStepId} onStep={identifier => { setUrlStepId(identifier); storeValue(`${urlStorageKey}:step`, identifier); }} onAction={performAction} busy={busy || stale} ai={report.ai} recoveryOnly />}
      </details>}
    </>}
    <details className="light-history" id="legacy-soar" onToggle={event => setLegacyOpen(event.currentTarget.open)}><summary>이전 방식의 요청 · 승인/제한/복구 이력</summary>
      {legacyOpen && <SoarClient username={username} observationId={observationId} historyOnly />}
    </details>
  </section>;
}

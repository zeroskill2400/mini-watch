"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { requestJson } from "../api/client";
import SoarRequest, { displayTime, stateLabel } from "./SoarRequest";
import { PlaybookDefinition } from "./Playbook";

const ACTION_MESSAGES = {
  notify: "실제 AI 응답을 담당자 알림에 저장했습니다. 원본 근거와 대조하세요.",
  approve: "사람의 승인을 기록했습니다. 실제 실행 상태는 따로 확인하세요.",
  reject: "요청을 거절했습니다. 이 요청으로 제한을 실행하지 않습니다.",
  cancel: "실행 전 승인을 취소했습니다. 취소 이력은 보존합니다.",
  verify: "일반 사이트의 실제 저장 원본을 확인해 요청에 연결했습니다.",
  recover: "공지 저장 허용 복구를 승인했습니다. 실제 복구와 정상 저장 200을 이어서 확인하세요.",
  retry: "실패한 조치의 처리 상태를 다시 확인하도록 요청했습니다.",
};

function storeSelection(key, value) {
  try { localStorage.setItem(key, value); } catch {}
}

function readSelection(key) {
  try { return localStorage.getItem(key) || ""; } catch { return ""; }
}

export default function SoarClient({ username, observationId, historyOnly = false }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [stale, setStale] = useState(true);
  const [selectedId, setSelectedId] = useState("");
  const [candidateId, setCandidateId] = useState("");
  const [lastReadAt, setLastReadAt] = useState("");
  const selectedRef = useRef("");
  const candidateRef = useRef("");
  const versionRef = useRef(0);
  const fetchingRef = useRef(false);
  const mutatingRef = useRef(false);
  const storageKey = `day5-soar-selection-v1:${username}`;

  const selectRequest = useCallback(identifier => {
    selectedRef.current = identifier;
    setSelectedId(identifier);
    storeSelection(storageKey, identifier);
  }, [storageKey]);

  const refresh = useCallback(async () => {
    if (fetchingRef.current) return;
    fetchingRef.current = true;
    const version = ++versionRef.current;
    try {
      const result = await requestJson("/api/soar");
      if (version !== versionRef.current) return;
      setReport(result);
      setStale(false);
      setError(current => current.startsWith("상태 조회 실패:") ? "" : current);
      setLastReadAt(new Date().toISOString());
      setCandidateId(candidateRef.current);
      const retained = result.requests.some(record => record.id === selectedRef.current);
      if (retained) setSelectedId(selectedRef.current);
      else selectRequest(result.requests[0]?.id || "");
    } catch (requestError) {
      if (version !== versionRef.current) return;
      setError(`상태 조회 실패: ${requestError.message}`);
      setStale(true);
    } finally {
      fetchingRef.current = false;
      if (version === versionRef.current) setLoading(false);
    }
  }, [selectRequest]);

  useEffect(() => {
    const retained = readSelection(storageKey);
    selectedRef.current = retained;
    candidateRef.current = readSelection(`${storageKey}:candidate`);
    const kickoff = setTimeout(refresh, 0);
    const interval = setInterval(() => {
      if (!mutatingRef.current) refresh();
    }, 3000);
    return () => {
      clearTimeout(kickoff);
      clearInterval(interval);
      versionRef.current += 1;
    };
  }, [refresh, storageKey, observationId]);

  function chooseCandidate(identifier) {
    candidateRef.current = identifier;
    setCandidateId(identifier);
    storeSelection(`${storageKey}:candidate`, identifier);
  }

  async function performAction(action, requestId) {
    if (mutatingRef.current || stale) return;
    if (historyOnly && !["recover", "verify", "retry"].includes(action)) return;
    if (historyOnly && action === "retry" && report?.requests.find(record => record.id === requestId)?.state !== "recovery_error") return;
    mutatingRef.current = true;
    versionRef.current += 1;
    setPending(action);
    setMessage("");
    setError("");
    try {
      const result = await requestJson(`/api/soar/requests/${encodeURIComponent(requestId)}/${action}`, "POST", {});
      selectRequest(result.request.id);
      setReport(current => ({ ...current, requests: current.requests.map(record => record.id === result.request.id ? result.request : record) }));
      setMessage(ACTION_MESSAGES[action]);
      await refresh();
    } catch (requestError) {
      setError(`${requestError.status ? `HTTP ${requestError.status} · ` : ""}${requestError.message} 이 오류를 공지 저장의 정책 거절 403이나 조치 성공으로 보지 않습니다.`);
      await refresh();
    } finally {
      mutatingRef.current = false;
      setPending("");
    }
  }

  async function createRequest() {
    if (historyOnly || !candidate?.eligible || report?.playbook?.valid !== true || mutatingRef.current || stale) return;
    mutatingRef.current = true;
    versionRef.current += 1;
    setPending("create");
    setMessage("");
    setError("");
    try {
      const result = await requestJson("/api/soar/requests", "POST", { case_id: candidate.case_id });
      selectRequest(result.request.id);
      setMessage("플레이북 실행 한 건을 대응 요청에 만들었습니다. 정의와 사건 근거를 고정했으며 아직 저장을 제한하지 않습니다.");
      await refresh();
    } catch (requestError) {
      setError(`${requestError.status ? `HTTP ${requestError.status} · ` : ""}${requestError.message}`);
    } finally {
      mutatingRef.current = false;
      setPending("");
    }
  }

  function manualRefresh() {
    setError("");
    refresh();
  }

  const candidates = report?.candidates || [];
  const candidate = candidates.find(record => record.case_id === candidateId) || candidates.find(record => record.eligible) || candidates[0];
  const selected = report?.requests.find(record => record.id === selectedId);
  const busy = loading || Boolean(pending);

  return <section id="soar" className="soar-panel" aria-labelledby="soar-title" aria-busy={busy}>
    <div className="detection-heading-row">
      <div><p className="detection-eyebrow">Day5 · 이전 방식</p><h2 id="soar-title">{historyOnly ? "이전 요청 이력" : "대응 자동화"}</h2></div>
      <span className="detection-caution">{historyOnly ? "이력 조회 · 필요한 복구만" : "사람 승인 필수 · 공지 저장만 제한"}</span>
    </div>
    {historyOnly ? <p>기존 요청과 근거를 보존합니다. 이 영역에서는 새 요청을 만들거나 제한을 승인하지 않으며, 기존 제한의 확인과 저장 허용 복구만 합니다.</p> : <><p>플레이북에 대응 순서를 작성하고, 사건마다 실행 한 건을 만듭니다. 사람이 승인한 조치만 프로그램이 실행합니다.</p><ol className="soar-flow" aria-label="대응 흐름"><li>사건·요청</li><li>AI 알림</li><li>사람 승인</li><li>자동 실행</li><li>실제 저장 확인·복구</li></ol></>}
    <div className="detection-actions">
      <button id="soar-refresh" onClick={manualRefresh} disabled={busy}>대응 상태 새로고침</button>
      <a href="http://localhost:8085/notice" target="_blank" rel="noopener noreferrer">일반 사이트 공지 열기</a>
    </div>
    <p className="detection-small-note">상태는 3초마다 조회합니다. 새로고침은 실행 버튼이 아닙니다.</p>
    <p id="soar-status" className="soar-status" role="status">{pending === "notify" ? "실제 AI API에 요약을 요청하고 있습니다. 응답이 없으면 실패로 남습니다." : pending ? "요청을 처리하고 있습니다…" : loading ? "대응 상태를 불러오는 중입니다." : message}</p>
    {error && <p className="error" role="alert" id="soar-error">{error}</p>}
    {stale && report && <p className="error">아래는 마지막 조회 결과입니다. 최신 상태를 다시 확인할 때까지 변경 버튼을 잠급니다.</p>}
    {report && <>
      {!historyOnly && <><PlaybookDefinition playbook={report.playbook} />
      <div className="soar-overview">
        <div><span>자동 실행 설정</span><strong id="soar-execute-setting">{report.rules.execute_approved ? "켜짐 · 승인된 요청 자동 처리" : "꺼짐 · 승인 뒤 실행 대기"}</strong><code>EXECUTE_APPROVED = {report.rules.execute_approved ? "True" : "False"}</code></div>
        <div><span>일반 사이트의 현재 정책</span><strong id="soar-policy-state">{!report.policy.available ? "정책 확인 불가" : report.policy.blocked ? "공지 저장 제한 중" : "공지 저장 허용"}</strong><span>요청 상태와 실제 정책은 별도로 확인합니다.</span></div>
      </div>
      <section className="soar-candidates" aria-labelledby="soar-candidates-title">
        <h3 id="soar-candidates-title">새 요청 후보 미리보기</h3>
        <p>준비된 해시 일치 근거와 실패 횟수로 요청 대상을 고릅니다. 현재 기준: <strong id="soar-request-threshold">실패 {report.rules.request_min_failures}회 이상</strong>.</p>
        <p className="detection-small-note">{report.observation ? `현재 관찰 시작: ${displayTime(report.observation.started_at)}` : "아래 사건 만들기·근거 확인에서 새 관찰 시작을 먼저 누르세요."} 기준을 바꾸거나 새 관찰을 시작해도 이미 만든 요청은 삭제하지 않습니다.</p>
        {candidates.length === 0 ? <p className="log-empty">현재 연결할 사건이 없습니다. 아래에서 관찰을 시작하고 일반 사이트의 로그인·공지 저장으로 실제 근거를 만드세요.</p> : <>
          <label htmlFor="soar-candidate">비교할 사건
            <select id="soar-candidate" value={candidate?.case_id || ""} onChange={event => chooseCandidate(event.target.value)} disabled={busy}>
              {candidates.map(record => <option key={record.case_id} value={record.case_id}>{record.case.username || "로그인 근거 미확인"} · 실패 {record.failure_count}회 · {displayTime(record.case.write?.occurred_at)} · {record.case_id}</option>)}
            </select>
          </label>
          {candidate && <div className="soar-candidate" data-case-id={candidate.case_id}>
            <p><strong id="soar-candidate-result">{candidate.eligible ? "새 요청 대상" : "현재 기준에서 제외"}</strong> · {candidate.reason}</p>
            <p><code>{candidate.case.server_id}</code> · <code>{candidate.case.target_path}</code> · 실패 <strong>{candidate.failure_count}회</strong></p>
            <p className="detection-small-note">실패 입력 이름과 정상 로그인 계정이 같아도 같은 사람의 행동이라고 단정하지 않습니다.</p>
            <details className="detection-raw"><summary>후보 사건과 근거 보기</summary><pre>{JSON.stringify({ case: candidate.case, evidence: candidate.evidence }, null, 2)}</pre></details>
            {candidate.request_id ? <div className="actions soar-create-actions"><button onClick={() => selectRequest(candidate.request_id)} disabled={busy}>기존 대응 요청 보기</button><span>같은 사건의 요청을 중복 생성하지 않습니다.</span></div> : <button id="soar-create" className="refresh-logs soar-create-actions" onClick={createRequest} disabled={busy || stale || !candidate.eligible || report.playbook?.valid !== true}>대응 요청 만들기</button>}
            <p className="detection-small-note">대응 요청 만들기는 이 사건으로 플레이북 실행 한 건을 시작하는 버튼입니다.</p>
          </div>}
        </>}
      </section></>}
      <section className="soar-requests" aria-labelledby="soar-requests-title">
        <div className="detection-heading-row"><h3 id="soar-requests-title">플레이북 실행 · 대응 요청과 알림함</h3><span>{report.requests.length}건 · 서버에 이력 보존</span></div>
        {report.requests.length === 0 ? <p className="log-empty">{historyOnly ? "보존된 이전 요청이 없습니다." : "아직 대응 요청이 없습니다. 후보를 확인한 뒤 대응 요청 만들기를 누르세요."}</p> : <>
          <label htmlFor="soar-request-select">확인할 요청
            <select id="soar-request-select" value={selected?.id || ""} onChange={event => selectRequest(event.target.value)} disabled={busy}>
              {report.requests.map(record => <option key={record.id} value={record.id}>{displayTime(record.created_at)} · {stateLabel(record.state)} · {record.id}</option>)}
            </select>
          </label>
          {selected && <SoarRequest request={selected} rules={report.rules} ai={report.ai} busy={busy} stale={stale} onAction={performAction} recoveryOnly={historyOnly} />}
        </>}
      </section>
      <p className="detection-small-note">마지막 상태 조회: <time dateTime={lastReadAt}>{displayTime(lastReadAt)}</time>. 화면 선택은 이 브라우저에, 요청 이력은 서버에 저장합니다.</p>
    </>}
  </section>;
}

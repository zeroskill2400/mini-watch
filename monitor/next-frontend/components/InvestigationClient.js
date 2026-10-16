"use client";
import { useState } from "react";
import { requestJson } from "../api/client";

function Evidence({ event, label }) {
  if (!event) return <p className="log-empty">{label}: 연결된 원본이 없습니다.</p>;
  return <details className="detection-raw investigation-evidence">
    <summary>{label} · {event.occurred_at}</summary>
    <pre>{JSON.stringify(event.raw, null, 2)}</pre>
  </details>;
}

export default function InvestigationClient({ automationMode = false }) {
  const [report, setReport] = useState(null);
  const [pending, setPending] = useState("");
  const [message, setMessage] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [previousAnalysis, setPreviousAnalysis] = useState(null);
  const [selectedId, setSelectedId] = useState("");

  async function refresh() {
    setPending("refresh");
    setMessage("");
    try {
      const result = await requestJson("/api/investigation");
      setReport(result);
      if (!result.cases.some(record => record.id === selectedId)) {
        setAnalysis(null);
        setPreviousAnalysis(null);
        setSelectedId("");
      }
      setMessage("사건을 불러왔습니다. 센서 기록이 없으면 잠시 후 다시 눌러주세요.");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setPending("");
    }
  }

  async function analyze(caseId) {
    const completedAnalysis = selectedId === caseId ? analysis : null;
    setPending("ai");
    setMessage("");
    if (selectedId !== caseId) {
      setAnalysis(null);
      setPreviousAnalysis(null);
    }
    setSelectedId(caseId);
    try {
      const result = await requestJson("/api/investigation/ai", "POST", { case_id: caseId });
      setPreviousAnalysis(completedAnalysis);
      setAnalysis(result);
      setMessage("AI의 제안입니다. 원본과 비교한 뒤 사람이 판단하세요. 조치는 실행되지 않습니다.");
    } catch (error) {
      setMessage(error.message + (completedAnalysis ? " 아래는 이전에 성공한 응답입니다." : ""));
    } finally {
      setPending("");
    }
  }

  async function changePolicy(blocked) {
    setPending("policy");
    setMessage("");
    try {
      await requestJson("/api/investigation/policy", "POST", { blocked });
      const result = await requestJson("/api/investigation");
      setReport(result);
      setMessage(blocked
        ? "공지 변경을 제한했습니다. 일반 사이트에서 공지 저장을 눌러 확인하세요."
        : "제한을 해제했습니다. 일반 사이트에서 공지를 다시 저장해보세요.");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setPending("");
    }
  }

  return <details className="detection-log-review investigation">
    <summary>파일 변경·사건 조사</summary>
    <div className="investigation-body">
      <p>공지 파일 변경을 센서에서 확인하고, 앱 기록과 연결해 조사합니다.</p>
      <div className="detection-actions">
        <button id="investigation-refresh" className="refresh-logs" onClick={refresh} disabled={!!pending}>사건 새로고침</button>
        <a href="http://localhost:8085/notice" target="_blank" rel="noreferrer">일반 사이트 공지 열기</a>
      </div>
      <p className="detection-status" role="status">{pending === "ai" ? "실제 AI API에 요청하고 있습니다…" : message}</p>
      {!report && <p className="log-empty">공지 저장 후 사건 새로고침을 누르세요. 시작 시 가짜 사건은 만들어두지 않습니다.</p>}
      {report && <>
        <p className="detection-small-note">{report.observation ? `조회한 관찰 시작: ${report.observation.started_at}` : "위의 새 관찰 시작을 먼저 누르세요. 시작점이 없으면 사건을 연결하지 않습니다."}</p>
        <section className="investigation-stage" aria-labelledby="sensor-title">
          <p className="detection-eyebrow">파일을 직접 읽은 별도 출처</p>
          <h2 id="sensor-title">파일 센서 원본</h2>
          <p>센서는 <code>/classroom-data/notice.txt</code>의 내용을 읽어 변경을 관찰합니다. 로그인 계정은 알지 못합니다.</p>
          <p>현재 관찰 이후 앱 저장 <strong>{report.writes.length}건</strong> · 센서 변경 <strong>{report.file_events.length}건</strong></p>
          {report.file_events.length === 0
            ? <p className="log-empty">관찰된 변경이 없습니다. 서로 다른 내용으로 저장하고 잠시 후 새로고침하세요.</p>
            : report.file_events.slice(-10).reverse().map(event => <Evidence key={event.event_id} event={event} label="파일 변경" />)}
          <p className="detection-small-note">센서는 약 1초 간격으로 읽습니다. 다음 저장은 이번 변경이 보인 뒤 진행하세요. 시각은 파일 변경을 관찰한 시각입니다.</p>
        </section>

        <section className="investigation-stage" aria-labelledby="cases-title">
          <p className="detection-eyebrow">다른 출처를 근거로 연결</p>
          <h2 id="cases-title">앱 작업과 센서 비교</h2>
          <p className="detection-rule">{report.correlation.label}</p>
          {!report.correlation.require_same_hash && <p className="error">아직 서버·파일만 같은 비교 후보입니다. 내용이 다른 기록도 함께 보일 수 있습니다.</p>}
          <p className="detection-small-note">같은 입력 아이디의 로그인 실패는 조사할 배경이지, 정상 로그인 사용자와 같은 사람이라는 증거는 아닙니다.</p>
          {report.cases.length === 0 && <p className="log-empty">연결할 기록이 없습니다. 정상 로그인 후 공지를 저장하고 센서 기록을 확인하세요.</p>}
          {report.cases.map(record => <article key={record.id} className="investigation-case">
            <div className="detection-alert-heading">
              <h3>{record.username || "로그인 근거 미확인"} · 공지 저장</h3>
              <span>{record.hash_matches ? "내용 해시 일치" : "내용 해시 불일치"}</span>
            </div>
            <p><code>{record.server_id}</code> · <code>{record.target_path}</code></p>
            <p className="detection-small-note">
              {record.related_alert
                ? "같은 입력 아이디를 대상으로 한 반복 실패 경고가 있습니다. 행위자가 같은지는 알 수 없습니다."
                : "같은 입력 아이디를 대상으로 한 반복 실패 경고는 없습니다."}
            </p>
            <Evidence event={record.auth_success} label="실제 정상 로그인" />
            <Evidence event={record.write} label="앱 공지 저장" />
            <Evidence event={record.sensor} label="센서 파일 변경" />
            {!automationMode && <div className="actions investigation-case-actions">
              <button onClick={() => analyze(record.id)} disabled={!!pending || !report.ai.available || !report.correlation.require_same_hash || !record.hash_matches}>AI 분석 요청</button>
            </div>}
            {selectedId === record.id && analysis && <div className="investigation-ai-result">
              {previousAnalysis && <details className="detection-raw">
                <summary>이전 AI 응답과 요청 문장</summary>
                <pre>{JSON.stringify({ prompt: previousAnalysis.input.prompt, result: previousAnalysis.result }, null, 2)}</pre>
              </details>}
              <p className="detection-eyebrow">실제 API 응답 · {analysis.model}</p>
              <h4>AI 제안 · 우선순위 {({ low: "낮음", medium: "중간", high: "높음" })[analysis.result.priority] || analysis.result.priority}</h4>
              <p>{analysis.result.summary}</p>
              <h4>관찰한 내용</h4>
              <ul>{analysis.result.observations.map((item, index) => <li key={index}>{item}</li>)}</ul>
              <h4>사람이 확인할 항목</h4>
              <ul>{analysis.result.checks.map((item, index) => <li key={index}>{item}</li>)}</ul>
              <h4>단정하면 안 되는 점</h4>
              <ul>{analysis.result.cautions.map((item, index) => <li key={index}>{item}</li>)}</ul>
              <details className="detection-raw">
                <summary>AI에 보낸 근거와 반환한 근거 ID 비교</summary>
                <pre>{JSON.stringify({ input: analysis.input, evidence_ids: analysis.result.evidence_ids }, null, 2)}</pre>
              </details>
            </div>}
          </article>)}
        </section>

        {!automationMode && <section className="investigation-stage" aria-labelledby="ai-title">
          <p className="detection-eyebrow">요약은 AI, 판단은 사람</p>
          <h2 id="ai-title">AI 연결 상태</h2>
          <p>{report.ai.available
            ? "연결 설정이 있습니다. 해시까지 일치하는 사건의 AI 분석 요청을 누르세요. 실제 호출 결과는 요청 후 확인합니다."
            : "AI 연결이 준비되지 않았습니다. 강사가 API 연결을 준비한 뒤 진행하세요. 예시 답변으로 대신하지 않습니다."}</p>
          <p className="detection-small-note">AI는 선택한 사건의 제한된 근거만 읽고 제안합니다. 아래 제한 버튼을 대신 누르지 않습니다.</p>
        </section>}

        <section className="investigation-stage" aria-labelledby="policy-title">
          <p className="detection-eyebrow">실제 정책 확인</p>
          <h2 id="policy-title">공지 변경 제한</h2>
          <p>현재 상태: <strong id="notice-policy-state">{!report.policy.available ? "정책 확인 불가" : report.policy.blocked ? "공지 변경 제한 중" : "공지 변경 허용"}</strong></p>
          <p>수업용 공지 파일의 저장만 막습니다. 로그인·공지 읽기·제한 해제는 계속 가능합니다.</p>
          {automationMode ? <p>위 <a href="#soar">대응 자동화</a>에서 요청·사람 승인·자동 실행 순서로 진행합니다. 여기서 직접 제한하지 않습니다.</p> : <div className="actions">
            <button id="notice-block" onClick={() => changePolicy(true)} disabled={!!pending || !report.policy.available || report.policy.blocked}>공지 변경 제한</button>
            <button id="notice-unblock" onClick={() => changePolicy(false)} disabled={!!pending || !report.policy.available || !report.policy.blocked}>제한 해제</button>
          </div>}
          {(report.policy.audit || []).map(event => <Evidence key={event.event_id} event={event} label="정책 변경" />)}
        </section>
      </>}
    </div>
  </details>;
}

"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { requestJson } from "../api/client";

function rowNumber(event) {
  return Number(event.id.slice(event.source.length + 1));
}

function rawText(event) {
  return typeof event.raw === "string" ? event.raw : JSON.stringify(event.raw, null, 2);
}

function RawLogList({ events, source }) {
  if (events.length === 0) return <p className="log-empty">표시할 원본이 없습니다.</p>;
  return <ol className="raw-log-list" data-source={source}>
    {events.map(event => <li key={event.id} data-log-id={event.id}>
      <span className="log-label">원본 {rowNumber(event)}행</span>
      <pre>{rawText(event)}</pre>
    </li>)}
  </ol>;
}

export default function AnalysisClient() {
  const [report, setReport] = useState(null);
  const [query, setQuery] = useState("");
  const [showAll, setShowAll] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const requestVersion = useRef(0);

  const fetchReport = useCallback(async version => {
    try {
      const data = await requestJson("/api/analysis");
      if (version !== requestVersion.current) return;
      if (!data.ready) {
        setReport(null);
        setError("시연 결과가 준비되지 않았습니다. 감시 API의 정규화 설정을 확인한 뒤 새로고침하세요.");
        return;
      }
      setReport(data);
      setError("");
    } catch (requestError) {
      if (version !== requestVersion.current) return;
      setReport(null);
      setError(requestError.message);
    } finally {
      if (version === requestVersion.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const version = ++requestVersion.current;
    fetchReport(version);
    return () => { requestVersion.current += 1; };
  }, [fetchReport]);

  function refreshLogs() {
    setLoading(true);
    setError("");
    fetchReport(++requestVersion.current);
  }

  const matchingEvents = (report?.events || []).filter(event => event.path.includes(query.trim()));
  const sourceEvents = source => matchingEvents
    .filter(event => event.source === source)
    .sort((first, second) => rowNumber(second) - rowNumber(first));
  const appEvents = sourceEvents("app");
  const nginxEvents = sourceEvents("nginx");
  const visibleApp = showAll ? appEvents : appEvents.slice(0, 5);
  const visibleNginx = showAll ? nginxEvents : nginxEvents.slice(0, 5);
  const visibleEvents = [...visibleApp, ...visibleNginx];

  return <div className="analysis-demo" aria-busy={loading}>
    <ol className="log-flow" aria-label="게시판 요청이 지나가는 순서">
      <li>브라우저</li>
      <li>Nginx 웹서버</li>
      <li>Flask 게시판 앱</li>
    </ol>
    <p className="log-intro">게시판에 보낸 요청을 웹서버와 앱이 각각 기록합니다. 게시판을 조작한 뒤 새로고침하면 두 원본과 같은 열로 정규화한 결과가 함께 바뀝니다.</p>
    <div className="log-toolbar">
      <label htmlFor="log-path-search">경로 검색
        <input id="log-path-search" type="search" value={query}
          onChange={event => setQuery(event.target.value)} placeholder="예: /auth/login" />
      </label>
      <button className="refresh-logs" onClick={refreshLogs} disabled={loading}>로그 새로고침</button>
    </div>
    <div className="log-display-options">
      <label className="checkbox-label" htmlFor="show-all-logs">
        <input id="show-all-logs" type="checkbox" checked={showAll}
          onChange={event => setShowAll(event.target.checked)} />
        전체 보기
      </label>
      <span>{showAll ? "검색에 맞는 모든 기록" : "검색에 맞는 출처별 최신 5행"}</span>
    </div>
    <p className="log-status" role="status">{loading
      ? "원본과 정규화 결과를 함께 불러오는 중입니다."
      : error || (report?.events.length === 0
        ? "아직 기록이 없습니다. 게시판에서 로그인하거나 페이지를 연 뒤 새로고침하세요."
        : report && (matchingEvents.length === 0
          ? "이 경로에 해당하는 기록이 없습니다. 검색어를 바꾸거나 새 요청을 보내세요."
          : `같은 자료에서 원본과 정규화 결과 ${visibleEvents.length}행을 표시합니다.`))}</p>
    {report && <>
      <p className="log-order-note">출처별 원본 행 번호의 큰 순서로 표시합니다. 전체 발생 시각순이 아니며, 두 출처의 같은 행 번호가 같은 요청을 뜻하지는 않습니다.</p>
      <section className="log-stage" aria-labelledby="raw-log-heading">
        <h2 id="raw-log-heading">수집된 원본은 모양이 다릅니다</h2>
        <div className="raw-log-grid">
          <section className="raw-source raw-source-app" aria-labelledby="app-log-heading">
            <h3 id="app-log-heading">게시판 앱 로그 <span>app</span></h3>
            <p className="source-description">Flask가 요청을 처리한 뒤 남긴 JSON</p>
            <p className="log-file">classroom-logs/app.jsonl</p>
            <RawLogList events={visibleApp} source="app" />
          </section>
          <section className="raw-source raw-source-nginx" aria-labelledby="nginx-log-heading">
            <h3 id="nginx-log-heading">앞단 웹서버 로그 <span>nginx</span></h3>
            <p className="source-description">Nginx가 요청을 받아 전달하며 남긴 문자열</p>
            <p className="log-file">classroom-logs/nginx.log</p>
            <RawLogList events={visibleNginx} source="nginx" />
          </section>
        </div>
      </section>
      <section className="log-stage normalized-stage" aria-labelledby="normalized-log-heading">
        <h2 id="normalized-log-heading">정규화하면 같은 열로 읽습니다</h2>
        <p>위 원본에서 방법·경로·상태를 꺼내 같은 항목에 넣은 결과입니다.</p>
        <div className="log-table-scroll" role="region" aria-label="정규화한 통합 로그 표" tabIndex={0}>
          <table className="log-table">
            <thead><tr><th scope="col">출처</th><th scope="col">방법</th><th scope="col">경로</th><th scope="col">상태</th><th scope="col">원본</th></tr></thead>
            <tbody>{visibleEvents.map(event => <tr key={event.id} data-log-id={event.id}>
              <td><span className={`source-name source-${event.source}`}>{event.source}</span></td>
              <td className="log-method">{event.method}</td>
              <td className="log-path"><code>{event.path}</code></td>
              <td><span className={event.status_code >= 400 ? "http-status http-error" : "http-status"}>{event.status_code}</span></td>
              <td><details><summary>{rowNumber(event)}행 보기</summary><pre>{rawText(event)}</pre></details></td>
            </tr>)}</tbody>
          </table>
        </div>
        {visibleEvents.length === 0 && <p className="log-empty">표시할 정규화 결과가 없습니다.</p>}
        <p className="log-footnote">같은 요청이 두 출처에 남을 수 있어 로그 행 수와 요청 수는 다릅니다. 404 등 오류 상태만으로 공격을 판단하지 않습니다.</p>
      </section>
    </>}
  </div>;
}

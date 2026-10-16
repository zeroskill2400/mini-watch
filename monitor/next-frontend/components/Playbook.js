const STEP_LABELS = {
  ai_notify: "AI 요약 알림",
  human_approval: "사람 승인",
  restrict_notice: "공지 저장 제한",
  record_only: "기록만 남기기",
  verify_denied: "정책 거절 403 확인",
  human_recovery_approval: "복구 승인",
  restore_notice: "저장 허용 복구",
  verify_restored: "정상 저장 200 확인",
};

const EXPECTED_STEPS = ["ai_notify", "human_approval", "restrict_notice", "verify_denied", "human_recovery_approval", "restore_notice", "verify_restored"];
const STATUS_LABELS = { pending: "아직 시작 안 함", running: "처리 중", waiting: "대기", succeeded: "완료", rejected: "거절", skipped: "건너뜀", failed: "실패" };

function stepLabel(identifier) {
  return STEP_LABELS[identifier] || identifier || "없음";
}

function statusLabel(status) {
  return STATUS_LABELS[status] || status || "상태 미확인";
}

export function PlaybookDefinition({ playbook }) {
  const valid = playbook?.valid === true;
  const steps = Array.isArray(playbook?.steps) ? playbook.steps.map(step => typeof step === "string" ? step : JSON.stringify(step)) : [];
  const empty = steps.length === 0;
  return <section className="playbook-definition" aria-labelledby="playbook-definition-title">
    <div className="detection-heading-row">
      <h3 id="playbook-definition-title">플레이북 정의</h3>
      <strong id="playbook-definition-state" className={`playbook-badge ${valid ? "playbook-status-succeeded" : "playbook-status-waiting"}`}>{valid ? "작성 완료 · 새 실행 가능" : empty ? "미작성 · 새 실행 불가" : "작성 확인 필요 · 새 실행 불가"}</strong>
    </div>
    <p><strong>{playbook?.name || "플레이북 정보를 불러오지 못했습니다."}</strong>{playbook?.version ? ` · 형식 버전 ${playbook.version}` : ""}</p>
    {playbook?.definition_hash && <p className="detection-small-note">정의 식별값: <code id="playbook-definition-hash">{playbook.definition_hash}</code></p>}
    <p>시작 방법: <strong>{playbook?.trigger === "manual" ? "수동 · 사건을 고른 뒤 대응 요청 만들기" : "시작 방법 미확인"}</strong></p>
    <p className="detection-small-note">플레이북은 실행할 작업의 순서입니다. 대응 요청 한 건이 이 순서를 따라가는 실행(run) 한 건입니다.</p>
    {!valid && <div className="playbook-write-guide" id="playbook-write-guide">
      <p><code>monitor/backend/soar_rules.py</code>의 <code>PLAYBOOK_STEPS</code>에 수업의 7단계를 작성하고 감시 API에 반영하세요.</p>
      {playbook?.error && <p>{typeof playbook.error === "string" ? playbook.error : JSON.stringify(playbook.error)}</p>}
      <p>로그인·사건 조회와 기존 요청 처리는 계속할 수 있습니다. 새 요청만 만들 수 없습니다.</p>
    </div>}
    <p className="playbook-list-label">{empty ? "작성할 7단계 · 아직 적용하지 않음" : "현재 작성한 실행 순서"}</p>
    <ol id="playbook-definition-steps" className={`playbook-definition-steps${empty ? " playbook-unwritten" : ""}`}>
      {(empty ? EXPECTED_STEPS : steps).map((step, index) => <li key={`${step}-${index}`}><span>{stepLabel(step)}</span><code>{step}</code></li>)}
    </ol>
  </section>;
}

export function PlaybookRun({ request, formatTime }) {
  const snapshot = request.playbook_snapshot;
  const steps = request.step_runs || [];
  const finished = ["completed", "completed_no_action", "rejected", "cancelled"].includes(request.state);
  return <section className="playbook-run" aria-labelledby="playbook-run-title">
    <h4 id="playbook-run-title">플레이북 실행 진행</h4>
    {snapshot ? <><p><strong>{snapshot.name}</strong> · 형식 버전 {snapshot.version} · 실행 생성 때의 정의를 사용합니다.</p><p className="detection-small-note">고정된 정의 식별값: <code id="playbook-snapshot-hash">{snapshot.definition_hash}</code></p></> : <p className="detection-small-note">이전 형식의 요청입니다. 저장된 사건과 처리 기록을 확인하세요.</p>}
    <div className="playbook-next" id="playbook-next">
      <strong>다음 단계: <span id="playbook-next-step">{stepLabel(request.next_step)}</span></strong>
      <p id="playbook-waiting-reason">{request.waiting_reason || (finished ? "이 실행은 종료됐습니다. 단계별 결과와 근거를 확인하세요." : "서버의 다음 단계 안내가 없습니다. 아래 저장된 상태를 확인하세요.")}</p>
    </div>
    {snapshot?.legacy && <p className="detection-small-note">기존 요청의 저장된 근거로 단계 상태를 복원했습니다. 확인되지 않은 과거 시도 이력은 만들지 않습니다.</p>}
    {steps.length > 0 && <>
      <h4>단계별 진행</h4>
      <ol id="playbook-run-steps" className="playbook-run-steps">
        {steps.map((step, index) => <li key={`${step.step_id}-${index}`} data-step-id={step.step_id} data-step-status={step.status} aria-current={request.next_step === step.step_id ? "step" : undefined}>
          <div className="playbook-step-heading"><strong>{index + 1}. {stepLabel(step.step_id)}</strong><span className={`playbook-badge playbook-status-${step.status}`}>{statusLabel(step.status)}</span></div>
          {step.message && ["failed", "rejected", "skipped"].includes(step.status) && <p className="detection-small-note">{step.message}</p>}
          {step.attempts?.length > 0 ? <details className="playbook-attempts">
            <summary>시도·근거 보기 · {step.attempts.length}회</summary>
            <ol>{step.attempts.map((attempt, attemptIndex) => <li key={attempt.id || `${step.step_id}-${attemptIndex}`}>
              <p><strong>시도 {attemptIndex + 1} · {statusLabel(attempt.status)}</strong> · {attempt.operator || "서버"}</p>
              <p>{attempt.message}</p>
              {typeof attempt.input?.notification_prompt === "string" && <p>사용하려던 요약 지시: {attempt.input.notification_prompt}</p>}
              <p className="detection-small-note">시작 {formatTime(attempt.started_at)} · 종료 {formatTime(attempt.finished_at)}</p>
              {attempt.evidence_ids?.length > 0 ? <p>근거 ID: {attempt.evidence_ids.map(identifier => <code key={identifier}>{identifier} </code>)}</p> : <p className="detection-small-note">이 시도에 연결된 원본 근거 ID가 없습니다.</p>}
              {attempt.operation_id && <p>조치 번호: <code>{attempt.operation_id}</code></p>}
            </li>)}</ol>
          </details> : (snapshot?.legacy || step.status === "succeeded") && <p className="detection-small-note playbook-no-attempt">저장된 시도 이력 없음</p>}
        </li>)}
      </ol>
    </>}
    {snapshot && <details className="detection-raw soar-raw" id="playbook-snapshot"><summary>실행에 고정된 플레이북 보기</summary>
      <p>현재 파일의 정의를 바꿔도 이 요청의 순서와 요청 기준은 바뀌지 않습니다. 자동 실행 설정은 현재 서버 설정을 따릅니다.</p>
      <pre>{JSON.stringify(snapshot, null, 2)}</pre>
    </details>}
  </section>;
}

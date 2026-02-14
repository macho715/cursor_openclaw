# OpenClaw Gateway 설치 검증 체크리스트

## 1. 판정·근거·다음행동

| 항목 | 내용 |
|------|------|
| **판정** | 조건부 예 (명령 6개 + Cursor 스모크 프롬프트 1개로 검증 가능) |
| **근거** | "설치 정상"은 (1) 로컬 포트 LISTEN, (2) HTTP 200/정상 JSON, (3) Docker sandbox Up, (4) Cursor→Gateway 요청이 실제로 찍힘 — 4개로 판단 가능. ⚠️AMBER:[가정] Windows+Docker Desktop 사용. |
| **다음행동** | 아래 **호스트 스모크 테스트** 먼저 실행 → PASS면 **Cursor 스모크 프롬프트**를 보내고 **Gateway 로그에 요청이 찍히는지**로 E2E 확인. |

---

## 2. Windows 호스트 스모크 테스트 (안전, 읽기전용)

### 2-1) 포트 리스닝 확인 (필수)

PowerShell에서:

```powershell
Test-NetConnection 127.0.0.1 -Port 18789
Test-NetConnection 127.0.0.1 -Port 11434
```

**PASS 기준:** `TcpTestSucceeded : True`  
**FAIL이면:** Gateway/Ollama 미기동 또는 방화벽/바인딩 문제.

---

### 2-2) Ollama(OpenAI 호환) 응답 확인 (필수)

```powershell
curl.exe -sS http://127.0.0.1:11434/v1/models
```

**PASS 기준:** JSON이 나오고 `data`(또는 유사 목록)가 보임.  
**FAIL이면:** Ollama API 주소/포트 불일치 또는 Ollama 미기동.

---

### 2-3) OpenClaw Gateway(WebChat) 응답 확인 (필수)

토큰은 절대 그대로 붙여넣지 말고 `<TOKEN>` 자리만 바꾸세요 (로그/히스토리에 남음).

```powershell
curl.exe -I "http://127.0.0.1:18789/?token=<TOKEN>"
```

**PASS 기준:** `HTTP/1.1 200` 또는 `302` 등 정상 HTTP 응답.  
**FAIL이면:** 토큰 오류(401/403) 또는 Gateway 미기동.

> 보안: 예전에 토큰을 노출한 적이 있으면 **토큰 회전(재발급)** 후 진행 권장.

---

### 2-4) Docker sandbox 컨테이너 Up 확인 (필수)

```powershell
docker ps --filter "name=openclaw-sbx" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
```

**PASS 기준:** `Up ...` 상태가 최소 1개 이상.  
**FAIL이면:** Docker Desktop 미기동 또는 OpenClaw sandbox 실행 실패.

---

### 2-5) (권장) sandbox Mount 개수 확인 (격리 검증)

컨테이너 이름은 2-4에서 나온 값을 `<CONTAINER_NAME>`에 넣으세요.

```powershell
docker inspect <CONTAINER_NAME> --format "{{len .Mounts}}"
```

**권장 PASS 기준:** `0` (또는 기대한 최소값)  
**FAIL이면(큰 값/호스트 경로 마운트):** "호스트 파일 접근면"이 커져서 보안상 재검토 필요.

---

### 2-6) (선택) 실제 LISTEN PID 확인

```powershell
netstat -ano | findstr ":18789"
netstat -ano | findstr ":11434"
```

**PASS 기준:** `LISTENING` + PID 표시.

---

## 3. Cursor 로컬 모델 설정 (설정 적용 순서)

1. **Cursor 재시작** — 설정 적용을 위해 창을 다시 로드 (`Ctrl+Shift+P` → `Reload Window`)
2. **Settings → Models** — `Override OpenAI Base URL`이 켜져 있는지 확인
3. **OpenAI API 키** — Ollama는 `ollama` 같은 임의 문자열로 가능
4. **채팅창 상단** — 로컬 모델(예: `llama3.1:8b`) 선택

> **참고:** Cursor 포럼에 따르면 요청이 Cursor 서버를 거쳐 가기 때문에, localhost(127.0.0.1)는 동작하지 않을 수 있습니다. 이 경우 **OpenClaw 대시보드** (`http://127.0.0.1:18789/?token=...`)에서 채팅하는 방식을 권장합니다.

---

## 4. Cursor 내부 E2E 검증 ("Cursor가 진짜 Gateway를 쓰는지" 확인)

### 4-1) 가장 확실한 방법 (권장)

* **Gateway(18789) 콘솔/로그 창을 켠 상태에서**
* Cursor에서 **해당 모델/프로바이더(로컬 Gateway로 연결된 것)**를 선택하고
* 아래 프롬프트를 1회 보내세요.
* **동시에 Gateway 로그에 요청이 찍히면** "Cursor↔Gateway 연동"은 정상입니다.

---

### 4-2) Cursor 스모크 프롬프트 (복붙)

[`CURSOR_SMOKE_PROMPT.txt`](CURSOR_SMOKE_PROMPT.txt) 파일 내용을 Cursor에 붙여넣어 보내세요.

**PASS 판정(현실 기준):**

* Cursor 응답이 정상 출력되고,
* **Gateway 로그에 해당 요청이 들어온 흔적이 보이면** E2E PASS.

---

## 5. FAIL 패턴별 빠른 원인-조치 표

| No | 증상 | 가능 원인 | 다음 조치 |
|----|------|-----------|-----------|
| 1 | 18789 포트 FAIL | Gateway 미기동/바인딩 오류 | Gateway 재시작, loopback 바인드 확인 |
| 2 | 11434 포트 FAIL | Ollama 미기동 | Ollama 서비스 재시작 |
| 3 | 18789는 열림, 401/403 | 토큰 불일치/만료 | Cursor 설정 토큰 갱신 + 토큰 회전 |
| 4 | Docker ps에 없음 | Docker Desktop/컨테이너 미기동 | Docker 상태 확인 후 sandbox 재기동 |
| 5 | Cursor는 답하는데 Gateway 로그가 안 찍힘 | Cursor가 다른 provider로 응답 | Cursor에서 "로컬 Gateway 모델" 선택 재확인 + baseURL/키 매칭 |

---

## 6. 호스트 스모크 결과 예시 (6/6 PASS)

| No | 항목 | 결과 | 판정 |
| -: | --- | --- | --- |
| 1-1 | 포트 18789 (Gateway) | TcpTestSucceeded: True | PASS |
| 1-1 | 포트 11434 (Ollama) | TcpTestSucceeded: True | PASS |
| 1-2 | Ollama `/v1/models` | JSON 정상 (llama3.1:8b 등) | PASS |
| 1-3 | Gateway `/?token=...` | HTTP/1.1 200 OK | PASS |
| 1-4 | Docker sandbox | openclaw-sbx-agent-main-main-* Up | PASS |
| 1-5 | Sandbox Mount 개수 | 0~1 (격리 양호) | PASS |
| 1-6 | LISTEN PID | 18789, 11434 LISTENING | PASS |

→ **호스트 스모크 6/6 PASS** 후 **Cursor E2E** (4-2 프롬프트) 전송 → Gateway 로그에 요청 찍히면 **E2E PASS**.

---

## 7. 자동화 스크립트

호스트 스모크 테스트(2-1 ~ 2-6)를 자동 실행하려면:

```powershell
# 토큰은 환경변수 또는 -Token 인자로 전달 (로그에 기록되지 않음)
.\tools\smoke_test_openclaw.ps1
# 또는
$env:OPENCLAW_TOKEN = "<YOUR_TOKEN>"; .\tools\smoke_test_openclaw.ps1
```

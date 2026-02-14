# Ollama / OpenClaw 사용법 정리

> `cursor_openclaw_ollama_windows.md` 대화 로그 기반 정리 (2026-02-13)

---

## 1. Ollama 사용법 (Windows)

### 1.1 CLI에서 바로 쓰기

```powershell
# 대화형 채팅 (Enter로 전송, /bye 종료)
ollama run llama3.1:8b

# 한 번만 질문하고 끝
ollama run qwen2.5:7b-instruct "한국어로 인사해줘"
```

### 1.2 자주 쓰는 명령

| 명령 | 설명 |
|------|------|
| `ollama run <모델>` | 해당 모델로 대화 시작 |
| `ollama list` | 로컬 모델 목록 |
| `ollama pull <모델>` | 모델 다운로드 |
| `ollama ps` | 지금 로드된 모델 확인 |
| `ollama stop <모델>` | 모델 언로드 |
| `ollama rm <모델>` | 모델 삭제 |

### 1.3 API로 호출 (다른 앱/스크립트)

Ollama가 켜져 있으면 `http://localhost:11434` 로 요청합니다.

```powershell
# PowerShell 예시 (단일 생성)
Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post `
  -ContentType "application/json" `
  -Body '{"model":"llama3.1:8b","prompt":"Hello","stream":false}'
```

- 채팅 형식: `POST http://localhost:11434/api/chat`
- 문서: https://github.com/ollama/ollama/blob/main/docs/api.md

### 1.4 사전 확인

- 트레이에 Ollama 아이콘이 있거나 `ollama serve` 실행
- 브라우저에서 `http://localhost:11434` 접속 → "Ollama is running" 확인

---

## 2. OpenClaw 사용법

### 2.1 핵심 명령

| 명령 | 설명 |
|------|------|
| `openclaw gateway status` | 게이트웨이 상태 확인 |
| `openclaw dashboard` | 대시보드 열기 |
| `openclaw gateway` | 게이트웨이 수동 실행 (창 유지) |
| `openclaw health` | 헬스 체크 |
| `openclaw doctor` | 설정/환경 진단 |
| `openclaw doctor --fix` | 진단 후 자동 수정 (서비스 설치 등) |
| `openclaw onboard --install-daemon` | 온보딩 + 데몬 설치 (한 번만) |
| `openclaw configure --section models` | 모델/Provider 설정 |
| `openclaw configure --section web` | 웹 검색(Brave API) 설정 |

### 2.2 대시보드

- 주소: `http://127.0.0.1:18789/?token=<토큰>`
- 온보딩 시 받은 토큰을 쿼리에 유지해야 제어 가능
- 다시 열기: `openclaw dashboard`

### 2.3 Telegram 봇

1. 봇에게 `/start` 전송 → pairing code 수신
2. 승인:
   ```powershell
   openclaw pairing list telegram
   openclaw pairing approve telegram <CODE>
   ```
3. 이후 봇에게 메시지 보내면 OpenClaw가 응답

---

## 3. Ollama + OpenClaw 연동

### 3.1 한 번에 설정·실행 (권장)

```powershell
ollama launch openclaw
```

- OpenClaw가 Ollama를 모델 제공자로 설정하고 게이트웨이를 띄움
- 이미 게이트웨이가 떠 있으면 설정만 반영 후 자동 리로드

설정만 하고 서비스는 나중에 띄우려면:

```powershell
ollama launch openclaw --config
```

### 3.2 수동 설정

온보딩에서 "Skip for now" 했거나 나중에 Ollama로 바꾸려면:

```powershell
openclaw configure --section models
```

또는 config 직접 수정:

```powershell
openclaw config set models.providers.ollama.baseUrl "http://localhost:11434/v1"
openclaw config set models.providers.ollama.apiKey "ollama-local"
```

- 설정 파일: `%USERPROFILE%\.openclaw\openclaw.json`
- Provider: `Ollama`
- Base URL: `http://localhost:11434`
- 기본 모델: `llama3.1:8b` 또는 `qwen2.5:7b-instruct` (설치한 이름 그대로)

### 3.3 동작 순서

1. **Ollama 실행** — 트레이 또는 `ollama serve`
2. **OpenClaw에서 Ollama를 모델로 지정** — `openclaw configure --section models` 또는 config
3. **OpenClaw 실행** — `openclaw gateway` 또는 `openclaw doctor --fix` 후 데몬
4. **사용** — 대시보드 또는 Telegram

---

## 4. 웹 검색 (web_search)

- Brave Search API 키 필요
- 설정: `openclaw configure --section web` 또는 환경변수 `BRAVE_API_KEY`

---

## 5. 외부/인터넷 접속

### 5.1 Tailscale Serve (같은 Tailnet만)

```powershell
openclaw gateway --tailscale serve
```

- 접속: `https://<Tailnet MagicDNS>/`
- 같은 Tailnet 기기만 접속 가능

### 5.2 Tailscale Funnel (공개 인터넷)

```powershell
$env:OPENCLAW_GATEWAY_PASSWORD = "your-strong-password"
openclaw gateway --tailscale funnel --auth password
```

- 비밀번호 인증 필수
- 환경변수 `OPENCLAW_GATEWAY_PASSWORD` 권장 (config에 직접 넣지 말 것)

### 5.3 SSH 터널

클라이언트 PC에서:

```powershell
ssh -N -L 18789:127.0.0.1:18789 user@게이트웨이호스트
```

- 터널 유지 후 브라우저: `http://127.0.0.1:18789/?token=...`

---

## 6. 트러블슈팅

| 증상 | 확인 사항 |
|------|-----------|
| 연결 안 됨 / 타임아웃 | Ollama 실행 여부, `http://localhost:11434` 접속 테스트 |
| 모델을 찾을 수 없음 | OpenClaw 설정의 모델명과 `ollama list` 이름 일치 여부 (대소문자, 태그 포함) |
| 응답이 느림 | 첫 요청 시 모델 로드 → 한 번 질문 후 두 번째부터 속도 확인 |
| 설정 오류 | `openclaw doctor --fix` 실행 |

---

## 7. 참고 링크

- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Ollama – OpenClaw](https://docs.ollama.com/integrations/openclaw)
- [OpenClaw Gateway – Tailscale](https://docs.openclaw.ai/gateway/tailscale)
- [OpenClaw Remote Access](https://docs.openclaw.ai/gateway/remote)
- [OpenClaw Showcase](https://openclaw.ai/showcase)

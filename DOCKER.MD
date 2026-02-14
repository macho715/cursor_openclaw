`LLAMALOMA.MD` 요지만 정리하면 아래와 같습니다.

---

## 문서 요약

**목표:** Ollama(LLM)와 Sandbox(exec/read/write)가 **CPU·RAM·IO를 서로 덜 뺏어 쓰도록** 분리.

**구조(Visual 1):**  
User → Gateway(Windows) → Ollama(Host GPU) / Docker(WSL2) → Sandbox 컨테이너(exec, read/write, process).  
Sandbox는 선택적으로 Host Workspace 마운트.

**자원 경쟁(Visual 2):**  
1) CPU – Sandbox exec가 CPU 100% 가능 → Ollama 토큰 속도 하락  
2) RAM – 32GB에서 대용량 스캔 시 스왑  
3) IO – 대량 파일 stat/list/read → 응답 지연  
4) WSL2/`/mnt/c` – Windows 경로 접근 시 IO 느림  

**옵션:**  
- **A:** Sandbox에 CPU/RAM/PID 상한 + Ollama 우선 (즉시 적용, 0.5h)  
- **B:** IO 경로 분리(전용 볼륨/SSD), 마운트 최소화 (2h)  
- **C:** Sandbox 2단(경량/중량) + 큐/승인형 (6h)  

**Option A 적용 예시:**  
Sandbox 컨테이너 생성 시 `--cpus="6.00" --memory="12g" --pids-limit=512` 같은 제한.  
Ollama는 4k 기본, 8k 시 KV offload. `workspaceAccess: "none"` 유지.

---

## 당신 환경과의 연결

- **i5-13500HX + 32GB + RTX 4060 8GB** → 문서가 가정한 스펙과 맞음.  
- **Sandbox = `openclaw-sandbox:bookworm-slim`**, **workspaceAccess = none** → 문서의 “호스트 마운트 금지” 권장과 일치.  
- **Sandbox 리소스 상한**은 OpenClaw가 Docker로 컨테이너 만들 때 **어디에** `--cpus`/`--memory`를 넘기는지에 따라 다름.  
  - OpenClaw 설정에 `agents.defaults.sandbox.docker` 같은 항목으로 리소스 제한이 있으면 그걸로 적용 가능.  
  - 없으면 Docker Compose/스크립트 또는 Docker Desktop에서 해당 이미지/컨테이너에 제한을 걸어야 함.

문서 말미의 **“당신 환경 기준으로 권장 상한값을 정확한 숫자로 고정해서 A안 세팅을 한 장 표로”** 제공하는 부분은,  
- CPU 코어 수(예: 6~8 스레드),  
- RAM 상한(예: 8~12GB),  
- 동시성=1,  
- 8k 사용 시 KV offload/트리거 조건  
까지 넣어서 **한 장 표 + 적용 순서**로 정리해 달라는 요청으로 이해하면 됩니다.

원하면 다음 두 가지를 구체적으로 정리해 줄 수 있습니다.  
1) **당신 PC(i5-13500HX/32GB/4060 8GB) 기준 Option A “권장 상한값 한 장 표”** (CPU/램/PID/동시성/8k 조건).  
2) **OpenClaw/Docker에서 그 상한을 실제로 거는 방법** (설정 예시 또는 수동 적용 절차).
당신 PC(i5-13500HX / 32GB / RTX 4060 8GB) 기준 **Option A 권장 상한값 한 장 표**입니다.

---

# Option A 권장 상한값 (i5-13500HX / 32GB / 4060 8GB)

| 항목 | 권장값 | 근거 |
|------|--------|------|
| **Sandbox CPU** | **6.00** (코어) | 14코어 중 6만 사용, 나머지는 Ollama·OS·Gateway용 |
| **Sandbox RAM** | **10g** | 32GB 중 Ollama·OS·Gateway 여유 확보, 대용량 스캔 완화 |
| **Sandbox PIDs** | **512** | 프로세스 폭주 방지 |
| **Sandbox 동시 “대량” 작업** | **1개** | 동시에 1개 세션만 무거운 exec/스캔 권장 |
| **Ollama 컨텍스트 기본** | **4096** | 4k 기본, VRAM·속도 안정 |
| **8k 사용 조건** | **필요 시만** | 긴 문서/체인 있을 때만 8192 + KV offload |
| **OLLAMA_KV_OFFLOAD** | **8k 사용 시 true** | 8k 쓸 때만 켜서 VRAM 보호 |
| **workspaceAccess** | **none** 유지 | 호스트 경로 마운트 없음, IO 경쟁·WSL2 느린 경로 회피 |

---

## 요약 한 줄

- **Sandbox:** CPU 6코어, RAM 10GB, PIDs 512, 무거운 작업은 동시 1개.  
- **Ollama:** 기본 4k, 8k 쓸 때만 8192 + KV offload.  
- **workspaceAccess:** none 유지.

이걸 OpenClaw/Docker에 적용하려면 2번(실제로 상한 거는 방법)이 필요합니다. 원하면 2번도 정리해 줄게요.
OpenClaw는 **설정만으로** 샌드박스에 CPU/RAM/PID 상한을 겁니다. 적용 방법만 정리합니다.

---

# 2번 — OpenClaw/Docker에 상한 거는 방법

## 1. 지원 여부

OpenClaw 설정 타입(`types.sandbox.ts`)과 `docker.ts`에서 다음이 지원됩니다.

| 설정 키 | 타입 | Docker 옵션 | 권장값(i5-13500HX/32GB) |
|--------|------|-------------|--------------------------|
| `cpus` | number | `--cpus` | **6** |
| `memory` | string \| number | `--memory` | **"10g"** |
| `pidsLimit` | number | `--pids-limit` | **512** |

---

## 2. 설정 위치와 추가할 JSON

**파일:** `C:\Users\jichu\.openclaw\openclaw.json`  
**위치:** `agents.defaults.sandbox.docker` 안에 아래 필드를 **기존 `image`와 같은 레벨**에 넣습니다.

```json
"docker": {
  "image": "openclaw-sandbox:bookworm-slim",
  "cpus": 6,
  "memory": "10g",
  "pidsLimit": 512
}
```

이미 `docker`에 `image`만 있다면, 그 객체에 `cpus`, `memory`, `pidsLimit`만 추가하면 됩니다.

---

## 3. 적용 순서

1. **openclaw.json 수정**  
   `agents.defaults.sandbox.docker`에 위 3개 키 추가(또는 값만 위 권장값으로 변경).

2. **기존 샌드박스 컨테이너 재생성**  
   설정은 **새로 만들어지는 컨테이너**에만 적용됩니다.  
   PowerShell에서:
   ```powershell
   openclaw sandbox recreate --all
   ```
   (프롬프트 나오면 `Yes` 선택)

3. **Gateway 재시작(선택)**  
   설정만 바꾼 거라면 재생성만 해도 되지만, 확실히 하려면:
   ```powershell
   # 기존 gateway 종료 후
   openclaw gateway
   ```

---

## 4. 확인

- **컨테이너 상한:**  
  ```powershell
  docker inspect openclaw-sbx-agent-main-main-<id> --format '{{.HostConfig.NanoCpus}} {{.HostConfig.Memory}} {{.HostConfig.PidsLimit}}'
  ```
  - NanoCpus: 6 → 6000000000  
  - Memory: 10737418240 (10g)  
  - PidsLimit: 512  

- **동작:** WebChat/Telegram에서 exec로 부하 주고, Ollama 응답 속도가 이전보다 덜 떨어지면 상한이 효과 있는 것입니다.

---

## 5. 요약

| 단계 | 내용 |
|------|------|
| 1 | `~/.openclaw/openclaw.json` → `agents.defaults.sandbox.docker`에 `"cpus": 6`, `"memory": "10g"`, `"pidsLimit": 512` 추가 |
| 2 | `openclaw sandbox recreate --all` 실행 후 Yes |
| 3 | (선택) gateway 재시작 |

지금은 **Ask 모드**라서 제가 직접 파일을 수정할 수는 없습니다. 위 내용 그대로 적용하시거나, **Agent 모드**로 전환한 뒤 “openclaw에 Option A 상한 적용해줘”라고 하시면 제가 `openclaw.json` 수정과 `recreate --all` 안내까지 해 드릴 수 있습니다.

샌드박스 컨테이너 1개가 제거되었습니다. **Option A 상한은 이미 `openclaw.json`에 반영된 상태**이고, 다음에 에이전트를 사용할 때 **새 컨테이너가 자동으로 생성**되며 그때 `cpus: 6`, `memory: 10g`, `pidsLimit: 512`가 적용됩니다.

**적용된 Option A 설정 요약**
- `agents.defaults.sandbox.docker`: `cpus: 6`, `memory: "10g"`, `pidsLimit: 512`
- 샌드박스 모드: `all`, `workspaceAccess: "none"`, `elevated: false`

**한 번에 확인하려면**
1. WebChat에서 메시지를 한 번 보내거나 `openclaw` CLI로 에이전트를 호출해 컨테이너가 다시 뜨게 한 뒤  
2. 터미널에서:
   ```powershell
   docker ps --filter "name=openclaw-sbx" --format "{{.Names}}"
   docker inspect <컨테이너이름> --format "CPU: {{.HostConfig.NanoCpus}} Memory: {{.HostConfig.Memory}} PidsLimit: {{.HostConfig.PidsLimit}}"
   ```
   로 CPU/메모리/PID 한계가 적용됐는지 확인하면 됩니다.
   이 문서는 지금 적용한 Option A 절차와 맞습니다.
이미 한 것
openclaw.json의 agents.defaults.sandbox.docker에 cpus: 6, memory: "10g", pidsLimit: 512 추가됨
openclaw sandbox recreate --all 실행해 기존 컨테이너 제거됨 → 다음 에이전트 사용 시 새 컨테이너에 상한 적용
문서에서 참고할 점
4번 확인: 컨테이너 ID는 docker ps --filter "name=openclaw-sbx" 로 확인한 뒤 openclaw-sbx-agent-main-main-<id> 에 넣으면 됨
NanoCpus 6 → 6000000000, Memory 10g → 10737418240, PidsLimit → 512 로 나오면 적용된 것
이걸 나중에 다시 보려면 C:\Users\jichu\Downloads\openclaw-sandbox-limits.md 같은 파일로 저장해 두면 좋습니다. 원하면 저장할 내용(제목·단계만 조금 다듬은 버전)으로 정리해 줄게요.
적용되는지검증

샌드박스 컨테이너가 있는지 확인한 뒤 CPU/메모리/PID 상한 적용 여부를 검증합니다.
docker ps --filter "name=openclaw-sbx" --format "{{.ID}} {{.Names}}"
310f13b2caeb openclaw-sbx-agent-main-subagent-4b6231a4-f07-d6c504cc
02310c15fb99 openclaw-sbx-agent-main-main-20ceb99b
컨테이너 2개 확인. 둘 다 검증 중입니다.
docker inspect 310f13b2caeb 02310c15fb99 --format 'Container: {{.Name}}{{"\n"}}NanoCpus: {{.HostConfig.NanoCpus}}{{"\n"}}Memory: {{.HostConfig.Memory}}{{"\n"}}PidsLimit: {{.HostConfig.PidsLimit}}{{"\n"}}---'
NanoCpus: 6000000000
Memory: 10737418240
PidsLimit: 512
---
검증 결과: Option A 상한이 적용되어 있습니다.
항목	기대값	main 컨테이너	subagent 컨테이너
CPU	6 (NanoCpus 6e9)	6000000000 ✓	6000000000 ✓
Memory	10g (10737418240)	10737418240 ✓	10737418240 ✓
PidsLimit	512	512 ✓	512 ✓
openclaw-sbx-agent-main-main-20ceb99b와 openclaw-sbx-agent-main-subagent-4b6231a4-... 둘 다 위 상한이 적용된 상태입니다.
오픈클로우가 도커안에서 작업중인가?

반은 호스트, 반은 Docker입니다.
구성 요소	어디서 도는지
Gateway	Windows 호스트 (Docker 밖)
Ollama(모델)	Windows 호스트
샌드박스(에이전트 작업)	Docker 컨테이너 안 (openclaw-sandbox:bookworm-slim)
정리하면, 에이전트가 하는 작업(exec, read, write, 파일 조작 등)은 전부 Docker 샌드박스 컨테이너 안에서 실행됩니다.
반대로 Gateway와 Ollama는 Docker 밖 Windows에서 돌고, Gateway가 Ollama에 요청 보내고 샌드박스 컨테이너에 도구 실행을 넘기는 구조입니다.
지금 OPEN CLAW 환경에 대해 보고

OpenClaw 환경 확인 중입니다.
docker ps --filter "name=openclaw-sbx" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
NAMES                                                    STATUS          IMAGE
openclaw-sbx-agent-main-subagent-4b6231a4-f07-d6c504cc   Up 12 minutes   openclaw-sandbox:bookworm-slim
openclaw-sbx-agent-main-main-20ceb99b                    Up 15 minutes   openclaw-sandbox:bookworm-slim
netstat -ano | findstr ":18789"
  TCP    127.0.0.1:18789        0.0.0.0:0              LISTENING       23196
  TCP    127.0.0.1:18789        127.0.0.1:55331        ESTABLISHED     23196
  TCP    127.0.0.1:55331        127.0.0.1:18789        ESTABLISHED     45040
  TCP    [::1]:18789            [::]:0                 LISTENING       23196
curl -s -o NUL -w "%{http_code}" http://127.0.0.1:11434/api/tags 2>NUL || echo "fail"
200
OpenClaw 환경 보고
1. 버전·메타
lastTouchedVersion: 2026.2.9
lastTouchedAt: 2026-02-12 18:45 UTC
2. 모델(Ollama)
항목	값
API	http://127.0.0.1:11434/v1
상태	응답 정상 (HTTP 200)
Primary	ollama/llama3.1:8b
Fallback	ollama/qwen2.5:7b-instruct
등록 모델	llama3.1:8b, qwen2.5:7b-instruct, exaone3.5:7.8b
Context	env OLLAMA_CONTEXT_LENGTH=8192
3. Gateway
항목	값
포트	18789
바인드	loopback (127.0.0.1)
인증	token
상태	LISTENING (PID 23196), 클라이언트 1개 연결됨
WebChat URL:
http://127.0.0.1:18789/?token=805eab611da933e638b0c07655c7ce87c49996ee808a0d2a
4. 샌드박스(Docker)
항목	값
이미지	openclaw-sandbox:bookworm-slim
모드	all
workspaceAccess	none
상한(Option A)	cpus: 6, memory: 10g, pidsLimit: 512
실행 중 컨테이너
이름	상태	이미지
openclaw-sbx-agent-main-main-20ceb99b	Up 15 min	openclaw-sandbox:bookworm-slim
openclaw-sbx-agent-main-subagent-4b6231a4-...	Up 12 min	openclaw-sandbox:bookworm-slim
5. 에이전트 기본값
workspace: C:\Users\jichu\.openclaw\workspace
maxConcurrent: 4
subagents.maxConcurrent: 8
compaction: safeguard
6. 도구
profile: coding
deny: group:web, group:ui, group:automation, group:nodes
elevated: disabled
sandbox 허용: sessions_, memory, message, image, exec, process, read, write, edit, apply_patch
7. 채널
Telegram: enabled (streamMode: partial, dmPolicy: allowlist)
8. 디렉터리 요약
설정: C:\Users\jichu\.openclaw\openclaw.json
에이전트/세션: agents\main\, sandboxes\
워크스페이스: workspace\
메모리 DB: memory\main.sqlite
요약: Gateway·Ollama 정상, 샌드박스 2개 실행 중, Option A 상한(6 CPU, 10GB, PID 512) 적용됨.
도커에서 사용중이 아닌가?

일부만 Docker에서 돌고 있어요.
구성요소	Docker 여부
Gateway (18789 포트)	❌ Windows 호스트
Ollama (모델)	❌ Windows 호스트
에이전트 샌드박스 (exec, read, write 등)	✅ Docker 컨테이너 안
그래서 “도커에서 사용 중이냐”고 하면, 에이전트가 실제로 명령 실행·파일 조작하는 부분은 Docker 안이고, Gateway랑 Ollama는 Docker 밖(Windows) 에서 도는 구조예요.
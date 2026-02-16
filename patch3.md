## 판정: 예(Go) — SSOT 4종 + docker-compose + queue 생성 스캐폴딩(완전 채움) 제공

## 근거: Ollama는 Docker에서 `11434` 포트/볼륨 패턴이 표준이고, `/api/generate`로 워커가 “Diff-only” 산출 가능하며, Compose는 GPU 예약 문법을 공식 지원 ([Ollama Documentation][1])

## 다음행동: 아래 **파일 트리 그대로 생성 → `scripts/init_queue.sh` 실행 → `docker compose up` → `scripts/submit_task.sh`로 첫 task 투입**

---

# Exec

* 이 스캐폴딩은 **OpenClaw(Worker)가 Ollama로부터 “패치 제안(diff)”만 생성**하고, **적용/테스트/커밋은 Cursor(Control-Plane)가 수행**하도록 강제한다.
* 기본값은 **DRY_RUN=1**(실제 적용 금지)이며, **Kill-switch( `.autodev_queue/STOP` )** 존재 시 즉시 중단한다.
* Ollama 컨테이너는 공식 이미지/포트/모델볼륨 패턴을 따른다. ([Ollama Documentation][1])
* 워커는 Ollama의 `/api/generate` 엔드포인트를 호출해 응답을 받는다. ([Ollama Documentation][2])
* GPU는 Compose에서 `deploy.resources.reservations.devices`로 예약한다. ([Docker Documentation][3])

---

# EN Sources (≤3)

* Docker Docs — Enable GPU support (Docker Compose). ([Docker Documentation][3])
* Ollama Docs — Docker. ([Ollama Documentation][1])
* Ollama Docs — API: Generate a response (`/api/generate`). ([Ollama Documentation][2])

---

# 설정 요약 표

| No | Item         | Value                                                          | Risk          | Evidence                    |
| -: | ------------ | -------------------------------------------------------------- | ------------- | --------------------------- |
|  1 | Queue 디렉토리   | `.autodev_queue/`                                              | 낮음(로컬 폴더)     | 내부 설계                       |
|  2 | SSOT 4종      | `.autodev_ssot/{MANIFEST,BATON_CURRENT,POLICY,AUDIT_SCHEMA}.…` | 낮음(정책 고정)     | 내부 설계                       |
|  3 | Ollama 포트    | `127.0.0.1:11434` 바인딩                                          | 중간(내부망 노출 시)  | ([Ollama Documentation][1]) |
|  4 | Ollama 모델 볼륨 | `ollama:/root/.ollama`                                         | 낮음(모델 지속)     | ([Ollama Documentation][1]) |
|  5 | LLM 호출       | `POST http://ollama:11434/api/generate`                        | 중간(프롬프트 유출)   | ([Ollama Documentation][2]) |
|  6 | GPU 예약       | `deploy.resources.reservations.devices`                        | 중간(호스트/툴킷 의존) | ([Docker Documentation][3]) |
|  7 | 적용 권한        | Cursor만 apply/test/commit                                      | 낮음(권한분리)      | 내부 설계                       |
|  8 | Kill-switch  | `.autodev_queue/STOP` 존재 시 워커 중단                               | 낮음            | 내부 설계                       |

---

# Options A/B/C (AED / Risk / Time)

* **Option A (권장, Loose-coupled)**: 파일큐 + 워커 폴링 + 수동 Gate

  * Cost: **0.00 AED**, Risk: **낮음**, Time: **1.00–2.00d**
* **Option B (Semi-auto)**: Cursor가 inbox 감시 + 자동 제안 + Gate 자동 리포트

  * Cost: **0.00 AED**, Risk: **중간**, Time: **3.00–5.00d**
* **Option C (Full agent)**: 이벤트 기반 + 자동 failover/pause + KPI 대시보드

  * Cost: **0.00 AED**, Risk: **높음**, Time: **7.00–14.00d**

---

# Steps (바로 실행 루트)

1. 아래 **파일 트리 생성/복사**
2. `scripts/init_queue.sh` 실행(큐 생성)
3. `docker compose up -d` 로 Ollama 기동
4. (선택) 워커 기동: `docker compose --profile worker up -d --build`
5. `scripts/submit_task.sh` 로 task 투입 → `.autodev_queue/work/`에 patch 생성 확인
6. Cursor에서 patch 검토 → Gate → `git apply` → 테스트 → 커밋/PR

---

# 파일 트리 (그대로 생성)

```text
.
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README_AUTODEV.md
├── .autodev_ssot
│   ├── MANIFEST.json
│   ├── BATON_CURRENT.md
│   ├── POLICY.md
│   └── AUDIT_SCHEMA.json
├── tasks
│   └── task_template.json
├── scripts
│   ├── init_queue.sh
│   ├── submit_task.sh
│   ├── gate_local.sh
│   └── summarize_audit.py
└── openclaw_worker
    ├── Dockerfile
    ├── requirements.txt
    ├── worker.py
    └── prompts
        └── patch_system.txt
```

---

# 파일 경로별 “완전 채움” 스캐폴딩

## 1) `docker-compose.yml`

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    ports:
      # 외부 노출 최소화(로컬호스트 바인딩)
      - "127.0.0.1:11434:11434"
    volumes:
      - ollama:/root/.ollama

    # GPU 예약 (NVIDIA Container Toolkit 필요)
    # Compose 공식 GPU 가이드 문법(Deploy spec의 devices) 사용
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  openclaw-worker:
    build:
      context: ./openclaw_worker
    container_name: openclaw-worker
    depends_on:
      - ollama
    restart: unless-stopped

    # 기본은 DRY_RUN=1 (repo 적용 금지)
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_MODEL=${OLLAMA_MODEL:-qwen2.5-coder:7b}
      - QUEUE_DIR=/queue
      - REPO_DIR=/repo
      - SSOT_DIR=/ssot
      - POLL_SECONDS=2
      - DRY_RUN=1
      - MAX_FILE_BYTES=120000
      - MAX_CONTEXT_FILES=8

    volumes:
      - ./.autodev_queue:/queue
      - ./.autodev_ssot:/ssot:ro
      - ./:/repo:ro

    # 컨테이너 자체는 read-only, /queue만 쓰기 허용(볼륨)
    read_only: true
    tmpfs:
      - /tmp

    security_opt:
      - no-new-privileges:true

    # 기본 compose up 시 워커가 자동으로 안 뜨게(선택 프로필)
    profiles: ["worker"]

volumes:
  ollama: {}
```

> 참고(사실 포인트): Ollama Docker 실행 예시는 `-p 11434:11434` 및 `-v ollama:/root/.ollama` 패턴을 사용한다. ([Ollama Documentation][1])
> 참고(사실 포인트): `/api/generate`는 모델/프롬프트 기반 생성 엔드포인트다. ([Ollama Documentation][2])
> 참고(사실 포인트): Compose에서 GPU는 Deploy spec의 devices로 지정한다. ([Docker Documentation][3])

---

## 2) `.env.example`

```bash
# 기본 모델(로컬에 pull 되어 있어야 함)
OLLAMA_MODEL=qwen2.5-coder:7b
```

---

## 3) `.gitignore`

```gitignore
# 런타임 큐(커밋 금지)
.autodev_queue/

# 로컬 env
.env
```

---

## 4) `README_AUTODEV.md`

```md
# Claude Code + Cursor + OpenClaw + Ollama (Queue-based) 스캐폴딩

## 목표
- OpenClaw Worker는 **패치(diff)만 생성**
- Cursor(Control-Plane)만 **apply/test/commit**
- Claude Code는 **작업 티켓(task.json) 생성**까지

## 빠른 시작
1) 큐 초기화
   - ./scripts/init_queue.sh

2) Ollama 기동
   - docker compose up -d

3) (선택) 워커 기동(빌드 포함)
   - docker compose --profile worker up -d --build

4) task 투입
   - ./scripts/submit_task.sh "./tasks/task_template.json"

5) 산출물 확인
   - .autodev_queue/work/*.patch
   - .autodev_queue/work/*.report.json

## Cursor에서 적용 절차(권장)
- patch 검토
- Gate 스크립트 실행: ./scripts/gate_local.sh <patch>
- git apply <patch>
- 테스트/린트
- commit/PR

## Kill-switch
- .autodev_queue/STOP 파일이 존재하면 워커는 즉시 중단하고, 들어온 task는 blocked로 이동.
```

---

## 5) `.autodev_ssot/MANIFEST.json`  ✅(SSOT 1/4)

```json
{
  "schema_version": "1.0.0",
  "project_name": "autodev-queue-controlplane",
  "stage_current": "PILOT",
  "stage_next": "BUILD",
  "paths": {
    "queue_dir": ".autodev_queue",
    "ssot_dir": ".autodev_ssot",
    "kill_switch": ".autodev_queue/STOP",
    "audit_events": ".autodev_queue/audit/events.ndjson"
  },
  "ollama": {
    "base_url_in_compose_network": "http://ollama:11434",
    "generate_endpoint": "/api/generate",
    "default_model": "qwen2.5-coder:7b"
  },
  "guardrails": {
    "dry_run_default": true,
    "repo_mount_readonly": true,
    "max_file_bytes": 120000,
    "max_context_files": 8,
    "require_unified_diff": true,
    "deny_paths_glob": [
      ".git/**",
      ".autodev_queue/**",
      ".autodev_ssot/**",
      "**/*.pem",
      "**/*.key"
    ]
  },
  "roles": {
    "claude_code": ["task_authoring", "prompt_authoring"],
    "cursor": ["apply_patch", "run_tests", "commit", "merge", "gate_decision"],
    "openclaw": ["read_repo", "propose_diff", "write_work_artifacts"],
    "ollama": ["local_llm_runtime"]
  },
  "audit": {
    "append_only": true,
    "hash_alg": "sha256"
  }
}
```

---

## 6) `.autodev_ssot/BATON_CURRENT.md` ✅(SSOT 2/4)

```md
# BATON_CURRENT (작업 계약 / 단일 세션 기준)

## 세션 ID
- SESSION_ID: 2026-02-15T00:00:00Z
- OWNER: MR.CHA (로컬)

## 역할 분리(변경 금지)
- Claude Code: 작업 티켓(task.json) 생성 및 요구사항 정리
- Cursor(Control-Plane): 리뷰/적용/테스트/커밋/PR/머지 “최종권한”
- OpenClaw(Worker): 패치(diff) 제안만 (repo 적용 금지)
- Ollama: 로컬 LLM 실행

## 목표(Goal)
- task.json 입력을 기반으로, OpenClaw가 **unified diff(.patch)** 와 **리포트(.report.json)** 를 산출한다.

## 산출물(Deliverables)
- `.autodev_queue/work/<task_id>.patch`
- `.autodev_queue/work/<task_id>.report.json`
- `.autodev_queue/audit/events.ndjson` 에 append-only 이벤트 추가

## 금지(Non-goals)
- OpenClaw가 repo 파일을 수정/커밋/푸시/머지하는 행위 금지
- 비밀정보(토큰/키/계정) 프롬프트/로그 반출 금지
- allowlist 밖 파일 변경 제안 금지(필요 시 NEED_INPUT로 반려)

## 안전장치(Safety)
- 기본 DRY_RUN=1
- Kill-switch: `.autodev_queue/STOP` 존재 시 즉시 중단
- Repo는 컨테이너에서 read-only 마운트
```

---

## 7) `.autodev_ssot/POLICY.md` ✅(SSOT 3/4)

```md
# POLICY (SSOT)

## 1) 권한 행렬
| Actor | Allowed | Forbidden |
|---|---|---|
| Claude Code | task.json 생성, 요구사항/성공조건 작성 | repo 적용/커밋/머지 |
| Cursor | apply/test/commit/PR/merge, gate decision | worker 역할(LLM patch 자동적용) |
| OpenClaw | repo read, diff 제안, 산출물 저장, audit 기록 | apply/commit/merge, 토큰 사용 |
| Ollama | 로컬 생성 응답 | 외부 전송/원격 업로드 |

## 2) Gate 규칙(필수)
- (G1) STOP 존재 → 즉시 FAIL
- (G2) allowlist 외 파일 touched → FAIL
- (G3) unified diff 형식 아님 → FAIL
- (G4) 리스크 플래그(키/토큰/자격증명 패턴 탐지) → FAIL
- (G5) 테스트 요구가 있는 task인데 테스트 증적 없으면 → FAIL 또는 NEED_INPUT

## 3) 산출물 규격
- patch: git apply 가능한 unified diff
- report: JSON (status, summary, files_touched, risks, next_actions)

## 4) 로그(append-only)
- 모든 주요 상태 전이(Submitted/Claimed/Proposed/Blocked/Done)는 NDJSON 이벤트로 기록
```

---

## 8) `.autodev_ssot/AUDIT_SCHEMA.json` ✅(SSOT 4/4)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "autodev_audit_event",
  "type": "object",
  "required": [
    "ts",
    "level",
    "actor",
    "action",
    "task_id",
    "repo_ref",
    "inputs_sha256",
    "outputs_sha256",
    "meta"
  ],
  "properties": {
    "ts": { "type": "string", "description": "RFC3339 timestamp" },
    "level": { "type": "string", "enum": ["INFO", "WARN", "ERROR"] },
    "actor": { "type": "string", "enum": ["claude_code", "cursor", "openclaw", "system"] },
    "action": {
      "type": "string",
      "enum": [
        "TASK_SUBMITTED",
        "TASK_CLAIMED",
        "PATCH_PROPOSED",
        "TASK_BLOCKED",
        "STOP_DETECTED",
        "ERROR"
      ]
    },
    "task_id": { "type": "string" },
    "repo_ref": { "type": "string", "description": "commit SHA or snapshot id" },
    "inputs_sha256": { "type": "string" },
    "outputs_sha256": { "type": "string" },
    "meta": { "type": "object", "additionalProperties": true }
  },
  "additionalProperties": false
}
```

---

## 9) `tasks/task_template.json`

```json
{
  "task_id": "T20260215-0001",
  "title": "예시: README 문구 개선(안전한 변경)",
  "goal": "README_AUTODEV.md의 '빠른 시작' 섹션을 더 명확하게 수정한다.",
  "scope": {
    "target_files": ["README_AUTODEV.md"],
    "allow_patch_on_files": ["README_AUTODEV.md"],
    "deny_paths_glob": [".git/**", ".autodev_queue/**", ".autodev_ssot/**"]
  },
  "requirements": {
    "output_format": "unified_diff",
    "must_not": ["secrets", "tokens", "keys"],
    "tests": []
  },
  "context": {
    "notes": "문서만 변경. 기능 변경 금지."
  },
  "meta": {
    "created_by": "claude_code",
    "created_at": "2026-02-15T00:00:00Z"
  }
}
```

---

## 10) `scripts/init_queue.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
Q="${ROOT}/.autodev_queue"

mkdir -p "${Q}"/{inbox,claimed,work,pr,done,blocked,audit}

# audit 로그(append-only)
touch "${Q}/audit/events.ndjson"

# 상태 설명
cat > "${Q}/README_QUEUE.md" <<'EOF'
# .autodev_queue
- inbox: 새 task.json 투입
- claimed: 워커가 claim한 task
- work: patch/report 산출물
- pr: Cursor가 PR 후보로 정리(선택)
- done: 완료
- blocked: STOP/검증실패/정보부족
- audit: events.ndjson (append-only)
- STOP: 존재하면 워커 즉시 중단
EOF

# 큐는 보통 커밋하지 않음(로컬 런타임)
touch "${Q}/.keep"

echo "[OK] Queue initialized at: ${Q}"
echo "      Kill-switch: ${Q}/STOP"
```

---

## 11) `scripts/submit_task.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
Q="${ROOT}/.autodev_queue"

if [[ ! -d "${Q}/inbox" ]]; then
  echo "[ERR] queue not initialized. run: ./scripts/init_queue.sh"
  exit 1
fi

SRC="${1:-}"
if [[ -z "${SRC}" || ! -f "${SRC}" ]]; then
  echo "[ERR] usage: ./scripts/submit_task.sh <task.json>"
  exit 1
fi

# 파일명 충돌 방지
TS="$(date -u +%Y%m%dT%H%M%SZ)"
BASENAME="$(basename "${SRC}")"
DST="${Q}/inbox/${TS}__${BASENAME}"

cp "${SRC}" "${DST}"
echo "[OK] submitted: ${DST}"
```

---

## 12) `scripts/gate_local.sh`  (Cursor에서 적용 전 체크)

```bash
#!/usr/bin/env bash
set -euo pipefail

PATCH="${1:-}"
if [[ -z "${PATCH}" || ! -f "${PATCH}" ]]; then
  echo "[ERR] usage: ./scripts/gate_local.sh <path_to_patch>"
  exit 1
fi

# 최소 검증: unified diff 헤더 존재 여부
if ! grep -qE '^\+\+\+ |^--- ' "${PATCH}"; then
  echo "[FAIL] not a unified diff (missing +++/--- lines)"
  exit 2
fi

# 위험 패턴(토큰/키) 간단 탐지: 필요 시 규칙 강화
if grep -qiE '(BEGIN PRIVATE KEY|AKIA|SECRET_KEY|api_key|token=)' "${PATCH}"; then
  echo "[FAIL] potential secret pattern detected"
  exit 3
fi

echo "[PASS] basic gate checks passed"
```

---

## 13) `scripts/summarize_audit.py`

```python
import json
from pathlib import Path
from collections import Counter

AUDIT = Path(".autodev_queue/audit/events.ndjson")

def main():
    if not AUDIT.exists():
        print("[ERR] audit file not found:", AUDIT)
        return

    actions = Counter()
    actors = Counter()
    levels = Counter()

    for line in AUDIT.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        ev = json.loads(line)
        actions[ev.get("action")] += 1
        actors[ev.get("actor")] += 1
        levels[ev.get("level")] += 1

    print("== actions ==")
    for k, v in actions.most_common():
        print(f"{k}: {v}")

    print("\n== actors ==")
    for k, v in actors.most_common():
        print(f"{k}: {v}")

    print("\n== levels ==")
    for k, v in levels.most_common():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()
```

---

## 14) `openclaw_worker/requirements.txt`

```txt
requests==2.32.3
```

---

## 15) `openclaw_worker/Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY worker.py /app/worker.py
COPY prompts /app/prompts

ENTRYPOINT ["python", "-u", "/app/worker.py"]
```

---

## 16) `openclaw_worker/prompts/patch_system.txt`

```text
당신은 OpenClaw Worker이다. 당신의 유일한 임무는 "git apply 가능한 unified diff 패치"를 제안하는 것이다.

규칙:
1) 절대 repo에 적용하지 말 것(패치 제안만).
2) allowlist에 포함된 파일만 수정할 것.
3) 결과는 반드시 아래 포맷을 따를 것(추가 텍스트 금지).

출력 포맷(엄수):
---BEGIN_PATCH---
(여기에 unified diff)
---END_PATCH---
---BEGIN_NOTES---
- 변경 요약(간단)
- 리스크(있으면)
- 다음 행동(테스트/검토)
---END_NOTES---

만약 요구사항을 만족할 수 없으면:
---BEGIN_PATCH---
# NEED_INPUT
---END_PATCH---
---BEGIN_NOTES---
- 왜 불가능한지
- 필요한 입력 1~3개
---END_NOTES---
```

---

## 17) `openclaw_worker/worker.py`

```python
import os
import json
import time
import hashlib
import shutil
from pathlib import Path
import requests
from datetime import datetime, timezone

def now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()

def safe_read_text(path: Path, max_bytes: int) -> str:
    data = path.read_bytes()
    return data[:max_bytes].decode("utf-8", errors="replace")

def write_ndjson(audit_file: Path, event: dict) -> None:
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    with audit_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

def load_ssot(ssot_dir: Path) -> dict:
    manifest = json.loads((ssot_dir / "MANIFEST.json").read_text(encoding="utf-8"))
    return manifest

def stop_detected(queue_dir: Path) -> bool:
    return (queue_dir / "STOP").exists()

def claim_one_task(queue_dir: Path) -> Path | None:
    inbox = queue_dir / "inbox"
    claimed = queue_dir / "claimed"
    inbox.mkdir(parents=True, exist_ok=True)
    claimed.mkdir(parents=True, exist_ok=True)

    # 오래된 것부터 처리
    tasks = sorted(inbox.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not tasks:
        return None

    src = tasks[0]
    dst = claimed / src.name
    try:
        src.rename(dst)
        return dst
    except Exception:
        return None

def build_prompt(system_prompt: str, task: dict, repo_dir: Path, max_files: int, max_file_bytes: int) -> str:
    scope = task.get("scope", {})
    target_files = scope.get("target_files", [])
    allow_patch = set(scope.get("allow_patch_on_files", []))

    # 컨텍스트 파일: target_files에서 max_files개만
    ctx_files = []
    for rel in target_files[:max_files]:
        p = repo_dir / rel
        if p.exists() and p.is_file():
            ctx_files.append(rel)

    parts = []
    parts.append(system_prompt.strip())
    parts.append("\n[task_json]\n" + json.dumps(task, ensure_ascii=False, indent=2))
    parts.append("\n[repo_context]\n")

    for rel in ctx_files:
        p = repo_dir / rel
        content = safe_read_text(p, max_file_bytes)
        parts.append(f"\n---FILE:{rel}---\n{content}\n---END_FILE---\n")

    parts.append("\n[constraints]\n")
    parts.append(f"- allow_patch_on_files: {sorted(list(allow_patch))}\n")
    parts.append("- 반드시 allowlist 파일만 수정하고 unified diff로 출력할 것.\n")

    return "\n".join(parts)

def call_ollama_generate(base_url: str, model: str, prompt: str) -> str:
    url = base_url.rstrip("/") + "/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    r = requests.post(url, json=payload, timeout=600)
    r.raise_for_status()
    data = r.json()
    # Ollama /api/generate 응답에는 response 필드가 포함된다(일반적 사용 패턴).
    # 여기서는 방어적으로 가져온다.
    return data.get("response", "")

def extract_blocks(text: str) -> tuple[str, str]:
    def between(a: str, b: str) -> str:
        if a not in text or b not in text:
            return ""
        return text.split(a, 1)[1].split(b, 1)[0].strip("\n")

    patch = between("---BEGIN_PATCH---", "---END_PATCH---")
    notes = between("---BEGIN_NOTES---", "---END_NOTES---")
    return patch, notes

def main():
    queue_dir = Path(os.getenv("QUEUE_DIR", "/queue"))
    repo_dir = Path(os.getenv("REPO_DIR", "/repo"))
    ssot_dir = Path(os.getenv("SSOT_DIR", "/ssot"))
    poll_seconds = int(os.getenv("POLL_SECONDS", "2"))
    dry_run = os.getenv("DRY_RUN", "1") == "1"

    max_file_bytes = int(os.getenv("MAX_FILE_BYTES", "120000"))
    max_context_files = int(os.getenv("MAX_CONTEXT_FILES", "8"))

    base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

    # 파일 경로(고정)
    audit_file = queue_dir / "audit" / "events.ndjson"
    work_dir = queue_dir / "work"
    blocked_dir = queue_dir / "blocked"
    work_dir.mkdir(parents=True, exist_ok=True)
    blocked_dir.mkdir(parents=True, exist_ok=True)

    system_prompt_path = Path("/app/prompts/patch_system.txt")
    system_prompt = system_prompt_path.read_text(encoding="utf-8")

    manifest = load_ssot(ssot_dir)
    repo_ref = "UNKNOWN"  # 필요 시 Cursor가 커밋 SHA를 task에 주입 권장

    while True:
        if stop_detected(queue_dir):
            write_ndjson(audit_file, {
                "ts": now_rfc3339(),
                "level": "WARN",
                "actor": "system",
                "action": "STOP_DETECTED",
                "task_id": "-",
                "repo_ref": repo_ref,
                "inputs_sha256": sha256_text("STOP"),
                "outputs_sha256": sha256_text("STOP"),
                "meta": {"note": "Kill-switch file exists. Worker is idling."}
            })
            time.sleep(max(poll_seconds, 5))
            continue

        task_path = claim_one_task(queue_dir)
        if task_path is None:
            time.sleep(poll_seconds)
            continue

        # task 로드
        try:
            task = json.loads(task_path.read_text(encoding="utf-8"))
        except Exception as e:
            # 파싱 실패는 blocked로
            dst = blocked_dir / task_path.name
            shutil.move(str(task_path), str(dst))
            write_ndjson(audit_file, {
                "ts": now_rfc3339(),
                "level": "ERROR",
                "actor": "openclaw",
                "action": "TASK_BLOCKED",
                "task_id": "UNKNOWN",
                "repo_ref": repo_ref,
                "inputs_sha256": sha256_text(str(e)),
                "outputs_sha256": sha256_text("blocked"),
                "meta": {"reason": "invalid_json", "error": str(e), "path": dst.as_posix()}
            })
            continue

        task_id = task.get("task_id", Path(task_path.name).stem)

        # audit: claimed
        write_ndjson(audit_file, {
            "ts": now_rfc3339(),
            "level": "INFO",
            "actor": "openclaw",
            "action": "TASK_CLAIMED",
            "task_id": task_id,
            "repo_ref": repo_ref,
            "inputs_sha256": sha256_text(task_path.read_text(encoding="utf-8")),
            "outputs_sha256": sha256_text("claimed"),
            "meta": {"dry_run": dry_run, "model": model}
        })

        # prompt 구성
        prompt = build_prompt(
            system_prompt=system_prompt,
            task=task,
            repo_dir=repo_dir,
            max_files=max_context_files,
            max_file_bytes=max_file_bytes
        )

        prompt_hash = sha256_text(prompt)

        # LLM 호출
        try:
            llm_text = call_ollama_generate(base_url=base_url, model=model, prompt=prompt)
        except Exception as e:
            dst = blocked_dir / f"{task_id}.json"
            shutil.move(str(task_path), str(dst))
            write_ndjson(audit_file, {
                "ts": now_rfc3339(),
                "level": "ERROR",
                "actor": "openclaw",
                "action": "ERROR",
                "task_id": task_id,
                "repo_ref": repo_ref,
                "inputs_sha256": prompt_hash,
                "outputs_sha256": sha256_text(str(e)),
                "meta": {"reason": "ollama_call_failed", "error": str(e)}
            })
            continue

        patch, notes = extract_blocks(llm_text)

        status = "PROPOSED"
        if patch.strip().startswith("# NEED_INPUT") or patch.strip() == "":
            status = "NEED_INPUT"

        patch_path = work_dir / f"{task_id}.patch"
        report_path = work_dir / f"{task_id}.report.json"

        # DRY_RUN이라도 산출물은 생성(적용은 Cursor가 수행)
        patch_path.write_text(patch + "\n", encoding="utf-8")
        report = {
            "task_id": task_id,
            "status": status,
            "model": model,
            "dry_run": dry_run,
            "summary": notes.strip(),
            "artifacts": {
                "patch": patch_path.as_posix()
            },
            "next_actions": [
                "Cursor에서 patch 검토",
                "Gate 실행: scripts/gate_local.sh",
                "git apply 후 테스트/커밋"
            ],
            "ssot": {
                "schema_version": manifest.get("schema_version"),
                "guardrails": manifest.get("guardrails", {})
            }
        }
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        # audit: patch proposed
        outputs_hash = sha256_text((patch or "") + "\n" + (notes or ""))
        write_ndjson(audit_file, {
            "ts": now_rfc3339(),
            "level": "INFO" if status == "PROPOSED" else "WARN",
            "actor": "openclaw",
            "action": "PATCH_PROPOSED",
            "task_id": task_id,
            "repo_ref": repo_ref,
            "inputs_sha256": prompt_hash,
            "outputs_sha256": outputs_hash,
            "meta": {"status": status, "patch_path": patch_path.as_posix(), "report_path": report_path.as_posix()}
        })

        # 처리 완료: claimed task 파일은 done으로 옮겨도 되지만, 여기서는 감사 목적으로 work에 report만 두고 claimed에 남김
        # 필요 시 Cursor가 claimed를 done으로 이동하도록 운영규칙화 권장.

        time.sleep(0.2)

if __name__ == "__main__":
    main()
```

---

# cmd3 (바로 쓰는 3개 명령)

```bash
chmod +x ./scripts/init_queue.sh ./scripts/submit_task.sh ./scripts/gate_local.sh
./scripts/init_queue.sh
docker compose up -d && docker compose --profile worker up -d --build
```

---

# ZERO log (중단 템플릿)

| 단계 | 이유                                  | 위험          | Input Required(≤3)                                                                | 다음조치                               |
| -- | ----------------------------------- | ----------- | --------------------------------------------------------------------------------- | ---------------------------------- |
| 실행 | GPU/Compose/툴킷 불일치 또는 워커가 patch 미생성 | 운영 중단/시간 손실 | 1) OS(Win/Ubuntu) 2) `docker version`/`docker compose version` 3) `nvidia-smi` 결과 | Option A로 CPU-only 전환 또는 GPU 문법 분기 |

---

원하면, 다음 단계로 **“Cursor 전용 Gate 강화(allowlist 경로검증 + touched files 파싱 + 테스트 증적 첨부)”**까지 붙여서 **Gate FAIL 원인별 자동 분류**(audit 기반) 스캐폴딩도 바로 확장해 드립니다.

[1]: https://docs.ollama.com/docker?utm_source=chatgpt.com "Docker"
[2]: https://docs.ollama.com/api/generate?utm_source=chatgpt.com "Generate a response"
[3]: https://docs.docker.com/compose/how-tos/gpu-support/?utm_source=chatgpt.com "Enable GPU support - Docker Compose"

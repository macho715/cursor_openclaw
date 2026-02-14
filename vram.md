여러 작업(컨테이너·로컬 툴·WSL2)이 한 노트북 GPU/디스크를 동시에 잡아먹어 “연쇄 다운(크래시 캐스케이드)” 나는 걸 막는 **개발PC/WSL2 안전 러닝 아키텍처**를 제안드려요. 핵심은 “모델은 단 한 프로세스가 독점” + “나머지는 엄격한 쿼터와 감시자” 입니다.

---

# 왜 이렇게 구성하나요?

* **VRAM 고갈·GPU hang 방지:** 여러 컨테이너가 모델을 각자 로드하면 바로 폭주합니다 → **단일 모델 서버**가 GPU 메모리의 “단일 소유자”가 되게 합니다. ([NVIDIA Docs][1])
* **리소스 폭주 차단:** 컨테이너는 기본 무제한입니다. CPU/RAM 한도 안 걸면 호스트 전체를 굶깁니다. ([Docker Documentation][2])
* **Windows/WSL 제한 고려:** Windows 컨테이너는 `--cpuset-cpus` 등 하드 핀닝이 제한/미구현 이슈가 있습니다(대안: affinity). ([Docker Community Forums][3])
* **NVML/WSL 특이점:** WSL2에서 NVML 호출 일부가 불안정할 수 있어 우회 환경변수로 진단/감시가 필요합니다. ([GitHub][4])

---

# 권장 아키텍처 (간단)

* **OpenClaw 모델 러너(단일 GPU 소유자)**: 호스트 또는 전용 WSL2 배포판에 서비스로 실행, `localhost:50051`(HTTP/gRPC) 공개. WSL2에서 CUDA 드라이버/도구체인은 가이드에 따라 설치·검증합니다(`nvidia-smi`). ([NVIDIA Docs][1])
* **도커화된 헬퍼(ingest/컨버터/UI)**: 전부 **CPU/RAM 쿼터** 강제, 스토리지는 별도 볼륨. OpenClaw와는 `localhost` API로 통신. ([Docker Documentation][2])
* **스토리지 분리**: 무거운 R/W는 별도 NVMe/파티션으로 분리(시스템 디스크와 분리).
* **워치독(감시자)**: `nvidia-smi`/NVML 주기 폴링→ 임계치 초과 시 소음 컨테이너 `pause/stop` 및 감사 로그.

---

# 바로 쓰는 스니펫

**1) 헬퍼 컨테이너 쿼터 실행**

```bash
docker run --name helper \
  --cpus="1.5" --memory="2g" --memory-swap="2g" \
  -v openclaw-data:/data helper-image
```

(도커 기본은 무제한 → CPU/RAM 반드시 제한) ([Docker Documentation][2])

**2) I/O 소음 억제(지원 환경 한정)**

```bash
docker run --name io-helper \
  --blkio-weight-device "/dev/nvme0n1:300" io-image
```

(커널/플랫폼에 따라 효과 제한·폐기 옵션 전환 가능. 실제 호스트에서 지원 여부 확인) ([Docker Documentation][5])

**3) Windows 호스트 프로세스 CPU 친화도(대안)**

```powershell
$p = Start-Process 'C:\openclaw\openclaw.exe' -PassThru
Start-Sleep -Seconds 1
$proc = Get-Process -Id $p.Id
$proc.ProcessorAffinity = 0x0F    # CPU 0-3에 고정
```

(Windows 컨테이너의 cpuset 제약 이슈를 우회) ([Docker Community Forums][3])

**4) WSL2 CUDA 설치/검증 체크**

* Windows에 **WSL용 CUDA 드라이버** 설치 → WSL2 리눅스 내부에서 CUDA 툴킷 설치 → `nvidia-smi`로 확인. ([Microsoft Learn][6])

**5) NVML 워치독(로직 개요)**

```bash
# 5초마다 GPU 메모리/Util 체크 → N회 연속 95%↑면 소음 컨테이너 중단
while true; do
  read mem util <<<"$(nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits)"
  # ...임계치 판단 → docker pause/stop 대상 결정...
  sleep 5
done
```

(WSL2 NVML 오류 시 가해 프로세스에 `DALI_DISABLE_NVML=1`로 우회 수집 병행) ([GitHub][4])

**6) 실시간 모니터링**

```bash
docker stats   # 컨테이너별 CPU/메모리/네트워크/IO 확인
```

([Docker][7])

---

# 운영 체크리스트 (요약)

1. **단일 모델 호스트 결정**(호스트 vs 전용 WSL 배포판) 및 CUDA/드라이버 설치·검증. ([NVIDIA Docs][1])
2. **OpenClaw**를 단독 GPU 소유자로 배치(헬스엔드포인트 포함).
3. **모든 헬퍼 컨테이너에 `--cpus`/`--memory` 강제**, `docker stats`로 확인. ([Docker Documentation][2])
4. **무거운 볼륨은 별도 NVMe/파티션**으로 마운트.
5. **워치독 배치**: GPU 95%↑/VRAM 95%↑ N회 지속 시 offending 컨테이너 `pause/stop`+감사로그.
6. **Windows 한계 우회**: 필요한 경우 **호스트 프로세스 affinity**를 병행(컨테이너 cpuset 제약 이슈). ([Docker Community Forums][3])

---

# 주의·리스크

* 다중 컨테이너가 대형 모델을 **각자 로드** → VRAM 즉시 고갈/장애 → **단일 모델 서버 패턴으로 회피**. ([NVIDIA Docs][1])
* `--blkio-weight*`은 **플랫폼/커널 의존**(cgroup v2에서는 `io.weight`, 일부 환경에선 비효과/폐기) → **물리 디스크 분리**를 기본 전략으로. ([Docker Documentation][8])
* **NVML/WSL2** 불안정 사례 존재 → 오류 처리·우회 플래그 병행. ([GitHub][4])

---

필요하시면, **RTX 4060(8GB VRAM) 기준 OpenClaw+Ollama 조합 최적 preset(컨텍스트·배치·KV‑캐시·온디맨드 로드)**까지 바로 적용 가능한 `docker-compose`/PowerShell 템플릿으로 정리해 드릴게요.

[1]: https://docs.nvidia.com/cuda/wsl-user-guide/index.html?utm_source=chatgpt.com "CUDA on WSL User Guide"
[2]: https://docs.docker.com/engine/containers/resource_constraints/?utm_source=chatgpt.com "Resource constraints"
[3]: https://forums.docker.com/t/container-affinity-for-windows/75966?utm_source=chatgpt.com "Container affinity for Windows?"
[4]: https://github.com/NVIDIA/DALI/issues/2921?utm_source=chatgpt.com "A nvml internal driver error occured (on WSL2) · Issue #2921"
[5]: https://docs.docker.com/engine/containers/run/?utm_source=chatgpt.com "Running containers | Docker Docs"
[6]: https://learn.microsoft.com/en-us/windows/ai/directml/gpu-cuda-in-wsl?utm_source=chatgpt.com "Enable NVIDIA CUDA on WSL 2"
[7]: https://www.docker.com/blog/how-to-monitor-container-memory-and-cpu-usage-in-docker-desktop/?utm_source=chatgpt.com "How to Use the Resource Usage Docker Extension"
[8]: https://docs.docker.com/engine/deprecated/?utm_source=chatgpt.com "Deprecated Docker Engine features"
판정: **조건부(Go)**
근거: **⚠️AMBER:[가정]** Ollama/OpenClaw가 **HTTP health endpoint** 제공, WhatsApp은 **비공식 web session(whatsapp-web.js)** 방식(QR 1회 필요) 전제
다음행동: 아래 **파일 트리 그대로 생성 → `docker compose up -d` → Grafana 대시보드 접속(3000)**

---

## 0) 권장 파일 트리(SSOT)

```text
stack/
  docker-compose.yml
  .env
  prometheus/
    prometheus.yml
  grafana/
    provisioning/
      datasources/
        datasource.yml
      dashboards/
        dashboards.yml
    dashboards/
      kpi.json   # (선택) import용
  scripts/
    healthcheck.ps1
    restart_on_unhealthy.ps1
    healthcheck.sh
```

---

## 1) `.env` (토큰/키는 여기만)

```bash
# Ollama
OLLAMA_PORT=11434

# OpenClaw
OPENCLAW_PORT=50051
OPENCLAW_HTTP_PORT=8088

# Telegram
TG_BOT_TOKEN=REPLACE_ME
TG_ALLOWED_CHAT_IDS=REPLACE_ME   # "123,456" 형태

# WhatsApp (whatsapp-web.js 방식)
WA_CLIENT_ID=hvdc-wa
WA_ALLOWED_NUMBERS=REPLACE_ME    # "9715xxxx,9715yyyy"

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASS=admin
```

---

## 2) `docker-compose.yml` (Ollama + OpenClaw + Ingestion + KPI 대시보드)

> 핵심: **GPU는 Ollama만**, OpenClaw/ingestion은 **CPU/RAM 제한** + **healthcheck** + **restart unless-stopped**

```yaml
version: "3.9"

networks:
  llmnet:

volumes:
  ollama-data:
  openclaw-data:
  tg-data:
  wa-session:
  prometheus-data:
  grafana-data:

services:
  # 1) Ollama (GPU 단독 소유)
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    ports:
      - "${OLLAMA_PORT}:11434"
    environment:
      - NVIDIA_VISIBLE_DEVICES=0
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
    volumes:
      - ollama-data:/root/.ollama
    networks: [llmnet]
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://localhost:11434/api/tags >/dev/null 2>&1 || exit 1"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 20s

  # 2) OpenClaw (Ollama로만 호출, GPU 금지)
  openclaw:
    image: openclaw:latest
    container_name: openclaw
    restart: unless-stopped
    depends_on:
      ollama:
        condition: service_healthy
    ports:
      - "${OPENCLAW_PORT}:50051"
      - "${OPENCLAW_HTTP_PORT}:8088"   # /healthz 같은 HTTP health용
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_MODEL=exaone3.5:7.8b
      - OLLAMA_CONTEXT_LENGTH=8192
    deploy:
      resources:
        limits:
          cpus: "2.00"
          memory: 4g
    volumes:
      - openclaw-data:/data
    networks: [llmnet]
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://localhost:8088/healthz >/dev/null 2>&1 || exit 1"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 20s

  # 3) Telegram ingestion (예: bot polling → OpenClaw endpoint)
  tg-ingest:
    image: hvdc/tg-ingest:latest
    container_name: tg-ingest
    restart: unless-stopped
    depends_on:
      openclaw:
        condition: service_healthy
    environment:
      - TG_BOT_TOKEN=${TG_BOT_TOKEN}
      - TG_ALLOWED_CHAT_IDS=${TG_ALLOWED_CHAT_IDS}
      - OPENCLAW_HTTP=http://openclaw:8088
    deploy:
      resources:
        limits:
          cpus: "1.00"
          memory: 1g
    volumes:
      - tg-data:/data
    networks: [llmnet]
    healthcheck:
      test: ["CMD-SHELL", "test -f /data/ok || exit 1"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 20s

  # 4) WhatsApp ingestion (whatsapp-web.js 방식: QR 1회 필요)
  wa-ingest:
    image: hvdc/wa-ingest:latest
    container_name: wa-ingest
    restart: unless-stopped
    depends_on:
      openclaw:
        condition: service_healthy
    environment:
      - WA_CLIENT_ID=${WA_CLIENT_ID}
      - WA_ALLOWED_NUMBERS=${WA_ALLOWED_NUMBERS}
      - OPENCLAW_HTTP=http://openclaw:8088
    deploy:
      resources:
        limits:
          cpus: "1.00"
          memory: 1g
    volumes:
      - wa-session:/wa/session
    networks: [llmnet]
    healthcheck:
      test: ["CMD-SHELL", "test -f /wa/session/ready || exit 1"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 60s

  # 5) KPI 모니터링: Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks: [llmnet]

  # 6) Grafana (대시보드)
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_ADMIN_USER}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASS}
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
    ports:
      - "3000:3000"
    networks: [llmnet]

  # 7) cAdvisor (컨테이너 CPU/RAM/IO)
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:rw
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    networks: [llmnet]

  # 8) Node Exporter (호스트/WSL2 리눅스 메트릭)
  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    restart: unless-stopped
    ports:
      - "9100:9100"
    networks: [llmnet]

  # 9) GPU Exporter (NVIDIA DCGM Exporter)
  dcgm-exporter:
    image: nvidia/dcgm-exporter:latest
    container_name: dcgm-exporter
    restart: unless-stopped
    environment:
      - NVIDIA_VISIBLE_DEVICES=0
      - NVIDIA_DRIVER_CAPABILITIES=utility
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
    ports:
      - "9400:9400"
    networks: [llmnet]
```

---

## 3) `prometheus/prometheus.yml` (GPU+CPU 통합 수집)

```yaml
global:
  scrape_interval: 10s
  evaluation_interval: 10s

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["prometheus:9090"]

  - job_name: "cadvisor"
    static_configs:
      - targets: ["cadvisor:8080"]

  - job_name: "node"
    static_configs:
      - targets: ["node-exporter:9100"]

  - job_name: "gpu"
    static_configs:
      - targets: ["dcgm-exporter:9400"]

  - job_name: "ollama"
    metrics_path: "/metrics"
    static_configs:
      - targets: ["ollama:11434"]

  - job_name: "openclaw"
    metrics_path: "/metrics"
    static_configs:
      - targets: ["openclaw:8088"]
```

> ⚠️AMBER:[가정] `ollama/openclaw`가 `/metrics` 제공 안 하면, Prometheus 타겟에서 제거하고 **dcgm/cadvisor/node**만으로도 KPI 구성 가능.

---

## 4) Grafana 프로비저닝(자동 데이터소스/대시보드)

### `grafana/provisioning/datasources/datasource.yml`

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

### `grafana/provisioning/dashboards/dashboards.yml`

```yaml
apiVersion: 1
providers:
  - name: "HVDC-KPI"
    orgId: 1
    folder: "HVDC"
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /var/lib/grafana/dashboards
```

---

## 5) Auto-Restart & Healthcheck (PowerShell)

### 5.1 `scripts/healthcheck.ps1` (상태 요약)

```powershell
$services = @("ollama","openclaw","tg-ingest","wa-ingest","prometheus","grafana","cadvisor","node-exporter","dcgm-exporter")

Write-Host "=== Container Health Summary ==="
foreach ($s in $services) {
  $id = docker ps -aqf "name=^/$s$"
  if (-not $id) { Write-Host "$s : NOT FOUND"; continue }

  $st = docker inspect -f '{{.State.Status}}' $id
  $hl = docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' $id
  Write-Host ("{0,-14} : {1,-10} / {2}" -f $s, $st, $hl)
}
```

### 5.2 `scripts/restart_on_unhealthy.ps1` (unhealthy면 재시작)

```powershell
$targets = @("openclaw","tg-ingest","wa-ingest")
while ($true) {
  foreach ($t in $targets) {
    $id = docker ps -aqf "name=^/$t$"
    if (-not $id) { continue }

    $hl = docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' $id
    if ($hl -eq "unhealthy") {
      Write-Host "RESTART: $t is unhealthy"
      docker restart $t | Out-Null
    }
  }
  Start-Sleep -Seconds 15
}
```

---

## 6) Auto-Restart & Healthcheck (bash, WSL용)

### `scripts/healthcheck.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
services=(ollama openclaw tg-ingest wa-ingest prometheus grafana cadvisor node-exporter dcgm-exporter)

echo "=== Container Health Summary ==="
for s in "${services[@]}"; do
  id="$(docker ps -aqf "name=^/${s}$" || true)"
  if [[ -z "$id" ]]; then echo "$s : NOT FOUND"; continue; fi
  st="$(docker inspect -f '{{.State.Status}}' "$id")"
  hl="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$id")"
  printf "%-14s : %-10s / %s\n" "$s" "$st" "$hl"
done
```

---

## 7) KPI 대시보드에서 바로 보고 싶은 지표(추천)

| No | Item                     |              Value | Risk     | Evidence           |
| -: | ------------------------ | -----------------: | -------- | ------------------ |
|  1 | GPU VRAM 사용률(%)          |         목표 ≤ 90.00 | OOM/응답지연 | dcgm-exporter      |
|  2 | GPU Util(%)              |         목표 ≤ 95.00 | hang     | dcgm-exporter      |
|  3 | 컨테이너 메모리(GB)             | helper ≤ 1.00~2.00 | host 압박  | cAdvisor           |
|  4 | OpenClaw p95 latency(ms) |        목표 ≤ 800.00 | UX 저하    | (가정) /metrics      |
|  5 | 재시작 횟수(count)            |            목표 0.00 | 불안정      | docker events/Prom |

---

## Options (A/B/C)

* **A) 최소 안정형(권장)**: `dcgm + cadvisor + prometheus + grafana`만 KPI

  * Pros: 구현 쉬움, 즉시 가시성
  * Cons: app-level(p95, QPS) 부족
  * Time: 0.50~1.00h

* **B) 표준형**: A + OpenClaw `/metrics` 추가(요청수/latency)

  * Pros: 운영 KPI 완성도 상승
  * Cons: OpenClaw 코드/설정 필요
  * Time: 1.00~2.00h

* **C) 강화형**: B + 알림(예: TG webhook) + 자동 pause(소음 컨테이너)

  * Pros: 장애 전파 차단
  * Cons: 정책 튜닝 필요
  * Time: 2.00~4.00h

---

## 실행 명령(3개)

```bash
cd stack
docker compose up -d
docker compose ps
```

(Windows PowerShell)

```powershell
cd stack
docker compose up -d
pwsh .\scripts\healthcheck.ps1
```

---

## ZERO(중단) 필요 조건(딱 3개)

| 단계  | 이유                          | 위험          | 요청데이터                       | 다음조치            |
| --- | --------------------------- | ----------- | --------------------------- | --------------- |
| 배포  | OpenClaw health endpoint 없음 | 자동복구 실패     | `GET /healthz` 또는 health 명령 | healthcheck 수정  |
| KPI | GPU exporter 미동작            | VRAM 가시성 없음 | `dcgm-exporter` 로그          | toolkit/권한 점검   |
| WA  | WhatsApp 정책/인증 경로 불명확       | 계정 제한/세션 끊김 | 사용 방식(공식/비공식)               | ingestion 방식 확정 |

---

원하면, 다음을 **바로 붙여 넣을 수 있게** 추가로 드립니다(요청만 주면 됨):

1. `hvdc/tg-ingest` / `hvdc/wa-ingest` **Dockerfile + 최소 Node 앱 코드**(polling → OpenClaw POST)
2. Grafana `kpi.json`(GPU VRAM/Util + 컨테이너 CPU/RAM + 재시작 카운트) 기본 대시보드 1장
3. “GPU 95% 3회 연속 → tg-ingest/wa-ingest 자동 pause” 룰까지 포함한 운영 스크립트
판정: **조건부(Go)**
근거: **⚠️AMBER:[가정]** OpenClaw가 `POST /ingest`(또는 유사) **HTTP 수집 엔드포인트**를 제공한다는 전제(없으면 경로만 바꾸면 됨)
다음행동: 아래 파일을 `stack/`에 추가 → `docker compose build tg-ingest wa-ingest && docker compose up -d` → Grafana에서 `kpi.json` Import

---

# 1) `hvdc/tg-ingest` (Dockerfile + 최소 Node 코드)

## 1.1 폴더

```text
stack/ingest/tg/
  Dockerfile
  package.json
  index.js
```

## 1.2 `stack/ingest/tg/Dockerfile`

```dockerfile
FROM node:20-alpine

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev || npm i --omit=dev

COPY index.js ./

# healthcheck용 상태 파일
RUN mkdir -p /data
VOLUME ["/data"]

ENV NODE_ENV=production
CMD ["node", "index.js"]
```

## 1.3 `stack/ingest/tg/package.json`

```json
{
  "name": "hvdc-tg-ingest",
  "version": "0.1.0",
  "main": "index.js",
  "type": "module",
  "dependencies": {
    "axios": "^1.7.9",
    "node-telegram-bot-api": "^0.66.0"
  }
}
```

## 1.4 `stack/ingest/tg/index.js`

```js
import fs from "node:fs";
import path from "node:path";
import axios from "axios";
import TelegramBot from "node-telegram-bot-api";

const TG_BOT_TOKEN = process.env.TG_BOT_TOKEN;
const TG_ALLOWED_CHAT_IDS = (process.env.TG_ALLOWED_CHAT_IDS || "")
  .split(",")
  .map(s => s.trim())
  .filter(Boolean);

const OPENCLAW_HTTP = process.env.OPENCLAW_HTTP || "http://openclaw:8088";
const OPENCLAW_INGEST_PATH = process.env.OPENCLAW_INGEST_PATH || "/ingest"; // ⚠️가정
const OK_FILE = process.env.OK_FILE || "/data/ok";

if (!TG_BOT_TOKEN) {
  console.error("Missing TG_BOT_TOKEN");
  process.exit(1);
}

const bot = new TelegramBot(TG_BOT_TOKEN, { polling: true });

function isAllowed(chatId) {
  if (TG_ALLOWED_CHAT_IDS.length === 0) return true; // 비워두면 전체 허용(운영에서는 권장X)
  return TG_ALLOWED_CHAT_IDS.includes(String(chatId));
}

async function postToOpenClaw(payload) {
  const url = `${OPENCLAW_HTTP}${OPENCLAW_INGEST_PATH}`;
  await axios.post(url, payload, { timeout: 8000 });
}

bot.on("message", async (msg) => {
  try {
    const chatId = msg.chat?.id;
    if (!isAllowed(chatId)) return;

    const text = msg.text || msg.caption || "";
    if (!text) return;

    const payload = {
      source: "telegram",
      ts: new Date(msg.date * 1000).toISOString(),
      chat_id: String(chatId),
      user: msg.from?.username || msg.from?.first_name || "unknown",
      text,
      meta: {
        message_id: msg.message_id,
        chat_type: msg.chat?.type
      }
    };

    await postToOpenClaw(payload);

    // health mark (컨테이너 기동 및 루프 정상 동작)
    fs.mkdirSync(path.dirname(OK_FILE), { recursive: true });
    fs.writeFileSync(OK_FILE, "ok");

  } catch (e) {
    console.error("TG ingest error:", e?.message || e);
  }
});

console.log("TG ingest started (polling).");
```

---

# 2) `hvdc/wa-ingest` (Dockerfile + 최소 Node 코드)

## 2.1 폴더

```text
stack/ingest/wa/
  Dockerfile
  package.json
  index.js
```

## 2.2 `stack/ingest/wa/Dockerfile`

```dockerfile
FROM node:20-alpine

WORKDIR /app

# whatsapp-web.js는 chromium 필요
RUN apk add --no-cache chromium nss freetype harfbuzz ca-certificates ttf-freefont

ENV PUPPETEER_SKIP_DOWNLOAD=true
ENV CHROME_BIN=/usr/bin/chromium-browser

COPY package.json package-lock.json* ./
RUN npm ci --omit=dev || npm i --omit=dev

COPY index.js ./

RUN mkdir -p /wa/session
VOLUME ["/wa/session"]

ENV NODE_ENV=production
CMD ["node", "index.js"]
```

## 2.3 `stack/ingest/wa/package.json`

```json
{
  "name": "hvdc-wa-ingest",
  "version": "0.1.0",
  "main": "index.js",
  "type": "module",
  "dependencies": {
    "axios": "^1.7.9",
    "qrcode-terminal": "^0.12.0",
    "whatsapp-web.js": "^1.26.0"
  }
}
```

## 2.4 `stack/ingest/wa/index.js`

```js
import fs from "node:fs";
import path from "node:path";
import axios from "axios";
import qrcode from "qrcode-terminal";
import { Client, LocalAuth } from "whatsapp-web.js";

const WA_CLIENT_ID = process.env.WA_CLIENT_ID || "hvdc-wa";
const WA_ALLOWED_NUMBERS = (process.env.WA_ALLOWED_NUMBERS || "")
  .split(",")
  .map(s => s.trim().replace(/\s/g, ""))
  .filter(Boolean);

const OPENCLAW_HTTP = process.env.OPENCLAW_HTTP || "http://openclaw:8088";
const OPENCLAW_INGEST_PATH = process.env.OPENCLAW_INGEST_PATH || "/ingest"; // ⚠️가정
const READY_FILE = process.env.READY_FILE || "/wa/session/ready";

async function postToOpenClaw(payload) {
  const url = `${OPENCLAW_HTTP}${OPENCLAW_INGEST_PATH}`;
  await axios.post(url, payload, { timeout: 8000 });
}

function isAllowedNumber(from) {
  // from 예: "9715xxxxxxx@c.us"
  if (WA_ALLOWED_NUMBERS.length === 0) return true; // 운영에서는 권장X
  const num = String(from || "").split("@")[0];
  return WA_ALLOWED_NUMBERS.includes(num);
}

const client = new Client({
  authStrategy: new LocalAuth({
    clientId: WA_CLIENT_ID,
    dataPath: "/wa/session"
  }),
  puppeteer: {
    executablePath: process.env.CHROME_BIN || "/usr/bin/chromium-browser",
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  }
});

client.on("qr", (qr) => {
  console.log("WA QR received. Scan to authenticate:");
  qrcode.generate(qr, { small: true });
});

client.on("ready", () => {
  console.log("WA client ready.");
  fs.mkdirSync(path.dirname(READY_FILE), { recursive: true });
  fs.writeFileSync(READY_FILE, "ready");
});

client.on("message", async (msg) => {
  try {
    const from = msg.from; // sender
    if (!isAllowedNumber(from)) return;

    const payload = {
      source: "whatsapp",
      ts: new Date().toISOString(),
      from: String(from),
      text: msg.body || "",
      meta: {
        id: msg.id?._serialized || "",
        hasMedia: msg.hasMedia || false
      }
    };

    if (!payload.text) return;

    await postToOpenClaw(payload);
  } catch (e) {
    console.error("WA ingest error:", e?.message || e);
  }
});

console.log("WA ingest starting...");
client.initialize();
```

> WhatsApp은 **QR 1회 인증**이 필요합니다(컨테이너 로그에 QR 출력).

---

# 3) Compose에 빌드 연결(기존 `docker-compose.yml` 수정 블록)

아래처럼 `tg-ingest`, `wa-ingest` 서비스에 `build:` 추가(이미지명 대신).

```yaml
  tg-ingest:
    build: ./ingest/tg
    image: hvdc/tg-ingest:latest
    # 이하 기존 그대로...

  wa-ingest:
    build: ./ingest/wa
    image: hvdc/wa-ingest:latest
    # 이하 기존 그대로...
```

---

# 4) Grafana `kpi.json` (1장 기본 대시보드)

## 4.1 저장 위치

```text
stack/grafana/dashboards/kpi.json
```

## 4.2 `kpi.json`

```json
{
  "__inputs": [
    {
      "name": "DS_PROMETHEUS",
      "label": "Prometheus",
      "description": "",
      "type": "datasource",
      "pluginId": "prometheus",
      "pluginName": "Prometheus"
    }
  ],
  "__requires": [
    { "type": "grafana", "id": "grafana", "name": "Grafana", "version": "10.0.0" },
    { "type": "datasource", "id": "prometheus", "name": "Prometheus", "version": "1.0.0" }
  ],
  "annotations": { "list": [] },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "panels": [
    {
      "datasource": "${DS_PROMETHEUS}",
      "fieldConfig": { "defaults": {}, "overrides": [] },
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 0 },
      "id": 1,
      "options": { "legend": { "displayMode": "list", "placement": "bottom" } },
      "targets": [
        {
          "expr": "100 * (DCGM_FI_DEV_FB_USED{gpu=\"0\"} / DCGM_FI_DEV_FB_TOTAL{gpu=\"0\"})",
          "legendFormat": "GPU0 VRAM %"
        }
      ],
      "title": "GPU VRAM 사용률(%)",
      "type": "timeseries"
    },
    {
      "datasource": "${DS_PROMETHEUS}",
      "fieldConfig": { "defaults": {}, "overrides": [] },
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 0 },
      "id": 2,
      "options": { "legend": { "displayMode": "list", "placement": "bottom" } },
      "targets": [
        {
          "expr": "DCGM_FI_DEV_GPU_UTIL{gpu=\"0\"}",
          "legendFormat": "GPU0 Util %"
        }
      ],
      "title": "GPU Util(%)",
      "type": "timeseries"
    },
    {
      "datasource": "${DS_PROMETHEUS}",
      "fieldConfig": { "defaults": {}, "overrides": [] },
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 8 },
      "id": 3,
      "options": { "legend": { "displayMode": "list", "placement": "bottom" } },
      "targets": [
        {
          "expr": "100 * rate(container_cpu_usage_seconds_total{container_label_com_docker_compose_service=~\"tg-ingest|wa-ingest\"}[1m])",
          "legendFormat": "{{container_label_com_docker_compose_service}} CPU%"
        }
      ],
      "title": "Ingest 컨테이너 CPU(%)",
      "type": "timeseries"
    },
    {
      "datasource": "${DS_PROMETHEUS}",
      "fieldConfig": { "defaults": {}, "overrides": [] },
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 8 },
      "id": 4,
      "options": { "legend": { "displayMode": "list", "placement": "bottom" } },
      "targets": [
        {
          "expr": "container_memory_working_set_bytes{container_label_com_docker_compose_service=~\"tg-ingest|wa-ingest\"} / 1024 / 1024 / 1024",
          "legendFormat": "{{container_label_com_docker_compose_service}} GB"
        }
      ],
      "title": "Ingest 컨테이너 메모리(GB)",
      "type": "timeseries"
    },
    {
      "datasource": "${DS_PROMETHEUS}",
      "fieldConfig": { "defaults": {}, "overrides": [] },
      "gridPos": { "h": 8, "w": 24, "x": 0, "y": 16 },
      "id": 5,
      "options": { "legend": { "displayMode": "list", "placement": "bottom" } },
      "targets": [
        {
          "expr": "changes(container_start_time_seconds{container_label_com_docker_compose_service=~\"tg-ingest|wa-ingest\"}[1h])",
          "legendFormat": "{{container_label_com_docker_compose_service}} restarts(1h)"
        }
      ],
      "title": "재시작 카운트(최근 1h, 변화 기반)",
      "type": "timeseries"
    }
  ],
  "schemaVersion": 39,
  "style": "dark",
  "tags": ["HVDC", "KPI"],
  "templating": { "list": [] },
  "time": { "from": "now-6h", "to": "now" },
  "timepicker": {},
  "timezone": "browser",
  "title": "HVDC LLM Stack KPI (GPU/CPU/Restarts)",
  "version": 1
}
```

> DCGM 메트릭명이 환경에 따라 다를 수 있습니다. (예: `DCGM_FI_DEV_FB_USED`가 없으면 exporter metrics 페이지에서 실제 이름 확인 후 교체)

---

# 5) “GPU 95% 3회 연속 → tg/wa 자동 pause” 운영 스크립트

## 5.1 PowerShell `stack/scripts/gpu_pause_watchdog.ps1`

```powershell
$threshold = 95.00
$limitCount = 3
$count = 0

$targets = @("tg-ingest", "wa-ingest")

while ($true) {
  try {
    $raw = nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits
    $used, $total = $raw -split ","
    $used = [double]$used
    $total = [double]$total

    if ($total -le 0) { throw "Invalid total memory" }

    $pct = [math]::Round(($used / $total) * 100.00, 2)
    Write-Host ("GPU VRAM: {0}%" -f $pct)

    if ($pct -ge $threshold) {
      $count++
      Write-Host ("High VRAM count: {0}/{1}" -f $count, $limitCount)

      if ($count -ge $limitCount) {
        foreach ($t in $targets) {
          Write-Host ("PAUSE: {0}" -f $t)
          docker pause $t | Out-Null
        }
        $count = 0
      }
    } else {
      $count = 0
    }

  } catch {
    Write-Host ("Watchdog error: {0}" -f $_.Exception.Message)
    # 오류 시 count 리셋(오탐 방지)
    $count = 0
  }

  Start-Sleep -Seconds 5
}
```

## 5.2 bash `stack/scripts/gpu_pause_watchdog.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

threshold="95.00"
limit=3
count=0
targets=("tg-ingest" "wa-ingest")

while true; do
  if ! out="$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null)"; then
    count=0
    sleep 5
    continue
  fi

  used="$(echo "$out" | awk -F',' '{gsub(/ /,"",$1); print $1}')"
  total="$(echo "$out" | awk -F',' '{gsub(/ /,"",$2); print $2}')"

  if [[ -z "${used}" || -z "${total}" || "${total}" == "0" ]]; then
    count=0
    sleep 5
    continue
  fi

  pct="$(awk -v u="$used" -v t="$total" 'BEGIN{printf "%.2f",(u/t)*100}')"
  echo "GPU VRAM: ${pct}%"

  ge="$(awk -v a="$pct" -v b="$threshold" 'BEGIN{print (a>=b) ? 1 : 0}')"
  if [[ "$ge" == "1" ]]; then
    count=$((count+1))
    echo "High VRAM count: ${count}/${limit}"
    if [[ "$count" -ge "$limit" ]]; then
      for t in "${targets[@]}"; do
        echo "PAUSE: $t"
        docker pause "$t" >/dev/null 2>&1 || true
      done
      count=0
    fi
  else
    count=0
  fi

  sleep 5
done
```

---

# 6) 빌드/실행 명령(필수 3개)

```bash
cd stack
docker compose build tg-ingest wa-ingest
docker compose up -d
```

Grafana: `http://localhost:3000` → Dashboards → Import → `kpi.json`

---

# 7) 빠른 검증 체크(가정 최소화)

* tg-ingest 정상: 컨테이너 내 `/data/ok` 생성
* wa-ingest 정상: QR 스캔 후 `/wa/session/ready` 생성
* OpenClaw 수집 성공: OpenClaw 로그에 ingest 수신 흔적(또는 저장 파일/DB 업데이트)

---

원하면(“상세” 없이 바로) **OpenClaw 실제 수집 경로**에 맞춰 `OPENCLAW_INGEST_PATH`/payload 키를 **당신의 OpenClaw 스키마(예: thread_id/tag/anchor)**로 고정 패치 버전도 같이 드릴 수 있습니다.

# VRAM 안전 실행 가이드 (RTX 4060 8GB)

**상세 절차**: [RUNBOOK.md](RUNBOOK.md)

## 최소 실행 (ollama 단독, 다운 방지)

```bash
cd stack
docker compose up -d ollama
```

안정 확인 후 `docker compose up -d openclaw prometheus grafana`로 추가.

## 기본 실행 (전체)

```bash
cd stack
docker compose up -d
```

**실행되는 서비스**: ollama, openclaw, prometheus, grafana
- **제외됨**: dcgm-exporter, cadvisor, node-exporter, tg-ingest, wa-ingest

## 변경 사항

| 항목 | 이전 | 이후 |
|------|------|------|
| OLLAMA_CONTEXT_LENGTH | 8192 | **4096** |
| OLLAMA_NUM_PARALLEL | - | **1** |
| dcgm-exporter | 항상 실행 | profile `full` |
| cadvisor | 항상 실행 | profile `full` |
| node-exporter | 항상 실행 | profile `full` |
| tg-ingest, wa-ingest | 항상 실행 | profile `ingest` |

## 옵션 실행

```bash
# GPU 모니터링 + 컨테이너 메트릭 (VRAM 추가 사용 주의)
docker compose --profile full up -d

# Telegram/WhatsApp 수집 (Chromium RAM 사용 주의)
docker compose --profile ingest up -d

# 전체
docker compose --profile full --profile ingest up -d
```

**ingest 사용 시**: `stack/ingest/tg`, `stack/ingest/wa` 디렉터리가 vram.md 스펙대로 존재해야 함.

# LLM_PERFORMANCE_GATES.md (SSOT)

> **골든 환경:** RTX 4060 8GB / 32GB RAM (i5-13500HX)
> **용도:** 로컬 LLM 스택 CI 게이트 — 속도·메모리·안정성 자동 검증

---

## 기본 통과 조건(고정 임계값)

| No | 항목 | 임계값 | 단위 | 실패 조건 |
| -: | --- | ----- | --- | --------- |
|  1 | 모델 로드 시간 (`load_duration`) | ≤ 25 | s | 초과 |
|  2 | 단일 샘플 E2E (128 토큰 출력) | ≤ 3.5 | s | 초과 |
|  3 | 지속 생성 처리량 | ≥ 36 | tok/s | 미달 |
|  4 | GPU VRAM 피크 | ≤ 7.3 | GB | 초과 |
|  5 | 호스트 RAM 피크 | ≤ 27 | GB | 초과 |
|  6 | 인보이스 1페이지 E2E (OCR+KIE+파싱) | ≤ 4.5 | s | 초과 |

---

## 스위치 조건(quant/ctx 변경 시)

* 생성 처리량이 **기준 대비 −10% 초과 하락** → 실패
* 어떤 메모리 피크라도 **상한 초과** → 실패
* 실패 시 전 버전 결과와 **골든 로그(diff)** 첨부 필수

---

## 아티팩트(비교/회귀 추적용, 필수 보관)

| 소스 | 필드 |
| --- | --- |
| Ollama | `total_duration`, `eval_duration` |
| llama.cpp | `llama-bench` 전체 로그 |

---

## 측정 체크리스트

1. **콜드 스타트 로드**
   - `OLLAMA_NUM_PARALLEL=1 ollama run <model> 'Hello'`
   - 로그에서 `load_duration` 추출 → **≤25s** 확인

2. **128토큰 E2E**
   - 프롬프트 고정 → 128 토큰 강제 생성
   - `total_duration` 또는 실측 → **≤3.5s**

3. **지속 처리량**
   - 512~1024 토큰 생성 러닝 → 평균 tok/s → **≥36 tok/s**

4. **메모리 피크**
   - nvidia-smi(1s 샘플링) + OS 모니터
   - **VRAM ≤7.3GB, RAM ≤27GB**

5. **인보이스 1p E2E**
   - OCR→KIE→파싱 파이프, PDF 1장 고정 입력
   - 총 소요 **≤4.5s**

6. **변경 시 리그레션**
   - quant/ctx 변경 → 기준 대비 처리량 **−10% 초과↓** → 실패
   - 메모리 피크 상한 초과 → 실패

---

## 자동화 스니펫

**Ollama 메트릭 수집**
```bash
ollama run <model> -p "<prompt>"
# 로그에서 total_duration, eval_duration, 토큰 수 → tok/s 계산 → JSON 저장
```

**llama.cpp 벤치**
```bash
./llama-bench -m <gguf> -t <threads> -ngl <layers> -p 128 -n 512
# 결과 전부를 artifacts/llama-bench.log로 보관
```

**nvidia-smi 샘플링**
```bash
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used --format=csv -l 1 > artifacts/gpu_usage.csv
```

---

## 폴더/아티팩트 규약

```
artifacts/
  <RUN_ID>/
    metrics.json       # load/e2e/tok_s/peaks
    ollama.log
    llama-bench.log
    gpu_usage.csv
    host_mem.csv
baseline/
  metrics.json         # 통과 기준(골든)
```

**CI:** `metrics.json`을 baseline과 비교 → 임계 초과 시 **즉시 실패**.

---

## baseline/metrics.json 예시(골든)

```json
{
  "load_duration_s": 25.0,
  "e2e_128tokens_s": 3.5,
  "tok_per_sec": 36.0,
  "vram_peak_gb": 7.3,
  "ram_peak_gb": 27.0,
  "invoice_1p_e2e_s": 4.5,
  "env": "RTX4060_8GB_32GB_RAM"
}
```

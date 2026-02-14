---
name: queue-scan
description: `.autodev_queue` inbox/claimed/work/pr/done/blocked 카운트와 task 목록 스냅샷 생성. queue scan/state count 키워드면 사용.
---

# queue-scan

## Role
Folder Queue 전체 상태를 "읽기 전용"으로 스캔해 가시화한다.

## Steps
1) READ 승인 확보
2) 각 상태 폴더의 task 목록/카운트 수집
3) 결과를 JSON으로 반환(상태/경로 포함)

## Outputs
- `docs/skills/schemas/skill_outputs.schema.json`의 queue-scan branch

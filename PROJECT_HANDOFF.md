# 발전5사 계약규정 비교 프로젝트 handoff

## 프로젝트 식별

- 프로젝트명: `발전5사_계약규정_비교`
- 경로: `.`
- 분리 기준: ALIO canonical ontology와 별도 관리
- 현재 review snapshot: `contract_rule_comparison_2026-08-11`

## 완료 상태

중부발전을 제외한 4개 발전자회사에 대해 국가법령정보센터 `target=pi` 현행 계약규정 API 응답과 ALIO HWP 원본을 확보·구조화·비교했다.

- API 조문: 763개
- 정규화 unit: 4,969개
- 대응 후보: 1,152개
- 부칙: 108개
- 조문 traceability: pass
- supplementary traceability: pass
- API-HWP source QA: pass
- runner `py_compile`: pass

## 5사 coverage

- 남부·남동·동서·서부: API detail 조회 및 본문 비교 완료
- 중부: 해당 snapshot에서 독립 계약규정 API 행 미조회(`no_api_record`)
- 중부 상태는 `no_material`로 해석하지 않는다. 기관 홈페이지·ALIO·local-file fallback 탐색이 남아 있다.
- 상세 coverage note: `docs/power-subsidiaries-coverage-2026-08-10.md`
- 기계 판독용 coverage: `catalog/power_subsidiaries_coverage.json`

## 다음 작업

1. 별도 GitHub private repository 생성 여부를 결정한다.
2. `version_manifest`·source hash·parser version·structured diff·parameter diff 스키마를 고정한다.
3. 정기 API probe → deterministic QA → Git PR/tag 흐름을 만든다.
4. Git에서 승인된 version만 OpenCrab private project/pack에 update하는 pilot을 수행한다.
5. 중부발전 계약규정의 기관 홈페이지/ALIO/local-file fallback 탐색
6. 다중 정규화 unit 기준 항·호·목 내용 대응으로 확장
7. 부칙의 시행일·적용례·폐지·경과조치 비교 레이어 추가

상세 비교 문서: `docs/version-management-options-review-2026-08-11.md`

## 주의

- 조문번호는 provenance/tie-breaker일 뿐 대응의 주 기준이 아니다.
- 대응 점수는 법률상 동일성이나 엄격성 판정이 아니다.
- `OC=test`는 기존 probe snapshot에서만 사용한 공개 샘플값이다. 운영 호출에는 사용하지 않는다.
- 원문 전문은 로컬에 보존하고 외부 보고에는 raw row/본문 전문을 불필요하게 복사하지 않는다.

# PRD — 발전5사 계약규정 관리 및 비교

- 문서 상태: **Draft baseline**
- 제품명: **발전5사 계약규정 관리 및 비교**
- 프로젝트 식별자: `발전5사_계약규정_비교`
- GitHub: <https://github.com/han-nakta/power-five-contract-rules-management-comparison>
- 공개 상태: `public`
- 작성 기준: 현재까지의 프로젝트 대화·검증 snapshot·운영 방향 합의

## 1. 문서 목적

이 문서는 발전5사 계약규정의 원문, 구조화 결과, 개정 이력, 조문·부칙 변화, 회사 간 비교 결과를 **재현 가능하고 추적 가능한 방식으로 관리하기 위한 제품 요구사항**을 정의한다.

이 프로젝트의 1차 목적은 새로운 규정을 자동으로 판단하는 것이 아니라 다음 질문에 근거를 붙여 답할 수 있게 하는 것이다.

- 특정 회사의 특정 시점 규정 원문은 무엇이었는가?
- 이전 버전과 현재 버전에서 조문·항·호·목·부칙이 어떻게 달라졌는가?
- 금액·비율·기간·횟수·연산자·예외 조건이 변경되었는가?
- 변경 결과가 원문 추적성과 구조화 QA를 통과했는가?
- 같은 주제에 대해 발전자회사별 규정 표현과 조건은 어떻게 다른가?
- 의미 기반 질의를 하더라도 해당 답변을 원본과 Git 변경 이력으로 되돌아갈 수 있는가?

## 2. 제품 배경과 현재 기준선

### 2.1 프로젝트 경계

- 기존 `ALIO_온톨로지`/canonical ALIO 온톨로지 프로젝트와 분리한다.
- G2B API 데이터 및 G2B 온톨로지 작업과 섞지 않는다.
- 이 프로젝트는 발전자회사 계약규정 비교와 개정 버전관리에 필요한 source snapshot, 구조화 산출물, 비교 결과, QA, 실행 코드를 관리한다.
- 법률 자문, 계약 체결 승인, 규정의 법적 우열·엄격성 자동 판정 시스템으로 사용하지 않는다.

### 2.2 현재 검증 snapshot

현재 저장된 `contract_rule_comparison_2026-08-11` snapshot은 한국중부발전을 제외한 4개 발전자회사에 대해 생성되어 있다.

- 한국남부발전: API 조문 192개, 부칙 23개
- 한국남동발전: API 조문 196개, 부칙 31개
- 한국동서발전: API 조문 184개, 부칙 32개
- 한국서부발전: API 조문 191개, 부칙 22개
- API 조문 합계: **763개**
- 다중 정규화 unit: **4,969개**
- 내용 기반 조문 대응 후보: **1,152개**
- 구조화 부칙: **108개**
- 조문 추적성 QA: **pass**
- 부칙 추적성 QA: **pass**
- API-HWP source QA: **pass**
- 4개 문서 content version 상태: **match**

한국중부발전은 해당 `target=pi` snapshot에서 독립 계약규정 행을 확인하지 못해 `no_api_record`로 기록되어 있다. 이는 계약규정이 없다는 의미가 아니며, 기관 홈페이지·ALIO·local-file fallback 탐색이 필요한 상태다.

### 2.3 현재 저장소 상태

- 프로젝트 전용 GitHub repository를 생성하고 `main` branch에 initial snapshot을 push했다.
- repository는 사용자의 결정에 따라 **public**으로 운영한다.
- 공개 repository이므로 원문·문서·생성 산출물을 추가할 때마다 API key, 토큰, 개인정보, 로컬 절대경로, 공개가 허용되지 않은 자료가 포함되지 않았는지 publication gate를 거친다.
- Git/GitHub는 원문·구조화 데이터·QA·실행 코드의 canonical version store로 사용한다.
- OpenCrab MCP는 아직 이 프로젝트의 전용 project/pack을 생성하지 않은 상태이며, Git QA를 통과한 산출물을 대상으로 하는 파생 ontology/query layer로 도입한다.

## 3. 문제 정의

현재 규정 비교는 단일 시점의 문서 비교만으로는 다음 문제를 해결하기 어렵다.

1. API 응답과 ALIO HWP 원문 사이의 동일성·추적성을 계속 확인해야 한다.
2. 조문 번호가 바뀌거나 조문이 분할·통합되면 단순 번호 diff가 오탐을 낸다.
3. 금액·비율·기간·연산자·예외의 변화는 텍스트 diff만으로 의미를 안정적으로 설명하기 어렵다.
4. 부칙은 본문과 달리 시행일·적용례·폐지·경과조치가 핵심이므로 별도 구조와 비교 레이어가 필요하다.
5. Git은 정확한 파일 이력에는 강하지만 의미 관계를 직접 질의하지 못하고, OpenCrab은 관계·의미 탐색에는 강하지만 원문 byte-level rollback과 Git식 감사 이력을 대체하지 못한다.
6. 발전5사 전체를 목표로 하지만 현재 데이터는 4개사에 한정되어 있다.

## 4. 제품 목표

### 4.1 핵심 목표

- 개정 전후 원문과 산출물을 특정 버전으로 재현한다.
- 원문, API 응답, HWP, 구조화 레코드, 비교 결과, QA 결과 사이의 provenance를 보존한다.
- 조문번호뿐 아니라 내용·구조·수치·조건을 이용해 변경 후보를 만든다.
- 본문과 부칙을 분리하여 시행일·적용례·폐지·경과조치를 놓치지 않는다.
- 발전5사 간 동일·유사 주제의 규정 차이를 근거와 함께 탐색한다.
- 승인된 Git version만 선택적으로 OpenCrab ontology에 반영한다.
- 공개 저장소에서도 재배포 가능한 자료와 민감정보의 경계를 자동·반자동으로 점검한다.

### 4.2 성공 결과

사용자는 다음 흐름을 한 번의 재현 가능한 작업으로 수행할 수 있어야 한다.

```text
공식 API/ALIO 원문 확보
  -> version manifest·hash 생성
  -> 조문/부칙 구조화·정규화
  -> exact/semantic/parameter diff 생성
  -> deterministic QA
  -> Git commit·PR·tag
  -> (선택) OpenCrab private pack update
  -> 근거·버전·시행일이 포함된 비교 보고
```

## 5. 대상 사용자와 주요 사용 사례

### 5.1 대상 사용자

- 계약·구매·준법 담당자: 회사별 계약규정의 변경점과 적용 시점을 확인한다.
- 규정·감사 검토자: 원문과 구조화 결과의 근거 및 변경 이력을 검증한다.
- 데이터/자동화 담당자: 새 snapshot을 수집하고 parser·QA·diff pipeline을 재실행한다.
- 연구·분석 사용자: 여러 발전자회사의 주제별 차이와 개정 이벤트를 탐색한다.

### 5.2 주요 사용 사례

1. **과거 버전 재현**
   - 회사와 기준일을 선택한다.
   - 해당 Git tag/commit, API serial, source hash, 원문 경로를 확인한다.

2. **동일 회사 개정 비교**
   - 이전 version과 새 version을 선택한다.
   - 추가·삭제·재작성·이동·분할·통합 후보와 수치/조건 변화를 확인한다.

3. **회사 간 주제 비교**
   - 예산·계약방법·보증·검수·하자·제재 등 주제를 선택한다.
   - 대응 후보, 원문 excerpt, 시행일, source reference를 함께 확인한다.

4. **부칙 적용 영향 검토**
   - 시행일, 적용례, 폐지, 경과조치, 다른 규정 참조를 별도 목록으로 확인한다.
   - 본문 조문과 부칙을 혼합해 단정하지 않고 각각의 근거를 유지한다.

5. **의미 기반 질의**
   - Git에 존재하는 version_id/effective_at/source commit을 조건으로 제한한다.
   - OpenCrab query 결과를 원본 snapshot과 Git 이력으로 되돌아간다.

## 6. 범위

### 6.1 현재 기준선에 포함된 범위

- 국가법령정보센터 공공기관 규정 API(`target=pi`) 응답 snapshot
- ALIO에서 확보한 HWP 원문 및 추출 텍스트
- 조문·항·호·목 구조화
- 부칙 별도 구조화
- 다중 정규화 unit
- 내용 기반 조문 대응 후보
- 조문·부칙·API-HWP 추적성 QA
- 비교 summary와 Markdown review report
- 독립 재실행 runner
- 5사 coverage catalog와 중부발전 `no_api_record` 상태
- GitHub public repository 내 버전관리 기반

### 6.2 MVP에서 완료할 범위

- 발전5사 source registry와 coverage 상태를 명시한다.
- 중부발전의 API 미조회 상태를 기관 홈페이지·ALIO·local-file fallback까지 조사해 source kind를 확정한다.
- `version_manifest`와 source/API hash 규칙을 고정한다.
- 기관별 version directory 규칙과 release tag 규칙을 고정한다.
- exact diff, 구조화 article diff, numeric/parameter diff의 최소 schema를 고정한다.
- 새 snapshot이 들어오면 deterministic parser·QA·보고서를 재생성한다.
- QA 실패 시 release/tag 및 OpenCrab 반영을 차단한다.
- public repository publication scan을 자동화한다.

### 6.3 후속 범위

- 정기 API probe와 변경 감지 PR 자동 생성
- 발전5사 전체의 다중 버전 timeline
- 조문 split/merge와 항·호·목 수준의 정밀 alignment
- 부칙 시행일·적용례·폐지·경과조치의 전용 비교 보고
- Git QA 통과 산출물의 OpenCrab private project/pack pilot
- version/effective date/source commit 필터가 포함된 질의·보고 인터페이스

### 6.4 범위 밖

- 계약서 원문 작성·검토·체결 승인
- 규정의 법적 효력, 위법성, 우열, 엄격성 자동 판정
- 법률 자문 또는 전문가 검토의 대체
- G2B 공고·입찰 데이터 및 G2B ontology 결합
- OpenCrab을 법적 원문 또는 유일한 source of truth로 사용하는 것
- 사용자 승인 없는 외부 공개, marketplace share, cloud ingest

## 7. 기능 요구사항

### FR-01. Source registry와 coverage 관리

- 기관, 규정명, source kind, API serial, 행정규칙 ID, 원문 URL, 확보일, 시행일을 기록한다.
- `law_go_kr`, `alio`, `institution_site`, `local_file` 등 source kind를 구분한다.
- API 행이 없을 때 `no_api_record`와 `no_material`을 구분한다.
- 5개 기관의 상태가 catalog에서 기계 판독 가능해야 한다.

### FR-02. Version snapshot 수집

- API JSON과 HWP/원문을 개정 단위 snapshot으로 보존한다.
- fetch 시각, 응답 metadata, source URL, 원문 파일명, content hash를 기록한다.
- 기존 snapshot은 덮어쓰지 않고 새 version으로 추가한다.
- 운영 API key는 저장소에 포함하지 않고 실행 환경의 secret/config로 주입한다.
- 기존 probe에서 사용한 `OC=test`는 운영 key로 취급하지 않으며, 운영 호출에 재사용하지 않는다.

### FR-03. Version identity와 manifest

각 논리적 규정 version은 최소한 다음 필드를 가진다.

```text
version_id
institution
rule_title
administrative_rule_id
api_serial
promulgated_at
effective_at
fetched_at
api_sha256
source_sha256
parser_version
previous_version_id
change_status
qa_status
git_commit
git_tag
```

권장 version ID 형식:

```text
<institution>-<effective_date>-<api_serial>-<source_hash_prefix>
```

### FR-04. Provenance와 원문 추적성

- 구조화 조문은 source document와 API/HWP 원본 위치로 되돌아갈 수 있어야 한다.
- 부칙 레코드는 `text_raw`, `text_layout`, `text_semantic`, `text_semantic_compact`를 구분해 보존한다.
- 원본 API 경로와 부칙 인덱스, source path, hash를 기록한다.
- report의 모든 핵심 주장에는 version/source reference를 연결한다.

### FR-05. 조문·항·호·목 구조화

- 장·절·조·항·호·목을 분리 가능한 구조로 저장한다.
- 조문번호는 provenance와 tie-breaker로 사용하되, 대응의 유일한 기준으로 사용하지 않는다.
- API 구조와 HWP 추출 구조를 비교하고, content version 불일치를 QA 오류로 표시한다.

### FR-06. 변경 탐지와 diff

최소 세 종류의 diff를 분리한다.

- **Exact diff:** 원본/API 파일 hash, byte/file-level 변경
- **Structural diff:** 조문·항·호·목 추가·삭제·재배치·split·merge 후보
- **Semantic/parameter diff:** 금액·비율·기간·횟수·연산자·예외·의무/재량/금지 표현의 변화 후보

대응 점수와 자동 분류는 법률상 동일성의 증명이 아니며, 낮은 확신 후보는 사람 검토 대상으로 남긴다.

### FR-07. 부칙 전용 레이어

- 부칙을 본문 조문과 별도 JSONL 및 별도 QA로 관리한다.
- 개정 이벤트, 시행일, 적용례, 폐지, 경과조치, 다른 규정 참조, 수치·기간 facts를 추출한다.
- 부칙이 본문을 대체하거나 본문과 충돌한다고 자동 단정하지 않는다.
- 부칙 diff와 본문 diff를 report에서 구분한다.

### FR-08. 발전5사 횡단 비교

- 같은 topic 또는 normalized unit 후보를 기관 간 비교한다.
- 회사별 version/effective_at을 함께 표시한다.
- 대응 후보·차이 후보·미대응 후보를 구분한다.
- 원문 전문을 불필요하게 외부 보고에 복사하지 않고 source reference와 필요한 excerpt 중심으로 제공한다.

### FR-09. QA와 release gate

새 version은 다음 QA를 통과해야 release candidate가 된다.

- API response schema 및 rule identity 확인
- article traceability
- supplementary traceability
- API-HWP source comparison
- required field 누락 및 duplicate ID 검사
- hash/manifest 일관성 검사
- parser 실행 재현성 검사
- 공개 저장소 publication scan

QA 실패 version은 `qa_status=fail`로 남기고 Git tag 및 OpenCrab update를 차단한다.

### FR-10. Git/GitHub 버전관리

- Git/GitHub를 canonical version store로 사용한다.
- raw, derived, QA, report, script 변경은 commit으로 남긴다.
- 개정 또는 parser 변경은 branch/PR 단위로 검토할 수 있어야 한다.
- 승인된 snapshot은 tag로 식별한다.
- 과거 tag checkout만으로 필요한 원문·manifest·QA·보고서를 재생성할 수 있어야 한다.
- 현재 repository가 public이므로 공개 전 검사는 필수다.

권장 논리 구조:

```text
raw/api/<institution>/<effective_date>/
raw/source/<institution>/<effective_date>/
derived/structured/<institution>/<effective_date>/
derived/normalized/<institution>/<effective_date>/
derived/comparison/<from>__<to>/qa/<institution>/<effective_date>/
reports/<institution>/<effective_date>/
catalog/version_manifest.jsonl
```

현재 snapshot의 실제 디렉터리 구조는 기존 dated review를 유지하되, 후속 version schema가 확정되면 위 논리 구조로 점진적으로 정리한다.

### FR-11. OpenCrab 파생 ontology/query layer

OpenCrab은 Git에서 QA 통과한 산출물만 받는다.

- project: `발전5사_계약규정_비교`
- 기관별 private pack: 남부·남동·동서·서부·중부
- version update 필수 metadata:
  - `version_id`
  - `previous_version_id`
  - `effective_at`
  - `source_sha256`
  - `api_serial`
  - `git_commit` 또는 Git tag
  - `qa_status`
  - `occurred_at`
- 질의는 가능하면 `as_of`, `version_id`, `effective_at` 조건을 포함한다.
- OpenCrab에 존재하지만 Git source snapshot으로 되돌아갈 수 없는 event는 canonical amendment record로 인정하지 않는다.
- 기본 공유 범위는 private이며, 원문 전체 cloud ingest 여부는 별도 승인 사항이다.

### FR-12. 결과 보고와 사용성

- 모든 report는 기준일, version_id, source, QA 상태를 상단에 표시한다.
- 자동 생성 결과와 사람 검토 결론을 구분한다.
- `no_api_record`, `candidate`, `verified`, `unresolved` 등 상태를 명시한다.
- raw row나 민감 필드를 채팅·외부 보고에 불필요하게 노출하지 않는다.

## 8. 비기능 요구사항

### NFR-01. 재현성

같은 입력 snapshot, parser version, dependency 환경에서 동일한 구조화·diff·QA 결과를 생성해야 한다.

### NFR-02. 추적성

각 구조화 레코드와 핵심 비교 결과는 원본 source path/hash와 Git commit/tag로 역추적 가능해야 한다.

### NFR-03. 결정성

시간·랜덤성·비정렬 dictionary 출력 때문에 결과가 불필요하게 변하지 않도록 정렬·고정 규칙을 둔다.

### NFR-04. 공개 안전성

public repository에 push하기 전에 API key, token, 개인정보, 로컬 절대경로, 의도하지 않은 credential, 공개가 허용되지 않은 원문을 검사한다.

### NFR-05. 장애 격리

Git repository 또는 OpenCrab이 일시적으로 unavailable이어도 로컬 source snapshot과 QA는 독립적으로 보존·실행할 수 있어야 한다.

### NFR-06. 공급자 독립성

OpenCrab의 query/index 결과만으로 원문 이력을 재현하지 않는다. Git source snapshot을 유지하고, ontology layer는 교체 가능하게 설계한다.

### NFR-07. 운영 감사성

수집·파싱·비교·QA·승인·ingest 시각과 실행 결과를 manifest 또는 run record에 남긴다.

## 9. 데이터 모델 초안

### 9.1 핵심 엔터티

- `Institution`: 발전자회사 식별자와 공식명
- `Regulation`: 계약규정 논리 문서
- `RegulationVersion`: 시행일과 source snapshot을 가진 특정 버전
- `SourceSnapshot`: API JSON, HWP, 추출 텍스트 및 hash
- `ArticleSnapshot`: 조문·항·호·목의 버전별 구조화 레코드
- `SupplementaryProvision`: 부칙 레코드 및 개정/시행 관련 facts
- `AmendmentEvent`: 개정·추가·삭제·재작성·분할·통합 이벤트 후보
- `ComparisonCandidate`: 기관 간 또는 버전 간 대응 후보
- `QARun`: 실행 시각, parser version, 검사 결과, 오류·경고
- `Release`: Git commit/tag와 승인된 version 집합

### 9.2 핵심 관계

```text
Institution
  -> HAS_REGULATION -> Regulation
  -> HAS_VERSION -> RegulationVersion
RegulationVersion
  -> DERIVED_FROM -> SourceSnapshot
  -> CONTAINS -> ArticleSnapshot
  -> CONTAINS -> SupplementaryProvision
RegulationVersion
  -> PREVIOUS_VERSION -> RegulationVersion
AmendmentEvent
  -> TARGETS -> ArticleSnapshot / SupplementaryProvision
  -> EVIDENCED_BY -> SourceSnapshot / GitCommit
ArticleSnapshot
  -> MATCH_CANDIDATE -> ArticleSnapshot
  -> TRACEABLE_TO -> SourceSnapshot / GitCommit / source path
```

## 10. 권장 아키텍처

```text
[국가법령정보센터 target=pi API]   [ALIO HWP / 기관 fallback]
                 \                 /
                  -> source snapshot + manifest + hash
                              |
                   deterministic parser / normalizer
                              |
             articles + supplementary + normalized units
                              |
             exact/structural/semantic/parameter comparison
                              |
                         QA release gate
                              |
                    Git commit / PR / tag  (정본)
                              |
             OpenCrab private pack update (파생)
                              |
                 graph/evidence/query/report
```

각 계층은 다음 역할을 가진다.

- **Source layer:** 원문과 공식 수집 metadata 보존
- **Derived layer:** 조문·부칙·정규화·비교 후보 생성
- **QA layer:** 원문 대조·필수 필드·hash·재현성 확인
- **Git layer:** 불변 이력, diff, review, rollback, release
- **Ontology layer:** 관계·의미 탐색과 기관 간 질의

## 11. 릴리스·운영 정책

### 11.1 변경 흐름

1. API 또는 fallback source의 새 자료를 확보한다.
2. 기존 version과 새 자료의 identity/hash를 비교한다.
3. 변경이 있으면 새 version directory와 manifest를 만든다.
4. parser, normalizer, diff, QA를 실행한다.
5. generated report와 QA 결과를 branch/PR에 올린다.
6. 사람이 낮은 확신 대응 후보와 부칙 적용 영향을 검토한다.
7. QA 통과 후 merge 및 release tag를 만든다.
8. 필요할 때만 승인된 release를 OpenCrab private pack에 update한다.

### 11.2 변경 유형

- `source_refresh`: 원문/응답은 갱신되었으나 실질 조문 변화가 확인되지 않음
- `amendment_candidate`: 조문 또는 부칙 변경 후보 발견
- `parser_change`: parser/normalizer 변경으로 derived 결과가 달라짐
- `qa_correction`: 기존 산출물의 추적성·구조화 오류 수정
- `coverage_update`: 기관/source coverage 상태 변경

### 11.3 승인 원칙

- 자동 diff는 후보를 만들 수 있지만 법률적 결론을 확정하지 않는다.
- source identity 불일치, traceability 실패, 필수 hash 누락이 있으면 release하지 않는다.
- OpenCrab update는 Git release 이후에만 수행한다.
- public repository에 새 파일을 넣을 때 publication scan을 다시 실행한다.

## 12. 단계별 로드맵

### Phase 0 — 현재 baseline (**완료**)

- `발전5사_계약규정_비교` 독립 프로젝트 생성
- 현재 4개사 API/HWP snapshot 확보
- 조문·부칙·정규화·비교·QA 산출물 생성
- GitHub public repository 생성 및 initial snapshot push
- Git/GitHub 정본 + OpenCrab 파생 layer 방향 확정

### Phase 1 — 5사 coverage와 version schema

- 중부발전 fallback source 탐색 및 source registry 확정
- `version_manifest`와 hash/parser version 필드 확정
- version ID, directory, tag, status enum 확정
- 공개 source 및 재배포 정책 검토

### Phase 2 — deterministic diff와 release gate

- article/paragraph/item structural diff schema 확정
- numeric/parameter diff schema 확정
- 부칙 시행일·적용례·폐지·경과조치 diff 확장
- publication scan 및 QA 실패 차단 자동화

### Phase 3 — 정기 변경 감지

- 정기 API probe
- 새 serial/effective date/hash 감지
- 변경 시 branch/PR 자동 생성
- QA report와 사람이 검토할 후보 목록 자동 첨부

### Phase 4 — OpenCrab private pilot

- 한 기관의 current version과 실제 다음 개정 version으로 pilot
- private project/pack 및 version metadata 검증
- `as_of`/version/effective date 질의와 Git 역추적 검증
- pilot 검증 후 5사로 확장

### Phase 5 — 사용자 질의·보고 확장

- 주제별·기관별·시점별 비교 report
- 부칙 적용 영향 report
- unresolved/low-confidence 후보 검토 workflow
- 필요 시 별도 UI 또는 MCP query interface

## 13. 완료 기준(acceptance criteria)

제품의 MVP는 다음 조건을 모두 만족해야 한다.

- [ ] 5개 기관의 coverage 상태가 `catalog`에서 확인된다.
- [ ] 각 verified version에 `version_id`, 시행일, API serial 또는 fallback source identity, API/source hash, parser version이 있다.
- [ ] 이전 version과 새 version을 Git tag/commit으로 재현할 수 있다.
- [ ] 원본 API/HWP에서 구조화 조문·부칙 레코드로의 역추적이 가능하다.
- [ ] 본문과 부칙이 별도 레이어로 비교된다.
- [ ] exact, structural, semantic/parameter diff가 구분된다.
- [ ] 조문·부칙·source QA가 release gate로 실행된다.
- [ ] 낮은 확신 대응 후보와 자동 판정이 구분된다.
- [ ] public repository publication scan에서 key/token/credential/의도하지 않은 절대경로가 검출되지 않는다.
- [ ] OpenCrab update가 Git release 이후에만 실행되며, 모든 update가 Git source로 역추적된다.
- [ ] 결과 report에 기준 version, effective date, source, QA 상태가 표시된다.

현재 baseline은 5사 coverage와 formal version schema를 제외한 여러 항목을 선행 검증한 상태이며, Phase 1~2에서 MVP 기준을 완성한다.

## 14. 미결정 사항과 결정이 필요한 시점

다음은 구현 중 임의로 확정하지 않고 별도 판단이 필요한 항목이다.

- 중부발전의 공식 fallback source와 공개 저장소 포함 범위
- API/HWP 원문 각각의 재배포 가능 범위와 보존 정책
- 정기 probe 주기와 운영 시간대
- 공개 repository에서 raw HWP/API response를 계속 보존할지, hash·metadata 중심으로 전환할지
- OpenCrab에 원문 전문을 넣을지, normalized semantic evidence만 넣을지
- 기관별 규정 변경 후보를 최종 승인할 담당자와 review SLA
- semantic diff의 자동화 수준과 사람 검토 기준
- 향후 사용자용 UI가 필요한지, 우선 report/MCP query로 충분한지

## 15. 관련 문서와 산출물

- 프로젝트 개요: [`../README.md`](../README.md)
- 작업 handoff: [`../PROJECT_HANDOFF.md`](../PROJECT_HANDOFF.md)
- Git/OpenCrab 방안 비교: [`version-management-options-review-2026-08-11.md`](version-management-options-review-2026-08-11.md)
- 5사 coverage note: [`power-subsidiaries-coverage-2026-08-10.md`](power-subsidiaries-coverage-2026-08-10.md)
- 실행 결과: [`../reviews/contract_rule_comparison_2026-08-11/run_result.json`](../reviews/contract_rule_comparison_2026-08-11/run_result.json)
- 조문 추적성 QA: [`../reviews/contract_rule_comparison_2026-08-11/qa/traceability_report.json`](../reviews/contract_rule_comparison_2026-08-11/qa/traceability_report.json)
- 부칙 추적성 QA: [`../reviews/contract_rule_comparison_2026-08-11/qa/supplementary_traceability_report.json`](../reviews/contract_rule_comparison_2026-08-11/qa/supplementary_traceability_report.json)
- API-HWP source QA: [`../reviews/contract_rule_comparison_2026-08-11/qa/source_qa_report.json`](../reviews/contract_rule_comparison_2026-08-11/qa/source_qa_report.json)
- 비교 보고서: [`../reviews/contract_rule_comparison_2026-08-11/reports/contract_rule_comparison_review.md`](../reviews/contract_rule_comparison_2026-08-11/reports/contract_rule_comparison_review.md)

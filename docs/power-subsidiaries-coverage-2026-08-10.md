# Power-subsidiary contract-rule coverage probe (2026-08-10)

Session-derived coverage note for Korean public-institution contract-rule ingestion. It records a verified snapshot; repeat the live probe before treating dates or coverage as current.

## Scope and method

Use the National Law Information Center public-institution target, not ordinary `law`/`admrul` search:

```text
LIST   GET https://www.law.go.kr/DRF/lawSearch.do
       ?OC={OC_KEY}&target=pi&type=JSON
       &query={institution_name}&search=1&knd=5
       &display=100&page=1

DETAIL GET https://www.law.go.kr/DRF/lawService.do
       ?OC={OC_KEY}&target=pi&type=JSON
       &ID={행정규칙일련번호}
```

For each institution:

1. Search the short institution name with `search=1` and `knd=5`.
2. Filter returned rows by institution identity and a title containing `계약규정`.
3. Preserve `행정규칙일련번호` as the detail `ID` and `행정규칙ID` as a separate metadata field.
4. Fetch the detail response and assert the returned rule name matches the selected row; confirm `조문내용` and, when present, `부칙` before marking the source usable.
5. If no contract row appears, retry legal-name variants such as `한국중부발전주식회사` and `한국중부발전(주)`. A `search=2` body hit is only a candidate-document signal and can be a false positive from another institution's text.

Keep `OC` server-side. The `OC=test` value used in this snapshot was only the public sample/probe value; never copy it into production configuration.

## Snapshot results

| Institution | Search total | Contract-rule row | Detail serial / API ID | Administrative-rule ID | Response date | Raw `조문내용` nodes* |
|---|---:|---|---|---|---|---:|
| 한국남동발전 | 10 | `(한국남동발전주식회사) 계약규정` | `2200000154331` | `2134441` | `20250930` | 221 |
| 한국동서발전 | 9 | `(한국동서발전 주식회사) 계약규정` | `2200000140661` | `2134777` | `20241224` | 207 |
| 한국서부발전 | 10 | `한국서부발전(주) 계약규정` | `2200000143201` | `2134271` | `20250317` | 215 |
| 한국중부발전 | 1 | **not returned** | — | — | — | — |

`*` The node counts are repeated `조문내용` entries from the detail JSON, not article counts. Chapter/section headings may be mixed into the sequence.

For 한국중부발전, the short-name and full legal-name searches each returned one row only: `한국중부발전주식회사 정관` (`2200000107169`). The result is therefore `no_api_record` for a standalone contract rule under this `pi` snapshot, not proof that the institution has no contract rule. Keep institution-site or local-file discovery as a separate fallback source.

## Detail-response checks

The three positive detail calls returned the expected rule names and article-content arrays. Their first structural markers demonstrate the parser shape:

- 남동: `제1장 총칙`, `제1절 총칙`, `제1조(목적)`
- 동서: `제1절 총칙`, `제1조(목적)`
- 서부: `제1장 총칙`, `제1절 총칙`, `제1조(목적)`

Normalize these markers before building `몇조몇항` retrieval. Do not report the raw node count as the number of articles.

## Coverage interpretation

- Positive `pi` row + successful detail response: promote to the API source registry (`source_kind=law_go_kr`, `target=pi`).
- No positive row after name variants: mark `no_api_record`/`local_source_required`; do not convert it to `no_material`.
- Keep subordinate standards and institution-site files in `source_kind=local_file` or an explicit institution-site bucket. Do not infer their absence from a zero `pi` title search.
- If a future refresh changes a serial or date, re-fetch the detail and regenerate the local article index; retain the old snapshot for provenance.

## Official probe URLs

- Guide: <https://open.law.go.kr/LSO/openApi/guideList.do>
- Namdong search: <https://www.law.go.kr/DRF/lawSearch.do?OC=test&target=pi&type=JSON&query=%ED%95%9C%EA%B5%AD%EB%82%A8%EB%8F%99%EB%B0%9C%EC%A0%84&search=1&knd=5&display=100&page=1>
- Dongseo search: <https://www.law.go.kr/DRF/lawSearch.do?OC=test&target=pi&type=JSON&query=%ED%95%9C%EA%B5%AD%EB%8F%99%EC%84%9C%EB%B0%9C%EC%A0%84&search=1&knd=5&display=100&page=1>
- Seobu search: <https://www.law.go.kr/DRF/lawSearch.do?OC=test&target=pi&type=JSON&query=%ED%95%9C%EA%B5%AD%EC%84%9C%EB%B6%80%EB%B0%9C%EC%A0%84&search=1&knd=5&display=100&page=1>
- Jungbu search: <https://www.law.go.kr/DRF/lawSearch.do?OC=test&target=pi&type=JSON&query=%ED%95%9C%EA%B5%AD%EC%A4%91%EB%B6%80%EB%B0%9C%EC%A0%84&search=1&knd=5&display=100&page=1>

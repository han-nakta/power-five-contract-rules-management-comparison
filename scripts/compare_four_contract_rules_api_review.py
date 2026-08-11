#!/usr/bin/env python3
"""Run a four-company contract-rule comparison review.

This is a dated review runner, not the production comparison service.  It keeps
API responses and local source files separate, produces article/paragraph/item
normalizations, content-based alignment candidates, and source QA.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "reviews/contract_rule_comparison_2026-08-11"
RAW_API = RUN / "raw/api"
RAW_ALIO = RUN / "raw/alio_download"
STRUCTURED = RUN / "derived/structured"
NORMALIZED = RUN / "derived/normalized"
COMPARE = RUN / "derived/comparison"
QA = RUN / "qa"
REPORTS = RUN / "reports"

KST = timezone(timedelta(hours=9))

DOCS: dict[str, dict[str, Any]] = {
    "남부": {
        "institution_name": "한국남부발전(주)",
        "api_id": "2200000154339",
        "api_url": "https://www.law.go.kr/DRF/lawService.do?OC=test&target=pi&type=JSON&ID=2200000154339",
        "local_effective_at": "2026.01.13",
        "local_source": ROOT / "source/alio_original/02_한국남부발전(주)_계약규정(2026년도_1월_13일_개정).hwp",
        "local_text": ROOT / "source/extracted_text/한국남부발전(주)__hwp5txt.txt",
        "alio_detail_url": "https://www.alio.go.kr/item/itemBoard21110.do?apbaId=C0043&nowcode=21110&reportFormNo=21110&table_name=COMM_RULE&idx_name=RULE_NO&idx=2015&reportGbn=N&bid_type=K1400",
        "alio_download_url": "https://www.alio.go.kr/download/rulefiledown.json?fileNo=229540",
    },
    "남동": {
        "institution_name": "한국남동발전(주)",
        "api_id": "2200000154331",
        "api_url": "https://www.law.go.kr/DRF/lawService.do?OC=test&target=pi&type=JSON&ID=2200000154331",
        "local_effective_at": "2025.09.30",
        "local_source": ROOT / "source/alio_original/01_한국남동발전(주)_계약규정(2025년도_9월_30일_개정).hwp",
        "local_text": ROOT / "source/extracted_text/한국남동발전(주)__hwp5txt.txt",
        "alio_detail_url": "https://www.alio.go.kr/item/itemBoard21110.do?apbaId=C0042&nowcode=21110&reportFormNo=21110&table_name=COMM_RULE&idx_name=RULE_NO&idx=3055&reportGbn=N&bid_type=K1400",
        "alio_download_url": "https://www.alio.go.kr/download/rulefiledown.json?fileNo=222079",
    },
    "동서": {
        "institution_name": "한국동서발전(주)",
        "api_id": "2200000140661",
        "api_url": "https://www.law.go.kr/DRF/lawService.do?OC=test&target=pi&type=JSON&ID=2200000140661",
        "local_effective_at": "2025.12.30",
        "local_source": ROOT / "source/alio_original/03_한국동서발전(주)_계약규정(2025년_12월_30일_개정).hwp",
        "local_text": ROOT / "source/extracted_text/한국동서발전(주)__hwp5txt.txt",
        "alio_detail_url": "https://www.alio.go.kr/item/itemBoard21110.do?apbaId=C0066&nowcode=21110&reportFormNo=21110&table_name=COMM_RULE&idx_name=RULE_NO&idx=23435&reportGbn=N&bid_type=K1400",
        "alio_download_url": "https://www.alio.go.kr/download/rulefiledown.json?fileNo=226663",
    },
    "서부": {
        "institution_name": "한국서부발전(주)",
        "api_id": "2200000143201",
        "api_url": "https://www.law.go.kr/DRF/lawService.do?OC=test&target=pi&type=JSON&ID=2200000143201",
        "local_effective_at": "2025.03.17",
        "local_source": ROOT / "source/alio_original/04_한국서부발전(주)_계약규정(2025년도_3월_개정).hwp",
        "local_text": ROOT / "source/extracted_text/한국서부발전(주)__hwp5txt.txt",
        "alio_detail_url": "https://www.alio.go.kr/item/itemBoard21110.do?apbaId=C0082&nowcode=21110&reportFormNo=21110&table_name=COMM_RULE&idx_name=RULE_NO&idx=12925&reportGbn=N&bid_type=K1400",
        "alio_download_url": "https://www.alio.go.kr/download/rulefiledown.json?fileNo=213372",
    },
}

ARTICLE_RE = re.compile(
    r"^\s*제\s*(?P<n>[0-9０-９]+)\s*조"
    r"(?:(?:\s*의\s*(?P<sub_by_ui>[0-9０-９]+))"
    r"|(?:\s+(?P<sub_by_space>[0-9０-９]+)(?=\s*[\(（])))?"
    r"\s*(?P<rest>.*)$"
)
CHAPTER_RE = re.compile(r"^\s*제\s*([0-9０-９]+)\s*장\s*(.*)$")
SECTION_RE = re.compile(r"^\s*제\s*([0-9０-９]+)\s*절\s*(.*)$")
SUPPLEMENTARY_RE = re.compile(r"^\s*부\s*칙\b|^\s*부칙\b")
FULLWIDTH_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")
PARAGRAPH_MARKERS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
PARAGRAPH_RE = re.compile(r"(?<![가-힣A-Za-z0-9])([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])\s*")
NUM_ITEM_RE = re.compile(r"(?<![가-힣A-Za-z0-9])(\d{1,3})\s*\.\s*")
KOR_ITEM_RE = re.compile(r"(?<![가-힣A-Za-z0-9])([가-하])\s*\.\s*")
REVISION_TAG_RE = re.compile(r"<[^>]*(?:개정|신설|삭제|제정|시행)[^>]*>")
DATE_TAG_RE = re.compile(r"<\s*(?=[^>]*\d{2,4}\s*[.])[^>]*\d{1,2}\s*[.][^>]*>")
TABLE_TAG_RE = re.compile(r"<\s*표\s*>|\[\s*표\s*\]")
REVISION_PAREN_RE = re.compile(r"\([^)]*(?:개정|신설|삭제|제정|시행)[^)]*\)")
URL_RE = re.compile(r"https?://[^\s)>,]+", re.I)

TOPICS: dict[str, list[str]] = {
    "scope_and_principles": ["적용범위", "다른규정과의 관계", "용어의 정의", "계약에 관한 업무를 처리함에"],
    "committee": ["계약심의위원회", "특수계약심의위원회", "설계변경심의위원회", "심의위원회"],
    "request_and_preannouncement": ["계약의 요청", "계약요청 대상", "계약요청서", "사전공개", "사전예고", "구매규격", "구매요청서"],
    "contract_method": ["계약의 방법", "일반경쟁", "제한경쟁", "지명경쟁", "수의계약"],
    "bid_eligibility": ["입찰참가자격", "입찰자격", "자격심사", "사전심사"],
    "ethics_and_fairness": ["청렴계약", "공정계약", "공정거래", "이해충돌", "청렴서약"],
    "subcontracting": ["하도급", "직불", "하수급인"],
    "price_and_estimate": ["예정가격", "추정가격", "원가계산", "가격결정", "예산"],
    "security_and_guarantee": ["계약보증금", "입찰보증금", "하자보수보증금", "보증서"],
    "performance_and_inspection": ["계약이행", "검사", "검수", "인수", "납품", "하자"],
    "payment_and_advance": ["대금지급", "선금", "상생결제", "전자적 대금", "체불임금"],
    "delay_and_penalty": ["지체상금", "지연배상", "부정당업자", "입찰참가자격 제한", "제재"],
    "change_and_termination": ["계약금액 조정", "설계변경", "계약해제", "계약해지", "변경계약"],
    "joint_contract": ["공동계약", "공동수급체", "공동도급", "분담이행", "연대보증"],
    "dispute_and_review": ["이의", "청문", "분쟁", "재검토", "재심"],
    "external_rules": ["국가를 당사자로", "계약예규", "시행령", "시행규칙", "공기업·준정부기관"],
}

INSTITUTION_PATTERNS = [
    re.compile(r"한국\s*남부발전(?:\s*주식회사|\s*\(주\))?"),
    re.compile(r"한국\s*남동발전(?:\s*주식회사|\s*\(주\))?"),
    re.compile(r"한국\s*동서발전(?:\s*주식회사|\s*\(주\))?"),
    re.compile(r"한국\s*서부발전(?:\s*주식회사|\s*\(주\))?"),
]


def now_iso() -> str:
    return datetime.now(KST).isoformat(timespec="seconds")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def norm_digits(text: str) -> str:
    return text.translate(FULLWIDTH_DIGITS)


def safe_slug(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", text).strip("_")


def effective_date_in_text(text: str, yyyymmdd: str) -> bool:
    if not yyyymmdd or len(yyyymmdd) != 8:
        return False
    year, month, day = yyyymmdd[:4], str(int(yyyymmdd[4:6])), str(int(yyyymmdd[6:]))
    pattern = rf"{year}\s*(?:[.]|년)\s*0?{int(month)}\s*(?:[.]|월)\s*0?{int(day)}\s*(?:[.]|일)"
    return bool(re.search(pattern, text or ""))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def find_first(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            found = find_first(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_first(value, key)
            if found is not None:
                return found
    return None


def normalize_layout(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "")
    text = norm_digits(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    for old, new in {
        "（": "(", "）": ")", "｢": "「", "｣": "」", "％": "%",
        "․": "·", "・": "·", "ㆍ": "·", "‧": "·", "−": "-", "–": "-", "—": "-",
        "“": "“", "”": "”", "‘": "‘", "’": "’",
    }.items():
        text = text.replace(old, new)
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"공기업\s*[·ㆍ․・]\s*준정부기관", "공기업·준정부기관", text)
    return text


def remove_revision_annotations(text: str) -> str:
    text = REVISION_TAG_RE.sub(" ", text)
    text = DATE_TAG_RE.sub(" ", text)
    text = TABLE_TAG_RE.sub(" ", text)
    text = REVISION_PAREN_RE.sub(" ", text)
    # Deleted paragraph/item markers occur both as `삭제 <...>` and `(삭제)`.
    # They are structural revision markers, not substantive rule text.
    text = re.sub(r"(?<![가-힣])삭제(?=\s*(?:<|$|\d))", " ", text)
    # A few extracted files use short-date amendment suffixes without a word.
    text = re.sub(r"\s*[('‘’]?\d{2,4}\s*[.]\s*\d{1,2}\s*[.]\s*\d{1,2}\s*[.]?\s*(?:개정|신설|삭제)?", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def mask_institution(text: str) -> str:
    for pattern in INSTITUTION_PATTERNS:
        text = pattern.sub("[기관]", text)
    text = re.sub(r"(?<![가-힣])(당사|우리회사)(?![가-힣])", "[기관]", text)
    return text


def semantic_text(text: str, deleted: bool = False) -> str:
    if deleted:
        return ""
    text = normalize_layout(text)
    text = remove_revision_annotations(text)
    text = URL_RE.sub("[시스템]", text)
    text = mask_institution(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def revision_events(text: str) -> list[str]:
    found = REVISION_TAG_RE.findall(text or "") + REVISION_PAREN_RE.findall(text or "")
    found += re.findall(r"(?:제정|일부개정|전부개정|개정|신설|삭제)[^\n<)]{0,40}", text or "")
    result: list[str] = []
    for item in found:
        item = normalize_layout(item)
        if item and item not in result:
            result.append(item)
    return result


def detect_status(heading_or_text: str) -> str:
    head = (heading_or_text or "")[:160]
    if re.search(r"삭제", head):
        return "deleted"
    return "active"


def parse_article_heading(text: str) -> dict[str, str] | None:
    match = ARTICLE_RE.match(text or "")
    if not match:
        return None
    n = norm_digits(match.group("n"))
    sub = norm_digits(match.group("sub_by_ui") or match.group("sub_by_space") or "")
    rest = (match.group("rest") or "").strip()
    title = ""
    tail = rest
    if rest.startswith("("):
        end = rest.find(")")
        if end >= 0:
            title = rest[1:end].strip()
            tail = rest[end + 1 :].strip()
    elif rest.startswith("（"):
        end = rest.find("）")
        if end >= 0:
            title = rest[1:end].strip()
            tail = rest[end + 1 :].strip()
    elif re.match(r"삭제\b", rest):
        title = re.split(r"<|\(", rest, maxsplit=1)[0].strip()
    key = f"{n}의{sub}" if sub else n
    article_status = "active"
    if re.match(r"삭제\b", rest) or re.search(r"삭제", title) or re.match(r"^[\(（][^\)）]*삭제", rest):
        article_status = "deleted"
    return {
        "article_no": n,
        "article_subno": sub,
        "article_key": key,
        "title": title,
        "tail": tail,
        "status": article_status,
    }


def parse_local_heading_line(text: str) -> tuple[dict[str, str] | None, str]:
    """Parse an HWP heading, including revision-prefix + heading on one line."""
    direct = parse_article_heading(text)
    if direct:
        return direct, text
    for match in re.finditer(r"(?<![가-힣])제\s*[0-9０-９]+\s*조", text or ""):
        prefix = text[: match.start()]
        # HWP5txt sometimes puts `[제2항에서 이동, ...]제143조` on one line.
        if not re.fullmatch(r"(?:\s|\[[^\]]*\]|<[^>]*>|\([^)]*\))*", prefix):
            continue
        candidate = text[match.start() :]
        parsed = parse_article_heading(candidate)
        if parsed:
            return parsed, candidate
    return None, text


def split_marked(text: str, pattern: re.Pattern[str]) -> list[tuple[str, str]]:
    matches = list(pattern.finditer(text or ""))
    if not matches:
        return [("", (text or "").strip())] if (text or "").strip() else []
    result: list[tuple[str, str]] = []
    prefix = (text or "")[: matches[0].start()].strip()
    if prefix:
        result.append(("", prefix))
    for idx, match in enumerate(matches):
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        marker = match.group(1)
        body = text[match.end() : end].strip()
        result.append((marker, body))
    return result


def numeric_facts(text: str) -> list[dict[str, str]]:
    facts: list[dict[str, str]] = []
    patterns = [
        r"\d[\d,]*(?:\.\d+)?\s*(?:%|퍼센트|억원|만원|원|일|개월|년|명|인|개|건|회|배|분|시간)",
        r"\d+\s*억원", r"\d+\s*만원", r"\d+\s*천만원", r"\d+\s*일", r"\d+\s*개월",
        r"\d+\s*인\s*이내", r"\d+\s*개\s*이상", r"고시금액", r"추정가격",
    ]
    seen: set[tuple[int, int, str]] = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text or ""):
            key = (match.start(), match.end(), match.group(0))
            if key in seen:
                continue
            seen.add(key)
            start = max(0, match.start() - 32)
            end = min(len(text), match.end() + 32)
            facts.append({"value": match.group(0), "context": text[start:end]})
    return facts


def references(text: str) -> list[str]:
    refs = []
    patterns = [
        r"국가를 당사자로 하는 계약에 관한 법률(?:\s*시행령|\s*시행규칙)?",
        r"공기업\s*[·ㆍ․・]\s*준정부기관 계약사무규칙",
        r"계약사무규칙", r"계약예규", r"시행령", r"시행규칙",
        r"제\s*\d+\s*조(?:의\s*\d+)?(?:\s*제\s*\d+\s*항)?",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text or ""):
            value = normalize_layout(match.group(0))
            if value and value not in refs:
                refs.append(value)
    return refs


def classify_modality(text: str) -> list[str]:
    labels: list[str] = []
    if re.search(r"하여서는 아니|해서는 아니|금지|할 수 없다", text or ""):
        labels.append("prohibition")
    if re.search(r"하여야 한다|해야 한다|하여야", text or ""):
        labels.append("obligation")
    if re.search(r"할 수 있다|할 수 있는|수 있다", text or ""):
        labels.append("permission")
    if re.search(r"말한다|뜻한다|정의", text or ""):
        labels.append("definition")
    if re.search(r"다만|단,|단\s", text or ""):
        labels.append("exception")
    return labels or ["descriptive"]


def topic_labels(text: str, title: str = "") -> list[str]:
    labels: list[str] = []
    body = text or ""
    heading = title or ""
    for topic, words in TOPICS.items():
        haystacks = [body]
        if topic in {"scope_and_principles", "request_and_preannouncement", "committee", "ethics_and_fairness"}:
            haystacks.insert(0, heading)
        if any(word in haystack for word in words for haystack in haystacks):
            labels.append(topic)
    return labels


def make_unit(doc_key: str, article: dict[str, Any], unit_id: str, unit_type: str, raw: str, parent: str = "", marker: str = "") -> dict[str, Any]:
    deleted = article.get("status") == "deleted"
    layout = normalize_layout(raw)
    semantic = semantic_text(raw, deleted=deleted)
    return {
        "unit_id": unit_id,
        "document_key": doc_key,
        "institution_name": DOCS[doc_key]["institution_name"],
        "article_key": article["article_key"],
        "article_no": article["article_no"],
        "article_subno": article["article_subno"],
        "article_title": article.get("title", ""),
        "unit_type": unit_type,
        "marker": marker,
        "parent_unit_id": parent,
        "text_raw": raw,
        "text_layout": layout,
        "text_semantic": semantic,
        "text_semantic_compact": compact_text(semantic),
        "modality": classify_modality(semantic),
        "numeric_facts": numeric_facts(semantic),
        "references": references(semantic),
        "topics": topic_labels(semantic),
    }


def enrich_article(doc_key: str, article: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw_body = article.get("body_raw", "")
    units: list[dict[str, Any]] = []
    article_unit = make_unit(doc_key, article, f"{doc_key}:{article['article_key']}", "article", raw_body)
    article_unit["topics"] = topic_labels(article_unit["text_semantic"], article.get("title", ""))
    units.append(article_unit)
    paragraphs = split_marked(raw_body, PARAGRAPH_RE)
    if not paragraphs and raw_body.strip():
        paragraphs = [("", raw_body.strip())]
    paragraph_records: list[dict[str, Any]] = []
    for pidx, (marker, pbody) in enumerate(paragraphs, start=1):
        if not pbody:
            continue
        p_id = f"{doc_key}:{article['article_key']}:p{pidx}"
        p_unit = make_unit(doc_key, article, p_id, "paragraph", pbody, article_unit["unit_id"], marker)
        units.append(p_unit)
        item_records: list[dict[str, Any]] = []
        num_items = split_marked(pbody, NUM_ITEM_RE)
        kor_items = split_marked(pbody, KOR_ITEM_RE)
        item_parts = num_items if len(num_items) > 1 else kor_items if len(kor_items) > 1 else []
        for iidx, (imarker, ibody) in enumerate(item_parts, start=1):
            if not ibody:
                continue
            i_id = f"{p_id}:i{iidx}"
            i_unit = make_unit(doc_key, article, i_id, "item", ibody, p_id, imarker)
            units.append(i_unit)
            item_records.append({"unit_id": i_id, "marker": imarker, "text_raw": ibody})
        paragraph_records.append({"unit_id": p_id, "marker": marker, "text_raw": pbody, "items": item_records})
    result = dict(article)
    result.update({
        "institution_name": DOCS[doc_key]["institution_name"],
        "document_key": doc_key,
        "article_id": f"{doc_key}:{article['article_key']}",
        "title_layout": normalize_layout(article.get("title", "")),
        "title_semantic": semantic_text(article.get("title", "")),
        "body_layout": normalize_layout(raw_body),
        "body_semantic": semantic_text(raw_body, deleted=article.get("status") == "deleted"),
        "body_semantic_compact": compact_text(semantic_text(raw_body, deleted=article.get("status") == "deleted")),
        "revision_events": revision_events(article.get("raw_text", "")),
        "numeric_facts": numeric_facts(semantic_text(raw_body)),
        "references": references(semantic_text(raw_body)),
        "modality": classify_modality(semantic_text(raw_body)),
        "topics": topic_labels(semantic_text(raw_body), article.get("title", "")),
        "paragraphs": paragraph_records,
    })
    return result, units


def parse_api_document(doc_key: str, service: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    content = service.get("조문내용") or []
    if not isinstance(content, list):
        content = [content]
    articles: list[dict[str, Any]] = []
    units: list[dict[str, Any]] = []
    chapter = ""
    section = ""
    supplementary_markers: list[dict[str, Any]] = []
    table_markers: list[dict[str, Any]] = []
    for idx, raw_item in enumerate(content):
        raw_item = str(raw_item or "")
        stripped = raw_item.strip()
        cm = CHAPTER_RE.match(stripped)
        if cm:
            chapter = f"제{norm_digits(cm.group(1))}장 {cm.group(2).strip()}".strip()
            section = ""
            continue
        sm = SECTION_RE.match(stripped)
        if sm:
            section = f"제{norm_digits(sm.group(1))}절 {sm.group(2).strip()}".strip()
            continue
        if SUPPLEMENTARY_RE.match(stripped):
            supplementary_markers.append({"source_item_index": idx, "text_raw": raw_item})
            continue
        if re.search(r"^(?:<표>|\[표\]|별표\s*\d*|별지\s*\d*|서식\s*\d*)", stripped):
            table_markers.append({"source_item_index": idx, "text_raw": raw_item})
        heading = parse_article_heading(stripped)
        if not heading:
            continue
        article = {
            **heading,
            "chapter": chapter,
            "section": section,
            "heading_raw": stripped[: max(0, len(stripped) - len(heading["tail"]))].strip(),
            "raw_text": raw_item,
            "body_raw": heading["tail"],
            "source_item_index": idx,
            "source_path": f"AdmRulService.조문내용[{idx}]",
        }
        enriched, article_units = enrich_article(doc_key, article)
        articles.append(enriched)
        units.extend(article_units)
    return articles, units, {
        "raw_content_nodes": len(content),
        "chapters": sum(1 for x in content if CHAPTER_RE.match(str(x or "").strip())),
        "sections": sum(1 for x in content if SECTION_RE.match(str(x or "").strip())),
        "article_entries": len(articles),
        "article_keys": len({x["article_key"] for x in articles}),
        "deleted_articles": sum(x["status"] == "deleted" for x in articles),
        "supplementary_markers": supplementary_markers,
        "table_markers": table_markers,
    }


def fetch_api(doc_key: str, spec: dict[str, Any]) -> tuple[dict[str, Any], bytes, dict[str, Any]]:
    params = {"OC": "test", "target": "pi", "type": "JSON", "ID": spec["api_id"]}
    url = "https://www.law.go.kr/DRF/lawService.do?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        raw = response.read()
    obj = json.loads(raw.decode("utf-8-sig"))
    service = obj.get("AdmRulService") or find_first(obj, "AdmRulService")
    if not isinstance(service, dict):
        raise RuntimeError(f"No AdmRulService for {doc_key}")
    basic = service.get("행정규칙기본정보") or {}
    if isinstance(basic, list):
        basic = basic[0] if basic else {}
    if basic.get("행정규칙일련번호") != spec["api_id"]:
        raise RuntimeError(f"ID mismatch for {doc_key}: {basic.get('행정규칙일련번호')} != {spec['api_id']}")
    meta = {
        "document_key": doc_key,
        "institution_name": spec["institution_name"],
        "api_url": url,
        "api_id": spec["api_id"],
        "fetched_at": now_iso(),
        "raw_sha256": sha256_bytes(raw),
        "raw_bytes": len(raw),
        "basic": basic,
    }
    return obj, raw, meta


def fetch_alio_source(doc_key: str, spec: dict[str, Any]) -> dict[str, Any]:
    url = spec["alio_download_url"]
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        raw = response.read()
        content_type = response.headers.get("Content-Type", "")
        status = getattr(response, "status", 200)
    path = RAW_ALIO / f"{doc_key}_{spec['api_id']}.hwp"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return {
        "document_key": doc_key,
        "url": url,
        "path": str(path),
        "http_status": status,
        "content_type": content_type,
        "bytes": len(raw),
        "sha256": sha256_bytes(raw),
        "downloaded_at": now_iso(),
    }


def token_set(text: str) -> set[str]:
    return set(re.findall(r"[가-힣A-Za-z0-9]+", text or ""))


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def title_similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    at = compact_text(semantic_text(a.get("title", "")))
    bt = compact_text(semantic_text(b.get("title", "")))
    if not at and not bt:
        return 0.0
    return SequenceMatcher(None, at, bt).ratio()


def body_similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    aa = a.get("body_semantic_compact", "")
    bb = b.get("body_semantic_compact", "")
    if not aa and not bb:
        return 1.0
    if not aa or not bb:
        return 0.0
    seq = SequenceMatcher(None, aa, bb).ratio()
    jac = jaccard(token_set(a.get("body_semantic", "")), token_set(b.get("body_semantic", "")))
    return 0.7 * seq + 0.3 * jac


def alignment_score(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    bs = body_similarity(a, b)
    ts = title_similarity(a, b)
    at = set(a.get("topics") or []) - {"external_rules"}
    bt = set(b.get("topics") or []) - {"external_rules"}
    to = jaccard(at, bt)
    # Content is primary. Title/topic help when an article was split or renamed.
    score = 0.62 * bs + 0.23 * ts + 0.15 * to
    if a.get("status") == "deleted" or b.get("status") == "deleted":
        score *= 0.92
    if score >= 0.82:
        confidence = "high"
    elif score >= 0.62:
        confidence = "medium"
    elif score >= 0.45:
        confidence = "low"
    else:
        confidence = "weak"
    return {"score": round(score, 4), "body_similarity": round(bs, 4), "title_similarity": round(ts, 4), "topic_overlap": round(to, 4), "confidence": confidence}


def extract_api_articles(doc_key: str, obj: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    service = obj.get("AdmRulService") or find_first(obj, "AdmRulService")
    return parse_api_document(doc_key, service)


def extract_supplementary(doc_key: str, service: dict[str, Any]) -> list[dict[str, Any]]:
    block = service.get("부칙") or {}
    if not isinstance(block, dict):
        return []

    def as_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(x or "") for x in value]
        if value in (None, ""):
            return []
        return [str(value)]

    dates = as_list(block.get("부칙공포일자"))
    contents = as_list(block.get("부칙내용"))
    numbers = as_list(block.get("부칙공포번호"))
    count = max(len(dates), len(contents), len(numbers))
    rows: list[dict[str, Any]] = []
    for idx in range(count):
        raw = contents[idx] if idx < len(contents) else ""
        layout = normalize_layout(raw)
        semantic = semantic_text(raw)
        rows.append({
            "supplementary_id": f"{doc_key}:supplementary:{idx + 1}",
            "document_key": doc_key,
            "promulgation_date": dates[idx] if idx < len(dates) else "",
            "promulgation_no": numbers[idx] if idx < len(numbers) else "",
            "text_raw": raw,
            "text_layout": layout,
            "text_semantic": semantic,
            "text_semantic_compact": compact_text(semantic),
            "revision_events": revision_events(raw),
            "numeric_facts": numeric_facts(semantic),
            "references": references(semantic),
            "topics": ["supplementary"],
            "source_path": f"AdmRulService.부칙.부칙내용[{idx}]",
        })
    return rows


def parse_local_text(doc_key: str, text: str) -> list[dict[str, Any]]:
    articles: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    chapter = ""
    section = ""
    in_supplementary = False
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            if current is not None and not in_supplementary:
                current.setdefault("body_lines", []).append("")
            continue
        if SUPPLEMENTARY_RE.match(stripped):
            if current is not None:
                current["body_raw"] = "\n".join(current.pop("body_lines", []))
                articles.append(current)
                current = None
            in_supplementary = True
            continue
        if in_supplementary:
            continue
        cm = CHAPTER_RE.match(stripped)
        if cm:
            chapter = f"제{norm_digits(cm.group(1))}장 {cm.group(2).strip()}".strip()
            section = ""
            continue
        sm = SECTION_RE.match(stripped)
        if sm:
            section = f"제{norm_digits(sm.group(1))}절 {sm.group(2).strip()}".strip()
            continue
        heading, heading_text = parse_local_heading_line(stripped)
        if heading:
            if current is not None:
                current["body_raw"] = "\n".join(current.pop("body_lines", []))
                articles.append(current)
            current = {
                **heading,
                "chapter": chapter,
                "section": section,
                "heading_raw": heading_text,
                "raw_text": heading_text,
                "body_raw": "",
                "body_lines": [heading["tail"]] if heading["tail"] else [],
                "source_line_start": line_no,
            }
        elif current is not None:
            current.setdefault("body_lines", []).append(line.rstrip())
    if current is not None:
        current["body_raw"] = "\n".join(current.pop("body_lines", []))
        articles.append(current)
    return articles


def local_enriched(doc_key: str, article: dict[str, Any]) -> dict[str, Any]:
    result, _ = enrich_article(doc_key, article)
    return result


def best_match(source_article: dict[str, Any], api_articles: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    candidates = [(alignment_score(source_article, x), x) for x in api_articles]
    if not candidates:
        return None, {"score": 0.0, "confidence": "none"}
    metrics, target = max(candidates, key=lambda x: x[0]["score"])
    return target, metrics


def compare_pair(doc_a: str, arts_a: list[dict[str, Any]], doc_b: str, arts_b: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best_b_for_a: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    best_a_for_b: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for a in arts_a:
        target, metrics = best_match(a, arts_b)
        if target:
            best_b_for_a[a["article_id"]] = (target, metrics)
    for b in arts_b:
        target, metrics = best_match(b, arts_a)
        if target:
            best_a_for_b[b["article_id"]] = (target, metrics)
    rows: list[dict[str, Any]] = []
    for a in arts_a:
        item = best_b_for_a.get(a["article_id"])
        if not item:
            continue
        b, metrics = item
        reciprocal = best_a_for_b.get(b["article_id"], (None, {}))[0]
        rows.append({
            "document_a": doc_a,
            "document_b": doc_b,
            "article_a": a["article_key"],
            "article_b": b["article_key"],
            "title_a": a.get("title", ""),
            "title_b": b.get("title", ""),
            "status_a": a.get("status"),
            "status_b": b.get("status"),
            "source_a": a.get("source_path"),
            "source_b": b.get("source_path"),
            **metrics,
            "reciprocal": bool(reciprocal and reciprocal.get("article_id") == a["article_id"]),
            "numeric_fact_values_a": [x["value"] for x in a.get("numeric_facts", [])],
            "numeric_fact_values_b": [x["value"] for x in b.get("numeric_facts", [])],
            "topics_a": a.get("topics", []),
            "topics_b": b.get("topics", []),
            "excerpt_a": normalize_layout(a.get("body_raw", ""))[:240],
            "excerpt_b": normalize_layout(b.get("body_raw", ""))[:240],
        })
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def article_summary(articles: list[dict[str, Any]]) -> dict[str, Any]:
    topic_counter = Counter(topic for a in articles for topic in a.get("topics", []))
    return {
        "articles": len(articles),
        "unique_article_keys": len({a["article_key"] for a in articles}),
        "deleted_articles": sum(a.get("status") == "deleted" for a in articles),
        "body_chars_raw": sum(len(a.get("body_raw", "")) for a in articles),
        "paragraphs": sum(len(a.get("paragraphs", [])) for a in articles),
        "revision_event_count": sum(len(a.get("revision_events", [])) for a in articles),
        "numeric_fact_count": sum(len(a.get("numeric_facts", [])) for a in articles),
        "topic_counts": dict(sorted(topic_counter.items())),
    }


def build_reports(api_meta: dict[str, Any], api_articles: dict[str, list[dict[str, Any]]], api_struct: dict[str, dict[str, Any]], pairs: list[dict[str, Any]], source_qa: dict[str, Any], trace: dict[str, Any]) -> None:
    topic_rows: list[dict[str, Any]] = []
    for topic in TOPICS:
        item: dict[str, Any] = {"topic": topic}
        for doc_key, articles in api_articles.items():
            hits = [a for a in articles if topic in (a.get("topics") or [])]
            item[doc_key] = [{"article_key": a["article_key"], "title": a.get("title", ""), "source": a.get("source_path")} for a in hits]
        topic_rows.append(item)
    write_jsonl(COMPARE / "topic_matrix.jsonl", topic_rows)
    write_jsonl(COMPARE / "content_alignment_candidates.jsonl", pairs)

    pair_summary: dict[str, Any] = {}
    for pair in combinations(DOCS, 2):
        key = f"{pair[0]}-{pair[1]}"
        rows = [x for x in pairs if (x["document_a"], x["document_b"]) == pair]
        pair_summary[key] = {
            "rows": len(rows),
            "high": sum(x["confidence"] == "high" for x in rows),
            "medium": sum(x["confidence"] == "medium" for x in rows),
            "low": sum(x["confidence"] == "low" for x in rows),
            "weak": sum(x["confidence"] == "weak" for x in rows),
            "reciprocal": sum(bool(x["reciprocal"]) for x in rows),
            "mean_score": round(sum(x["score"] for x in rows) / len(rows), 4) if rows else 0,
        }
    summary = {
        "run": str(RUN),
        "created_at": now_iso(),
        "api_documents": {k: {"metadata": api_meta[k], "structure": api_struct[k], "summary": article_summary(api_articles[k])} for k in DOCS},
        "pair_summary": pair_summary,
        "source_qa": source_qa,
        "traceability": trace,
        "topic_matrix_path": str(COMPARE / "topic_matrix.jsonl"),
        "alignment_path": str(COMPARE / "content_alignment_candidates.jsonl"),
    }
    write_json(COMPARE / "comparison_summary.json", summary)

    report: list[str] = [
        "# 4개 발전자회사 계약규정 내용 기반 비교 리뷰",
        "",
        f"- 실행 시각: `{now_iso()}`",
        "- 범위: 한국남부발전·한국남동발전·한국동서발전·한국서부발전",
        "- 기준: 현재 `target=pi` API 응답의 현행 규정",
        "- 주의: 자동 비교는 법률상 우열 판단이 아니라 내용 대응 후보와 차이 후보를 생성한다.",
        "",
        "## 1. API 버전·구조 요약",
        "",
    ]
    for doc_key in DOCS:
        basic = api_meta[doc_key]["basic"]
        st = api_struct[doc_key]
        report.append(
            f"- {doc_key}: 발령 `{basic.get('발령일자','')}`, 생성 `{basic.get('생성일자','')}`, "
            f"원시 노드 `{st['raw_content_nodes']}`, 조문형 항목 `{st['article_entries']}`, "
            f"장 `{st['chapters']}`, 절 `{st['sections']}`, 부칙 `{st.get('supplementary_entries', 0)}`, "
            f"삭제 조문 `{st['deleted_articles']}`"
        )
    report += [
        "",
        "## 2. 내용 기반 대응 방식",
        "",
        "- 조문번호는 대응 점수에 사용하지 않고 출처 추적용으로만 보존했다.",
        "- 본문 의미 유사도 62%, 제목 유사도 23%, 주제 중첩 15%로 후보를 계산했다.",
        "- `external_rules`는 법령·시행령·계약예규 등의 교차참조 패싯으로 보존하지만, 내용 대응 점수의 주제 중첩에는 넣지 않았다.",
        "- `high`는 추가 확인 우선순위가 낮은 강한 대응 후보, `medium`은 검토 후보, `low/weak`는 분할·통합·주제 재분류가 필요한 후보로 본다.",
        "",
        "## 3. 회사 쌍별 대응 후보 요약",
        "",
    ]
    for key, value in pair_summary.items():
        report.append(
            f"- {key}: 후보 `{value['rows']}`, high `{value['high']}`, medium `{value['medium']}`, "
            f"low `{value['low']}`, weak `{value['weak']}`, 상호최적 `{value['reciprocal']}`, 평균점수 `{value['mean_score']}`"
        )
    report += ["", "## 4. 주제별 조문 존재 현황", ""]
    for row in topic_rows:
        present = []
        for doc_key in DOCS:
            if row[doc_key]:
                present.append(f"{doc_key}:{','.join(x['article_key'] for x in row[doc_key])}")
        report.append(f"- `{row['topic']}` — " + ("; ".join(present) if present else "탐지 없음"))
    report += [
        "",
        "## 5. 우선 검토할 내용 차이 후보",
        "",
    ]
    divergent = sorted(
        [x for x in pairs if x["confidence"] in {"medium", "low"} and x["topics_a"] and x["topics_b"]],
        key=lambda x: (x["score"], -len(x["excerpt_a"]) - len(x["excerpt_b"]))
    )
    for row in divergent[:30]:
        report.append(
            f"- {row['document_a']} 제{row['article_a']}({row['title_a']}) ↔ {row['document_b']} 제{row['article_b']}({row['title_b']}) "
            f"— 점수 `{row['score']}`, 본문 `{row['body_similarity']}`, 주제 `{','.join(row['topics_a'])}`"
        )
        report.append(f"  - A: {row['excerpt_a']}")
        report.append(f"  - B: {row['excerpt_b']}")
    report += [
        "",
        "## 6. 해석상 주의할 점",
        "",
        "- 같은 조문번호라도 회사별로 다른 주제를 담을 수 있으므로 번호 기반 diff를 사용하지 않았다.",
        "- 하나의 회사에서 조문이 분리되고 다른 회사에서 하나로 합쳐진 경우, 단일 대응이 아니라 후보 대응으로 남긴다.",
        "- 금액·기간·비율·의무 표현은 정규화 과정에서 보존했으며, 후속 단계에서 별도 매개변수 비교가 필요하다.",
        "- `부칙`과 별표·서식 후보는 본문 의미 비교와 분리했다.",
        "",
        "## 7. 산출물",
        "",
        f"- 원본 API: `{RAW_API}`",
        f"- 구조화 조문·부칙: `{STRUCTURED}`",
        f"- 다중 정규화·항목: `{NORMALIZED}`",
        f"- 내용 대응: `{COMPARE}`",
        f"- 추적성 QA: `{QA / 'traceability_report.json'}`",
        f"- 원본 파일 대조 QA: `{QA / 'source_qa_report.json'}`",
    ]
    (REPORTS / "contract_rule_comparison_review.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> None:
    for path in [RAW_API, RAW_ALIO, STRUCTURED, NORMALIZED, COMPARE, QA, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)
    api_meta: dict[str, Any] = {}
    api_articles: dict[str, list[dict[str, Any]]] = {}
    api_units: dict[str, list[dict[str, Any]]] = {}
    api_supplementary: dict[str, list[dict[str, Any]]] = {}
    api_struct: dict[str, dict[str, Any]] = {}
    raw_manifest: dict[str, Any] = {"run": str(RUN), "created_at": now_iso(), "documents": {}}

    for doc_key, spec in DOCS.items():
        obj, raw, meta = fetch_api(doc_key, spec)
        raw_path = RAW_API / f"{doc_key}_{spec['api_id']}.response.json"
        raw_path.write_bytes(raw)
        api_meta[doc_key] = meta
        articles, units, structure = extract_api_articles(doc_key, obj)
        service = obj.get("AdmRulService") or find_first(obj, "AdmRulService")
        supplementary = extract_supplementary(doc_key, service)
        api_articles[doc_key] = articles
        api_units[doc_key] = units
        api_supplementary[doc_key] = supplementary
        structure["supplementary_entries"] = len(supplementary)
        api_struct[doc_key] = structure
        write_jsonl(STRUCTURED / f"{doc_key}_articles.jsonl", articles)
        write_jsonl(STRUCTURED / f"{doc_key}_supplementary.jsonl", supplementary)
        write_jsonl(NORMALIZED / f"{doc_key}_units.jsonl", units)
        write_json(STRUCTURED / f"{doc_key}_structure.json", structure)
        raw_manifest["documents"][doc_key] = {
            **{key: str(value) if isinstance(value, Path) else value for key, value in spec.items()},
            "raw_api_path": str(raw_path),
            "raw_sha256": meta["raw_sha256"],
            "raw_bytes": meta["raw_bytes"],
            "api_basic": meta["basic"],
            "structure": structure,
        }
    write_json(RAW_API / "manifest.json", raw_manifest)

    alio_downloads: dict[str, Any] = {}
    for doc_key, spec in DOCS.items():
        alio_downloads[doc_key] = fetch_alio_source(doc_key, spec)
    write_json(RAW_ALIO / "manifest.json", {"created_at": now_iso(), "documents": alio_downloads})

    pairs: list[dict[str, Any]] = []
    for a, b in combinations(DOCS, 2):
        pairs.extend(compare_pair(a, api_articles[a], b, api_articles[b]))

    trace: dict[str, Any] = {"documents": {}, "all_pass": True}
    for doc_key, articles in api_articles.items():
        keys = [x["article_key"] for x in articles]
        duplicate_keys = sorted([k for k, count in Counter(keys).items() if count > 1])
        missing_raw = [x["article_key"] for x in articles if not x.get("raw_text")]
        invalid_sources = [x["article_key"] for x in articles if not isinstance(x.get("source_item_index"), int)]
        unit_count = len(api_units[doc_key])
        doc_trace = {
            "article_count": len(articles),
            "unit_count": unit_count,
            "duplicate_article_keys": duplicate_keys,
            "missing_raw_text": missing_raw,
            "invalid_source_refs": invalid_sources,
            "all_article_keys_unique": not duplicate_keys,
            "all_articles_have_raw_text": not missing_raw,
            "all_articles_have_source_refs": not invalid_sources,
        }
        doc_trace["pass"] = all(doc_trace[k] for k in ["all_article_keys_unique", "all_articles_have_raw_text", "all_articles_have_source_refs"])
        trace["documents"][doc_key] = doc_trace
        trace["all_pass"] = trace["all_pass"] and doc_trace["pass"]
    write_json(QA / "traceability_report.json", trace)

    supplementary_trace: dict[str, Any] = {"documents": {}, "all_pass": True}
    for doc_key, rows in api_supplementary.items():
        missing_text = [x["supplementary_id"] for x in rows if not x.get("text_raw")]
        invalid_sources = [x["supplementary_id"] for x in rows if not isinstance(x.get("source_path"), str)]
        item = {
            "supplementary_count": len(rows),
            "missing_raw_text": missing_text,
            "invalid_source_refs": invalid_sources,
            "pass": not missing_text and not invalid_sources,
        }
        supplementary_trace["documents"][doc_key] = item
        supplementary_trace["all_pass"] = supplementary_trace["all_pass"] and item["pass"]
    write_json(QA / "supplementary_traceability_report.json", supplementary_trace)

    source_qa: dict[str, Any] = {"documents": {}, "all_pass": True}
    for doc_key, spec in DOCS.items():
        local_source = spec["local_source"]
        local_text = spec["local_text"]
        row: dict[str, Any] = {
            "document_key": doc_key,
            "api_id": spec["api_id"],
            "api_effective_at": api_meta[doc_key]["basic"].get("발령일자", ""),
            "local_effective_at": spec["local_effective_at"],
            "catalog_label_status": "match" if api_meta[doc_key]["basic"].get("발령일자", "").replace(".", "") == spec["local_effective_at"].replace(".", "") else "mismatch",
            "version_status": "pending_content_check",
            "local_source_path": str(local_source),
            "local_text_path": str(local_text),
            "local_source_exists": local_source.is_file(),
            "local_text_exists": local_text.is_file(),
        }
        downloaded = alio_downloads[doc_key]
        row.update({
            "downloaded_source_path": downloaded["path"],
            "downloaded_source_exists": Path(downloaded["path"]).is_file(),
            "downloaded_source_sha256": downloaded["sha256"],
            "downloaded_source_bytes": downloaded["bytes"],
            "download_http_status": downloaded["http_status"],
            "download_content_type": downloaded["content_type"],
        })
        if local_source.is_file():
            data = local_source.read_bytes()
            row.update({
                "local_source_sha256": sha256_bytes(data),
                "local_source_bytes": len(data),
                "download_matches_existing_local": sha256_bytes(data) == downloaded["sha256"],
            })
        if local_text.is_file():
            text = local_text.read_text(encoding="utf-8", errors="ignore")
            local_articles_raw = parse_local_text(doc_key, text)
            local_articles = [local_enriched(doc_key, x) for x in local_articles_raw]
            write_jsonl(QA / f"{doc_key}_local_source_articles.jsonl", local_articles)
            row["local_article_count"] = len(local_articles)
            row["local_article_keys"] = len({x["article_key"] for x in local_articles})
            api_by_key = {x["article_key"]: x for x in api_articles[doc_key]}
            local_by_key = {x["article_key"]: x for x in local_articles}
            common = sorted(set(api_by_key) & set(local_by_key))
            only_api = sorted(set(api_by_key) - set(local_by_key))
            only_local = sorted(set(local_by_key) - set(api_by_key))
            similarities = [body_similarity(api_by_key[k], local_by_key[k]) for k in common]
            exact = sum(api_by_key[k].get("body_semantic_compact", "") == local_by_key[k].get("body_semantic_compact", "") for k in common)
            row.update({
                "common_article_keys": len(common),
                "only_api_article_keys": only_api[:80],
                "only_local_article_keys": only_local[:80],
                "exact_semantic_body_matches": exact,
                "semantic_match_ratio": round(exact / len(common), 4) if common else 0,
                "mean_common_body_similarity": round(sum(similarities) / len(similarities), 4) if similarities else 0,
                "api_effective_date_found_in_local_text": effective_date_in_text(text, row["api_effective_at"]),
            })
            # Sample low-similarity same-key rows for manual source review.
            mismatches = []
            for k in common:
                score = body_similarity(api_by_key[k], local_by_key[k])
                if score < 0.75:
                    mismatches.append({
                        "article_key": k,
                        "api_title": api_by_key[k].get("title", ""),
                        "local_title": local_by_key[k].get("title", ""),
                        "score": round(score, 4),
                        "api_excerpt": normalize_layout(api_by_key[k].get("body_raw", ""))[:220],
                        "local_excerpt": normalize_layout(local_by_key[k].get("body_raw", ""))[:220],
                    })
            row["low_similarity_samples"] = sorted(mismatches, key=lambda x: x["score"])[:25]
            content_match = bool(
                row["common_article_keys"] == row["local_article_keys"] == len(api_articles[doc_key])
                and row["mean_common_body_similarity"] >= 0.95
                and (row["api_effective_date_found_in_local_text"] or row["catalog_label_status"] == "match")
            )
            row["content_version_status"] = "match" if content_match else "uncertain"
            row["version_status"] = row["content_version_status"]
        else:
            row["content_version_status"] = "unavailable"
            row["version_status"] = row["content_version_status"]
        row["pass"] = bool(
            row["local_source_exists"]
            and row["local_text_exists"]
            and row["downloaded_source_exists"]
            and row.get("download_matches_existing_local", False)
            and row["content_version_status"] == "match"
        )
        source_qa["documents"][doc_key] = row
        source_qa["all_pass"] = source_qa["all_pass"] and row["pass"]
    write_json(QA / "source_qa_report.json", source_qa)

    build_reports(api_meta, api_articles, api_struct, pairs, source_qa, trace)
    final = {
        "run": str(RUN),
        "raw_manifest": str(RAW_API / "manifest.json"),
        "comparison_summary": str(COMPARE / "comparison_summary.json"),
        "report": str(REPORTS / "contract_rule_comparison_review.md"),
        "traceability_pass": trace["all_pass"],
        "supplementary_traceability_pass": supplementary_trace["all_pass"],
        "supplementary_traceability_report": str(QA / "supplementary_traceability_report.json"),
        "source_qa_all_pass": source_qa["all_pass"],
        "api_article_counts": {k: len(v) for k, v in api_articles.items()},
        "alignment_rows": len(pairs),
    }
    write_json(RUN / "run_result.json", final)
    print(json.dumps(final, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

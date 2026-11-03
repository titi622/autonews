"""뉴스타파 공직자 재산 정보(jaesan.newstapa.org) 크롤러.

사이트는 Next.js 앱이며, 데이터는 아래 두 경로로 받을 수 있다.
  - 검색:  GET /api/search?q=<이름|소속>&page=<n>&limit=<n>&sort=wealth|name   -> JSON
  - 상세:  GET /people/<uniqueId>  (헤더 RSC: 1)  -> React Server Component 페이로드.
           줄 단위 "<id>:<json>" 형식이며 personDetail 객체 안에 연도별 records/details가 들어 있다.
  - 기타:  /api/person/count, /api/person/is_new, /api/chart, /api/person/search?id=1,2,3

사용 예:
  python crawlers/newstapa_jaesan.py search 고동진
  python crawlers/newstapa_jaesan.py detail g-69xFm-pi4m_
  python crawlers/newstapa_jaesan.py search 국회 --all --out data/assembly.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://jaesan.newstapa.org"
HEADERS = {"User-Agent": "Mozilla/5.0 (autonews crawler)", "Accept": "*/*"}


def _get(path: str, extra_headers: dict | None = None, retries: int = 3) -> bytes:
    req = urllib.request.Request(BASE + path, headers={**HEADERS, **(extra_headers or {})})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def count() -> int:
    return json.loads(_get("/api/person/count"))["totalPeople"]


def search(q: str, page: int = 1, limit: int = 24, sort: str = "wealth") -> dict:
    qs = urllib.parse.urlencode({"q": q, "page": page, "limit": limit, "sort": sort})
    return json.loads(_get(f"/api/search?{qs}"))


def search_all(q: str, limit: int = 100, sort: str = "wealth", delay: float = 0.3) -> list[dict]:
    out: list[dict] = []
    page = 1
    while True:
        res = search(q, page=page, limit=limit, sort=sort)
        out.extend(res.get("results", []))
        if len(out) >= res.get("total", 0) or not res.get("results"):
            break
        page += 1
        time.sleep(delay)
    return out


def _find_person_detail(obj):
    """RSC 페이로드 안에서 personDetail 객체를 재귀 탐색한다."""
    if isinstance(obj, dict):
        if "personDetail" in obj:
            return obj["personDetail"]
        for v in obj.values():
            r = _find_person_detail(v)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _find_person_detail(v)
            if r is not None:
                return r
    return None


def detail(unique_id: str) -> dict:
    raw = _get(f"/people/{unique_id}", {"RSC": "1"}).decode("utf-8")
    for line in raw.split("\n"):
        i = line.find(":")
        if i <= 0:
            continue
        body = line[i + 1:]
        if "personDetail" not in body:
            continue
        try:
            obj = json.loads(body)
        except json.JSONDecodeError:
            continue
        found = _find_person_detail(obj)
        if found is not None:
            return found
    raise ValueError(f"personDetail not found for {unique_id}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("q")
    s.add_argument("--all", action="store_true", help="모든 페이지 수집")
    s.add_argument("--sort", default="wealth", choices=["wealth", "name"])
    s.add_argument("--out")
    d = sub.add_parser("detail")
    d.add_argument("unique_id")
    d.add_argument("--out")
    sub.add_parser("count")
    a = ap.parse_args(argv)

    if a.cmd == "count":
        print(count())
        return 0
    if a.cmd == "search":
        data = search_all(a.q, sort=a.sort) if a.all else search(a.q, sort=a.sort)["results"]
    else:
        data = detail(a.unique_id)

    text = json.dumps(data, ensure_ascii=False, indent=2)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"saved {a.out}", file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

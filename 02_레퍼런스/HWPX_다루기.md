# 한글 문서를 파이썬으로 다루기 — 전날 삽질 정리

라이브러리: `python-hwpx` 6.6.0 (Apache-2.0, 순수 파이썬 + lxml)

```
pip install python-hwpx
```

## 제일 먼저 알아야 할 것: .hwp 는 못 읽는다

`python-hwpx` 는 **.hwpx (ZIP+XML) 전용**이다. 구형 `.hwp` (OLE2 바이너리)는 열리지 않는다.
`03_자료/원본_과업지시서/` 11건 중 10건이 .hwp 다. 길은 셋뿐이다.

1. 한글로 열어 `다른 이름으로 저장 → HWPX` — 가장 빠르다
2. 이미 뽑아 둔 `03_자료/발췌/*.json` 의 텍스트를 쓴다 (이 용도로 만든 파일이다)
3. OLE2 를 직접 파싱한다 — 한 시간은 날아간다. 현장에서는 하지 마라

나라장터 첨부는 .hwpx 와 .hwp 가 섞여 있다. 매직넘버로 가른다.

| 앞 4바이트 | 정체 |
|---|---|
| `50 4B 03 04` | ZIP → .hwpx (읽을 수 있다) |
| `D0 CF 11 E0` | OLE2 → 구형 .hwp (못 읽는다) |
| `25 50 44 46` | PDF |

## 기본

```python
from hwpx import HwpxDocument
HPt = '{http://www.hancom.co.kr/hwpml/2011/paragraph}t'   # 글자가 담긴 노드

doc = HwpxDocument.open('서식.hwpx')
sec = doc.sections[0]

for i, p in enumerate(sec.paragraphs):                     # 문단 읽기
    t = ''.join(x.text or '' for x in p.element.iter(HPt))
    print(i, t)

doc.save_to_path('결과.hwpx')
print(len(doc.validate().issues))                          # 0 이어야 한다
```

## 서식을 잃지 않고 새 줄을 넣는 법

**새로 만들지 말고, 원하는 모양의 문단을 복제해서 글자만 갈아 끼운다.**
글꼴·크기·들여쓰기·줄간격이 전부 그 문단에 붙어 있으므로 한 번에 따라온다.

```python
import copy
HP = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'

def clone(proto, text):
    e = copy.deepcopy(proto.element)
    runs = e.findall(HP + 'run')
    for r in runs[1:]: e.remove(r)          # run 하나만 남긴다
    if runs:
        ts = runs[0].findall(HPt)
        for t in ts[1:]: runs[0].remove(t)
        if ts:
            ts[0].text = text
            for c in list(ts[0]): ts[0].remove(c)
    for seg in e.findall(HP + 'linesegarray'):
        e.remove(seg)                        # 줄 배치 캐시는 지운다. 안 지우면 글자가 겹친다
    return e

sec.insert_paragraphs(idx, [clone(sec.paragraphs[표본], '넣을 글'), ...])
```

문단 삭제는 **반드시 뒤에서부터**. 앞에서 지우면 인덱스가 밀린다.

```python
for i in range(끝, 시작 - 1, -1):
    sec.remove_paragraph(i)
```

## 함정

**`apply_paragraph_format()` 을 쓰지 마라.**
header.xml 에 정의되지 않은 paraPr id 를 참조하는 문단을 만든다.
`validate()` 는 통과하는데 한글에서 열면 서식이 조용히 깨진다.
서식에 이미 있는 id 를 재사용하는 게 유일하게 안전한 길이다.

**`doc.tables.all` 은 메서드가 아니라 속성이다.** `all()` 로 부르면 터진다.

**글꼴 이름은 한 글자도 틀리면 안 된다.**
경기천년체는 OTF판과 TTF판의 **이름이 다르다**.

| 설치본 | 한글에서 써야 하는 이름 |
|---|---|
| OTF | `경기천년바탕OTF Regular`, `경기천년제목OTF Medium`, `경기천년제목OTF Bold` |
| TTF | `경기천년바탕 Regular`, `경기천년제목 Medium` |

틀리면 에러가 아니라 **조용히 바탕글로 바뀐다.** 폰트가 안 먹는다고 코드를 세 번 고치기 전에
`C:\Windows\Fonts` 에서 설치본이 어느 쪽인지 먼저 보라. (`00_점검/환경점검.py` 가 봐 준다)

**목차는 문단이 아니라 표다.** 셀 하나에 문단이 수십 개 들어 있다.
통째로 덮어쓰면 서식이 다 날아간다. 줄 단위로 고쳐야 한다.

**쪽 나눔은 문단 속성이다.** `par.element.set('pageBreak', '1')`.
서식에서 쪽 나눔이 걸려 있던 문단을 지우면 쪽 나눔도 같이 사라진다. 장 머리에 다시 걸어 줘야 한다.

**글자 치환은 표 안까지 훑어야 한다.** `sec.paragraphs` 만 돌면 표 안의 글자를 놓친다.

```python
for t in sec.element.iter(HPt):        # 표 안까지 전부
    if t.text: t.text = t.text.replace(옛것, 새것)
```

**사업명·담당자 이름이 서식에 박혀 있다.** 라벨이 기관마다 다르다 —
`과 업 명`, `용 역 명`, `사 업 명` 이 다 나온다. 하나만 보고 찾으면 치환이 전부 불발된다.

**직급만 보고 이름을 지우면 조항이 깨진다.**
`제14조(민·형사상 책임)` 의 `책임` 을 직급으로 보면 `제14조(민·○○○ 책임)` 이 된다.
부서·기관 이름이 앞에 붙은 경우만 지우는 게 안전하다.

## HWPUNIT

1 HWPUNIT = 1/7200 인치. 글자 크기는 pt × 100 (15pt → 1500).

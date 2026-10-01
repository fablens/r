# -*- coding: utf-8 -*-
"""환경점검.py — 현장 PC 가 일할 준비가 됐는지 한 번에 본다.

    python 환경점검.py

네트워크는 보지 않는다. 그건 배관점검.html 로 본다.
"""
import sys, os, glob, platform

OK, NG = "[O]", "[X]"
bad = 0

def say(ok, *a):
    global bad
    print(OK if ok else NG, *a)
    if not ok: bad += 1

print("=" * 52)
print(" 환경 점검")
print("=" * 52)
say(sys.version_info >= (3, 10), "파이썬", platform.python_version(),
    "" if sys.version_info >= (3, 10) else "→ 3.10 이상 필요")
print("   실행 경로:", sys.executable)

try:
    import hwpx
    from hwpx import HwpxDocument
    say(True, "python-hwpx", getattr(hwpx, "__version__", "설치됨"))
    try:
        import lxml.etree as E
        say(True, "lxml", E.__version__)
    except Exception as e:
        say(False, "lxml 없음 —", e)
except Exception as e:
    say(False, "python-hwpx 없음 → 01_설치/설치.bat 실행 —", e)

# 글꼴 — 설치된 이름이 OTF판인지 TTF판인지가 중요하다
if os.name == "nt":
    d = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    f = [os.path.basename(x) for x in glob.glob(os.path.join(d, "*경기천년*"))]
    say(bool(f), "경기천년체 설치본 %d개" % len(f))
    for x in sorted(f): print("     ", x)
    if f:
        print("   ※ 파일명에 OTF 가 있으면 한글에서 쓸 이름도 '경기천년바탕OTF Regular' 꼴이다.")
        print("      이름이 한 글자라도 다르면 한글은 조용히 바탕글로 바꿔 버린다.")
else:
    print("   (글꼴 점검은 윈도우에서만)")

# 서식 / 자료
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p, what in [("03_자료/서식", "서식 .hwpx"),
                ("03_자료/원본_과업지시서", "공개 공고문"),
                ("03_자료/발췌", "발췌 JSON")]:
    g = glob.glob(os.path.join(root, p, "*"))
    say(bool(g), "%s %d건" % (what, len(g)))

# 서식이 실제로 열리는지
try:
    from hwpx import HwpxDocument
    s = sorted(glob.glob(os.path.join(root, "03_자료/서식", "*.hwpx")))
    if s:
        doc = HwpxDocument.open(s[0])
        n = len(doc.sections[0].paragraphs)
        say(n > 50, "%s 열림 — 문단 %d개" % (os.path.basename(s[0])[:34], n))
        say(len(doc.validate().issues) == 0, "서식 자체 검증 통과")
except Exception as e:
    say(False, "서식 열기 실패 —", e)

print("-" * 52)
print("문제 없음. 시작하세요." if not bad else "문제 %d건. 위를 먼저 해결하세요." % bad)

# Gemini 호출 — 전날 삽질 정리

## 1. 모델 이름을 코드에 박지 마라

전날 테스트에서 **키는 멀쩡한데 모델 이름이 죽어** LLM 경로 전체가 멈췄다.

```
gemini-2.0-flash  →  404  "This model is no longer available."
gemini-2.5-flash  →  404
```

**404 와 401 을 구별하라.** 401/403 은 키 문제, 404 는 모델 이름 문제다.
시작할 때 목록을 받아 거기서 고른다.

```
GET https://generativelanguage.googleapis.com/v1beta/models?key=<KEY>
```

전날(10/1) 실제로 생성까지 된 것: `gemini-3-flash-preview`, `gemini-3.1-flash-lite`
503(과부하)이던 것: `gemini-flash-latest`, `gemini-3.8-flash`

**503 은 모델이 없는 게 아니라 붐비는 것이다.** 다른 모델로 넘어가면 된다.

## 2. 사고 토큰이 출력 예산을 같이 먹는다

gemini-3 계열은 생각을 한다. 그 토큰이 `maxOutputTokens` 에 **같이 잡힌다.**
넘치면 에러가 아니라 `finishReason: "MAX_TOKENS"` 와 **중간에 잘린 JSON** 이 온다.
`JSON.parse` 가 터지고, 겉으로는 "답을 읽지 못했습니다" 로만 보인다.

18항목을 한 번에 시켰을 때 실측:

```
사고 2,135 토큰 + 본문 1,641 토큰 = 3,776    ← 근거 없이, 짧은 프롬프트
```

근거를 붙이면 여기서 몇 배로 늘어난다. 그래서:

```json
"generationConfig": {
  "temperature": 0.35,
  "maxOutputTokens": 16384,
  "responseMimeType": "application/json",
  "thinkingConfig": { "thinkingLevel": "low" }
}
```

`thinkingLevel: "low"` 는 사고를 174토큰까지 줄인다. `thinkingBudget: 0` 으로 완전히 끌 수도 있다.
**`finishReason` 을 반드시 확인하라.** `STOP` 이 아니면 결과를 믿지 마라.

## 3. 응답은 part 를 전부 이어붙인다

`parts[0].text` 만 읽으면 안 된다. 생각하는 모델은 part 를 여러 개 낸다.

```js
const c = (j.candidates||[])[0]||{};
const txt = ((c.content&&c.content.parts)||[]).map(p=>p.text||'').join('');
```

part 안에 `thoughtSignature` 가 섞여 와도 `text` 만 모으면 된다.

## 4. JSON 모드를 써도 울타리가 붙어 올 때가 있다

```js
let s = String(txt).trim().replace(/^```(?:json)?\s*/i,'').replace(/```\s*$/,'');
s = s.slice(s.indexOf('{'), s.lastIndexOf('}')+1);
JSON.parse(s);
```

## 5. 브라우저에서 바로 불러도 된다

CORS 가 열려 있어 서버가 필요 없다. 다만 **키가 네트워크 탭에 그대로 보인다.**
현장 시연에서는 개발자도구를 열지 마라. 끝나고 키를 재발급하라.

## 6. 쓸 만한 프롬프트 규칙

실제로 효과가 있던 것만:

- 쓸 항목 이름을 **그대로** 돌려 달라고 못 박는다 (`{"항목명": ["문장"]}`)
- 금액·기간·장소·규모는 **입력값에 있는 것만** 쓰라고 명시한다 — 안 하면 지어낸다
- 문장 끝을 `~한다`, `~하여야 한다` 로 고정한다 — 안 하면 `~합니다` 가 섞인다
- 한 줄 40~90자로 길이를 묶는다 — 안 하면 한 줄이 300자가 된다
- 근거를 베끼지 말라고 쓴다. 그래도 베끼면 근거를 더 짧게 자른다

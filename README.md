# 🥚 Sally 블로그 자동화 시스템

매일 아침 7시, Sally의 네이버 블로그 글이 자동으로 준비되고 **텔레그램으로 알림**이 와요.

## 🎯 이게 뭐예요?

GitHub Actions가 매일 아침 7시에 자동으로 실행돼서:
1. 오늘의 주제를 선정하고 (요일별 카테고리)
2. Sally 톤으로 블로그 글을 작성하고
3. 태그 30개, 썸네일 문구, 이미지 프롬프트까지 만들어서
4. **텔레그램으로 바로 보내줘요** 📱

**Sally님이 할 일**: 텔레그램 알림 받고 → 글 복사 → 네이버 블로그에 붙여넣기 → 사진 추가 → 발행 (약 10분)

## 💰 비용

**월 0원** (Gemini 2.5 Flash 무료 티어 + GitHub Actions 무료 + 텔레그램 무료)

---

## 🚀 처음 한 번만 세팅하기 (25분)

### 1단계: Gemini API 키 발급 (5분)

1. https://aistudio.google.com 접속
2. Google 계정으로 로그인
3. **`Get API key`** 클릭 → **`Create API key`**
4. 새 프로젝트에서 키 생성
5. **생성된 키를 복사** (메모장에 임시 저장)
   - 예시: `AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 2단계: 텔레그램 봇 만들기 (5분)

1. 텔레그램에서 **`@BotFather`** 검색 → 대화 시작
2. `/newbot` 입력
3. 봇 이름 입력 (예: `Sally Blog Bot`)
4. 봇 아이디 입력 (예: `sally_blog_auto_bot` - 반드시 `_bot`으로 끝)
5. **Bot Token 복사해서 저장**
   - 예시: `7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 3단계: Chat ID 알아내기 (2분)

1. 방금 만든 봇과 대화 시작 (BotFather가 알려준 봇 링크 클릭해서 `/start` 입력)
2. 봇에게 아무 메시지 보내기 (예: "안녕")
3. 브라우저에서 아래 주소 접속 (`<TOKEN>` 자리에 본인 봇 토큰 붙여넣기):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
4. 결과에서 `"chat":{"id": 123456789` 부분 **숫자 복사**
   - 예시: `123456789`

### 4단계: GitHub 레포 만들기 (5분)

1. https://github.com 접속 → 우측 상단 `+` → `New repository`
2. Repository name: `sally-blog-auto` (아무거나 괜찮아요)
3. **Public** 선택 (Private이면 Actions 무료 한도가 작음)
4. **`Create repository`** 클릭
5. 이 폴더 파일들 전부 업로드 (드래그 앤 드롭)

### 5단계: GitHub Secrets 등록 (5분)

레포 페이지 → **`Settings`** → **`Secrets and variables`** → **`Actions`** → **`New repository secret`**

**총 3개를 등록해야 해요:**

| Name | Secret |
|------|--------|
| `GEMINI_API_KEY` | 1단계에서 복사한 Gemini 키 |
| `TELEGRAM_BOT_TOKEN` | 2단계에서 복사한 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 3단계에서 복사한 숫자 |

⚠️ **이름 정확히 입력**: 대소문자, 밑줄 위치 전부 맞아야 해요.

### 6단계: 첫 실행 테스트 (3분)

1. 레포 상단 **`Actions`** 탭
2. 왼쪽 `Sally 블로그 자동 생성` 클릭
3. 우측 **`Run workflow`** 버튼 → **`Run workflow`** 클릭
4. 1~2분 기다리기
5. **텔레그램에 알림 와요!** 📱
6. 봇이 보낸 파일 그대로 네이버에 복붙하시면 돼요

---

## 📱 텔레그램으로 받는 내용

매일 아침 7시에 이렇게 와요:

**메시지 1**: 오늘의 글 요약 + 체크리스트 + GitHub 링크  
**메시지 2**: `post.md` 파일 첨부 (탭하면 전체 글 열림)  
**메시지 3**: 태그 30개 (복사 버튼 한 번으로 복사)

---

## 📁 파일 구조

```
sally-blog-auto/
├── .github/workflows/
│   └── daily-post.yml          ← 자동 실행 스케줄
├── scripts/
│   ├── generate_post.py        ← 글 생성 스크립트
│   └── send_telegram.py        ← 텔레그램 알림 스크립트
├── prompts/
│   └── sally_style.md          ← Sally 톤 가이드
├── posts/                      ← 매일 여기에 쌓임
│   └── 2026-04-21/
│       ├── post.md             ← ⭐ 네이버 붙여넣을 글
│       ├── tags.txt            ← 태그 30개
│       ├── thumbnail.txt       ← 썸네일 문구
│       ├── image_prompts.md    ← 이미지 생성 프롬프트
│       └── meta.json           ← 메타 정보
└── README.md                   ← 이 파일
```

---

## 🗓 요일별 주제 로테이션

저품질 블로그 방지를 위해 요일별 카테고리 다름:

- **월요일**: 천안 맛집·카페
- **화요일**: 대학생 꿀팁·자기계발
- **수요일**: 자격증·어학 후기
- **목요일**: MZ 트렌드·SNS
- **금요일**: 천안 대학생 혜택·공모전
- **토요일**: 일상·라이프
- **일요일**: 외부활동·서포터즈 후기

주제 수정하려면 `scripts/generate_post.py`의 `TOPIC_CATEGORIES` 편집.

---

## 💡 매일 아침 루틴 (10분)

1. 📱 텔레그램 알림 확인
2. 📎 봇이 보낸 `post.md` 파일 탭해서 열기
3. 📋 전체 텍스트 복사
4. 🌐 네이버 블로그 글쓰기 → 붙여넣기
5. 🖼 `[사진: ...]` 자리에 사진 넣기
6. ✏️ `[확인필요: ...]` 부분 공식 사이트에서 검증 후 수정
7. 🏷 텔레그램에 온 태그 복사해서 하단에 붙여넣기
8. 🚀 발행!

---

## ⚠️ 주의사항

- **[확인필요] 부분은 반드시 검증**: AI가 지어낸 가짜 정보일 수 있어요. 맛집 주소·가격, 공모전 마감일·지원금 금액 등은 공식 사이트에서 확인 필수.
- **네이버 정책**: 발행은 Sally님이 직접 하셔야 해요 (자동 발행은 어뷰징).
- **AI 티 수정**: 생성된 글 한 번 훑어보고 어색한 부분 본인 말투로 다듬기.
- **봇 토큰 유출 주의**: Bot Token 절대 공유 금지. 유출되면 BotFather에서 `/revoke` 로 재발급.

---

## 🛠 트러블슈팅

**Q. 텔레그램 알림이 안 와요**  
- Secret 이름 정확히 `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` 인지 확인
- 봇에게 먼저 `/start` 보냈는지 확인 (안 보내면 봇이 메시지 못 보냄)
- Chat ID가 숫자만 있는지 (따옴표 X)
- Actions 탭에서 실행 로그 확인

**Q. getUpdates에 아무것도 안 보여요**  
A. 봇에게 먼저 아무 메시지나 보내세요. 그다음 다시 접속.

**Q. API 키 에러**  
A. Secret 이름 `GEMINI_API_KEY` 정확히 맞는지 (대소문자, 밑줄).

**Q. 글이 이상하게 나와요**  
A. `scripts/generate_post.py`의 `SALLY_STYLE` 변수에 규칙 추가/수정.

**Q. 시간을 바꾸고 싶어요**  
A. `.github/workflows/daily-post.yml`의 `cron: '0 22 * * *'` 수정  
- UTC 기준 (한국시간 - 9시간)
- 한국 오전 7시 = `'0 22 * * *'` (UTC 전날 22시)
- 한국 오전 9시 = `'0 0 * * *'`
- 한국 오후 6시 = `'0 9 * * *'`

**Q. 수동으로 글 생성하고 싶을 때**  
A. Actions 탭 → `Sally 블로그 자동 생성` → Run workflow

---

## 🎯 다음 단계 (나중에 원하시면)

- [ ] 이미지 자동 생성 (Imagen, Stable Diffusion)
- [ ] 네이버 데이터랩 실시간 트렌드 연동
- [ ] 텔레그램에서 버튼으로 주제 선택
- [ ] 블로그 통계 주간 리포트

필요해지면 추가해드릴게요!

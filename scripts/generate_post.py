"""
Sally 블로그 자동 생성 스크립트
매일 아침 실행되어 오늘의 블로그 글을 생성합니다.

[v2.1 변경사항]
- grounding(Google Search) 제거 → 구버전 SDK 호환성 문제 해결
- 카테고리별 '실존하는 공식 URL' 하드코딩 방식으로 전환
- 프롬프트에 공식 사이트 URL 전달 → Gemini가 지어내는 대신 이 URL을 언급
- "가짜 경험 금지" 프롬프트 강제 유지
- 출처 섹션에 공식 URL 자동 삽입
"""

import os
import json
import random
from datetime import datetime
from pathlib import Path
import google.generativeai as genai

# ========== 설정 ==========
API_KEY = os.environ.get('GEMINI_API_KEY')
if not API_KEY:
    raise ValueError("GEMINI_API_KEY 환경변수가 없어요. GitHub Secrets에 등록해주세요.")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# ========== Sally 블로그 DNA ==========
SALLY_STYLE = """
[Sally 블로그 스타일 가이드 - 반드시 준수]

◆ 블로그 정체성
- 닉네임: Sally, 블로그명: Sally의 삶은 계란
- 포지션: 천안 대학생들에게 유용한 정보를 큐레이션해서 전달하는 정보 전달자
- 타겟: 천안 대학생 (상명대·호서대·단국대·백석대), 자기계발 MZ

◆ ⚠️ 가장 중요한 규칙 (절대 위반 금지)
- Sally는 직접 경험하지 않은 일을 "경험했다"고 쓰면 절대 안 됩니다.
- "서포터즈 1기로 활동했어요", "합격했어요", "발대식에 참여했어요" 같은 허위 경험 서술 금지.
- 대신 "정보 전달자" 톤으로 작성: "찾아봤어요", "정리해봤어요", "알아봤어요", "이런 정보가 있더라고요".
- 실제로 존재하지 않는 특정 프로그램명·공모전명·자격증명을 지어내면 안 됩니다.
- 구체적인 프로그램명을 언급할 때는 제공된 [공식 URL 리스트]에 있는 사이트들을 안내하는 형태로만 작성하세요.
- 상세 내용(마감일, 상금, 신청 조건 등)은 대부분 `[확인필요: 공식 사이트에서 최신 정보 확인]` 으로 표시하세요.
- "아래 공식 사이트에서 현재 모집 중인 프로그램을 확인해보세요" 같은 안내형 문구를 적극 사용하세요.

◆ 말투 규칙
- 기본: 친근한 존댓말 ("~해요", "~거든요", "~잖아요", "~더라고요")
- 감정 표현: ㅎㅎ, ㅋㅋㅋ, ㅠㅠ 자연스럽게 섞기
- 강조어: "진짜", "정말", "완전", "너무너무", "확실히" 자주 사용
- 느낌표 2~3개 연속 가능 ("유용해요!!", "꿀정보!!!")
- 절대 금지: "~에 대해 알아보도록 하겠습니다", "다음과 같습니다", "결론적으로"

◆ 오프닝 공식 (반드시 이 순서로)
🐾 [핵심 키워드] [서브 설명]

[주제 한 줄 요약]

안녕하세요~! 여러분 Sally입니다~!

[공감형 도입 3~4줄: "요즘 ~찾고 계신 분들 많지 않나요?" 스타일]

[이 글에서 뭘 알려주는지 한 줄 예고]

◆ 섹션 이모지 규칙
- 📍 기본정보/개요
- 📋 상세정보/자격요건/혜택
- ⏰ 일정/마감일
- 💰 비용/지원금
- 🔗 신청 링크/공식 사이트
- ✅ 이런 분들께 추천 (체크리스트)
- ⚠️ 주의사항/꼭 확인할 점
- 💬 마무리 한 마디

◆ 문단 구조
- 문장 1~2개마다 엔터 (빈 줄)
- 한 문단 3줄 넘지 않기
- 정보는 리스트·소제목으로 구조화

◆ 필수 구성
1. 🐾 오프닝 + Sally 인사
2. 공감형 도입 3~4줄 + 글 예고
3. 📍 개요 섹션 (이 정보가 왜 유용한지, 어디서 찾을 수 있는지)
4. 📋 어떤 종류의 프로그램/혜택이 있는지 (구체 사례 대신 '유형' 위주)
5. 🔗 공식 사이트 안내 (제공된 URL들을 자연스럽게 소개)
6. ⚠️ 주의사항 섹션 (중복지원 제한, 자격 요건 확인 등 일반적 주의점)
7. ✅ 이런 분들께 추천합니다 (6~7개 체크리스트)
8. 💬 마무리 한 마디
9. 시그니처 클로징: "더 궁금한 점은 아래 공식 사이트에서 확인해보세요! Sally가 정리한 정보가 도움이 됐다면 댓글 남겨주세요 :)"

◆ 이미지 자리 표시
- 본문 중간 3~5군데에 `[사진: 무엇을 캡처하거나 찍으면 좋을지]` 로 표시
- 공식 사이트 스크린샷 위주로 안내 (본인 사진 부담 줄이기)
"""

# ========== 주제 풀 (카테고리별 공식 URL 포함) ==========
TOPIC_CATEGORIES = {
    "monday": {
        "category": "대학생 공모전 정보",
        "themes": [
            "대학생이 참여 가능한 공모전 찾는 법",
            "요즘 많이 열리는 대학생 공모전 유형 정리",
            "아이디어·영상·수기 공모전 종합 안내",
            "공모전 준비할 때 확인해야 할 기본 정보",
        ],
        "source_urls": [
            ("캠퍼스픽 공모전", "https://www.campuspick.com/contest"),
            ("링커리어 공모전", "https://linkareer.com/list/contest"),
            ("씽유 공모전", "https://www.thinkcontest.com/"),
            ("위비티 공모전", "https://www.wevity.com/"),
            ("대한민국 공모전 광장", "https://www.all-con.co.kr/"),
        ],
    },
    "tuesday": {
        "category": "청년정책 신청 가이드",
        "themes": [
            "청년도약계좌 제도 이해하기",
            "국민취업지원제도 Ⅰ·Ⅱ유형 차이",
            "청년내일채움공제 개요",
            "청년월세특별지원 제도 안내",
            "대학생 국가장학금 기본 정보",
            "청년마음건강바우첗 안내",
        ],
        "source_urls": [
            ("온라인청년센터(청년정책 통합포털)", "https://www.youthcenter.go.kr/"),
            ("복지로", "https://www.bokjiro.go.kr/"),
            ("정부24", "https://www.gov.kr/"),
            ("한국장학재단", "https://www.kosaf.go.kr/"),
            ("고용24 (국민취업지원제도)", "https://www.work24.go.kr/"),
        ],
    },
    "wednesday": {
        "category": "자격증 접수·일정",
        "themes": [
            "대학생이 준비할 만한 국가기술자격증 유형 정리",
            "어학 시험 종류와 차이 (토익·오픽·텝스)",
            "컴활·워드 등 사무용 자격증 개요",
            "SQLD·정보처리기사 등 IT 자격증 개요",
            "GTQ·컬러리스트 등 디자인 자격증 안내",
            "한국사능력검정시험 취업 가산점 활용법",
        ],
        "source_urls": [
            ("Q-net (한국산업인력공단)", "https://www.q-net.or.kr/"),
            ("대한상공회의소 자격평가사업단 (컴활 등)", "https://license.korcham.net/"),
            ("토익 위원회", "https://exam.toeic.co.kr/"),
            ("한국사능력검정시험", "https://www.historyexam.go.kr/"),
            ("정보처리기사 (큐넷)", "https://www.q-net.or.kr/crf005.do?id=crf00506"),
        ],
    },
    "thursday": {
        "category": "대외활동·서포터즈 모집",
        "themes": [
            "대학생 서포터즈 활동의 종류와 특징",
            "기업·공공기관 서포터즈 차이점",
            "대학생 기자단 지원 가이드",
            "해외탐방 지원 프로그램 찾는 법",
            "장학금을 주는 대외활동 정리",
            "문화·예술 분야 서포터즈 개요",
        ],
        "source_urls": [
            ("캠퍼스픽 대외활동", "https://www.campuspick.com/activity"),
            ("링커리어 대외활동", "https://linkareer.com/list/activity"),
            ("대학내일 대외활동", "https://univ20.com/"),
            ("씽유 대외활동", "https://www.thinkcontest.com/"),
            ("잡코리아 대외활동", "https://www.jobkorea.co.kr/"),
        ],
    },
    "friday": {
        "category": "천안·충남 청년 혜택",
        "themes": [
            "천안시 청년 지원사업 찾는 법",
            "충청남도 청년정책 종합 안내",
            "천안·충남 대학생이 받을 수 있는 혜택 유형",
            "지역 청년센터·청년공간 활용 가이드",
            "청년 주거지원 제도 개요",
            "상명대·호서대·단국대·백석대 학생 지역 혜택 찾기",
        ],
        "source_urls": [
            ("천안시청 청년정책", "https://www.cheonan.go.kr/youth.do"),
            ("충청남도 청년정책", "https://www.chungnam.go.kr/yfprMain.do"),
            ("충남청년이음 플랫폼", "https://www.cnyouth.or.kr/"),
            ("온라인청년센터", "https://www.youthcenter.go.kr/"),
            ("대한민국 구석구석 천안", "https://korean.visitkorea.or.kr/"),
        ],
    },
    "saturday": {
        "category": "IT·개발 교육·부트캠프",
        "themes": [
            "대학생이 받을 수 있는 무료·국비 개발 교육 종류",
            "K-디지털 트레이닝 개요",
            "주요 SW 아카데미 프로그램 비교",
            "부트캠프 선택할 때 체크 포인트",
            "AI·데이터 분야 교육 프로그램 유형",
            "개발 교육 지원금·훈련수당 정리",
        ],
        "source_urls": [
            ("HRD-Net (K-디지털 트레이닝)", "https://www.hrd.go.kr/"),
            ("SSAFY (삼성청년SW아카데미)", "https://www.ssafy.com/"),
            ("우아한테크코스", "https://woowacourse.github.io/"),
            ("네이버 부스트캠프", "https://boostcamp.connect.or.kr/"),
            ("프로그래머스 데브코스", "https://programmers.co.kr/school"),
        ],
    },
    "sunday": {
        "category": "주간 정보 정리·회고",
        "themes": [
            "이번주 대학생이 챙겨볼 만한 정보 정리",
            "공모전·대외활동·자격증 정보 찾는 사이트 총정리",
            "대학생 필수 북마크 사이트 모음",
            "취업 준비 시작 단계별 가이드",
        ],
        "source_urls": [
            ("캠퍼스픽", "https://www.campuspick.com/"),
            ("링커리어", "https://linkareer.com/"),
            ("온라인청년센터", "https://www.youthcenter.go.kr/"),
            ("Q-net", "https://www.q-net.or.kr/"),
            ("HRD-Net", "https://www.hrd.go.kr/"),
        ],
    },
}


def get_today_topic():
    """오늘 요일에 맞는 주제 카테고리에서 랜덤 선택"""
    weekday_map = ["monday", "tuesday", "wednesday", "thursday",
                   "friday", "saturday", "sunday"]
    today = weekday_map[datetime.now().weekday()]
    day_data = TOPIC_CATEGORIES[today]
    theme = random.choice(day_data["themes"])
    source_urls = day_data["source_urls"]
    return day_data["category"], theme, source_urls


def format_urls_for_prompt(source_urls):
    """URL 리스트를 프롬프트용 텍스트로 포맷"""
    lines = []
    for title, url in source_urls:
        lines.append(f"- {title}: {url}")
    return "\n".join(lines)


def generate_topic_detail(category, theme, source_urls):
    """블로그 글 구성 기획"""
    urls_text = format_urls_for_prompt(source_urls)

    prompt = f"""당신은 천안 대학생 블로거 Sally의 콘텐츠 기획자입니다.
아래 주제로 블로그 글의 구성을 JSON으로 만들어주세요.

대분류: {category}
주제: {theme}

[참고할 공식 사이트 URL]
{urls_text}

다음 JSON 형식으로만 답하세요 (다른 설명 없이):
{{
  "post_title": "블로그 제목 (32자 이내, '정리', '총정리', '찾는 법', '신청 방법' 등 정보성 키워드 포함)",
  "main_keyword": "네이버 검색 최적화 메인 키워드",
  "sub_keywords": ["서브키워드1", "서브키워드2", "서브키워드3", "서브키워드4"],
  "hook": "도입부 훅 한 줄 (요즘 ~찾고 계신 분들 많죠? 스타일)",
  "outline": ["소제목1", "소제목2", "소제목3", "소제목4", "소제목5"],
  "target_readers": "이 글을 읽을 타겟 독자"
}}"""

    response = model.generate_content(prompt)
    text = response.text.strip()

    if text.startswith('```'):
        text = text.split('```')[1]
        if text.startswith('json'):
            text = text[4:]
        text = text.strip()

    return json.loads(text)


def generate_blog_post(category, theme, detail, source_urls):
    """Sally 스타일로 블로그 본문 작성"""
    urls_text = format_urls_for_prompt(source_urls)

    prompt = f"""{SALLY_STYLE}

---

위 스타일 가이드를 100% 준수해서 네이버 블로그 포스팅을 작성해주세요.

[오늘의 글 정보]
- 대분류: {category}
- 주제: {theme}
- 제목: {detail['post_title']}
- 메인 키워드: {detail['main_keyword']}
- 서브 키워드: {', '.join(detail['sub_keywords'])}
- 도입 훅: {detail['hook']}
- 구성: {' → '.join(detail['outline'])}

[⭐ 반드시 본문에 자연스럽게 언급할 공식 사이트 URL]
{urls_text}

[작성 규칙 - 절대 준수]
1. ⚠️ 특정 공모전명/프로그램명을 함부로 지어내지 마세요. 
   예: "청춘 에너자이저 서포터즈 1기" 같은 허구의 이름 금지.
   대신 "캠퍼스픽에서 '대학생'으로 필터하면 다양한 공모전이 뜨더라고요" 같은 안내형 서술 사용.
2. ⚠️ "참여했어요", "합격했어요" 같은 직접 경험 서술 절대 금지. 
   "알아봤어요", "정리해봤어요", "찾아보니까 이런 사이트가 있더라고요" 스타일.
3. 구체적인 숫자(상금, 마감일, 지원 금액)는 대부분 `[확인필요: 공식 사이트 최신 공고]` 로 표시.
4. 분량: 2,000~2,500자
5. Sally 오프닝 공식으로 시작
6. 문단 사이 빈 줄 충분히 (모바일 가독성)
7. 이미지 자리 3~5군데 `[사진: 구체적 가이드 - 주로 공식 사이트 스크린샷]` 로 표시
8. 📍📋⏰💰🔗⚠️✅💬 섹션 이모지 반드시 사용
9. 🔗 섹션에서 위에 제공된 공식 사이트 URL을 **전부** 소개하세요. 각 사이트의 특징을 Sally 톤으로 한 줄씩 설명.
10. 마지막에 Sally 시그니처 클로징 필수

[출력]
제목은 제외하고 본문만 작성하세요. 네이버 블로그에 바로 붙여넣을 수 있는 형태로요.
"""

    response = model.generate_content(prompt)
    return response.text.strip()


def generate_tags(detail, category):
    """Sally 스타일 태그 30개 생성"""
    prompt = f"""Sally의 네이버 블로그에 쓸 태그 30개를 만들어주세요.

주제: {detail['post_title']}
메인 키워드: {detail['main_keyword']}
서브 키워드: {', '.join(detail['sub_keywords'])}
카테고리: {category}

규칙:
- 지역 키워드 (천안, 상명대, 호서대, 단국대, 백석대 중 맞는 것)
- 주제 롱테일 키워드 10개 이상 (검색 유입 목적)
- 소통 키워드: 서이추, 서로이웃, 서이추환영, 소통해요, 이웃추가
- 정체성 키워드: 대학생블로그, 대학생정보, 자기계발, 취업준비
- 정보성 키워드: 정리, 총정리, 꿀정보, 신청방법 등 자연스럽게

출력: 각 태그 앞에 # 붙여서 한 줄에 하나씩, 총 30개. 다른 설명 없이 태그만 출력하세요."""

    response = model.generate_content(prompt)
    return response.text.strip()


def generate_thumbnail_text(detail):
    """썸네일 문구 생성"""
    prompt = f"""네이버 블로그 썸네일 이미지에 올릴 문구를 만들어주세요.

주제: {detail['post_title']}
메인 키워드: {detail['main_keyword']}

규칙:
- 2줄
- 줄당 10~15자
- 정보성 임팩트 (숫자, '총정리', '찾는 법', '꿀정보' 등 활용)
- Sally 스타일 친근함

출력 예시:
대학생 공모전
찾는 사이트 5곳

다른 설명 없이 2줄만 출력하세요."""

    response = model.generate_content(prompt)
    return response.text.strip()


def generate_image_prompts(detail, post_content):
    """이미지 생성용 프롬프트 만들기"""
    prompt = f"""블로그 포스팅에 쓸 이미지 5장의 가이드를 만들어주세요.

블로그 주제: {detail['post_title']}
메인 키워드: {detail['main_keyword']}
본문 요약: {post_content[:500]}

각 이미지마다 다음 형식으로:

### 이미지 N: [무슨 이미지인지 한국어 설명]
**촬영/캡처 가이드**: [공식 사이트 스크린샷인지, 포스터 이미지인지, 직접 제작 다이어그램인지 등 구체적 안내]
**영어 프롬프트 (AI 생성 시)**: [DALL-E/Midjourney용 영어 프롬프트]
**용도**: [블로그 어느 섹션에 들어갈지]
**무료 대안**: [Unsplash/Pexels 검색 키워드]

정보성 블로그이므로 공식 사이트 스크린샷, 포스터, 인포그래픽 위주로 안내해주세요."""

    response = model.generate_content(prompt)
    return response.text.strip()


def format_sources_section(source_urls):
    """본문 하단에 붙일 출처 섹션 생성"""
    if not source_urls:
        return ""

    section = "\n\n---\n\n## 🔗 참고 공식 사이트\n\n"
    for i, (title, url) in enumerate(source_urls, 1):
        section += f"{i}. [{title}]({url})\n"

    section += "\n> 모든 정보는 공식 사이트에서 최종 확인 부탁드려요! 모집 일정·지원 조건은 자주 바뀌거든요 😊\n"
    return section


def main():
    today = datetime.now().strftime('%Y-%m-%d')
    output_dir = Path(f'posts/{today}')
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📅 오늘 날짜: {today}")

    # 1. 주제 선정
    category, theme, source_urls = get_today_topic()
    print(f"📝 오늘의 카테고리: {category}")
    print(f"🎯 오늘의 주제: {theme}")
    print(f"🔗 참고 URL {len(source_urls)}개 준비됨")

    # 2. 주제 상세화
    print("🧩 글 구성 기획 중...")
    detail = generate_topic_detail(category, theme, source_urls)
    print(f"✏️ 제목: {detail['post_title']}")

    # 3. 블로그 본문 생성
    print("📝 블로그 본문 작성 중...")
    post_content = generate_blog_post(category, theme, detail, source_urls)

    # 4. 태그 생성
    print("🏷️ 태그 생성 중...")
    tags = generate_tags(detail, category)

    # 5. 썸네일 문구
    print("🎨 썸네일 문구 생성 중...")
    thumbnail = generate_thumbnail_text(detail)

    # 6. 이미지 프롬프트
    print("🖼️ 이미지 가이드 생성 중...")
    image_prompts = generate_image_prompts(detail, post_content)

    # 7. 출처 섹션
    sources_section = format_sources_section(source_urls)

    # 8. 파일 저장
    post_md = f"""# {detail['post_title']}

> 생성일: {today}
> 카테고리: {category}
> 메인 키워드: {detail['main_keyword']}

---

{post_content}

{sources_section}

---

## 📌 태그 (복사해서 하단에 붙여넣기)

{tags}
"""

    (output_dir / 'post.md').write_text(post_md, encoding='utf-8')
    (output_dir / 'tags.txt').write_text(tags, encoding='utf-8')
    (output_dir / 'thumbnail.txt').write_text(thumbnail, encoding='utf-8')
    (output_dir / 'image_prompts.md').write_text(image_prompts, encoding='utf-8')

    # 메타 정보
    meta = {
        'date': today,
        'category': category,
        'theme': theme,
        'title': detail['post_title'],
        'main_keyword': detail['main_keyword'],
        'sub_keywords': detail['sub_keywords'],
        'source_urls': [{'title': t, 'url': u} for t, u in source_urls],
    }
    (output_dir / 'meta.json').write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )

    print(f"✅ 완료! posts/{today}/ 폴더에 저장됨")
    print(f"   - post.md (본문 + 출처)")
    print(f"   - tags.txt")
    print(f"   - thumbnail.txt")
    print(f"   - image_prompts.md")
    print(f"   - meta.json")


if __name__ == '__main__':
    main()

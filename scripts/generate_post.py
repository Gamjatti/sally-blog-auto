"""
Sally 블로그 자동 생성 스크립트
매일 아침 실행되어 오늘의 블로그 글을 생성합니다.

[v2.0 변경사항]
- Google Search grounding 활성화 → 실시간 정보 기반 글 작성
- 카테고리 개편: 공모전/청년정책/자격증/대외활동 중심 (정보성)
- "가짜 경험 금지" 프롬프트 강제
- 출처 링크 자동 수집 및 본문 삽입
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

# 일반 모델 (주제 선정, 태그 생성 등 검색 불필요한 작업용)
model = genai.GenerativeModel('gemini-2.5-flash')

# 검색 기반 모델 (본문 작성용 - 실시간 정보 필수)
model_with_search = genai.GenerativeModel(
    'gemini-2.5-flash',
    tools='google_search_retrieval'
)

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
- 대신 "정보 전달자" 톤으로 작성: "찾아봤어요", "정리했어요", "알아봤어요", "이런 정보가 있더라고요".
- 실제로 존재하지 않는 프로그램·공모전·자격증을 지어내면 안 됩니다.
- 검색 결과에서 확인된 정보만 사용하세요. 추측·상상 금지.
- 정확한 날짜·금액·링크가 필요한 부분은 `[확인필요: 공식 사이트 확인 요망]` 으로 표시하세요.

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
3. 📍 개요 섹션 (무슨 정보인지, 왜 유용한지)
4. 📋 핵심 정보 섹션 (자격요건·혜택·주최기관 등) 
5. ⏰ 일정·마감일 섹션 (있으면)
6. 💰 비용/지원금 섹션 (있으면)
7. 🔗 신청 방법·공식 링크 섹션
8. ⚠️ 주의사항 섹션 (놓치기 쉬운 점)
9. ✅ 이런 분들께 추천합니다 (6~7개 체크리스트)
10. 💬 마무리 한 마디
11. 시그니처 클로징: "더 궁금한 점은 아래 공식 사이트에서 확인해보세요! Sally가 정리한 정보가 도움이 됐다면 댓글 남겨주세요 :)"

◆ 이미지 자리 표시
- 본문 중간 3~5군데에 `[사진: 무엇을 캡처하거나 찍으면 좋을지]` 로 표시
- 공식 사이트 스크린샷, 포스터 이미지, 설명 다이어그램 등 안내
"""

# ========== 주제 풀 (정보성 콘텐츠 중심으로 전면 개편) ==========
TOPIC_CATEGORIES = {
    "monday": {
        "category": "이번주 마감 공모전",
        "search_queries": [
            "2026년 대학생 공모전 마감임박",
            "이번주 마감 공모전 대학생",
            "2026 대학생 아이디어 공모전 접수중",
        ],
        "themes": [
            "이번주 마감 대학생 공모전 TOP 5",
            "이번주 접수 마감 아이디어 공모전 정리",
            "4월 마감 대학생 공모전 총정리",
            "이번주 마감 영상·콘텐츠 공모전",
            "마감임박 수기·에세이 공모전",
        ]
    },
    "tuesday": {
        "category": "청년정책 신청 가이드",
        "search_queries": [
            "2026 청년정책 신청방법 대학생",
            "청년도약계좌 2026 신청",
            "국민취업지원제도 청년 신청",
            "충청남도 청년정책 2026",
        ],
        "themes": [
            "청년도약계좌 신청 방법과 혜택",
            "국민취업지원제도 Ⅰ·Ⅱ유형 차이",
            "청년내일채움공제 신청 가이드",
            "청년월세특별지원 신청법",
            "대학생 국가장학금 놓치지 않기",
            "청년마음건강바우처 신청 방법",
        ]
    },
    "wednesday": {
        "category": "자격증 접수·일정",
        "search_queries": [
            "2026 자격증 접수일정 대학생 추천",
            "이번달 접수중 자격증",
            "대학생 취업 자격증 2026 상반기 일정",
            "컴활 토익 SQLD 접수일정",
        ],
        "themes": [
            "이번달 접수 중인 대학생 취업 자격증",
            "컴활 1급·2급 2026 상반기 시험일정",
            "SQLD 접수일정과 준비 기간",
            "GTQ 포토샵 시험일정 정리",
            "토익·오픽 시험일정 한눈에 보기",
            "사회조사분석사 2급 일정과 난이도",
            "한국사능력검정시험 일정·가산점 활용",
        ]
    },
    "thursday": {
        "category": "대외활동·서포터즈 모집",
        "search_queries": [
            "2026 대학생 서포터즈 모집",
            "이번달 모집 대학생 대외활동",
            "기업 서포터즈 모집 대학생 2026",
            "공공기관 서포터즈 모집중",
        ],
        "themes": [
            "이번달 모집 중인 대학생 서포터즈 정리",
            "지금 지원 가능한 기업 서포터즈 TOP 5",
            "공공기관 대학생 기자단 모집 현황",
            "해외탐방 지원 대외활동 모집",
            "장학금 주는 대외활동 모집",
            "문화·예술 분야 대학생 서포터즈",
        ]
    },
    "friday": {
        "category": "천안·충남 청년 혜택",
        "search_queries": [
            "천안시 청년정책 2026",
            "충청남도 청년 지원사업 2026",
            "천안 대학생 혜택",
            "충남청년센터 프로그램",
        ],
        "themes": [
            "천안시 청년 지원금·바우처 총정리",
            "충남 청년 취업지원 프로그램 정리",
            "천안 대학생이 받을 수 있는 문화·교통 혜택",
            "충남청년센터·청년공간 이용 가이드",
            "천안 청년 주거지원 사업",
            "상명대·호서대·단국대·백석대 학생 지역 혜택",
        ]
    },
    "saturday": {
        "category": "IT·개발 교육·부트캠프",
        "search_queries": [
            "2026 국비지원 IT 부트캠프 모집",
            "대학생 개발자 교육 무료 2026",
            "네이버 카카오 SW 교육 대학생",
            "K-디지털 트레이닝 신청",
        ],
        "themes": [
            "대학생이 받을 수 있는 무료 개발 교육 정리",
            "K-디지털 트레이닝 신청 가이드",
            "네이버·카카오 대학생 개발자 교육 프로그램",
            "삼성·LG 청년 SW 아카데미 모집 일정",
            "SSAFY 전형과 준비 팁",
            "우아한테크코스·부스트캠프 비교",
        ]
    },
    "sunday": {
        "category": "다음주 마감·시작 예정",
        "search_queries": [
            "다음주 마감 공모전 대학생",
            "다음주 시작 청년정책 신청",
            "이번주말 마감 자격증 접수",
        ],
        "themes": [
            "다음주 마감 예정 공모전·대외활동 총정리",
            "다음주 시작되는 청년정책 신청 일정",
            "이번주말 놓치면 안 되는 접수 마감",
            "다음주 주요 일정 한눈에 보기",
        ]
    }
}


def get_today_topic():
    """오늘 요일에 맞는 주제 카테고리에서 랜덤 선택"""
    weekday_map = ["monday", "tuesday", "wednesday", "thursday", 
                   "friday", "saturday", "sunday"]
    today = weekday_map[datetime.now().weekday()]
    day_data = TOPIC_CATEGORIES[today]
    theme = random.choice(day_data["themes"])
    search_query = random.choice(day_data["search_queries"])
    return day_data["category"], theme, search_query


def extract_grounding_sources(response):
    """Gemini 응답에서 검색 출처 URL 추출"""
    sources = []
    try:
        candidates = response.candidates
        if not candidates:
            return sources
        
        grounding_metadata = getattr(candidates[0], 'grounding_metadata', None)
        if not grounding_metadata:
            return sources
        
        # grounding_chunks에서 URL과 제목 추출
        chunks = getattr(grounding_metadata, 'grounding_chunks', []) or []
        for chunk in chunks:
            web = getattr(chunk, 'web', None)
            if web:
                uri = getattr(web, 'uri', None)
                title = getattr(web, 'title', '') or '출처'
                if uri:
                    sources.append({'title': title, 'url': uri})
    except Exception as e:
        print(f"⚠️ 출처 추출 중 오류 (무시 가능): {e}")
    
    return sources


def search_current_info(search_query, theme):
    """실시간 검색으로 최신 정보 수집"""
    today = datetime.now().strftime('%Y년 %m월 %d일')
    
    prompt = f"""오늘은 {today}이에요. 한국의 대학생 블로거 Sally가 쓸 블로그 글의 소재를 찾고 있어요.

다음 주제로 **지금 현재 유효한 실제 정보**를 검색해서 정리해주세요:

주제: {theme}
검색 키워드: {search_query}

다음 형식으로 정리해주세요:

## 검색 결과 요약

### 발견한 실제 프로그램/정책/자격증 (3~5개)
각 항목마다:
- **이름**: 정확한 공식 명칭
- **주최/운영기관**: 실제 기관명
- **대상**: 지원자격
- **일정**: 접수기간·마감일·시험일 등 (확인된 것만)
- **혜택/내용**: 지원금·상금·특전
- **공식 링크**: 신청·확인 가능한 URL
- **출천 날짜**: 정보를 확인한 페이지의 게시일자 (알 수 있다면)

### 놓치기 쉬운 주의사항
- 중복지원 제한, 서류 준비물, 자격 제한 등

**중요**: 
- 검색으로 확인되지 않는 정보는 "확인 필요"로 표시하세요.
- 2024년·2025년 지난 정보는 걸러주세요. 2026년 기준 유효한 것만.
- 없으면 없다고 솔직히 쓰세요. 지어내지 마세요.
"""
    
    response = model_with_search.generate_content(prompt)
    sources = extract_grounding_sources(response)
    return response.text.strip(), sources


def generate_topic_detail(category, theme, research_summary):
    """검색 결과를 바탕으로 블로그 글 구성 기획"""
    prompt = f"""당신은 천안 대학생 블로거 Sally의 콘텐츠 기획자입니다.
아래 리서치 결과를 바탕으로 블로그 글의 구성을 JSON으로 만들어주세요.

대분류: {category}
주제: {theme}

[리서치 결과]
{research_summary}

다음 JSON 형식으로만 답하세요 (다른 설명 없이):
{{
  "post_title": "블로그 제목 (32자 이내, '정리', '총정리', '마감임박', '신청 방법' 등 정보성 키워드 포함)",
  "main_keyword": "네이버 검색 최적화 메인 키워드",
  "sub_keywords": ["서브키워드1", "서브키워드2", "서브키워드3", "서브키워드4"],
  "hook": "도입부 훅 한 줄 (요즘 ~찾고 계신 분들 많죠? 스타일)",
  "outline": ["소제목1", "소제목2", "소제목3", "소제목4", "소제목5"],
  "target_readers": "이 글을 읽을 타겟 독자"
}}"""
    
    response = model.generate_content(prompt)
    text = response.text.strip()
    
    # JSON 코드 블록 제거
    if text.startswith('```'):
        text = text.split('```')[1]
        if text.startswith('json'):
            text = text[4:]
        text = text.strip()
    
    return json.loads(text)


def generate_blog_post(category, theme, detail, research_summary, sources):
    """Sally 스타일로 블로그 본문 작성 (리서치 결과 기반)"""
    sources_text = ""
    if sources:
        sources_text = "\n\n[참고한 실제 출처 목록 - 본문에 자연스럽게 언급 가능]\n"
        for i, src in enumerate(sources[:8], 1):
            sources_text += f"{i}. {src['title']}: {src['url']}\n"
    
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

[⭐ 리서치 결과 - 반드시 이 정보만 사용할 것]
{research_summary}
{sources_text}

[작성 규칙 - 절대 준수]
1. ⚠️ 위 리서치 결과에 있는 실제 프로그램·정책·자격증만 언급하세요. 새로 지어내지 마세요.
2. ⚠️ "참여했어요", "합격했어요" 같은 직접 경험 서술 절대 금지. 
   대신 "알아봤어요", "정리해봤어요", "찾아보니까 이런 혜택이 있더라고요" 스타일.
3. 분량: 2,000~2,500자
4. Sally 오프닝 공식으로 시작
5. 문단 사이 빈 줄 충분히 (모바일 가독성)
6. 이미지 자리 3~5군데 `[사진: 구체적 가이드]` 로 표시 (공식 사이트 스크린샷, 포스터 캡처 등)
7. 날짜·금액·링크 중 확실하지 않은 부분은 `[확인필요: 공식 사이트에서 확인]` 표시
8. 📍📋⏰💰🔗⚠️✅💬 섹션 이모지 반드시 사용
9. 각 프로그램·정책마다 **공식 사이트 URL**을 본문에 함께 적으세요 (리서치에서 확인된 것만)
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
- 정보성 임팩트 (숫자, '총정리', '마감임박', '꿀정보' 등 활용)
- Sally 스타일 친근함

출력 예시:
이번주 마감임박
대학생 공모전 TOP 5

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


def format_sources_section(sources):
    """본문 하단에 붙일 출처 섹션 생성"""
    if not sources:
        return ""
    
    section = "\n\n---\n\n## 🔗 참고한 공식 사이트\n\n"
    seen = set()
    idx = 1
    for src in sources:
        url = src.get('url', '')
        title = src.get('title', '출처')
        if url in seen or not url:
            continue
        seen.add(url)
        section += f"{idx}. [{title}]({url})\n"
        idx += 1
        if idx > 8:
            break
    
    section += "\n> 모든 정보는 공식 사이트에서 최종 확인 부탁드려요! 정책·일정은 자주 바뀌거든요 😊\n"
    return section


def main():
    today = datetime.now().strftime('%Y-%m-%d')
    output_dir = Path(f'posts/{today}')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📅 오늘 날짜: {today}")
    
    # 1. 주제 선정
    category, theme, search_query = get_today_topic()
    print(f"📝 오늘의 카테고리: {category}")
    print(f"🎯 오늘의 주제: {theme}")
    print(f"🔍 검색 쿼리: {search_query}")
    
    # 2. 실시간 검색 (가장 중요!)
    print("🌐 Google Search로 실시간 정보 수집 중... (30초~1분)")
    research_summary, sources = search_current_info(search_query, theme)
    print(f"✅ 출처 {len(sources)}개 확보")
    
    # 3. 주제 상세화
    print("🧩 글 구성 기획 중...")
    detail = generate_topic_detail(category, theme, research_summary)
    print(f"✏️ 제목: {detail['post_title']}")
    
    # 4. 블로그 본문 생성 (리서치 결과 기반)
    print("📝 블로그 본문 작성 중...")
    post_content = generate_blog_post(category, theme, detail, research_summary, sources)
    
    # 5. 태그 생성
    print("🏷️ 태그 생성 중...")
    tags = generate_tags(detail, category)
    
    # 6. 썸네일 문구
    print("🎨 썸네일 문구 생성 중...")
    thumbnail = generate_thumbnail_text(detail)
    
    # 7. 이미지 프롬프트
    print("🖼️ 이미지 가이드 생성 중...")
    image_prompts = generate_image_prompts(detail, post_content)
    
    # 8. 출처 섹션
    sources_section = format_sources_section(sources)
    
    # 9. 파일 저장
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
    (output_dir / 'research.md').write_text(
        f"# 리서치 결과\n\n검색 쿼리: {search_query}\n\n---\n\n{research_summary}",
        encoding='utf-8'
    )
    
    # 메타 정보
    meta = {
        'date': today,
        'category': category,
        'theme': theme,
        'title': detail['post_title'],
        'main_keyword': detail['main_keyword'],
        'sub_keywords': detail['sub_keywords'],
        'search_query': search_query,
        'sources_count': len(sources),
        'sources': [{'title': s['title'], 'url': s['url']} for s in sources[:8]]
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
    print(f"   - research.md (검색 결과 원본)")
    print(f"   - meta.json")


if __name__ == '__main__':
    main()

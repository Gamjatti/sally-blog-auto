"""
Sally 블로그 자동 생성 스크립트
매일 아침 실행되어 오늘의 블로그 글을 생성합니다.
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
- 타겟: 천안 대학생 (상명대·호서대·단국대·백석대), 자기계발 MZ
- 카테고리: 일상후기, 외부활동, 자격증공부

◆ 말투 규칙
- 기본: 친근한 존댓말 ("~해요", "~거든요", "~잖아요", "~더라고요")
- 감정 표현: ㅎㅎ, ㅋㅋㅋ, ㅠㅠ 자연스럽게 섞기
- 강조어: "진짜", "정말", "완전", "너무너무", "확실히" 자주 사용
- 느낌표 2~3개 연속 가능 ("좋았어요!!", "추천입니다!!!")
- 절대 금지: "~에 대해 알아보도록 하겠습니다", "다음과 같습니다", "결론적으로"

◆ 오프닝 공식 (반드시 이 순서로)
🐾 [핵심 키워드] [서브 설명]
[주제 한 줄 요약]

안녕하세요~! 여러분 Sally입니다~!

[공감형 도입 3~4줄: "요즘 ~하지 않나요?" 스타일]

◆ 섹션 이모지 규칙
- 📍 위치/정보/기본내용
- 🍬 디테일/포인트/숨은매력
- 🔥 강력추천/핵심포인트
- ✅ 이런 분들께 추천
- 💬 마무리 한 마디
- 🚨 주의사항

◆ 문단 구조
- 문장 1~2개마다 엔터 (빈 줄)
- 한 문단 3줄 넘지 않기

◆ 필수 구성
1. 🐾 오프닝 + Sally 인사
2. 공감형 도입 3~4줄
3. 📍 기본정보/배경 섹션
4. 본문 (사진 들어갈 자리는 `[사진: 무엇을 찍으면 좋을지]` 로 표시, 5~8군데)
5. 🍬 디테일의 차이 섹션
6. ✅ 이런 분들께 진심 추천합니다 (6~7개 체크리스트)
7. 💬 마무리 한 마디
8. 시그니처 클로징: "궁금한 점 있으시면 댓글이나 메시지 주세요! Sally가 직접 [다녀온/해본/알아본] 후기니까 더 자세히 알려드릴게요 :)"

◆ 확인 필요 사항
- 정확하지 않은 수치/금액/날짜는 `[확인필요: 설명]` 으로 표시
- 예: `[확인필요: 정확한 신청 기간]`
"""

# ========== 주제 풀 ==========
TOPIC_CATEGORIES = {
    "monday": {
        "category": "천안 맛집·카페",
        "themes": [
            "호서대 근처 혼밥 가능한 맛집",
            "상명대 학생 점심 추천 식당",
            "두정동·불당동 신상 카페",
            "쌍용동 가성비 맛집",
            "천안 대학가 24시간 스터디카페",
            "신부동 데이트 맛집",
            "백석동 브런치 카페",
        ]
    },
    "tuesday": {
        "category": "대학생 꿀팁·자기계발",
        "themes": [
            "대학생 생산성 루틴 만들기",
            "시험기간 효율적인 공부법",
            "취업 준비 시작하는 법",
            "자취생을 위한 돈 관리 팁",
            "대학생 토익/오픽 공부 루틴",
            "MBTI별 공부 스타일 비교",
        ]
    },
    "wednesday": {
        "category": "자격증·어학 후기",
        "themes": [
            "HSK 공부 루틴 공유",
            "컴활 자격증 단기 합격 후기",
            "토익 스피킹 IM3 달성 후기",
            "사회조사분석사 공부법",
            "SQLD 벼락치기 후기",
            "GTQ 포토샵 1급 후기",
        ]
    },
    "thursday": {
        "category": "MZ 트렌드·SNS",
        "themes": [
            "요즘 대학생들 사이 유행하는 것",
            "인스타 릴스 만드는 꿀팁",
            "Z세대 소비 트렌드",
            "요즘 뜨는 챌린지",
            "대학생 취미로 좋은 것 추천",
        ]
    },
    "friday": {
        "category": "천안 대학생 혜택·공모전",
        "themes": [
            "천안시 청년 지원금 총정리",
            "대학생 대외활동 추천 (신규 모집)",
            "대학생 서포터즈 꿀팁",
            "천안 문화비·교통비 혜택",
            "대학생 무료 전시·공연 정보",
            "공모전 수상 팁",
        ]
    },
    "saturday": {
        "category": "일상·라이프",
        "themes": [
            "대학생 주말 생산적 보내기",
            "자취방 꾸미기 팁",
            "데일리 룩 추천",
            "혼자 시간 보내기 좋은 장소",
        ]
    },
    "sunday": {
        "category": "외부활동·서포터즈 후기",
        "themes": [
            "대학생 서포터즈 활동 후기",
            "이번 주 참여한 대외활동",
            "블로그 이웃 소통 후기",
            "한 주 돌아보기",
        ]
    }
}


def get_today_topic():
    """오늘 요일에 맞는 주제 카테고리에서 랜덤 선택"""
    weekday_map = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    today = weekday_map[datetime.now().weekday()]
    day_data = TOPIC_CATEGORIES[today]
    theme = random.choice(day_data["themes"])
    return day_data["category"], theme


def generate_topic_detail(category, theme):
    """주제를 구체적인 소재로 확장"""
    prompt = f"""당신은 천안 대학생 블로거 Sally의 콘텐츠 기획자입니다.

아래 주제를 바탕으로 오늘 작성할 블로그 글의 구체적인 소재를 JSON 형식으로 만들어주세요.

대분류: {category}
주제: {theme}

다음 JSON 형식으로만 답하세요 (다른 설명 없이):
{{
  "post_title": "블로그 제목 (32자 이내, Sally 스타일: 숫자·후기·꿀팁 키워드 포함)",
  "main_keyword": "네이버 검색 최적화 메인 키워드",
  "sub_keywords": ["서브키워드1", "서브키워드2", "서브키워드3"],
  "hook": "도입부 첫 문장 (요즘 ~하지 않나요? 스타일)",
  "outline": ["소제목1", "소제목2", "소제목3", "소제목4"],
  "target_readers": "이 글을 읽을 타겟 독자 설명"
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


def generate_blog_post(category, theme, detail):
    """Sally 스타일로 블로그 본문 작성"""
    prompt = f"""{SALLY_STYLE}

---

위 스타일 가이드를 100% 준수해서 네이버 블로그 포스팅을 작성해주세요.

[오늘의 소재]
- 대분류: {category}
- 주제: {theme}
- 제목: {detail['post_title']}
- 메인 키워드: {detail['main_keyword']}
- 서브 키워드: {', '.join(detail['sub_keywords'])}
- 도입 훅: {detail['hook']}
- 구성: {' → '.join(detail['outline'])}

[작성 규칙]
1. 2,000~2,500자 분량
2. 반드시 Sally 오프닝 공식으로 시작
3. 문단 사이 빈 줄 충분히 (모바일 가독성)
4. 사진 들어갈 자리 5~8군데 `[사진: 구체적 가이드]` 로 표시
5. 불확실한 정보는 `[확인필요: 설명]` 표시
6. 📍🍬✅💬 섹션 이모지 반드시 사용
7. 마지막에 Sally 시그니처 클로징 필수

[출력]
제목은 제외하고 본문만 작성해주세요. 네이버 블로그에 바로 붙여넣을 수 있는 형태로요."""

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
- 지역 키워드 필수 (천안, 상명대, 호서대, 단국대, 백석대 등)
- 주제 롱테일 키워드 8~10개
- 소통 키워드: 서이추, 서로이웃, 서이추환영, 소통해요, 이웃추가
- 정체성 키워드: 대학생블로그, 대학생일상, 자기계발

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
- 임팩트 있게, 궁금증 유발
- Sally 스타일 (친근함)

출력 예시:
호서대 혼밥 성지
마라탕 라화쿵부 후기

다른 설명 없이 2줄만 출력하세요."""

    response = model.generate_content(prompt)
    return response.text.strip()


def generate_image_prompts(detail, post_content):
    """이미지 생성용 프롬프트 만들기 (DALL-E, Midjourney 등에서 사용)"""
    prompt = f"""블로그 포스팅에 쓸 이미지 5장의 생성 프롬프트를 만들어주세요.

블로그 주제: {detail['post_title']}
메인 키워드: {detail['main_keyword']}
본문 요약: {post_content[:500]}

각 이미지마다 다음 형식으로:

### 이미지 N: [무슨 이미지인지 한국어 설명]
**영어 프롬프트**: [DALL-E/Midjourney용 영어 프롬프트, 구체적으로]
**용도**: [블로그 어느 섹션에 들어갈지]
**무료 대안**: [무료 이미지 검색 키워드 - Unsplash/Pexels용]

사진을 직접 찍는 게 제일 좋지만, AI 이미지 생성할 때 참고할 수 있게 해주세요."""

    response = model.generate_content(prompt)
    return response.text.strip()


def main():
    # 오늘 날짜 폴더
    today = datetime.now().strftime('%Y-%m-%d')
    output_dir = Path(f'posts/{today}')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📅 오늘 날짜: {today}")
    
    # 1. 주제 선정
    category, theme = get_today_topic()
    print(f"📝 오늘의 카테고리: {category}")
    print(f"🎯 오늘의 주제: {theme}")
    
    # 2. 주제 상세화
    print("🔍 주제 구체화 중...")
    detail = generate_topic_detail(category, theme)
    print(f"✏️  제목: {detail['post_title']}")
    
    # 3. 블로그 본문 생성
    print("📝 블로그 본문 작성 중... (시간 조금 걸려요)")
    post_content = generate_blog_post(category, theme, detail)
    
    # 4. 태그 생성
    print("🏷️  태그 생성 중...")
    tags = generate_tags(detail, category)
    
    # 5. 썸네일 문구
    print("🎨 썸네일 문구 생성 중...")
    thumbnail = generate_thumbnail_text(detail)
    
    # 6. 이미지 프롬프트
    print("🖼️  이미지 프롬프트 생성 중...")
    image_prompts = generate_image_prompts(detail, post_content)
    
    # 7. 파일 저장
    # post.md - 네이버 붙여넣기용
    post_md = f"""# {detail['post_title']}

> 생성일: {today}  
> 카테고리: {category}  
> 메인 키워드: {detail['main_keyword']}

---

{post_content}

---

## 📌 태그 (복사해서 하단에 붙여넣기)

{tags}
"""
    (output_dir / 'post.md').write_text(post_md, encoding='utf-8')
    (output_dir / 'tags.txt').write_text(tags, encoding='utf-8')
    (output_dir / 'thumbnail.txt').write_text(thumbnail, encoding='utf-8')
    (output_dir / 'image_prompts.md').write_text(image_prompts, encoding='utf-8')
    
    # 메타 정보 저장
    meta = {
        'date': today,
        'category': category,
        'theme': theme,
        'title': detail['post_title'],
        'main_keyword': detail['main_keyword'],
        'sub_keywords': detail['sub_keywords']
    }
    (output_dir / 'meta.json').write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    
    print(f"✅ 완료! posts/{today}/ 폴더에 저장됨")
    print(f"   - post.md")
    print(f"   - tags.txt")
    print(f"   - thumbnail.txt")
    print(f"   - image_prompts.md")


if __name__ == '__main__':
    main()

"""
텔레그램으로 오늘의 블로그 글 알림 전송
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
REPO = os.environ.get('GITHUB_REPOSITORY', 'your-username/sally-blog-auto')

if not BOT_TOKEN or not CHAT_ID:
    print("⚠️  텔레그램 설정이 없어요. 알림 스킵합니다.")
    exit(0)


def send_message(text, parse_mode='Markdown'):
    """텔레그램 메시지 전송"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': CHAT_ID,
        'text': text,
        'parse_mode': parse_mode,
        'disable_web_page_preview': False
    }
    response = requests.post(url, json=data)
    if not response.ok:
        # Markdown 파싱 실패 시 일반 텍스트로 재시도
        data.pop('parse_mode', None)
        response = requests.post(url, json=data)
    return response.ok


def send_document(file_path, caption=''):
    """텔레그램으로 파일 전송"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    with open(file_path, 'rb') as f:
        files = {'document': f}
        data = {'chat_id': CHAT_ID, 'caption': caption}
        response = requests.post(url, files=files, data=data)
    return response.ok


def main():
    today = datetime.now().strftime('%Y-%m-%d')
    post_dir = Path(f'posts/{today}')
    
    if not post_dir.exists():
        send_message(f"⚠️ 오늘({today}) 생성된 글이 없어요. 로그를 확인해주세요.")
        return
    
    # 메타 정보 읽기
    meta_file = post_dir / 'meta.json'
    if meta_file.exists():
        meta = json.loads(meta_file.read_text(encoding='utf-8'))
        title = meta.get('title', '오늘의 글')
        category = meta.get('category', '')
        main_kw = meta.get('main_keyword', '')
    else:
        title = '오늘의 글'
        category = ''
        main_kw = ''
    
    # 본문 미리보기 (첫 400자)
    post_file = post_dir / 'post.md'
    preview = ''
    if post_file.exists():
        content = post_file.read_text(encoding='utf-8')
        # 메타 헤더 스킵하고 본문만
        if '---' in content:
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2]
        preview = content.strip()[:400]
    
    # 썸네일 문구
    thumbnail = ''
    thumb_file = post_dir / 'thumbnail.txt'
    if thumb_file.exists():
        thumbnail = thumb_file.read_text(encoding='utf-8').strip()
    
    # GitHub 파일 직접 링크
    github_url = f"https://github.com/{REPO}/blob/main/posts/{today}/post.md"
    github_raw = f"https://github.com/{REPO}/tree/main/posts/{today}"
    
    # 메시지 구성
    message = f"""🌅 *좋은 아침이에요 Sally님\\!*

오늘의 블로그 글이 준비됐어요\\! 🥚

📝 *제목*
{title}

📂 *카테고리*: {category}
🎯 *메인 키워드*: {main_kw}

✨ *썸네일 문구*
```
{thumbnail}
```

📖 *미리보기*
{preview[:300]}\\.\\.\\.

✅ *오늘의 체크리스트*
1\\. 아래 링크에서 글 복사
2\\. 네이버 블로그에 붙여넣기  
3\\. \\[사진\\] 자리에 이미지 추가
4\\. \\[확인필요\\] 부분 검증
5\\. 태그 붙여넣고 발행 🚀

⏱ *예상 소요시간*: 10분"""
    
    # Markdown V2 특수문자 이스케이프가 복잡하니 일반 HTML로 보내기
    html_message = f"""🌅 <b>좋은 아침이에요 Sally님!</b>

오늘의 블로그 글이 준비됐어요! 🥚

📝 <b>제목</b>
{title}

📂 <b>카테고리</b>: {category}
🎯 <b>메인 키워드</b>: {main_kw}

✨ <b>썸네일 문구</b>
<pre>{thumbnail}</pre>

📖 <b>미리보기</b>
<i>{preview[:300]}...</i>

✅ <b>오늘 할 일</b>
1. 아래 파일 받아서 네이버에 복붙
2. [사진] 자리에 이미지 추가
3. [확인필요] 부분 검증
4. 태그 붙여넣고 발행 🚀

⏱ <b>예상 소요시간</b>: 10분

🔗 <a href="{github_url}">GitHub에서 보기</a>
📁 <a href="{github_raw}">오늘 폴더 전체</a>"""
    
    # HTML로 전송
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': CHAT_ID,
        'text': html_message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    response = requests.post(url, json=data)
    
    if response.ok:
        print("✅ 텔레그램 알림 전송 완료")
    else:
        print(f"❌ 텔레그램 전송 실패: {response.text}")
        # 그래도 plain text로 재시도
        send_message(f"오늘의 글 준비됨! {github_url}")
    
    # post.md 파일도 첨부로 전송 (바로 복사하기 편하게)
    if post_file.exists():
        send_document(
            str(post_file),
            caption=f"📝 {title}\n\n파일 열어서 전체 복사하시면 돼요!"
        )
        print("✅ 글 파일 전송 완료")
    
    # 태그 파일도 전송
    tags_file = post_dir / 'tags.txt'
    if tags_file.exists():
        tags_content = tags_file.read_text(encoding='utf-8')
        tag_message = f"🏷 <b>오늘의 태그 30개</b>\n\n<code>{tags_content}</code>\n\n위 태그 전체 복사해서 블로그 하단에 붙여넣으세요!"
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': CHAT_ID,
            'text': tag_message,
            'parse_mode': 'HTML'
        }
        requests.post(url, json=data)
        print("✅ 태그 전송 완료")


if __name__ == '__main__':
    main()

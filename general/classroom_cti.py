from urllib.parse import urlsplit


SOURCE = '수업용 로컬 CTI API'
DATASET = {
    'guide.classroom.test': 20,
    'update.classroom.test': 40,
    'flagged.classroom.test': 90,
}


def lookup_url(url):
    if not isinstance(url, str) or len(url) > 2000:
        raise ValueError('조회 URL은 2000자 이내 문자열이어야 합니다.')
    parsed = urlsplit(url)
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('http 또는 https 형식의 URL을 확인해 주세요.')
    domain = parsed.hostname.lower()
    score = DATASET.get(domain)
    return {
        'source': SOURCE, 'dataset_version': 1, 'synthetic': True,
        'url': url, 'domain': domain, 'score': score,
        'status': 'found' if score is not None else 'not_listed',
        'note': '실제 위협 평판이 아닌 수업용 점수입니다. 해당 URL에는 접속하지 않았습니다.' if score is not None else '수업용 목록에 없는 URL입니다. 안전하다는 뜻이 아닙니다. 해당 URL에는 접속하지 않았습니다.',
    }

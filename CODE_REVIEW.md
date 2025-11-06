# 시스템 리소스 모니터링 시스템 코드 리뷰 보고서

## 개요

**프로젝트명**: System Resource Monitoring System
**리뷰 대상**: system_monitor 패키지 전체
**리뷰 일자**: 2025-11-06
**리뷰 범위**: 보안 취약점, 코드 품질, 개선사항

---

## 1. 심각도 분류 기준

- **치명적 (Critical)**: 즉시 수정 필요, 시스템 보안에 직접적 위협
- **높음 (High)**: 빠른 시일 내 수정 필요, 공격에 악용될 수 있음
- **중간 (Medium)**: 수정 권장, 특정 조건에서 문제 발생 가능
- **낮음 (Low)**: 개선 권장, 보안 강화 차원
- **정보 (Info)**: 모범 사례 권장

---

## 2. 보안 취약점 분석

### 2.1 경로 주입 (Path Injection) 취약점 [심각도: 높음]

**위치**:
- `monitor.py:180` - 사용자 입력 output 경로
- `graph_generator.py:23-24` - output_dir 디렉토리 생성
- `pdf_reporter.py:27-28` - output_dir 디렉토리 생성

**문제점**:
```python
# monitor.py:180
parser.add_argument('-o', '--output', type=str, default='output',
                    help='Output directory for reports and graphs (default: output)')

# graph_generator.py:23-24
self.output_dir = output_dir
os.makedirs(output_dir, exist_ok=True)
```

사용자가 제공하는 경로에 대한 검증이 없어 다음과 같은 공격이 가능합니다:
- 경로 순회 공격 (Path Traversal): `../../etc/sensitive_dir`
- 절대 경로 지정: `/etc/`, `/root/`
- 심볼릭 링크 공격
- 시스템 디렉토리 덮어쓰기

**영향**:
- 의도하지 않은 위치에 파일 생성
- 기존 시스템 파일 덮어쓰기 가능
- 권한 상승 공격의 발판

**권장 사항**:
1. 경로 정규화 및 검증 구현
2. 허용된 기본 디렉토리 내에서만 동작하도록 제한
3. 절대 경로 거부
4. `..` 포함 경로 거부
5. 경로 생성 전 권한 확인

---

### 2.2 파일 권한 관리 부재 [심각도: 중간]

**위치**:
- `graph_generator.py:66, 92, 117, 142` - plt.savefig()
- `pdf_reporter.py:147-258` - PDF 파일 생성

**문제점**:
```python
# graph_generator.py:66
plt.savefig(output_path, dpi=150, bbox_inches='tight')

# pdf_reporter.py:147
pdf_path = os.path.join(self.output_dir, pdf_filename)
doc = SimpleDocTemplate(pdf_path, pagesize=letter, ...)
```

생성되는 파일의 권한이 시스템 umask에 의존하며, 명시적으로 설정되지 않습니다.

**영향**:
- 민감한 시스템 정보가 포함된 리포트가 다른 사용자에게 노출될 수 있음
- 기본 권한이 너무 관대할 경우 정보 유출 위험

**권장 사항**:
1. 파일 생성 후 명시적 권한 설정 (예: 0o600)
2. 디렉토리 생성시 적절한 권한 설정 (예: 0o700)
3. 민감한 정보 포함 여부에 따라 권한 차등 적용

```python
# 권장 예시
os.chmod(output_path, 0o600)  # 소유자만 읽기/쓰기
```

---

### 2.3 리소스 소진 (DoS) 취약점 [심각도: 중간]

**위치**:
- `monitor.py:48` - total_iterations 계산
- `resource_collector.py:173` - data_history 누적

**문제점**:
```python
# monitor.py:48
total_iterations = (duration_minutes * 60) // interval_seconds

# 예: duration=10000, interval=1 => 600,000 iterations
# 메모리 사용량이 무제한으로 증가
```

**영향**:
- 악의적 사용자가 매우 큰 duration 값 설정 가능
- 메모리 소진으로 시스템 다운
- 디스크 공간 소진

**권장 사항**:
1. duration과 interval에 상한선 설정
2. 메모리 사용량 모니터링 및 제한
3. 데이터 히스토리 크기 제한
4. 디스크 공간 사전 확인

```python
# 권장 예시
MAX_DURATION_MINUTES = 1440  # 24시간
MAX_ITERATIONS = 10000

if args.duration > MAX_DURATION_MINUTES:
    print(f"Error: Duration cannot exceed {MAX_DURATION_MINUTES} minutes")
    sys.exit(1)
```

---

### 2.4 정보 노출 (Information Disclosure) [심각도: 중간]

**위치**:
- `resource_collector.py:57, 76, 95, 129, 157` - Exception 메시지 출력
- `monitor.py:82, 112, 127, 208-209` - 에러 정보 출력

**문제점**:
```python
# resource_collector.py:57
except Exception as e:
    print(f"CPU 정보 수집 오류: {e}")

# monitor.py:208-209
except Exception as e:
    print(f"\nFatal error: {e}")
    import traceback
    traceback.print_exc()
```

**영향**:
- 내부 시스템 경로 노출
- 시스템 구조 정보 노출
- 공격자가 시스템 환경 파악 가능
- 스택 트레이스로 인한 추가 정보 노출

**권장 사항**:
1. 프로덕션 환경에서 상세 에러 메시지 비활성화
2. 로깅 시스템 도입하여 에러를 파일에 기록
3. 사용자에게는 일반적인 에러 메시지만 표시
4. 디버그 모드 플래그 추가

---

### 2.5 입력 검증 부족 [심각도: 높음]

**위치**:
- `monitor.py:186-197` - 명령행 인자 검증

**문제점**:
```python
# monitor.py:186-197
if args.duration <= 0:
    print("Error: Duration must be greater than 0")
    sys.exit(1)

if args.interval <= 0:
    print("Error: Interval must be greater than 0")
    sys.exit(1)
```

**검증 누락 사항**:
1. duration 상한선 미설정 (예: 999999999 입력 가능)
2. interval 상한선 미설정
3. output 경로 검증 전무
4. 정수 오버플로우 체크 없음
5. 타입 검증만 있고 범위 검증 불충분

**영향**:
- 시스템 리소스 남용
- 의도하지 않은 동작
- 서비스 거부 공격

**권장 사항**:
```python
# 상한선 설정
MAX_DURATION = 1440  # 24시간
MAX_INTERVAL = 3600  # 1시간
MIN_INTERVAL = 1

# 경로 검증
import os.path
if not os.path.basename(args.output) == args.output:
    print("Error: Output path must be a simple directory name")
    sys.exit(1)

# 범위 검증
if not (0 < args.duration <= MAX_DURATION):
    print(f"Error: Duration must be between 1 and {MAX_DURATION}")
    sys.exit(1)
```

---

### 2.6 경쟁 조건 (Race Condition) [심각도: 낮음]

**위치**:
- `graph_generator.py:24, 65-66` - 디렉토리 생성 및 파일 저장
- `pdf_reporter.py:28, 147-148` - 디렉토리 생성 및 파일 저장

**문제점**:
```python
# graph_generator.py:24
os.makedirs(output_dir, exist_ok=True)

# graph_generator.py:65-66
output_path = os.path.join(self.output_dir, 'cpu_graph.png')
plt.savefig(output_path, dpi=150, bbox_inches='tight')
```

디렉토리 존재 확인과 파일 생성 사이에 시간 간격이 있어 TOCTOU (Time-of-Check-Time-of-Use) 취약점 존재

**영향**:
- 동시 실행시 파일 충돌
- 심볼릭 링크 공격 가능성
- 파일 덮어쓰기

**권장 사항**:
1. 파일명에 타임스탬프나 UUID 추가하여 유니크하게 생성
2. 파일 존재 여부 확인 후 생성
3. 원자적(atomic) 파일 작성 방식 사용

---

### 2.7 하드코딩된 경로 [심각도: 낮음]

**위치**:
- `resource_collector.py:83` - 디스크 경로 하드코딩

**문제점**:
```python
# resource_collector.py:83
disk = psutil.disk_usage('/')
```

루트 디렉토리만 모니터링하며, 다른 마운트 포인트는 무시됩니다.

**영향**:
- Windows 환경에서 오류 발생 가능
- 중요한 다른 파티션 모니터링 불가

**권장 사항**:
1. 모든 마운트 포인트 검색하여 모니터링
2. 설정 파일로 모니터링 대상 지정 가능하게 구현
3. OS별 분기 처리

---

### 2.8 안전하지 않은 임시 파일 사용 [심각도: 중간]

**위치**:
- 모든 출력 파일 생성 위치

**문제점**:
고정된 파일명 사용으로 예측 가능:
- `cpu_graph.png`
- `memory_graph.png`
- `disk_graph.png`
- `network_graph.png`
- `gpu_graph.png`

**영향**:
- 심볼릭 링크 공격 가능
- 다른 사용자의 파일 덮어쓰기 가능
- 정보 유출

**권장 사항**:
1. tempfile 모듈 사용
2. 파일명에 랜덤 요소 추가
3. 사용자별 격리된 디렉토리 사용

---

### 2.9 의존성 보안 [심각도: 정보]

**위치**:
- `requirements.txt`

**현재 의존성**:
```
psutil==5.9.8
matplotlib==3.8.2
reportlab==4.0.9
Pillow==10.2.0
GPUtil==1.4.0
```

**권장 사항**:
1. 정기적인 의존성 취약점 스캔 (pip-audit, safety 등)
2. 주기적인 업데이트
3. 보안 패치 모니터링
4. 최소 권한 원칙 적용

**확인 필요 사항**:
- 각 패키지의 알려진 CVE 확인
- EOL(End of Life) 여부 확인
- 대체 패키지 검토

---

## 3. 코드 품질 문제

### 3.1 로깅 시스템 부재 [심각도: 중간]

**문제점**:
- print() 문으로만 출력
- 로그 레벨 구분 없음
- 로그 파일 저장 없음
- 감사(audit) 추적 불가

**권장 사항**:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
```

---

### 3.2 예외 처리 개선 필요 [심각도: 중간]

**문제점**:
- 광범위한 Exception 캐치
- 구체적인 예외 타입 미사용
- 복구 전략 부재

**현재 코드**:
```python
except Exception as e:
    print(f"CPU 정보 수집 오류: {e}")
    return {'percent': 0, ...}
```

**권장 사항**:
```python
except (psutil.AccessDenied, PermissionError) as e:
    logger.warning(f"CPU 정보 접근 거부: {e}")
    return {'percent': 0, ...}
except psutil.NoSuchProcess as e:
    logger.error(f"프로세스를 찾을 수 없음: {e}")
    return None
except Exception as e:
    logger.exception(f"예상치 못한 오류: {e}")
    raise
```

---

### 3.3 설정 관리 부재 [심각도: 낮음]

**문제점**:
- 모든 설정이 하드코딩
- 환경별 설정 불가
- 재사용성 저하

**권장 사항**:
1. 설정 파일 도입 (YAML, JSON, INI)
2. 환경 변수 지원
3. 설정 검증 로직

---

### 3.4 테스트 부재 [심각도: 중간]

**문제점**:
- 단위 테스트 없음
- 통합 테스트 없음
- 코드 커버리지 측정 불가

**권장 사항**:
```python
# tests/test_resource_collector.py
import unittest
from unittest.mock import patch, MagicMock

class TestResourceCollector(unittest.TestCase):
    def setUp(self):
        self.collector = ResourceCollector()

    def test_collect_cpu_info(self):
        result = self.collector.collect_cpu_info()
        self.assertIn('percent', result)
        self.assertIsInstance(result['percent'], (int, float))
```

---

### 3.5 데이터 검증 부족 [심각도: 중간]

**위치**:
- `graph_generator.py:37-38` - 데이터 추출시 검증 없음

**문제점**:
```python
cpu_percent = [entry['cpu']['percent'] for entry in data_history]
```

데이터가 None이거나 예상 형식이 아닐 경우 오류 발생

**권장 사항**:
```python
cpu_percent = [
    entry['cpu']['percent']
    for entry in data_history
    if entry and 'cpu' in entry and 'percent' in entry['cpu']
]
```

---

### 3.6 메모리 관리 [심각도: 낮음]

**문제점**:
- data_history가 메모리에 무제한 누적
- 대용량 데이터 처리시 메모리 부족 가능

**권장 사항**:
1. 순환 버퍼 구현
2. 데이터베이스나 파일에 중간 저장
3. 메모리 사용량 모니터링

---

### 3.7 동시성 고려 부족 [심각도: 낮음]

**문제점**:
- 동시 실행시 파일 충돌 가능
- 스레드 안전성 미고려

**권장 사항**:
1. 파일 잠금 메커니즘
2. 프로세스/스레드 ID 기반 파일명
3. 동시성 제어 로직

---

## 4. 보안 모범 사례 권장사항

### 4.1 최소 권한 원칙
- 필요한 최소한의 시스템 권한만 요청
- sudo 실행 요구사항 최소화
- 읽기 전용 접근 우선

### 4.2 입력 검증
```python
def validate_output_path(path: str) -> bool:
    """출력 경로 검증"""
    # 상대 경로만 허용
    if os.path.isabs(path):
        return False

    # .. 포함 거부
    if '..' in path:
        return False

    # 허용된 문자만 사용
    import re
    if not re.match(r'^[a-zA-Z0-9_\-]+$', path):
        return False

    return True
```

### 4.3 보안 헤더 및 메타데이터
PDF 리포트에 보안 관련 메타데이터 추가:
```python
doc = SimpleDocTemplate(
    pdf_path,
    author="System Monitor",
    subject="System Resource Report",
    creator="Monitoring System v1.0",
    # 암호화 옵션 추가 가능
)
```

### 4.4 데이터 민감도 고려
수집되는 데이터의 민감도 분류:
- **공개 가능**: CPU 사용률, 메모리 사용률
- **내부 전용**: 네트워크 트래픽 패턴
- **민감**: 프로세스별 상세 정보 (현재 미수집)

### 4.5 감사 로깅
```python
logger.info(f"Monitoring started by user {os.getlogin()} at {datetime.now()}")
logger.info(f"Parameters: duration={duration_minutes}, interval={interval_seconds}")
logger.info(f"Output directory: {output_dir}")
```

---

## 5. 성능 관련 이슈

### 5.1 CPU 사용률 측정 오버헤드
**위치**: `resource_collector.py:30`
```python
cpu_percent = psutil.cpu_percent(interval=1, percpu=False)
```

매 수집마다 1초 대기하므로 전체 수집 시간 증가

**권장**: interval을 0으로 설정하고 비동기 측정 방식 고려

### 5.2 그래프 생성 최적화
matplotlib 백엔드 선택으로 성능 개선 가능:
```python
import matplotlib
matplotlib.use('Agg')  # GUI 없는 백엔드
```

---

## 6. 플랫폼 호환성

### 6.1 Windows 호환성 문제
- `resource_collector.py:83`: `/` 경로가 Windows에서 작동 안함
- CPU 온도 센서 경로가 Linux 전용

### 6.2 macOS 호환성 문제
- 온도 센서 접근 방식이 다름
- 일부 psutil 기능 제한적

**권장**:
```python
import platform

if platform.system() == 'Windows':
    disk_path = 'C:\\'
elif platform.system() == 'Darwin':  # macOS
    disk_path = '/'
else:  # Linux
    disk_path = '/'
```

---

## 7. 우선순위별 개선 권장사항

### 즉시 수정 필요 (Priority 1)
1. ✅ **경로 주입 취약점 수정** - 경로 검증 로직 추가
2. ✅ **입력 검증 강화** - 상한선 설정 및 경로 검증
3. ✅ **리소스 소진 방지** - 최대값 제한

### 단기 개선 (Priority 2)
4. ✅ **로깅 시스템 도입** - logging 모듈 사용
5. ✅ **파일 권한 설정** - 생성 파일에 적절한 권한 부여
6. ✅ **에러 처리 개선** - 구체적 예외 처리 및 정보 노출 방지

### 중기 개선 (Priority 3)
7. ✅ **테스트 코드 작성** - 단위 테스트 및 통합 테스트
8. ✅ **설정 파일 지원** - 유연한 설정 관리
9. ✅ **플랫폼 호환성** - Windows, macOS 지원

### 장기 개선 (Priority 4)
10. ✅ **데이터베이스 통합** - 대용량 데이터 처리
11. ✅ **웹 인터페이스** - 실시간 모니터링 대시보드
12. ✅ **알림 기능** - 임계값 초과시 알림

---

## 8. 종합 평가

### 8.1 장점
- ✅ 명확한 모듈 구조
- ✅ 타입 힌팅 사용
- ✅ 문서화 (docstring)
- ✅ 의존성 버전 고정
- ✅ 사용자 친화적 CLI

### 8.2 주요 약점
- ⚠️ 보안 검증 부족
- ⚠️ 에러 처리 미흡
- ⚠️ 테스트 부재
- ⚠️ 로깅 시스템 없음
- ⚠️ 플랫폼 호환성 제한적

### 8.3 보안 위험도 평가

| 항목 | 위험도 | 상태 |
|------|--------|------|
| 경로 주입 | 높음 | 🔴 수정 필요 |
| 리소스 소진 | 중간 | 🟡 개선 권장 |
| 정보 노출 | 중간 | 🟡 개선 권장 |
| 입력 검증 | 높음 | 🔴 수정 필요 |
| 파일 권한 | 중간 | 🟡 개선 권장 |
| 의존성 보안 | 낮음 | 🟢 양호 |

**전체 보안 등급**: **C+ (개선 필요)**

---

## 9. 결론

이 시스템 모니터링 도구는 **기본적인 기능은 잘 구현**되어 있으나, **프로덕션 환경에서 사용하기 위해서는 보안 강화가 필수**입니다.

### 9.1 프로덕션 배포 전 필수 조치사항
1. 경로 검증 로직 구현
2. 입력값 범위 제한
3. 로깅 시스템 도입
4. 파일 권한 명시적 설정
5. 보안 테스트 수행

### 9.2 권장 개발 프로세스
1. 보안 코딩 가이드라인 수립
2. 정기적인 보안 감사
3. 의존성 취약점 스캔 자동화
4. CI/CD 파이프라인에 보안 검사 통합
5. 침투 테스트 수행

### 9.3 최종 권고사항
현재 상태로는 **개발/테스트 환경**에서만 사용하고, 위에서 언급한 **Priority 1, 2 항목을 모두 수정한 후** 프로덕션 환경에 배포할 것을 권장합니다.

---

## 10. 참고 자료

### 보안 가이드라인
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- CWE (Common Weakness Enumeration): https://cwe.mitre.org/
- Python Security Best Practices: https://python.readthedocs.io/en/stable/library/security_warnings.html

### 관련 CVE
- 정기적으로 확인 필요: https://nvd.nist.gov/

### 보안 도구
- Bandit: Python 보안 취약점 스캐너
- Safety: 의존성 취약점 체커
- pip-audit: PyPI 패키지 감사 도구

---

**리뷰어**: Claude Code Review System
**최종 업데이트**: 2025-11-06
**다음 리뷰 권장일**: 2025-12-06

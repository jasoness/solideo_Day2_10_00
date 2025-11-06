# System Resource Monitoring System

시스템 리소스(CPU, 메모리, 디스크, 네트워크, GPU)를 모니터링하고 결과를 PDF 리포트로 생성하는 Python 기반 모니터링 시스템입니다.

## 주요 기능

- **실시간 시스템 리소스 모니터링**
  - CPU 사용률 및 온도
  - 메모리 및 스왑 사용률
  - 디스크 사용률 및 I/O
  - 네트워크 트래픽 (업로드/다운로드 속도)
  - GPU 사용률 및 온도 (사용 가능한 경우)

- **시각화**
  - 모든 리소스에 대한 시간별 그래프 생성
  - 고품질 PNG 이미지로 저장

- **PDF 리포트 생성**
  - 전문적인 PDF 리포트 자동 생성
  - 그래프와 통계 정보 포함
  - 다운로드 가능한 형식

## 시스템 요구사항

- Python 3.7 이상
- Linux, Windows, macOS 지원
- (선택사항) NVIDIA GPU (GPU 모니터링을 위해)

## 설치 방법

### 1. 저장소 클론 또는 다운로드

```bash
git clone <repository-url>
cd solideo_Day2_10_00
```

### 2. 가상 환경 생성 (권장)

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 또는
venv\Scripts\activate  # Windows
```

### 3. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

## 사용 방법

### 기본 사용법 (5분간 모니터링)

```bash
cd system_monitor
python monitor.py
```

### 커스텀 설정

#### 모니터링 시간 변경 (10분)

```bash
python monitor.py -d 10
```

#### 데이터 수집 간격 변경 (10초마다)

```bash
python monitor.py -i 10
```

#### 출력 디렉토리 지정

```bash
python monitor.py -o /path/to/output
```

#### 모든 옵션 사용

```bash
python monitor.py -d 10 -i 5 -o custom_output
```

### 명령행 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `-d, --duration` | 모니터링 지속 시간 (분) | 5 |
| `-i, --interval` | 데이터 수집 간격 (초) | 5 |
| `-o, --output` | 출력 디렉토리 경로 | output |
| `-h, --help` | 도움말 표시 | - |

## 출력 파일

모니터링이 완료되면 다음 파일들이 생성됩니다:

### 그래프 파일 (PNG)
- `cpu_graph.png` - CPU 사용률 및 온도
- `memory_graph.png` - 메모리 및 스왑 사용률
- `disk_graph.png` - 디스크 사용률
- `network_graph.png` - 네트워크 트래픽
- `gpu_graph.png` - GPU 사용률 및 온도 (가능한 경우)

### PDF 리포트
- `system_monitor_report_YYYYMMDD_HHMMSS.pdf` - 종합 모니터링 리포트

## 프로젝트 구조

```
solideo_Day2_10_00/
├── system_monitor/
│   ├── __init__.py              # 패키지 초기화
│   ├── monitor.py               # 메인 실행 스크립트
│   ├── resource_collector.py   # 리소스 데이터 수집
│   ├── graph_generator.py      # 그래프 생성
│   └── pdf_reporter.py          # PDF 리포트 생성
├── requirements.txt             # 필요한 패키지 목록
└── README.md                    # 이 파일
```

## 모듈 설명

### resource_collector.py
시스템 리소스 정보를 수집하는 모듈입니다.
- `ResourceCollector` 클래스로 CPU, 메모리, 디스크, 네트워크, GPU 정보 수집
- psutil과 GPUtil 라이브러리 사용
- 실시간 네트워크 속도 계산

### graph_generator.py
수집된 데이터를 그래프로 시각화하는 모듈입니다.
- `GraphGenerator` 클래스로 matplotlib 기반 그래프 생성
- 각 리소스별 개별 그래프 생성
- 고해상도 PNG 형식으로 저장

### pdf_reporter.py
PDF 리포트를 생성하는 모듈입니다.
- `PDFReporter` 클래스로 reportlab 기반 PDF 생성
- 그래프와 통계 정보를 포함한 전문적인 리포트
- 요약 테이블 및 상세 통계 포함

### monitor.py
메인 실행 스크립트입니다.
- 모든 모듈을 통합하여 실행
- 명령행 인터페이스 제공
- 진행 상황 표시 및 에러 핸들링

## 예제

### 예제 1: 빠른 테스트 (1분)

```bash
python monitor.py -d 1 -i 2
```

이 명령은 1분간 2초마다 데이터를 수집합니다.

### 예제 2: 상세 모니터링 (30분)

```bash
python monitor.py -d 30 -i 10 -o detailed_report
```

이 명령은 30분간 10초마다 데이터를 수집하여 `detailed_report` 디렉토리에 저장합니다.

### 예제 3: 모듈 개별 사용

```python
from system_monitor import ResourceCollector, GraphGenerator, PDFReporter
import time

# 데이터 수집
collector = ResourceCollector()
for _ in range(10):
    collector.collect_all()
    time.sleep(5)

# 그래프 생성
generator = GraphGenerator()
graphs = generator.generate_all_graphs(collector.get_history())

# PDF 리포트 생성
reporter = PDFReporter()
pdf_path = reporter.generate_report(collector.get_history(), graphs, 1)
print(f"Report saved: {pdf_path}")
```

## 문제 해결

### GPU 정보를 가져올 수 없습니다

NVIDIA GPU가 없거나 드라이버가 설치되지 않은 경우 GPU 정보는 수집되지 않습니다. 이는 정상적인 동작이며, 다른 리소스는 계속 모니터링됩니다.

### CPU 온도 정보가 표시되지 않습니다

일부 시스템에서는 온도 센서에 접근할 수 없습니다. 이 경우 CPU 온도 그래프는 "Data Not Available" 메시지를 표시합니다.

### 권한 오류

일부 시스템 정보는 관리자 권한이 필요할 수 있습니다. 필요한 경우 sudo로 실행하세요:

```bash
sudo python monitor.py
```

### 패키지 설치 오류

가상 환경을 사용하거나 pip를 업그레이드하세요:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 의존성

- **psutil** (5.9.8): 시스템 및 프로세스 유틸리티
- **matplotlib** (3.8.2): 그래프 생성
- **reportlab** (4.0.9): PDF 생성
- **Pillow** (10.2.0): 이미지 처리
- **GPUtil** (1.4.0): GPU 모니터링 (선택사항)

## 라이선스

이 프로젝트는 LICENSE.md 파일에 명시된 라이선스 하에 배포됩니다.

## 기여

버그 리포트, 기능 요청, 풀 리퀘스트를 환영합니다!

## 작성자

System Monitor Team

## 버전 히스토리

- **v1.0.0** (2024-11-06)
  - 초기 릴리스
  - CPU, 메모리, 디스크, 네트워크, GPU 모니터링 기능
  - 그래프 생성 및 PDF 리포트 기능

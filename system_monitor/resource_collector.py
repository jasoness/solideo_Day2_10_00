"""
시스템 리소스 수집 모듈
CPU, 메모리, 디스크, 네트워크, GPU 온도 등을 수집합니다.
"""

import psutil
import time
from datetime import datetime
from typing import Dict, List, Optional

try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False


class ResourceCollector:
    """시스템 리소스를 수집하는 클래스"""

    def __init__(self):
        """초기화"""
        self.data_history: List[Dict] = []
        self.network_last = psutil.net_io_counters()
        self.last_time = time.time()

    def collect_cpu_info(self) -> Dict:
        """CPU 정보 수집"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1, percpu=False)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            # CPU 온도 수집 (Linux의 경우)
            cpu_temp = None
            try:
                temps = psutil.sensors_temperatures()
                if 'coretemp' in temps:
                    cpu_temp = temps['coretemp'][0].current
                elif 'cpu_thermal' in temps:
                    cpu_temp = temps['cpu_thermal'][0].current
                elif temps:
                    # 첫 번째 사용 가능한 온도 센서 사용
                    first_sensor = list(temps.keys())[0]
                    cpu_temp = temps[first_sensor][0].current
            except (AttributeError, KeyError, IndexError):
                cpu_temp = None

            return {
                'percent': cpu_percent,
                'count': cpu_count,
                'freq_current': cpu_freq.current if cpu_freq else None,
                'freq_max': cpu_freq.max if cpu_freq else None,
                'temperature': cpu_temp
            }
        except Exception as e:
            print(f"CPU 정보 수집 오류: {e}")
            return {'percent': 0, 'count': 0, 'freq_current': None, 'freq_max': None, 'temperature': None}

    def collect_memory_info(self) -> Dict:
        """메모리 정보 수집"""
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            return {
                'total': mem.total,
                'available': mem.available,
                'used': mem.used,
                'percent': mem.percent,
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_percent': swap.percent
            }
        except Exception as e:
            print(f"메모리 정보 수집 오류: {e}")
            return {'total': 0, 'available': 0, 'used': 0, 'percent': 0,
                    'swap_total': 0, 'swap_used': 0, 'swap_percent': 0}

    def collect_disk_info(self) -> Dict:
        """디스크 정보 수집"""
        try:
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()

            return {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent,
                'read_bytes': disk_io.read_bytes if disk_io else 0,
                'write_bytes': disk_io.write_bytes if disk_io else 0
            }
        except Exception as e:
            print(f"디스크 정보 수집 오류: {e}")
            return {'total': 0, 'used': 0, 'free': 0, 'percent': 0,
                    'read_bytes': 0, 'write_bytes': 0}

    def collect_network_info(self) -> Dict:
        """네트워크 정보 수집 (속도 계산 포함)"""
        try:
            current_time = time.time()
            network_current = psutil.net_io_counters()

            # 시간 간격 계산
            time_delta = current_time - self.last_time

            # 전송량 차이 계산
            bytes_sent_diff = network_current.bytes_sent - self.network_last.bytes_sent
            bytes_recv_diff = network_current.bytes_recv - self.network_last.bytes_recv

            # 초당 속도 계산 (Mbps)
            upload_speed = (bytes_sent_diff / time_delta) * 8 / 1_000_000 if time_delta > 0 else 0
            download_speed = (bytes_recv_diff / time_delta) * 8 / 1_000_000 if time_delta > 0 else 0

            # 다음 계산을 위해 저장
            self.network_last = network_current
            self.last_time = current_time

            return {
                'bytes_sent': network_current.bytes_sent,
                'bytes_recv': network_current.bytes_recv,
                'packets_sent': network_current.packets_sent,
                'packets_recv': network_current.packets_recv,
                'upload_speed_mbps': upload_speed,
                'download_speed_mbps': download_speed
            }
        except Exception as e:
            print(f"네트워크 정보 수집 오류: {e}")
            return {'bytes_sent': 0, 'bytes_recv': 0, 'packets_sent': 0,
                    'packets_recv': 0, 'upload_speed_mbps': 0, 'download_speed_mbps': 0}

    def collect_gpu_info(self) -> Optional[Dict]:
        """GPU 정보 수집"""
        if not GPU_AVAILABLE:
            return None

        try:
            gpus = GPUtil.getGPUs()
            if not gpus:
                return None

            gpu_data = []
            for gpu in gpus:
                gpu_data.append({
                    'id': gpu.id,
                    'name': gpu.name,
                    'load': gpu.load * 100,  # 백분율로 변환
                    'memory_used': gpu.memoryUsed,
                    'memory_total': gpu.memoryTotal,
                    'memory_percent': (gpu.memoryUsed / gpu.memoryTotal * 100) if gpu.memoryTotal > 0 else 0,
                    'temperature': gpu.temperature
                })

            return {'gpus': gpu_data}
        except Exception as e:
            print(f"GPU 정보 수집 오류: {e}")
            return None

    def collect_all(self) -> Dict:
        """모든 시스템 리소스 정보 수집"""
        timestamp = datetime.now()

        data = {
            'timestamp': timestamp,
            'cpu': self.collect_cpu_info(),
            'memory': self.collect_memory_info(),
            'disk': self.collect_disk_info(),
            'network': self.collect_network_info(),
            'gpu': self.collect_gpu_info()
        }

        self.data_history.append(data)
        return data

    def get_history(self) -> List[Dict]:
        """수집된 데이터 히스토리 반환"""
        return self.data_history

    def clear_history(self):
        """히스토리 초기화"""
        self.data_history = []


if __name__ == "__main__":
    # 테스트 코드
    collector = ResourceCollector()
    print("시스템 리소스 수집 테스트...")

    for i in range(3):
        data = collector.collect_all()
        print(f"\n[{i+1}회] 수집 시간: {data['timestamp']}")
        print(f"CPU 사용률: {data['cpu']['percent']}%")
        print(f"메모리 사용률: {data['memory']['percent']}%")
        print(f"디스크 사용률: {data['disk']['percent']}%")
        print(f"네트워크 업로드: {data['network']['upload_speed_mbps']:.2f} Mbps")
        print(f"네트워크 다운로드: {data['network']['download_speed_mbps']:.2f} Mbps")
        if data['gpu']:
            for gpu in data['gpu']['gpus']:
                print(f"GPU {gpu['id']} ({gpu['name']}): {gpu['load']:.1f}%, 온도: {gpu['temperature']}°C")
        time.sleep(2)

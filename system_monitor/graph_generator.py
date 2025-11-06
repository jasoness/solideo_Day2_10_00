"""
그래프 생성 모듈
수집된 데이터를 시각화하여 그래프로 생성합니다.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from typing import List, Dict
import os


class GraphGenerator:
    """시스템 리소스 데이터를 그래프로 생성하는 클래스"""

    def __init__(self, output_dir: str = "output"):
        """
        초기화

        Args:
            output_dir: 그래프를 저장할 디렉토리
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # 한글 폰트 설정 (Linux 환경)
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['axes.unicode_minus'] = False

    def _extract_timestamps(self, data_history: List[Dict]) -> List[datetime]:
        """타임스탬프 추출"""
        return [entry['timestamp'] for entry in data_history]

    def generate_cpu_graph(self, data_history: List[Dict]) -> str:
        """CPU 사용률 및 온도 그래프 생성"""
        timestamps = self._extract_timestamps(data_history)
        cpu_percent = [entry['cpu']['percent'] for entry in data_history]
        cpu_temp = [entry['cpu']['temperature'] for entry in data_history if entry['cpu']['temperature'] is not None]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # CPU 사용률 그래프
        ax1.plot(timestamps, cpu_percent, 'b-', linewidth=2, label='CPU Usage')
        ax1.set_ylabel('CPU Usage (%)', fontsize=12)
        ax1.set_title('CPU Usage Over Time', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 100)
        ax1.legend()

        # CPU 온도 그래프
        if cpu_temp and len(cpu_temp) == len(timestamps):
            ax2.plot(timestamps, cpu_temp, 'r-', linewidth=2, label='CPU Temperature')
            ax2.set_ylabel('Temperature (°C)', fontsize=12)
            ax2.set_title('CPU Temperature Over Time', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
        else:
            ax2.text(0.5, 0.5, 'CPU Temperature Data Not Available',
                     ha='center', va='center', transform=ax2.transAxes, fontsize=12)
            ax2.set_title('CPU Temperature Over Time', fontsize=14, fontweight='bold')

        ax2.set_xlabel('Time', fontsize=12)
        plt.tight_layout()

        output_path = os.path.join(self.output_dir, 'cpu_graph.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        return output_path

    def generate_memory_graph(self, data_history: List[Dict]) -> str:
        """메모리 사용률 그래프 생성"""
        timestamps = self._extract_timestamps(data_history)
        mem_percent = [entry['memory']['percent'] for entry in data_history]
        swap_percent = [entry['memory']['swap_percent'] for entry in data_history]

        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(timestamps, mem_percent, 'b-', linewidth=2, label='Memory Usage', marker='o', markersize=3)
        ax.plot(timestamps, swap_percent, 'orange', linewidth=2, label='Swap Usage', marker='s', markersize=3)

        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Usage (%)', fontsize=12)
        ax.set_title('Memory and Swap Usage Over Time', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 100)
        ax.legend(fontsize=10)

        plt.tight_layout()

        output_path = os.path.join(self.output_dir, 'memory_graph.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        return output_path

    def generate_disk_graph(self, data_history: List[Dict]) -> str:
        """디스크 사용률 그래프 생성"""
        timestamps = self._extract_timestamps(data_history)
        disk_percent = [entry['disk']['percent'] for entry in data_history]

        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(timestamps, disk_percent, 'g-', linewidth=2, label='Disk Usage', marker='o', markersize=3)
        ax.fill_between(timestamps, disk_percent, alpha=0.3, color='g')

        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Usage (%)', fontsize=12)
        ax.set_title('Disk Usage Over Time', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 100)
        ax.legend(fontsize=10)

        plt.tight_layout()

        output_path = os.path.join(self.output_dir, 'disk_graph.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        return output_path

    def generate_network_graph(self, data_history: List[Dict]) -> str:
        """네트워크 트래픽 그래프 생성"""
        timestamps = self._extract_timestamps(data_history)
        upload_speed = [entry['network']['upload_speed_mbps'] for entry in data_history]
        download_speed = [entry['network']['download_speed_mbps'] for entry in data_history]

        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(timestamps, upload_speed, 'r-', linewidth=2, label='Upload Speed', marker='^', markersize=4)
        ax.plot(timestamps, download_speed, 'b-', linewidth=2, label='Download Speed', marker='v', markersize=4)

        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Speed (Mbps)', fontsize=12)
        ax.set_title('Network Traffic Over Time', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=10)

        plt.tight_layout()

        output_path = os.path.join(self.output_dir, 'network_graph.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        return output_path

    def generate_gpu_graph(self, data_history: List[Dict]) -> str:
        """GPU 사용률 및 온도 그래프 생성"""
        # GPU 데이터가 있는지 확인
        has_gpu = any(entry['gpu'] is not None for entry in data_history)

        if not has_gpu:
            # GPU가 없는 경우 빈 그래프 생성
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, 'GPU Not Available or No Data',
                    ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_title('GPU Usage and Temperature', fontsize=14, fontweight='bold')
            output_path = os.path.join(self.output_dir, 'gpu_graph.png')
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            return output_path

        timestamps = self._extract_timestamps(data_history)

        # GPU 개수 확인
        num_gpus = len(data_history[0]['gpu']['gpus']) if data_history[0]['gpu'] else 0

        if num_gpus == 0:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, 'No GPU Detected',
                    ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_title('GPU Usage and Temperature', fontsize=14, fontweight='bold')
            output_path = os.path.join(self.output_dir, 'gpu_graph.png')
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            return output_path

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # 각 GPU에 대한 데이터 수집 및 플롯
        colors = ['b', 'r', 'g', 'orange', 'purple']
        for gpu_id in range(num_gpus):
            gpu_load = [entry['gpu']['gpus'][gpu_id]['load'] for entry in data_history if entry['gpu']]
            gpu_temp = [entry['gpu']['gpus'][gpu_id]['temperature'] for entry in data_history if entry['gpu']]
            gpu_name = data_history[0]['gpu']['gpus'][gpu_id]['name']

            color = colors[gpu_id % len(colors)]

            # GPU 사용률
            ax1.plot(timestamps, gpu_load, color=color, linewidth=2,
                     label=f'GPU {gpu_id} ({gpu_name})', marker='o', markersize=3)

            # GPU 온도
            ax2.plot(timestamps, gpu_temp, color=color, linewidth=2,
                     label=f'GPU {gpu_id} ({gpu_name})', marker='s', markersize=3)

        ax1.set_ylabel('GPU Load (%)', fontsize=12)
        ax1.set_title('GPU Usage Over Time', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 100)
        ax1.legend(fontsize=9)

        ax2.set_xlabel('Time', fontsize=12)
        ax2.set_ylabel('Temperature (°C)', fontsize=12)
        ax2.set_title('GPU Temperature Over Time', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(fontsize=9)

        plt.tight_layout()

        output_path = os.path.join(self.output_dir, 'gpu_graph.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        return output_path

    def generate_all_graphs(self, data_history: List[Dict]) -> Dict[str, str]:
        """모든 그래프 생성"""
        if not data_history:
            raise ValueError("데이터가 없습니다.")

        graphs = {
            'cpu': self.generate_cpu_graph(data_history),
            'memory': self.generate_memory_graph(data_history),
            'disk': self.generate_disk_graph(data_history),
            'network': self.generate_network_graph(data_history),
            'gpu': self.generate_gpu_graph(data_history)
        }

        return graphs


if __name__ == "__main__":
    # 테스트 코드
    print("그래프 생성 모듈 테스트는 실제 데이터가 필요합니다.")
    print("메인 스크립트를 통해 실행하세요.")

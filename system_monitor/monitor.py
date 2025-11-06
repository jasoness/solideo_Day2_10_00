#!/usr/bin/env python3
"""
시스템 리소스 모니터링 메인 스크립트

5분간 시스템 리소스를 모니터링하고 결과를 PDF 리포트로 생성합니다.
"""

import sys
import time
import argparse
from datetime import datetime
from resource_collector import ResourceCollector
from graph_generator import GraphGenerator
from pdf_reporter import PDFReporter


def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    """진행 상황 표시"""
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
    if iteration == total:
        print()


def monitor_system(duration_minutes: int = 5, interval_seconds: int = 5, output_dir: str = "output"):
    """
    시스템 리소스 모니터링 실행

    Args:
        duration_minutes: 모니터링 지속 시간 (분)
        interval_seconds: 데이터 수집 간격 (초)
        output_dir: 출력 디렉토리
    """
    print("=" * 70)
    print("         System Resource Monitoring System         ")
    print("=" * 70)
    print(f"\nMonitoring Configuration:")
    print(f"  - Duration: {duration_minutes} minutes")
    print(f"  - Sampling Interval: {interval_seconds} seconds")
    print(f"  - Output Directory: {output_dir}")
    print(f"  - Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "=" * 70)

    # 수집기 초기화
    collector = ResourceCollector()
    total_iterations = (duration_minutes * 60) // interval_seconds

    print(f"\nStarting data collection... ({total_iterations} data points)")
    print("Please wait, this will take approximately", duration_minutes, "minutes.\n")

    # 데이터 수집
    for i in range(total_iterations):
        try:
            # 데이터 수집
            data = collector.collect_all()

            # 진행 상황 표시
            elapsed_time = (i + 1) * interval_seconds
            remaining_time = (total_iterations - i - 1) * interval_seconds
            print_progress_bar(
                i + 1, total_iterations,
                prefix=f'Progress [{elapsed_time}s / {duration_minutes * 60}s]',
                suffix=f'Remaining: {remaining_time}s | CPU: {data["cpu"]["percent"]:.1f}% | Mem: {data["memory"]["percent"]:.1f}%',
                length=40
            )

            # 마지막 반복이 아니면 대기
            if i < total_iterations - 1:
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\n\nMonitoring interrupted by user.")
            if i > 0:
                print(f"Collected {i + 1} data points. Generating report with available data...")
                break
            else:
                print("No data collected. Exiting...")
                return
        except Exception as e:
            print(f"\nError during data collection: {e}")
            if i > 0:
                print("Continuing with available data...")
                break
            else:
                print("Failed to collect any data. Exiting...")
                return

    # 데이터 히스토리 가져오기
    data_history = collector.get_history()

    if not data_history:
        print("\nNo data collected. Exiting...")
        return

    print(f"\n\nData collection completed! Collected {len(data_history)} data points.")
    print("\n" + "=" * 70)

    # 그래프 생성
    print("\nGenerating graphs...")
    graph_generator = GraphGenerator(output_dir=output_dir)

    try:
        graph_paths = graph_generator.generate_all_graphs(data_history)
        print("  ✓ CPU graph generated")
        print("  ✓ Memory graph generated")
        print("  ✓ Disk graph generated")
        print("  ✓ Network graph generated")
        print("  ✓ GPU graph generated")
    except Exception as e:
        print(f"\nError generating graphs: {e}")
        return

    # PDF 리포트 생성
    print("\nGenerating PDF report...")
    pdf_reporter = PDFReporter(output_dir=output_dir)

    try:
        pdf_path = pdf_reporter.generate_report(
            data_history=data_history,
            graph_paths=graph_paths,
            monitoring_duration=duration_minutes
        )
        print(f"  ✓ PDF report generated successfully!")
    except Exception as e:
        print(f"\nError generating PDF report: {e}")
        return

    # 완료 메시지
    print("\n" + "=" * 70)
    print("         Monitoring Complete!         ")
    print("=" * 70)
    print(f"\nReport saved to: {pdf_path}")
    print(f"Graphs saved in: {output_dir}/")
    print("\nSummary:")
    print(f"  - Total monitoring time: {len(data_history) * interval_seconds} seconds")
    print(f"  - Data points collected: {len(data_history)}")
    print(f"  - Average CPU usage: {sum(d['cpu']['percent'] for d in data_history) / len(data_history):.2f}%")
    print(f"  - Average memory usage: {sum(d['memory']['percent'] for d in data_history) / len(data_history):.2f}%")
    print(f"  - Average disk usage: {sum(d['disk']['percent'] for d in data_history) / len(data_history):.2f}%")
    print("\n" + "=" * 70)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='System Resource Monitoring Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor for 5 minutes (default)
  python monitor.py

  # Monitor for 10 minutes with 10-second intervals
  python monitor.py -d 10 -i 10

  # Specify custom output directory
  python monitor.py -o /path/to/output
        """
    )

    parser.add_argument(
        '-d', '--duration',
        type=int,
        default=5,
        help='Monitoring duration in minutes (default: 5)'
    )

    parser.add_argument(
        '-i', '--interval',
        type=int,
        default=5,
        help='Data collection interval in seconds (default: 5)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default='output',
        help='Output directory for reports and graphs (default: output)'
    )

    args = parser.parse_args()

    # 입력 검증
    if args.duration <= 0:
        print("Error: Duration must be greater than 0")
        sys.exit(1)

    if args.interval <= 0:
        print("Error: Interval must be greater than 0")
        sys.exit(1)

    if args.interval > args.duration * 60:
        print("Error: Interval cannot be greater than total duration")
        sys.exit(1)

    # 모니터링 실행
    try:
        monitor_system(
            duration_minutes=args.duration,
            interval_seconds=args.interval,
            output_dir=args.output
        )
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

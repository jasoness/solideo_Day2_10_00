"""
PDF 리포트 생성 모듈
수집된 데이터와 그래프를 PDF 리포트로 생성합니다.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
from typing import List, Dict
import os


class PDFReporter:
    """시스템 모니터링 데이터를 PDF 리포트로 생성하는 클래스"""

    def __init__(self, output_dir: str = "output"):
        """
        초기화

        Args:
            output_dir: PDF를 저장할 디렉토리
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """커스텀 스타일 생성"""
        # 제목 스타일
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        # 섹션 제목 스타일
        self.section_style = ParagraphStyle(
            'SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2e5c8a'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )

        # 일반 텍스트 스타일
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6
        )

    def _format_bytes(self, bytes_value: int) -> str:
        """바이트를 읽기 쉬운 형식으로 변환"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"

    def _create_summary_table(self, data_history: List[Dict]) -> Table:
        """요약 테이블 생성"""
        if not data_history:
            return None

        first_data = data_history[0]
        last_data = data_history[-1]

        # CPU 통계
        cpu_values = [entry['cpu']['percent'] for entry in data_history]
        cpu_avg = sum(cpu_values) / len(cpu_values)
        cpu_max = max(cpu_values)
        cpu_min = min(cpu_values)

        # 메모리 통계
        mem_values = [entry['memory']['percent'] for entry in data_history]
        mem_avg = sum(mem_values) / len(mem_values)
        mem_max = max(mem_values)

        # 디스크 통계
        disk_percent = last_data['disk']['percent']
        disk_total = self._format_bytes(last_data['disk']['total'])
        disk_used = self._format_bytes(last_data['disk']['used'])

        # 네트워크 통계
        total_sent = last_data['network']['bytes_sent']
        total_recv = last_data['network']['bytes_recv']

        data = [
            ['Resource', 'Statistics'],
            ['CPU Usage', f'Avg: {cpu_avg:.1f}% | Min: {cpu_min:.1f}% | Max: {cpu_max:.1f}%'],
            ['Memory Usage', f'Avg: {mem_avg:.1f}% | Max: {mem_max:.1f}%'],
            ['Disk Usage', f'{disk_percent:.1f}% ({disk_used} / {disk_total})'],
            ['Network Sent', f'{self._format_bytes(total_sent)}'],
            ['Network Received', f'{self._format_bytes(total_recv)}'],
        ]

        # GPU 정보 추가
        if last_data['gpu'] and last_data['gpu']['gpus']:
            for gpu in last_data['gpu']['gpus']:
                gpu_info = f"GPU {gpu['id']} ({gpu['name']}): {gpu['load']:.1f}% | Temp: {gpu['temperature']}°C"
                data.append(['GPU', gpu_info])

        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))

        return table

    def generate_report(self, data_history: List[Dict], graph_paths: Dict[str, str],
                        monitoring_duration: int) -> str:
        """
        PDF 리포트 생성

        Args:
            data_history: 수집된 데이터 히스토리
            graph_paths: 생성된 그래프 파일 경로들
            monitoring_duration: 모니터링 시간 (분)

        Returns:
            생성된 PDF 파일 경로
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"system_monitor_report_{timestamp}.pdf"
        pdf_path = os.path.join(self.output_dir, pdf_filename)

        # PDF 문서 생성
        doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)

        # 스토리 생성 (PDF 내용)
        story = []

        # 제목
        title = Paragraph("System Resource Monitoring Report", self.title_style)
        story.append(title)
        story.append(Spacer(1, 0.2*inch))

        # 리포트 정보
        report_info = f"""
        <para align=center>
        <b>Report Generated:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br/>
        <b>Monitoring Duration:</b> {monitoring_duration} minutes<br/>
        <b>Total Data Points:</b> {len(data_history)}<br/>
        <b>Monitoring Period:</b> {data_history[0]['timestamp'].strftime("%H:%M:%S")} -
        {data_history[-1]['timestamp'].strftime("%H:%M:%S")}
        </para>
        """
        story.append(Paragraph(report_info, self.normal_style))
        story.append(Spacer(1, 0.3*inch))

        # 요약 테이블
        story.append(Paragraph("Executive Summary", self.section_style))
        summary_table = self._create_summary_table(data_history)
        if summary_table:
            story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))

        # 페이지 나누기
        story.append(PageBreak())

        # CPU 그래프
        story.append(Paragraph("CPU Usage and Temperature", self.section_style))
        if os.path.exists(graph_paths['cpu']):
            cpu_img = Image(graph_paths['cpu'], width=6*inch, height=4*inch)
            story.append(cpu_img)
        story.append(Spacer(1, 0.2*inch))

        # 메모리 그래프
        story.append(Paragraph("Memory and Swap Usage", self.section_style))
        if os.path.exists(graph_paths['memory']):
            mem_img = Image(graph_paths['memory'], width=6*inch, height=3*inch)
            story.append(mem_img)
        story.append(Spacer(1, 0.2*inch))

        # 페이지 나누기
        story.append(PageBreak())

        # 디스크 그래프
        story.append(Paragraph("Disk Usage", self.section_style))
        if os.path.exists(graph_paths['disk']):
            disk_img = Image(graph_paths['disk'], width=6*inch, height=3*inch)
            story.append(disk_img)
        story.append(Spacer(1, 0.2*inch))

        # 네트워크 그래프
        story.append(Paragraph("Network Traffic", self.section_style))
        if os.path.exists(graph_paths['network']):
            net_img = Image(graph_paths['network'], width=6*inch, height=3*inch)
            story.append(net_img)
        story.append(Spacer(1, 0.2*inch))

        # GPU 그래프 (있는 경우)
        if os.path.exists(graph_paths['gpu']):
            story.append(PageBreak())
            story.append(Paragraph("GPU Usage and Temperature", self.section_style))
            gpu_img = Image(graph_paths['gpu'], width=6*inch, height=4*inch)
            story.append(gpu_img)

        # 페이지 나누기 및 상세 데이터
        story.append(PageBreak())
        story.append(Paragraph("Detailed Statistics", self.section_style))

        # 상세 통계 테이블
        cpu_values = [entry['cpu']['percent'] for entry in data_history]
        mem_values = [entry['memory']['percent'] for entry in data_history]
        disk_values = [entry['disk']['percent'] for entry in data_history]

        detailed_data = [
            ['Metric', 'Average', 'Minimum', 'Maximum'],
            ['CPU Usage (%)', f'{sum(cpu_values)/len(cpu_values):.2f}',
             f'{min(cpu_values):.2f}', f'{max(cpu_values):.2f}'],
            ['Memory Usage (%)', f'{sum(mem_values)/len(mem_values):.2f}',
             f'{min(mem_values):.2f}', f'{max(mem_values):.2f}'],
            ['Disk Usage (%)', f'{sum(disk_values)/len(disk_values):.2f}',
             f'{min(disk_values):.2f}', f'{max(disk_values):.2f}'],
        ]

        detailed_table = Table(detailed_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        detailed_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        story.append(detailed_table)

        # PDF 빌드
        doc.build(story)

        return pdf_path


if __name__ == "__main__":
    print("PDF 리포트 생성 모듈 테스트는 실제 데이터가 필요합니다.")
    print("메인 스크립트를 통해 실행하세요.")

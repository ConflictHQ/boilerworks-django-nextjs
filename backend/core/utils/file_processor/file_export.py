from datetime import datetime
from typing import Iterable

import pytz
from config import settings
from core.utils.file_processor.file_export_util import FileExportMixin, SupportedFileFormats
from core.views import FileExport
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, QueryDict


class ChatHistory(FileExport, FileExportMixin):
    chat_identifier: str = ""
    file_format: SupportedFileFormats = SupportedFileFormats.PDF

    def validate_params(self, request: WSGIRequest) -> None | HttpResponse:
        chat_identifier: str = request.GET.get('chat_identifier', None)
        if not chat_identifier:
            return HttpResponse(
                'chat_identifier query parameter is required.',
                status=400
            )
        self.chat_identifier = chat_identifier.replace(' ', '_')
        return None

    def get_filename(self, params: QueryDict) -> str:
        return f'{self.chat_identifier}.{self.file_format}'

    def get_queryset(self, request: WSGIRequest) -> Iterable:
        from core.utils.api.rocketchat_rest_client import RocketchatRestClient
        client = RocketchatRestClient()
        return RocketchatRestClient.read_channel(client, self.chat_identifier)

    def iter_items(self, queryset, buffer):
        import io

        import emoji
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        elements = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,
            spaceAfter=20,
            alignment=1,
        )
        title = Paragraph(f'Chat history for {self.chat_identifier}', title_style)
        elements.append(title)
        elements.append(Spacer(1, 6))
        sorted_by_date = sorted(queryset, key=lambda i: i.get('ts', ''))
        line_style = ParagraphStyle(
            'CustomChatLine',
            parent=styles['Normal'],
            fontSize=10,
            alignment=0,
        )

        for item in sorted_by_date:
            time = self.parse_time(item.get('ts', ''))
            user = item.get('u', {}).get('username', 'has-no-username')
            msg = emoji.demojize(item.get('msg', ''), language='en')
            elements.append(
                Paragraph(
                    f'<b>[{time}] </b><font color="blue">{user}</font>: {msg}<br/>',
                    style=line_style
                )
            )

        doc.build(elements)
        pdf_content = pdf_buffer.getvalue()
        pdf_buffer.close()
        chunk_size = 8192
        for i in range(0, len(pdf_content), chunk_size):
            yield pdf_content[i:i + chunk_size]

    @classmethod
    def parse_time(cls, timestamp: str):
        try:
            # Parse ISO format and assign UTC timezone
            utc_dt = datetime.fromisoformat(timestamp.replace('Z', '')).replace(tzinfo=pytz.UTC)
            # Convert to Mountain Time
            mt_dt = utc_dt.astimezone(pytz.timezone(settings.SYSTEM_TIME_ZONE))
            return mt_dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return timestamp

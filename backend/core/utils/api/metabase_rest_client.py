import logging

from config import settings
from core.models import MetabaseChart, MetabaseObjectType, MetabaseUnimportedChart, ReportType
from core.utils.request_handler import RequestHandler

logger = logging.getLogger(__name__)


class MetabaseRestClient:
    request_handler = RequestHandler()

    def __init__(self):

        self.server_url = settings.METABASE_SITE_URL
        self.admin_headers = {
            'x-api-key': settings.METABASE_BACKEND_API_KEY,
        }
        self.metabase_api_urls = {
            MetabaseObjectType.DASHBOARD.name: self.server_url + '/api/dashboard',
            MetabaseObjectType.QUESTION.name: self.server_url + '/api/card',
        }

    def create_unimported_chart_record(self, unimported_dashboard, unimported_chart_type: MetabaseObjectType):
        return MetabaseUnimportedChart(
            metabase_chart_id=unimported_dashboard['id'],
            type=unimported_chart_type.name,
            title=unimported_dashboard['name'],
            description=unimported_dashboard['description'],
            creator_email=unimported_dashboard['creator']['email'],
            is_embedding_enabled=unimported_dashboard['enable_embedding'],
            created_at=unimported_dashboard['created_at'])

    def get_charts_in_db(self):
        metabase_charts_entries = MetabaseChart.objects.all().values('metabase_chart_id', 'type')
        unimported_charts_entries = MetabaseUnimportedChart.objects.all().values('metabase_chart_id', 'type')

        dashboard_ids = set()
        question_ids = set()

        for entry in metabase_charts_entries:
            if entry['type'] == 'DASHBOARD':
                dashboard_ids.add(entry['metabase_chart_id'])
            elif entry['type'] == 'QUESTION':
                question_ids.add(entry['metabase_chart_id'])

        for entry in unimported_charts_entries:
            if entry['type'] == 'DASHBOARD':
                dashboard_ids.add(entry['metabase_chart_id'])
            elif entry['type'] == 'QUESTION':
                question_ids.add(entry['metabase_chart_id'])

        return {
            'dashboard': dashboard_ids,
            'question': question_ids
        }

    def get_and_save_unimported_metabase_charts(self):
        dashboard_response = self.get_metabase_dashboards()
        card_response = self.get_metabase_cards()

        charts_in_db = self.get_charts_in_db()

        unimported_chart_new_entries = []

        for dashboard in dashboard_response:
            if dashboard['id'] not in charts_in_db['dashboard']:
                unimported_chart_new_entries.append(self.create_unimported_chart_record(dashboard, MetabaseObjectType.DASHBOARD))

        for card in card_response:
            if card['id'] not in charts_in_db['question']:
                unimported_chart_new_entries.append(self.create_unimported_chart_record(card, MetabaseObjectType.QUESTION))

        if unimported_chart_new_entries:
            MetabaseUnimportedChart.objects.bulk_create(unimported_chart_new_entries)

    def get_metabase_cards(self):
        response = self.request_handler.make_request(
            method='GET',
            url=self.server_url + '/api/card/?f=all',
            headers=self.admin_headers,
        )

        if not response:
            logger.error(f'Failed to get Metabase users: {response}')
            raise Exception(f'Failed to get Metabase users: {response}')

        return response

    def get_metabase_dashboards(self):
        response = self.request_handler.make_request(
            method='GET',
            url=self.server_url + '/api/dashboard/?f=all',
            headers=self.admin_headers,
        )

        if not response:
            logger.error(f'Failed to get Metabase dashboards: {response}')
            raise Exception(f'Failed to get Metabase dashboards: {response}')

        return response

    def set_chart_as_embedding_enabled(self, metabase_chart_id, type: ReportType):
        url_per_type = f'{self.metabase_api_urls[type]}/{metabase_chart_id}'
        body = {
            'enable_embedding': True
        }

        response = self.request_handler.make_request(
            method='PUT',
            url=url_per_type,
            headers=self.admin_headers,
            json=body
        )

        return response

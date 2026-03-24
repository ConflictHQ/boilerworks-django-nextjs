import logging
from typing import Dict, List, Type

from core.models.internationalization import Locale, SiteLabel
from core.models.process import DataProcessEntity, ProcessStatus
from core.systems import EntityProcessor

logger = logging.getLogger(__name__)


class SiteLabelProcessor(EntityProcessor):
    @classmethod
    def process(cls, records, user_id: Type[int], overwrite: bool = False) -> ProcessStatus:
        record: DataProcessEntity
        process_status = ProcessStatus.DONE
        locale = Locale.objects.get(language_code=records[0].data['language_code'])
        for record in records:
            if not record.data:
                record.update_status(ProcessStatus.IGNORED)
                continue
            try:
                SiteLabel.objects.update_or_create(
                    key=record.data['key'],
                    locale=locale,
                    defaults={
                        'text': record.data['text'],
                        'created_by_id': user_id,
                        'updated_by_id': user_id
                    }

                )

                record.update_status(ProcessStatus.DONE)
            except Exception as e:
                key = record.get('key', None)
                logger.exception(f'Could not process site label with key: {key} of file :{record.process_id}', e)
                error_message = None
                process_status = ProcessStatus.FAILED
                if e.args and e.args[0]:
                    error_message = e.args[0]
                record.update_status(ProcessStatus.FAILED, error_message)
        return process_status

    @classmethod
    def load_api_data(cls, process) -> List[Dict]:
        pass

# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['TestRule::test_eval_actions_dry_run 1'] = '2023-10-28 00:00 - test_logger - INFO - Executing in transaction actions:<br/>2023-10-28 00:00 - test_logger.hello_world - INFO - Hello World - 2023-10-28T00:00:00+00:00<br/>2023-10-28 00:00 - test_logger - INFO - No post transaction actions defined<br/>2023-10-28 00:00 - test_logger - INFO - Dry run: Rolling back transaction'

snapshots['TestRule::test_eval_post_transaction_actions 1'] = '2023-10-28 00:00 - test_logger - INFO - Executing post transaction actions:<br/>2023-10-28 00:00 - test_logger.hello_world - INFO - Hello World - 2023-10-28T00:00:00+00:00'

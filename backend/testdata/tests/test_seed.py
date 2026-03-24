"""
Tests for the seed management command.

Verifies that the command discovers the fixture files and calls loaddata
for each one, in order, without actually loading data into the test DB.
"""
from io import StringIO
from unittest.mock import patch

import testdata.management.commands.seed as seed_module
from django.core.management import call_command
from django.test import TestCase


class SeedCommandTest(TestCase):

    def _run_seed(self, **kwargs):
        out = StringIO()
        with patch.object(seed_module, 'management') as mock_mgmt:
            call_command('seed', stdout=out, **kwargs)
        return out.getvalue(), mock_mgmt

    def test_loads_all_fixture_files(self):
        output, mock_mgmt = self._run_seed()
        loaddata_calls = [
            c for c in mock_mgmt.call_command.call_args_list
            if c.args[0] == 'loaddata'
        ]
        self.assertEqual(len(loaddata_calls), 6)
        self.assertIn('Seeded 6', output)

    def test_fixture_files_loaded_in_sorted_order(self):
        output, mock_mgmt = self._run_seed()
        loaddata_calls = [
            c for c in mock_mgmt.call_command.call_args_list
            if c.args[0] == 'loaddata'
        ]
        fixture_names = [c.args[1].rsplit('/', 1)[-1] for c in loaddata_calls]
        self.assertEqual(fixture_names, sorted(fixture_names))

    def test_flush_flag_runs_flush_before_loaddata(self):
        output, mock_mgmt = self._run_seed(flush=True)
        first_call = mock_mgmt.call_command.call_args_list[0]
        self.assertEqual(first_call.args[0], 'flush')

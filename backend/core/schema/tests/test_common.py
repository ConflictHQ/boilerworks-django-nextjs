import datetime
from unittest.mock import MagicMock

from django.test import TestCase

from core.schema.common import (
    CaseInsensitiveOrderingFilter,
    GlobalIDUtils,
    MutationResult,
    ValidationError,
    permission_filtered_queryset,
    unpack_nested_errors,
)
from core.schema.scalars import TimeDelta


class GlobalIDUtilsTest(TestCase):
    """Tests for relay Global ID encoding/decoding utilities."""

    def test_round_trip_encode_decode(self):
        type_name = "UserType"
        pk = "42"
        global_id = GlobalIDUtils.to_global_id(type_name, pk)
        decoded_type, decoded_pk = GlobalIDUtils.from_global_id(global_id)
        self.assertEqual(decoded_type, type_name)
        self.assertEqual(decoded_pk, pk)

    def test_get_pk_with_matching_type(self):
        global_id = GlobalIDUtils.to_global_id("UserType", "7")
        pk = GlobalIDUtils.get_pk(global_id, expected_type="UserType")
        self.assertEqual(pk, "7")

    def test_get_pk_with_mismatched_type_raises(self):
        global_id = GlobalIDUtils.to_global_id("UserType", "7")
        from graphql import GraphQLError
        with self.assertRaises(GraphQLError) as ctx:
            GlobalIDUtils.get_pk(global_id, expected_type="ProfileType")
        self.assertIn("expected ProfileType", str(ctx.exception))
        self.assertIn("got UserType", str(ctx.exception))

    def test_get_pk_with_mismatched_type_returns_none_when_not_raising(self):
        global_id = GlobalIDUtils.to_global_id("UserType", "7")
        pk = GlobalIDUtils.get_pk(
            global_id, expected_type="ProfileType", raise_on_mismatch=False
        )
        self.assertIsNone(pk)

    def test_get_pk_without_type_check(self):
        global_id = GlobalIDUtils.to_global_id("UserType", "99")
        pk = GlobalIDUtils.get_pk(global_id)
        self.assertEqual(pk, "99")

    def test_get_pk_flexible_with_integer_string(self):
        pk = GlobalIDUtils.get_pk_flexible("42")
        self.assertEqual(pk, "42")

    def test_get_pk_flexible_with_integer(self):
        pk = GlobalIDUtils.get_pk_flexible(123)
        self.assertEqual(pk, "123")

    def test_get_pk_flexible_with_global_id(self):
        global_id = GlobalIDUtils.to_global_id("UserType", "5")
        pk = GlobalIDUtils.get_pk_flexible(global_id, expected_type="UserType")
        self.assertEqual(pk, "5")

    def test_get_pk_flexible_with_empty_string(self):
        pk = GlobalIDUtils.get_pk_flexible("")
        self.assertIsNone(pk)

    def test_get_pk_flexible_with_none(self):
        pk = GlobalIDUtils.get_pk_flexible(None)
        self.assertIsNone(pk)


class ValidationErrorTest(TestCase):
    """Tests for validation error types."""

    def test_unpack_flat_errors(self):
        errors = {"email": ["This field is required.", "Enter a valid email."]}
        result = unpack_nested_errors(errors)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].field, "email")
        self.assertEqual(len(result[0].messages), 2)
        self.assertIn("This field is required.", result[0].messages)

    def test_unpack_nested_errors(self):
        errors = {
            "profile": {
                "address": {
                    "zipcode": ["Invalid zip code."]
                }
            }
        }
        result = unpack_nested_errors(errors)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].field, "profile.address.zipcode")
        self.assertEqual(result[0].messages, ["Invalid zip code."])

    def test_unpack_mixed_flat_and_nested(self):
        errors = {
            "username": ["Already taken."],
            "profile": {
                "phone": ["Invalid format."]
            }
        }
        result = unpack_nested_errors(errors)
        fields = {e.field for e in result}
        self.assertEqual(fields, {"username", "profile.phone"})


class MutationResultTest(TestCase):
    """Tests for MutationResult factory methods."""

    def test_success(self):
        result = MutationResult.success()
        self.assertTrue(result.ok)
        self.assertEqual(result.errors, [])

    def test_from_serializer_errors(self):
        errors = {
            "name": ["This field is required."],
            "nested": {"key": ["Bad value."]}
        }
        result = MutationResult.from_serializer_errors(errors)
        self.assertFalse(result.ok)
        self.assertEqual(len(result.errors), 2)
        fields = {e.field for e in result.errors}
        self.assertEqual(fields, {"name", "nested.key"})

    def test_from_form_errors(self):
        errors = {"email": ["Enter a valid email address."]}
        result = MutationResult.from_form_errors(errors)
        self.assertFalse(result.ok)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].field, "email")


class TimeDeltaScalarTest(TestCase):
    """Tests for the TimeDelta custom scalar."""

    def test_serialize_timedelta(self):
        td = datetime.timedelta(hours=1, minutes=30)
        result = TimeDelta.serialize(td)
        self.assertEqual(result, 5400.0)

    def test_serialize_zero(self):
        td = datetime.timedelta(0)
        result = TimeDelta.serialize(td)
        self.assertEqual(result, 0.0)

    def test_serialize_negative(self):
        td = datetime.timedelta(seconds=-60)
        result = TimeDelta.serialize(td)
        self.assertEqual(result, -60.0)

    def test_serialize_non_timedelta_raises(self):
        from graphql import GraphQLError
        with self.assertRaises(GraphQLError):
            TimeDelta.serialize("not a timedelta")

    def test_parse_value_int(self):
        result = TimeDelta.parse_value(3600)
        self.assertEqual(result, datetime.timedelta(hours=1))

    def test_parse_value_float(self):
        result = TimeDelta.parse_value(90.5)
        self.assertEqual(result, datetime.timedelta(seconds=90.5))

    def test_parse_value_timedelta_passthrough(self):
        td = datetime.timedelta(minutes=5)
        result = TimeDelta.parse_value(td)
        self.assertEqual(result, td)

    def test_parse_value_non_numeric_raises(self):
        from graphql import GraphQLError
        with self.assertRaises(GraphQLError):
            TimeDelta.parse_value("abc")


class PermissionFilteredQuerysetTest(TestCase):
    """Tests for the permission_filtered_queryset helper."""

    def test_calls_model_get_queryset(self):
        mock_user = MagicMock()
        mock_info = MagicMock()
        mock_info.context.user = mock_user

        mock_qs = MagicMock(spec=["model", "filter"])
        mock_model = MagicMock()
        mock_model.get_queryset.return_value = mock_qs
        mock_qs.model = mock_model

        result = permission_filtered_queryset(mock_qs, mock_info)

        mock_model.get_queryset.assert_called_once_with(mock_qs, mock_user)
        self.assertEqual(result, mock_qs)

    def test_returns_unfiltered_if_no_get_queryset(self):
        mock_info = MagicMock()
        mock_qs = MagicMock(spec=["model", "filter"])
        mock_model = MagicMock(spec=[])  # No get_queryset
        mock_qs.model = mock_model

        result = permission_filtered_queryset(mock_qs, mock_info)
        self.assertEqual(result, mock_qs)

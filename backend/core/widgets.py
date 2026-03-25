"""Custom Django admin widgets.

JSONEditorWidget: renders a JSON field with syntax highlighting and
basic validation. Uses a simple <textarea> with monospace font and
client-side JSON validation — no external JS libraries needed.
"""
import json

from django.forms import widgets


class JSONEditorWidget(widgets.Textarea):
    """A textarea widget with JSON formatting and validation."""

    template_name = 'admin/widgets/json_editor.html'

    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'vLargeTextField json-editor',
            'rows': 20,
            'style': 'font-family: monospace; font-size: 13px; tab-size: 2; white-space: pre;',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def format_value(self, value):
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return json.dumps(parsed, indent=2)
            except (json.JSONDecodeError, TypeError):
                return value
        if isinstance(value, (dict, list)):
            return json.dumps(value, indent=2)
        return value

    class Media:
        js = ('admin/js/json_editor.js',)
        css = {'all': ('admin/css/json_editor.css',)}


class FormBuilderWidget(widgets.Textarea):
    """Visual form schema builder widget.

    Renders a drag-and-drop field editor that generates JSON Schema.
    Includes a JSON tab for direct editing.
    """

    template_name = 'admin/widgets/form_builder.html'

    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'vLargeTextField form-schema-builder',
            'rows': 20,
            'style': 'font-family: monospace; font-size: 13px; tab-size: 2; white-space: pre;',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def format_value(self, value):
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return json.dumps(parsed, indent=2)
            except (json.JSONDecodeError, TypeError):
                return value
        if isinstance(value, (dict, list)):
            return json.dumps(value, indent=2)
        return value

    class Media:
        js = ('admin/js/form_builder.js',)
        css = {'all': ('admin/css/form_builder.css',)}


class WorkflowStatesWidget(widgets.Textarea):
    """Visual workflow states builder widget."""

    template_name = 'admin/widgets/json_editor.html'

    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'vLargeTextField workflow-states-builder',
            'rows': 12,
            'style': 'font-family: monospace; font-size: 13px; tab-size: 2; white-space: pre;',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def format_value(self, value):
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return json.dumps(parsed, indent=2)
            except (json.JSONDecodeError, TypeError):
                return value
        if isinstance(value, (dict, list)):
            return json.dumps(value, indent=2)
        return value

    class Media:
        js = ('admin/js/workflow_builder.js',)
        css = {'all': ('admin/css/workflow_builder.css',)}


class WorkflowTransitionsWidget(widgets.Textarea):
    """Visual workflow transitions builder widget.

    Paired with WorkflowStatesWidget — the JS links both together.
    """

    template_name = 'admin/widgets/json_editor.html'

    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'vLargeTextField workflow-transitions-builder',
            'rows': 12,
            'style': 'font-family: monospace; font-size: 13px; tab-size: 2; white-space: pre;',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def format_value(self, value):
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return json.dumps(parsed, indent=2)
            except (json.JSONDecodeError, TypeError):
                return value
        if isinstance(value, (dict, list)):
            return json.dumps(value, indent=2)
        return value

    class Media:
        js = ()  # JS is loaded by WorkflowStatesWidget
        css = {'all': ()}

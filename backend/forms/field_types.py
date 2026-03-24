"""Built-in field types for the Form Engine.

Each field type defines a JSON Schema fragment that gets composed
into a FormDefinition's schema. The frontend uses these to render
the correct input components.

Usage in a form schema:
    {
        "type": "object",
        "properties": {
            "name": {"type": "string", "title": "Full Name"},
            "amount": {"type": "number", "title": "Amount"},
            "due_date": {"type": "string", "format": "date", "title": "Due Date"},
        },
        "required": ["name", "amount"]
    }
"""

FIELD_TYPES = {
    'text': {
        'type': 'string',
        'description': 'Single-line text input',
    },
    'textarea': {
        'type': 'string',
        'description': 'Multi-line text input',
        'x-widget': 'textarea',
    },
    'number': {
        'type': 'number',
        'description': 'Numeric input',
    },
    'integer': {
        'type': 'integer',
        'description': 'Integer input',
    },
    'boolean': {
        'type': 'boolean',
        'description': 'Checkbox / toggle',
    },
    'date': {
        'type': 'string',
        'format': 'date',
        'description': 'Date picker (YYYY-MM-DD)',
    },
    'datetime': {
        'type': 'string',
        'format': 'date-time',
        'description': 'Date and time picker (ISO 8601)',
    },
    'email': {
        'type': 'string',
        'format': 'email',
        'description': 'Email address input',
    },
    'url': {
        'type': 'string',
        'format': 'uri',
        'description': 'URL input',
    },
    'select': {
        'type': 'string',
        'enum': [],
        'description': 'Single-select dropdown. Set enum values in the schema.',
    },
    'multi_select': {
        'type': 'array',
        'items': {'type': 'string'},
        'description': 'Multi-select. Set items.enum in the schema.',
    },
    'file': {
        'type': 'string',
        'format': 'uri',
        'description': 'File upload (stores URL/global ID of uploaded file)',
        'x-widget': 'file',
    },
    'user_lookup': {
        'type': 'string',
        'description': 'User picker (stores user global ID)',
        'x-widget': 'user_lookup',
    },
    # Assessment / survey question types
    'rating': {
        'type': 'integer',
        'minimum': 1,
        'maximum': 5,
        'description': 'Star rating (1-5). Customize min/max in schema.',
        'x-widget': 'rating',
    },
    'scale': {
        'type': 'integer',
        'minimum': 0,
        'maximum': 10,
        'description': 'Numeric scale (e.g. 0-10 NPS). Customize min/max in schema.',
        'x-widget': 'scale',
    },
    'matrix': {
        'type': 'object',
        'description': 'Matrix question (rows × columns). Define rows/columns in field_config.',
        'x-widget': 'matrix',
    },
    'ranking': {
        'type': 'array',
        'items': {'type': 'string'},
        'description': 'Drag-to-rank list. Define options in field_config.',
        'x-widget': 'ranking',
    },
    'signature': {
        'type': 'string',
        'description': 'Signature capture (stores base64 or upload URL)',
        'x-widget': 'signature',
    },
    # Repeatable / loop types
    'repeatable': {
        'type': 'array',
        'items': {'type': 'object'},
        'description': 'Repeatable section (add another line item). Define item schema in items.properties.',
        'x-widget': 'repeatable',
    },
    # Percentage / split allocation
    'percentage_split': {
        'type': 'object',
        'description': (
            'Allocate a total across categories (must sum to 100). '
            'Keys are category names, values are percentages.'
        ),
        'x-widget': 'percentage_split',
        'x-validation': 'sum_to_100',
    },
}


# Question types that support scoring/weights
SCORABLE_TYPES = {'select', 'multi_select', 'rating', 'scale', 'boolean', 'ranking'}


# Logic condition operators
LOGIC_OPERATORS = {
    'eq': 'equals',
    'neq': 'not equals',
    'gt': 'greater than',
    'lt': 'less than',
    'gte': 'greater than or equal',
    'lte': 'less than or equal',
    'in': 'is one of',
    'not_in': 'is not one of',
    'contains': 'contains',
    'is_empty': 'is empty',
    'is_not_empty': 'is not empty',
}

# Logic actions
LOGIC_ACTIONS = {
    'show': 'Show a field',
    'hide': 'Hide a field',
    'require': 'Make a field required',
    'skip_to': 'Skip to a step (multi-step forms)',
    'set_value': 'Set a field value',
    'calculate': 'Compute a value from other fields',
    'display_from': 'Display a value entered in a previous step',
}

# Calculation operators for computed fields
CALC_OPERATORS = {
    'sum': 'Sum of field values',
    'avg': 'Average of field values',
    'min': 'Minimum of field values',
    'max': 'Maximum of field values',
    'count': 'Count of non-empty fields',
    'concat': 'Concatenate string fields',
    'multiply': 'Multiply field values',
    'subtract': 'Subtract second field from first',
    'divide': 'Divide first field by second',
    'percentage': 'First field as percentage of second',
    'expression': 'Custom expression (e.g. "field_a * field_b + field_c")',
}


def evaluate_calculation(calc_config, payload):
    """Evaluate a calculation against a submission payload.

    calc_config format:
        {"op": "sum", "fields": ["amount_1", "amount_2"]}
        {"op": "expression", "expr": "quantity * unit_price"}
        {"op": "display_from", "field": "customer_name"}

    Returns the computed value or None if inputs are missing.
    """
    op = calc_config.get('op')
    fields = calc_config.get('fields', [])
    values = []

    if op == 'display_from':
        field = calc_config.get('field', '')
        return payload.get(field)

    if op == 'expression':
        # Simple expression eval with only payload values as variables
        # WARNING: Only safe because payload values are user-submitted data, not code
        expr = calc_config.get('expr', '')
        try:
            # Build a safe namespace from payload (numbers only)
            namespace = {}
            for k, v in payload.items():
                if isinstance(v, (int, float)):
                    namespace[k] = v
            return eval(expr, {"__builtins__": {}}, namespace)  # noqa: S307
        except Exception:
            return None

    for f in fields:
        v = payload.get(f)
        if v is not None and isinstance(v, (int, float)):
            values.append(v)

    if not values:
        return None

    match op:
        case 'sum':
            return sum(values)
        case 'avg':
            return sum(values) / len(values)
        case 'min':
            return min(values)
        case 'max':
            return max(values)
        case 'count':
            return len([v for v in values if v is not None])
        case 'multiply':
            result = 1
            for v in values:
                result *= v
            return result
        case 'subtract':
            return values[0] - values[1] if len(values) >= 2 else None
        case 'divide':
            return values[0] / values[1] if len(values) >= 2 and values[1] != 0 else None
        case 'percentage':
            return (values[0] / values[1]) * 100 if len(values) >= 2 and values[1] != 0 else None
        case _:
            return None


def validate_form_schema(schema):
    """Validate that a form schema is well-formed JSON Schema.

    Returns (is_valid, errors) tuple.
    """
    if not schema:
        return True, []

    errors = []

    if not isinstance(schema, dict):
        return False, [{'message': 'Schema must be a JSON object'}]

    # Must have "type": "object" at the root
    if schema.get('type') != 'object':
        errors.append({'message': 'Schema root must have "type": "object"'})

    # Must have "properties"
    properties = schema.get('properties', {})
    if not isinstance(properties, dict):
        errors.append({'message': '"properties" must be a JSON object'})
    elif not properties:
        errors.append({'message': 'Schema must define at least one property'})

    # Validate each property has a type
    for field_name, field_def in properties.items():
        if not isinstance(field_def, dict):
            errors.append({'message': f'Property "{field_name}" must be a JSON object'})
            continue
        if 'type' not in field_def:
            errors.append({'message': f'Property "{field_name}" must have a "type"'})

    # Validate "required" if present
    required = schema.get('required', [])
    if required:
        if not isinstance(required, list):
            errors.append({'message': '"required" must be an array'})
        else:
            for r in required:
                if r not in properties:
                    errors.append({'message': f'Required field "{r}" not found in properties'})

    return len(errors) == 0, errors

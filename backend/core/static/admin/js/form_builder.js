/**
 * Form Schema Builder widget for Django admin.
 * Visual field editor that generates JSON Schema.
 */
(function() {
  'use strict';

  // -----------------------------------------------------------------------
  // Field type definitions (mirrors backend/forms/field_types.py)
  // -----------------------------------------------------------------------
  var FIELD_TYPES = {
    text:        { type: 'string', label: 'Text', group: 'Basic' },
    textarea:    { type: 'string', label: 'Textarea', group: 'Basic', xWidget: 'textarea' },
    number:      { type: 'number', label: 'Number', group: 'Basic' },
    integer:     { type: 'integer', label: 'Integer', group: 'Basic' },
    boolean:     { type: 'boolean', label: 'Checkbox', group: 'Basic' },
    email:       { type: 'string', label: 'Email', group: 'Basic', format: 'email' },
    url:         { type: 'string', label: 'URL', group: 'Basic', format: 'uri' },
    date:        { type: 'string', label: 'Date', group: 'Date & Time', format: 'date' },
    datetime:    { type: 'string', label: 'Date & Time', group: 'Date & Time', format: 'date-time' },
    time:        { type: 'string', label: 'Time', group: 'Date & Time', xWidget: 'time' },
    select:      { type: 'string', label: 'Dropdown', group: 'Choice', hasOptions: true },
    multi_select:{ type: 'array', label: 'Multi-select', group: 'Choice', hasOptions: true },
    radio:       { type: 'string', label: 'Radio Buttons', group: 'Choice', hasOptions: true, xWidget: 'radio' },
    file:        { type: 'string', label: 'File Upload', group: 'Media', format: 'uri', xWidget: 'file' },
    signature:   { type: 'string', label: 'Signature', group: 'Media', xWidget: 'signature' },
    image:       { type: 'string', label: 'Image (display)', group: 'Display', xWidget: 'image', display: true },
    rating:      { type: 'integer', label: 'Star Rating', group: 'Assessment', xWidget: 'rating', hasMinMax: true, defaultMin: 1, defaultMax: 5 },
    scale:       { type: 'integer', label: 'Scale / Slider', group: 'Assessment', xWidget: 'scale', hasMinMax: true, defaultMin: 0, defaultMax: 10 },
    pin:         { type: 'string', label: 'PIN Input', group: 'Special', xWidget: 'pin' },
    percentage_split: { type: 'object', label: 'Percentage Split', group: 'Special', xWidget: 'percentage_split' },
    text_block:     { type: 'string', label: 'Text Block', group: 'Display', xWidget: 'text_block', display: true },
    section_header: { type: 'string', label: 'Section Header', group: 'Display', xWidget: 'section_header', display: true },
    page_break:     { type: 'string', label: 'Page Break', group: 'Display', xWidget: 'page_break', display: true },
  };

  // Group ordering
  var GROUPS = ['Basic', 'Choice', 'Date & Time', 'Assessment', 'Media', 'Special', 'Display'];

  // -----------------------------------------------------------------------
  // Reverse-detect field type from schema definition
  // -----------------------------------------------------------------------
  function detectFieldType(schema) {
    var xw = schema['x-widget'];
    if (xw) {
      for (var key in FIELD_TYPES) {
        if (FIELD_TYPES[key].xWidget === xw) return key;
      }
    }
    if (schema.format === 'email') return 'email';
    if (schema.format === 'uri' && xw !== 'file') return 'url';
    if (schema.format === 'date') return 'date';
    if (schema.format === 'date-time') return 'datetime';
    if (schema.type === 'string' && schema.enum) return 'select';
    if (schema.type === 'array') return 'multi_select';
    if (schema.type === 'number') return 'number';
    if (schema.type === 'integer') return 'integer';
    if (schema.type === 'boolean') return 'boolean';
    return 'text';
  }

  // -----------------------------------------------------------------------
  // Parse JSON Schema → field list
  // -----------------------------------------------------------------------
  function schemaToFields(json) {
    var schema;
    try { schema = typeof json === 'string' ? JSON.parse(json) : json; } catch(e) { return []; }
    if (!schema || !schema.properties) return [];

    var required = new Set(schema.required || []);
    var fields = [];
    for (var name in schema.properties) {
      var prop = schema.properties[name];
      var fieldType = detectFieldType(prop);
      var ft = FIELD_TYPES[fieldType];
      var field = {
        name: name,
        title: prop.title || '',
        fieldType: fieldType,
        required: required.has(name),
        description: prop.description || '',
        placeholder: prop.placeholder || '',
        options: [],
        minimum: prop.minimum,
        maximum: prop.maximum,
        xSrc: prop['x-src'] || '',
        xAccept: prop['x-accept'] || '',
        xMinLabel: prop['x-min-label'] || '',
        xMaxLabel: prop['x-max-label'] || '',
      };

      if (ft && ft.hasOptions) {
        if (fieldType === 'multi_select') {
          field.options = (prop.items && prop.items.enum) || prop.enum || [];
        } else {
          field.options = prop.enum || [];
        }
      }

      if (ft && ft.hasMinMax) {
        if (field.minimum == null) field.minimum = ft.defaultMin;
        if (field.maximum == null) field.maximum = ft.defaultMax;
      }

      fields.push(field);
    }
    return fields;
  }

  // -----------------------------------------------------------------------
  // Field list → JSON Schema
  // -----------------------------------------------------------------------
  function fieldsToSchema(fields) {
    var schema = { type: 'object', properties: {}, required: [] };
    for (var i = 0; i < fields.length; i++) {
      var f = fields[i];
      if (!f.name) continue;
      var ft = FIELD_TYPES[f.fieldType] || FIELD_TYPES.text;
      var prop = { type: ft.type };

      if (f.title) prop.title = f.title;
      if (f.description) prop.description = f.description;
      if (f.placeholder) prop.placeholder = f.placeholder;
      if (ft.format) prop.format = ft.format;
      if (ft.xWidget) prop['x-widget'] = ft.xWidget;

      // Options for select/radio/multi_select
      if (ft.hasOptions && f.options && f.options.length > 0) {
        var opts = f.options.filter(function(o) { return o.trim() !== ''; });
        if (f.fieldType === 'multi_select') {
          prop.items = { type: 'string', enum: opts };
        } else {
          prop.enum = opts;
        }
      }

      // Min/max for numeric
      if (f.minimum != null && f.minimum !== '') prop.minimum = Number(f.minimum);
      if (f.maximum != null && f.maximum !== '') prop.maximum = Number(f.maximum);

      // Special attributes
      if (f.xSrc) prop['x-src'] = f.xSrc;
      if (f.xAccept) prop['x-accept'] = f.xAccept;
      if (f.xMinLabel) prop['x-min-label'] = f.xMinLabel;
      if (f.xMaxLabel) prop['x-max-label'] = f.xMaxLabel;

      if (ft.xWidget === 'percentage_split') {
        prop['x-validation'] = 'sum_to_100';
      }

      schema.properties[f.name] = prop;
      if (f.required) schema.required.push(f.name);
    }
    if (schema.required.length === 0) delete schema.required;
    return schema;
  }

  // -----------------------------------------------------------------------
  // Slugify field name
  // -----------------------------------------------------------------------
  function slugify(text) {
    return text.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').substring(0, 64);
  }

  // -----------------------------------------------------------------------
  // Create element helper
  // -----------------------------------------------------------------------
  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      for (var key in attrs) {
        if (key === 'className') node.className = attrs[key];
        else if (key === 'textContent') node.textContent = attrs[key];
        else if (key === 'innerHTML') node.innerHTML = attrs[key];
        else if (key.startsWith('on')) node.addEventListener(key.slice(2).toLowerCase(), attrs[key]);
        else node.setAttribute(key, attrs[key]);
      }
    }
    if (children) {
      if (!Array.isArray(children)) children = [children];
      for (var i = 0; i < children.length; i++) {
        if (typeof children[i] === 'string') node.appendChild(document.createTextNode(children[i]));
        else if (children[i]) node.appendChild(children[i]);
      }
    }
    return node;
  }

  // -----------------------------------------------------------------------
  // FormBuilder class
  // -----------------------------------------------------------------------
  function FormBuilder(textarea) {
    this.textarea = textarea;
    this.fields = schemaToFields(textarea.value);
    this.openFieldIndex = -1;
    this.dragIndex = -1;

    this.wrapper = el('div', { className: 'form-builder-wrapper' });
    textarea.parentNode.insertBefore(this.wrapper, textarea);

    // Tabs
    this.tabVisual = el('button', { type: 'button', className: 'fb-tab active', textContent: 'Visual Builder' });
    this.tabJson = el('button', { type: 'button', className: 'fb-tab', textContent: 'JSON' });
    var tabs = el('div', { className: 'fb-tabs' }, [this.tabVisual, this.tabJson]);
    this.wrapper.appendChild(tabs);

    // Visual panel
    this.visualPanel = el('div', { className: 'fb-visual' });
    this.fieldsList = el('div', { className: 'fb-fields-list' });
    this.visualPanel.appendChild(this.fieldsList);
    this.visualPanel.appendChild(this._buildAddBar());
    this.wrapper.appendChild(this.visualPanel);

    // JSON panel (contains the original textarea)
    this.jsonPanel = el('div', { className: 'fb-json', style: 'display:none' });
    this.jsonPanel.appendChild(textarea);
    this.wrapper.appendChild(this.jsonPanel);

    // Tab switching
    var self = this;
    this.tabVisual.addEventListener('click', function() {
      self.tabVisual.classList.add('active');
      self.tabJson.classList.remove('active');
      self.visualPanel.style.display = 'block';
      self.jsonPanel.style.display = 'none';
      // Sync from textarea in case user edited JSON directly
      self.fields = schemaToFields(self.textarea.value);
      self.render();
    });

    this.tabJson.addEventListener('click', function() {
      self.tabJson.classList.add('active');
      self.tabVisual.classList.remove('active');
      self.visualPanel.style.display = 'none';
      self.jsonPanel.style.display = 'block';
      self.syncToTextarea();
      // Re-format
      try {
        var parsed = JSON.parse(self.textarea.value);
        self.textarea.value = JSON.stringify(parsed, null, 2);
      } catch(e) {}
    });

    this.render();
  }

  FormBuilder.prototype.syncToTextarea = function() {
    var schema = fieldsToSchema(this.fields);
    this.textarea.value = JSON.stringify(schema, null, 2);
  };

  FormBuilder.prototype.render = function() {
    var self = this;
    this.fieldsList.innerHTML = '';

    if (this.fields.length === 0) {
      this.fieldsList.appendChild(el('div', { className: 'fb-empty' }, [
        el('div', { className: 'fb-empty-icon', textContent: '📋' }),
        el('div', { textContent: 'No fields yet. Click "Add Field" below to get started.' }),
      ]));
      return;
    }

    this.fields.forEach(function(field, index) {
      self.fieldsList.appendChild(self._buildFieldCard(field, index));
    });
  };

  FormBuilder.prototype._buildFieldCard = function(field, index) {
    var self = this;
    var ft = FIELD_TYPES[field.fieldType] || FIELD_TYPES.text;
    var isOpen = this.openFieldIndex === index;

    // Header
    var handle = el('span', { className: 'fb-drag-handle', textContent: '⠿', draggable: 'true', title: 'Drag to reorder' });
    var nameSpan = el('span', { className: 'fb-field-name', textContent: field.title || field.name || '(unnamed)' });
    var typeBadge = el('span', { className: 'fb-field-type-badge', textContent: ft.label });
    var badges = [typeBadge];
    if (field.required) badges.push(el('span', { className: 'fb-field-required-badge', textContent: 'Required' }));
    if (ft.display) badges.push(el('span', { className: 'fb-field-display-badge', textContent: 'Display' }));

    var moveUpBtn = el('button', { type: 'button', title: 'Move up', innerHTML: '&#9650;', onClick: function(e) { e.stopPropagation(); self._moveField(index, -1); }});
    var moveDownBtn = el('button', { type: 'button', title: 'Move down', innerHTML: '&#9660;', onClick: function(e) { e.stopPropagation(); self._moveField(index, 1); }});
    var deleteBtn = el('button', { type: 'button', className: 'fb-delete-btn', title: 'Remove field', textContent: '✕', onClick: function(e) { e.stopPropagation(); self._removeField(index); }});
    var actions = el('div', { className: 'fb-field-actions' }, [moveUpBtn, moveDownBtn, deleteBtn]);

    var headerChildren = [handle, nameSpan].concat(badges).concat([actions]);
    var header = el('div', { className: 'fb-field-header' }, headerChildren);
    header.addEventListener('click', function() {
      self.openFieldIndex = self.openFieldIndex === index ? -1 : index;
      self.render();
    });

    // Config panel
    var config = el('div', { className: 'fb-field-config' + (isOpen ? ' open' : '') });
    if (isOpen) {
      config.appendChild(this._buildConfigPanel(field, index));
    }

    // Card container
    var card = el('div', { className: 'fb-field-card' }, [header, config]);

    // Drag and drop
    handle.addEventListener('dragstart', function(e) {
      self.dragIndex = index;
      card.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', String(index));
    });
    handle.addEventListener('dragend', function() {
      card.classList.remove('dragging');
      self.dragIndex = -1;
    });
    card.addEventListener('dragover', function(e) {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
    });
    card.addEventListener('drop', function(e) {
      e.preventDefault();
      var fromIndex = self.dragIndex;
      if (fromIndex < 0 || fromIndex === index) return;
      var moved = self.fields.splice(fromIndex, 1)[0];
      self.fields.splice(index, 0, moved);
      self.openFieldIndex = index;
      self.syncToTextarea();
      self.render();
    });

    return card;
  };

  FormBuilder.prototype._buildConfigPanel = function(field, index) {
    var self = this;
    var ft = FIELD_TYPES[field.fieldType] || FIELD_TYPES.text;
    var grid = el('div', { className: 'fb-config-grid' });

    // Field Name
    grid.appendChild(this._configInput('Field Name (slug)', 'text', field.name, function(val) {
      field.name = slugify(val);
      self._fieldChanged(index);
    }));

    // Title
    grid.appendChild(this._configInput('Title', 'text', field.title, function(val) {
      field.title = val;
      self._fieldChanged(index);
    }));

    // Type
    var typeSelect = el('select');
    GROUPS.forEach(function(group) {
      var optgroup = el('optgroup', { label: group });
      var hasItems = false;
      for (var key in FIELD_TYPES) {
        if (FIELD_TYPES[key].group === group) {
          var opt = el('option', { value: key, textContent: FIELD_TYPES[key].label });
          if (key === field.fieldType) opt.selected = true;
          optgroup.appendChild(opt);
          hasItems = true;
        }
      }
      if (hasItems) typeSelect.appendChild(optgroup);
    });
    typeSelect.addEventListener('change', function() {
      var newType = this.value;
      var newFt = FIELD_TYPES[newType];
      field.fieldType = newType;
      if (newFt.hasMinMax) {
        field.minimum = field.minimum || newFt.defaultMin;
        field.maximum = field.maximum || newFt.defaultMax;
      }
      if (newFt.hasOptions && !field.options.length) {
        field.options = ['Option 1', 'Option 2'];
      }
      self.openFieldIndex = index;
      self._fieldChanged(index);
      self.render();
    });
    var typeField = el('div', { className: 'fb-config-field' }, [
      el('label', { textContent: 'Field Type' }),
      typeSelect,
    ]);
    grid.appendChild(typeField);

    // Required
    var reqCheckbox = el('input', { type: 'checkbox' });
    reqCheckbox.checked = field.required;
    reqCheckbox.addEventListener('change', function() {
      field.required = this.checked;
      self._fieldChanged(index);
    });
    grid.appendChild(el('div', { className: 'fb-config-field fb-checkbox-field' }, [
      reqCheckbox,
      el('label', { textContent: 'Required' }),
    ]));

    // Description
    var descTA = el('textarea', { rows: '2' });
    descTA.value = field.description;
    descTA.addEventListener('input', function() { field.description = this.value; self._fieldChanged(index); });
    grid.appendChild(el('div', { className: 'fb-config-field full-width' }, [
      el('label', { textContent: 'Description / Help Text' }),
      descTA,
    ]));

    // Placeholder (for input types)
    if (!ft.display) {
      grid.appendChild(this._configInput('Placeholder', 'text', field.placeholder, function(val) {
        field.placeholder = val;
        self._fieldChanged(index);
      }));
    }

    // Options (for select, multi_select, radio)
    if (ft.hasOptions) {
      grid.appendChild(this._buildOptionsEditor(field, index));
    }

    // Min/Max (for rating, scale, number, integer)
    if (ft.hasMinMax || field.fieldType === 'number' || field.fieldType === 'integer') {
      grid.appendChild(this._configInput('Minimum', 'number', field.minimum, function(val) {
        field.minimum = val === '' ? undefined : Number(val);
        self._fieldChanged(index);
      }));
      grid.appendChild(this._configInput('Maximum', 'number', field.maximum, function(val) {
        field.maximum = val === '' ? undefined : Number(val);
        self._fieldChanged(index);
      }));
    }

    // Scale labels
    if (field.fieldType === 'scale') {
      grid.appendChild(this._configInput('Min Label', 'text', field.xMinLabel, function(val) {
        field.xMinLabel = val;
        self._fieldChanged(index);
      }));
      grid.appendChild(this._configInput('Max Label', 'text', field.xMaxLabel, function(val) {
        field.xMaxLabel = val;
        self._fieldChanged(index);
      }));
    }

    // File accept
    if (field.fieldType === 'file') {
      grid.appendChild(this._configInput('Accept Types', 'text', field.xAccept, function(val) {
        field.xAccept = val;
        self._fieldChanged(index);
      }, 'e.g. .pdf,.jpg,.png'));
    }

    // Image source
    if (field.fieldType === 'image') {
      grid.appendChild(el('div', { className: 'fb-config-field full-width' }, [
        el('label', { textContent: 'Image URL' }),
        (function() {
          var inp = el('input', { type: 'text', placeholder: 'https://...' });
          inp.value = field.xSrc;
          inp.addEventListener('input', function() { field.xSrc = this.value; self._fieldChanged(index); });
          return inp;
        })(),
      ]));
    }

    return grid;
  };

  FormBuilder.prototype._configInput = function(label, type, value, onChange, placeholder) {
    var inp = el('input', { type: type });
    inp.value = value != null ? value : '';
    if (placeholder) inp.placeholder = placeholder;
    inp.addEventListener('input', function() { onChange(this.value); });
    return el('div', { className: 'fb-config-field' }, [
      el('label', { textContent: label }),
      inp,
    ]);
  };

  FormBuilder.prototype._buildOptionsEditor = function(field, index) {
    var self = this;
    var container = el('div', { className: 'fb-config-field full-width' });
    container.appendChild(el('label', { textContent: 'Options' }));

    var list = el('div', { className: 'fb-options-list' });

    (field.options || []).forEach(function(opt, optIndex) {
      var inp = el('input', { type: 'text' });
      inp.value = opt;
      inp.addEventListener('input', function() {
        field.options[optIndex] = this.value;
        self._fieldChanged(index);
      });
      var removeBtn = el('button', { type: 'button', textContent: '✕', onClick: function() {
        field.options.splice(optIndex, 1);
        self._fieldChanged(index);
        self.render();
      }});
      list.appendChild(el('div', { className: 'fb-option-row' }, [inp, removeBtn]));
    });

    var addBtn = el('button', { type: 'button', className: 'fb-add-option-btn', textContent: '+ Add option', onClick: function() {
      field.options.push('');
      self._fieldChanged(index);
      self.render();
    }});

    container.appendChild(list);
    container.appendChild(addBtn);
    return container;
  };

  FormBuilder.prototype._buildAddBar = function() {
    var self = this;
    var picker = el('div', { className: 'fb-type-picker' });
    var btn = el('button', { type: 'button', className: 'fb-add-field-btn', textContent: '+ Add Field' });
    var menu = el('div', { className: 'fb-type-picker-menu' });

    GROUPS.forEach(function(group) {
      menu.appendChild(el('div', { className: 'fb-type-group-label', textContent: group }));
      for (var key in FIELD_TYPES) {
        if (FIELD_TYPES[key].group === group) {
          (function(typeKey) {
            menu.appendChild(el('button', {
              type: 'button',
              className: 'fb-type-option',
              textContent: FIELD_TYPES[typeKey].label,
              onClick: function() {
                self._addField(typeKey);
                menu.classList.remove('open');
              },
            }));
          })(key);
        }
      }
    });

    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      menu.classList.toggle('open');
    });

    // Close on outside click
    document.addEventListener('click', function(e) {
      if (!picker.contains(e.target)) menu.classList.remove('open');
    });

    picker.appendChild(btn);
    picker.appendChild(menu);
    return el('div', { className: 'fb-add-field-bar' }, [picker]);
  };

  FormBuilder.prototype._addField = function(typeKey) {
    var ft = FIELD_TYPES[typeKey];
    var baseName = typeKey === 'section_header' ? 'section' : typeKey === 'text_block' ? 'text_block' : 'field';
    var name = baseName + '_' + (this.fields.length + 1);
    var field = {
      name: name,
      title: ft.label,
      fieldType: typeKey,
      required: false,
      description: '',
      placeholder: '',
      options: ft.hasOptions ? ['Option 1', 'Option 2'] : [],
      minimum: ft.hasMinMax ? ft.defaultMin : undefined,
      maximum: ft.hasMinMax ? ft.defaultMax : undefined,
      xSrc: '',
      xAccept: '',
      xMinLabel: '',
      xMaxLabel: '',
    };
    this.fields.push(field);
    this.openFieldIndex = this.fields.length - 1;
    this.syncToTextarea();
    this.render();
  };

  FormBuilder.prototype._removeField = function(index) {
    if (!confirm('Remove "' + (this.fields[index].title || this.fields[index].name) + '"?')) return;
    this.fields.splice(index, 1);
    if (this.openFieldIndex === index) this.openFieldIndex = -1;
    else if (this.openFieldIndex > index) this.openFieldIndex--;
    this.syncToTextarea();
    this.render();
  };

  FormBuilder.prototype._moveField = function(index, direction) {
    var newIndex = index + direction;
    if (newIndex < 0 || newIndex >= this.fields.length) return;
    var temp = this.fields[index];
    this.fields[index] = this.fields[newIndex];
    this.fields[newIndex] = temp;
    if (this.openFieldIndex === index) this.openFieldIndex = newIndex;
    else if (this.openFieldIndex === newIndex) this.openFieldIndex = index;
    this.syncToTextarea();
    this.render();
  };

  FormBuilder.prototype._fieldChanged = function() {
    this.syncToTextarea();
  };

  // -----------------------------------------------------------------------
  // Init on DOM load
  // -----------------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.form-schema-builder').forEach(function(textarea) {
      new FormBuilder(textarea);
    });
  });
})();

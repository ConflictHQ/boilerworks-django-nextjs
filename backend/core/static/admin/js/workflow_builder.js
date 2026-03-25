/**
 * Workflow Builder widget for Django admin.
 * Visual state/transition editor that generates workflow JSON.
 *
 * Manages TWO textareas: one for states JSON, one for transitions JSON.
 * Identified by CSS classes: .workflow-states-builder and .workflow-transitions-builder.
 */
(function() {
  'use strict';

  var STATE_COLORS = [
    '#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6',
    '#06b6d4', '#ec4899', '#14b8a6', '#f97316', '#6366f1',
  ];

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      for (var key in attrs) {
        if (key === 'className') node.className = attrs[key];
        else if (key === 'textContent') node.textContent = attrs[key];
        else if (key === 'innerHTML') node.innerHTML = attrs[key];
        else if (key.startsWith('on') && key.length > 2) node.addEventListener(key.slice(2).toLowerCase(), attrs[key]);
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

  function slugify(text) {
    return text.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').substring(0, 64);
  }

  // -----------------------------------------------------------------------
  // WorkflowBuilder
  // -----------------------------------------------------------------------
  function WorkflowBuilder(statesTextarea, transitionsTextarea) {
    this.statesTA = statesTextarea;
    this.transitionsTA = transitionsTextarea;
    this.states = this._parseJSON(statesTextarea.value) || [];
    this.transitions = this._parseJSON(transitionsTextarea.value) || [];
    this.editingState = null; // index or null
    this.editingTransition = null;

    // Build wrapper — find the fieldset row for states
    this.wrapper = el('div', { className: 'workflow-builder-wrapper' });
    var statesRow = statesTextarea.closest('.form-row') || statesTextarea.parentNode;
    statesRow.parentNode.insertBefore(this.wrapper, statesRow);

    // Tabs
    this.tabVisual = el('button', { type: 'button', className: 'wb-tab active', textContent: 'Visual Builder' });
    this.tabJson = el('button', { type: 'button', className: 'wb-tab', textContent: 'JSON' });
    var tabs = el('div', { className: 'wb-tabs' }, [this.tabVisual, this.tabJson]);
    this.wrapper.appendChild(tabs);

    // Visual panel
    this.visualPanel = el('div');
    this.wrapper.appendChild(this.visualPanel);

    // Tab switching
    var self = this;
    this.tabVisual.addEventListener('click', function() {
      self.tabVisual.classList.add('active');
      self.tabJson.classList.remove('active');
      self.visualPanel.style.display = 'block';
      statesRow.style.display = 'none';
      var transRow = transitionsTextarea.closest('.form-row') || transitionsTextarea.parentNode;
      transRow.style.display = 'none';
      self.states = self._parseJSON(self.statesTA.value) || [];
      self.transitions = self._parseJSON(self.transitionsTA.value) || [];
      self.render();
    });

    this.tabJson.addEventListener('click', function() {
      self.tabJson.classList.add('active');
      self.tabVisual.classList.remove('active');
      self.visualPanel.style.display = 'none';
      statesRow.style.display = '';
      var transRow = transitionsTextarea.closest('.form-row') || transitionsTextarea.parentNode;
      transRow.style.display = '';
      self._sync();
    });

    // Initially hide JSON rows
    statesRow.style.display = 'none';
    var transRow = transitionsTextarea.closest('.form-row') || transitionsTextarea.parentNode;
    transRow.style.display = 'none';

    this.render();
  }

  WorkflowBuilder.prototype._parseJSON = function(val) {
    try { return JSON.parse(val); } catch(e) { return null; }
  };

  WorkflowBuilder.prototype._sync = function() {
    this.statesTA.value = JSON.stringify(this.states, null, 2);
    this.transitionsTA.value = JSON.stringify(this.transitions, null, 2);
  };

  WorkflowBuilder.prototype.render = function() {
    var self = this;
    this.visualPanel.innerHTML = '';
    this._sync();

    var panel = el('div', { className: 'wb-side-panel' });

    // States section
    var statesSection = el('div', { className: 'wb-panel-section' });
    statesSection.appendChild(el('div', { className: 'wb-panel-title', textContent: 'States' }));

    var stateList = el('div', { className: 'wb-state-list' });
    if (this.states.length === 0) {
      stateList.appendChild(el('div', { className: 'wb-empty', textContent: 'No states defined' }));
    }
    this.states.forEach(function(state, i) {
      stateList.appendChild(self._buildStateRow(state, i));
    });
    statesSection.appendChild(stateList);
    statesSection.appendChild(el('button', {
      type: 'button', className: 'wb-add-btn', textContent: '+ Add State',
      onClick: function() { self._addState(); },
    }));

    if (this.editingState !== null) {
      statesSection.appendChild(this._buildEditStatePanel());
    }

    // Transitions section
    var transSection = el('div', { className: 'wb-panel-section' });
    transSection.appendChild(el('div', { className: 'wb-panel-title', textContent: 'Transitions' }));

    var transList = el('div');
    if (this.transitions.length === 0) {
      transList.appendChild(el('div', { className: 'wb-empty', textContent: 'No transitions defined' }));
    }
    this.transitions.forEach(function(t, i) {
      transList.appendChild(self._buildTransitionRow(t, i));
    });
    transSection.appendChild(transList);

    if (this.states.length >= 2) {
      transSection.appendChild(el('button', {
        type: 'button', className: 'wb-add-btn', textContent: '+ Add Transition',
        onClick: function() { self._addTransition(); },
      }));
    }

    if (this.editingTransition !== null) {
      transSection.appendChild(this._buildEditTransitionPanel());
    }

    panel.appendChild(statesSection);
    panel.appendChild(transSection);
    this.visualPanel.appendChild(panel);

    // Validation warnings
    var warnings = this._validate();
    if (warnings.length > 0) {
      var warnDiv = el('div', { style: 'background:#fefce8; border:1px solid #fde047; border-radius:6px; padding:8px 12px; margin-top:8px; font-size:12px; color:#854d0e;' });
      warnings.forEach(function(w) {
        warnDiv.appendChild(el('div', { textContent: '⚠ ' + w }));
      });
      this.visualPanel.appendChild(warnDiv);
    }
  };

  WorkflowBuilder.prototype._buildStateRow = function(state, index) {
    var self = this;
    var badges = [];
    if (state.is_initial) badges.push(el('span', { className: 'wb-badge wb-badge-start', textContent: 'Start' }));
    if (state.is_final) badges.push(el('span', { className: 'wb-badge wb-badge-end', textContent: 'End' }));

    var editBtn = el('button', { type: 'button', textContent: '✎', title: 'Edit', onClick: function(e) {
      e.stopPropagation();
      self.editingState = self.editingState === index ? null : index;
      self.editingTransition = null;
      self.render();
    }});
    var deleteBtn = el('button', { type: 'button', className: 'wb-delete', textContent: '✕', title: 'Remove', onClick: function(e) {
      e.stopPropagation();
      self._removeState(index);
    }});

    var children = [
      el('span', { className: 'wb-color-dot', style: 'background:' + (state.color || '#6b7280') }),
      el('span', { className: 'wb-state-label-text', textContent: state.label || state.name }),
      el('span', { className: 'wb-state-name-text', textContent: state.name }),
    ].concat(badges).concat([editBtn, deleteBtn]);

    return el('div', { className: 'wb-state-row' }, children);
  };

  WorkflowBuilder.prototype._buildTransitionRow = function(t, index) {
    var self = this;
    var editBtn = el('button', { type: 'button', textContent: '✎', title: 'Edit', onClick: function(e) {
      e.stopPropagation();
      self.editingTransition = self.editingTransition === index ? null : index;
      self.editingState = null;
      self.render();
    }});
    var deleteBtn = el('button', { type: 'button', className: 'wb-delete', textContent: '✕', title: 'Remove', onClick: function(e) {
      e.stopPropagation();
      self.transitions.splice(index, 1);
      if (self.editingTransition === index) self.editingTransition = null;
      self._sync();
      self.render();
    }});

    return el('div', { className: 'wb-transition-row' }, [
      el('span', { className: 'wb-transition-label', textContent: t.label || '(unnamed)' }),
      el('span', { className: 'wb-transition-path', textContent: t.from_state + ' → ' + t.to_state }),
      editBtn,
      deleteBtn,
    ]);
  };

  WorkflowBuilder.prototype._buildEditStatePanel = function() {
    var self = this;
    var state = this.states[this.editingState];
    if (!state) return el('div');

    var grid = el('div', { className: 'wb-edit-grid' });

    // Name
    var nameInp = el('input', { type: 'text', value: state.name || '' });
    grid.appendChild(el('div', { className: 'wb-edit-field' }, [el('label', { textContent: 'Name (slug)' }), nameInp]));

    // Label
    var labelInp = el('input', { type: 'text', value: state.label || '' });
    grid.appendChild(el('div', { className: 'wb-edit-field' }, [el('label', { textContent: 'Label' }), labelInp]));

    // Color
    var colorInp = el('input', { type: 'color', value: state.color || '#6b7280' });
    grid.appendChild(el('div', { className: 'wb-edit-field' }, [el('label', { textContent: 'Color' }), colorInp]));

    // Is Initial
    var initCb = el('input', { type: 'checkbox' });
    initCb.checked = !!state.is_initial;
    grid.appendChild(el('div', { className: 'wb-edit-field wb-checkbox-row' }, [initCb, el('label', { textContent: 'Initial State' })]));

    // Is Final
    var finalCb = el('input', { type: 'checkbox' });
    finalCb.checked = !!state.is_final;
    grid.appendChild(el('div', { className: 'wb-edit-field wb-checkbox-row' }, [finalCb, el('label', { textContent: 'Final State' })]));

    var actions = el('div', { className: 'wb-edit-actions' });
    actions.appendChild(el('button', { type: 'button', className: 'wb-save-btn', textContent: 'Save', onClick: function() {
      state.name = slugify(nameInp.value);
      state.label = labelInp.value;
      state.color = colorInp.value;
      state.is_initial = initCb.checked;
      state.is_final = finalCb.checked;
      // If marking as initial, unmark others
      if (state.is_initial) {
        self.states.forEach(function(s, i) { if (i !== self.editingState) s.is_initial = false; });
      }
      self.editingState = null;
      self._sync();
      self.render();
    }}));
    actions.appendChild(el('button', { type: 'button', className: 'wb-cancel-btn', textContent: 'Cancel', onClick: function() {
      self.editingState = null;
      self.render();
    }}));

    var panel = el('div', { className: 'wb-edit-panel' }, [grid, actions]);
    return panel;
  };

  WorkflowBuilder.prototype._buildEditTransitionPanel = function() {
    var self = this;
    var t = this.transitions[this.editingTransition];
    if (!t) return el('div');

    var grid = el('div', { className: 'wb-edit-grid' });

    // Label
    var labelInp = el('input', { type: 'text', value: t.label || '' });
    grid.appendChild(el('div', { className: 'wb-edit-field full-width' }, [el('label', { textContent: 'Label' }), labelInp]));

    // From state
    var fromSelect = el('select');
    this.states.forEach(function(s) {
      var opt = el('option', { value: s.name, textContent: s.label || s.name });
      if (s.name === t.from_state) opt.selected = true;
      fromSelect.appendChild(opt);
    });
    grid.appendChild(el('div', { className: 'wb-edit-field' }, [el('label', { textContent: 'From State' }), fromSelect]));

    // To state
    var toSelect = el('select');
    this.states.forEach(function(s) {
      var opt = el('option', { value: s.name, textContent: s.label || s.name });
      if (s.name === t.to_state) opt.selected = true;
      toSelect.appendChild(opt);
    });
    grid.appendChild(el('div', { className: 'wb-edit-field' }, [el('label', { textContent: 'To State' }), toSelect]));

    var actions = el('div', { className: 'wb-edit-actions' });
    actions.appendChild(el('button', { type: 'button', className: 'wb-save-btn', textContent: 'Save', onClick: function() {
      t.label = labelInp.value;
      t.from_state = fromSelect.value;
      t.to_state = toSelect.value;
      self.editingTransition = null;
      self._sync();
      self.render();
    }}));
    actions.appendChild(el('button', { type: 'button', className: 'wb-cancel-btn', textContent: 'Cancel', onClick: function() {
      self.editingTransition = null;
      self.render();
    }}));

    return el('div', { className: 'wb-edit-panel' }, [grid, actions]);
  };

  WorkflowBuilder.prototype._addState = function() {
    var count = this.states.length;
    var isFirst = count === 0;
    this.states.push({
      name: 'state_' + (count + 1),
      label: 'State ' + (count + 1),
      is_initial: isFirst,
      is_final: false,
      color: STATE_COLORS[count % STATE_COLORS.length],
    });
    this.editingState = this.states.length - 1;
    this.editingTransition = null;
    this._sync();
    this.render();
  };

  WorkflowBuilder.prototype._removeState = function(index) {
    var name = this.states[index].name;
    if (!confirm('Remove state "' + (this.states[index].label || name) + '"?\nThis will also remove related transitions.')) return;
    this.states.splice(index, 1);
    this.transitions = this.transitions.filter(function(t) {
      return t.from_state !== name && t.to_state !== name;
    });
    if (this.editingState === index) this.editingState = null;
    this._sync();
    this.render();
  };

  WorkflowBuilder.prototype._addTransition = function() {
    var from = this.states[0] ? this.states[0].name : '';
    var to = this.states.length > 1 ? this.states[1].name : from;
    this.transitions.push({
      from_state: from,
      to_state: to,
      label: 'Transition ' + (this.transitions.length + 1),
      conditions: [],
      actions: [],
      timeout_hours: null,
    });
    this.editingTransition = this.transitions.length - 1;
    this.editingState = null;
    this._sync();
    this.render();
  };

  WorkflowBuilder.prototype._validate = function() {
    var warnings = [];
    var names = {};
    var initialCount = 0;
    this.states.forEach(function(s) {
      if (names[s.name]) warnings.push('Duplicate state name: "' + s.name + '"');
      names[s.name] = true;
      if (s.is_initial) initialCount++;
    });
    if (this.states.length > 0 && initialCount !== 1) {
      warnings.push('Exactly one state must be marked as initial (found ' + initialCount + ')');
    }
    this.transitions.forEach(function(t) {
      if (!names[t.from_state]) warnings.push('Transition references unknown state: "' + t.from_state + '"');
      if (!names[t.to_state]) warnings.push('Transition references unknown state: "' + t.to_state + '"');
    });
    return warnings;
  };

  // -----------------------------------------------------------------------
  // Init
  // -----------------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', function() {
    var statesTA = document.querySelector('.workflow-states-builder');
    var transitionsTA = document.querySelector('.workflow-transitions-builder');
    if (statesTA && transitionsTA) {
      new WorkflowBuilder(statesTA, transitionsTA);
    }
  });
})();

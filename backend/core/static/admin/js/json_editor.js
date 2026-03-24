/**
 * JSON Editor widget for Django admin.
 * Auto-formats on blur, validates on change, shows errors inline.
 */
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.json-editor').forEach(function(textarea) {
    // Add format button
    const wrapper = document.createElement('div');
    wrapper.style.position = 'relative';
    textarea.parentNode.insertBefore(wrapper, textarea);
    wrapper.appendChild(textarea);

    const toolbar = document.createElement('div');
    toolbar.style.cssText = 'display:flex; gap:8px; margin-bottom:4px;';

    const formatBtn = document.createElement('button');
    formatBtn.type = 'button';
    formatBtn.textContent = '⚡ Format';
    formatBtn.className = 'button';
    formatBtn.style.cssText = 'font-size:12px; padding:2px 8px; cursor:pointer;';
    formatBtn.onclick = function() {
      try {
        const parsed = JSON.parse(textarea.value);
        textarea.value = JSON.stringify(parsed, null, 2);
        clearError();
      } catch(e) {
        showError(e.message);
      }
    };

    const validateBtn = document.createElement('button');
    validateBtn.type = 'button';
    validateBtn.textContent = '✓ Validate';
    validateBtn.className = 'button';
    validateBtn.style.cssText = 'font-size:12px; padding:2px 8px; cursor:pointer;';
    validateBtn.onclick = function() {
      try {
        JSON.parse(textarea.value);
        clearError();
        showSuccess('Valid JSON');
      } catch(e) {
        showError(e.message);
      }
    };

    const status = document.createElement('span');
    status.style.cssText = 'font-size:12px; line-height:24px; margin-left:8px;';

    toolbar.appendChild(formatBtn);
    toolbar.appendChild(validateBtn);
    toolbar.appendChild(status);
    wrapper.insertBefore(toolbar, textarea);

    function showError(msg) {
      status.textContent = '❌ ' + msg;
      status.style.color = '#dc2626';
      textarea.style.borderColor = '#dc2626';
    }

    function showSuccess(msg) {
      status.textContent = '✅ ' + msg;
      status.style.color = '#16a34a';
      textarea.style.borderColor = '#16a34a';
      setTimeout(function() { status.textContent = ''; textarea.style.borderColor = ''; }, 2000);
    }

    function clearError() {
      status.textContent = '';
      textarea.style.borderColor = '';
    }

    // Auto-format on blur
    textarea.addEventListener('blur', function() {
      try {
        const parsed = JSON.parse(textarea.value);
        textarea.value = JSON.stringify(parsed, null, 2);
        clearError();
      } catch(e) {
        showError(e.message);
      }
    });
  });
});

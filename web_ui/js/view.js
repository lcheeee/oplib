// View 层：纯展示层，不包含业务逻辑，不知道 Controller 的存在

const View = {
    // 渲染标签页（被动更新）
    renderTab(tabId) {
        const tabButtons = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');
        
        // 移除所有活动状态
        tabButtons.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        
        // 添加活动状态
        const activeBtn = document.querySelector(`[data-tab="${tabId}"]`);
        const activeContent = document.getElementById(tabId);
        if (activeBtn) activeBtn.classList.add('active');
        if (activeContent) activeContent.classList.add('active');
    },

    // 显示结果
    showResult(elementId, message, type = 'info') {
        const element = document.getElementById(elementId);
        element.textContent = '';
        element.className = `result ${type} show`;
        
        if (typeof message === 'object') {
            const pre = document.createElement('pre');
            pre.textContent = JSON.stringify(message, null, 2);
            element.appendChild(pre);
        } else {
            element.textContent = message;
        }
    },

    // 显示加载状态
    showLoading(elementId) {
        const element = document.getElementById(elementId);
        element.textContent = '处理中...';
        element.className = 'result info show';
        const loading = document.createElement('span');
        loading.className = 'loading';
        element.appendChild(loading);
    },

    // 隐藏结果
    hideResult(elementId) {
        const element = document.getElementById(elementId);
        element.classList.remove('show');
    },

    // 显示报告列表（纯展示，不包含事件处理）
    showReportsList(reports) {
        const container = document.getElementById('reports-list');
        container.innerHTML = '';
        
        if (!reports || reports.length === 0) {
            container.innerHTML = '<p>暂无报告文件</p>';
            return;
        }

        reports.forEach(report => {
            const item = document.createElement('div');
            item.className = 'report-item';
            item.textContent = report;
            item.setAttribute('data-report-path', report);
            container.appendChild(item);
        });
    },

    // 显示报告内容
    showReportContent(data) {
        const container = document.getElementById('report-content');
        container.className = 'result info show report-content';
        
        const pre = document.createElement('pre');
        pre.textContent = JSON.stringify(data, null, 2);
        container.appendChild(pre);
    },

    // 获取表单值（纯数据获取，不包含业务逻辑）
    getFormValue(id) {
        const element = document.getElementById(id);
        return element ? element.value.trim() : '';
    },

    // 设置表单值（纯数据设置）
    setFormValue(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.value = value;
        }
    },

    // 获取表单数据（批量获取）
    getFormData(formId) {
        const form = document.getElementById(formId);
        if (!form) return {};
        
        const data = {};
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            if (input.id) {
                data[input.id] = input.value.trim();
            }
        });
        return data;
    },

    // 更新表单字段（根据 Model 状态）
    updateFormField(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.value = value;
        }
    },

    // 清空表单
    clearForm(formId) {
        const form = document.getElementById(formId);
        if (!form) return;
        
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            if (input.type === 'checkbox' || input.type === 'radio') {
                input.checked = false;
            } else {
                input.value = '';
            }
        });
    },

    // 禁用/启用表单
    setFormDisabled(formId, disabled) {
        const form = document.getElementById(formId);
        if (!form) return;
        
        const inputs = form.querySelectorAll('input, textarea, select, button');
        inputs.forEach(input => {
            input.disabled = disabled;
        });
    }
};


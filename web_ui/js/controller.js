// Controller 层：事件处理和协调 Model 与 View

const Controller = {
    // 初始化：绑定所有事件
    init() {
        // 标签页切换事件
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabId = e.target.getAttribute('data-tab');
                this.switchTab(tabId);
            });
        });

        // 配置生成按钮事件
        document.getElementById('generate-config-btn')
            ?.addEventListener('click', () => this.generateConfig());

        // 传感器配置按钮事件
        document.getElementById('configure-sensor-btn')
            ?.addEventListener('click', () => this.configureSensor());

        // 工作流执行按钮事件
        document.getElementById('run-workflow-btn')
            ?.addEventListener('click', () => this.runWorkflow());

        // 加载报告按钮事件
        document.getElementById('load-report-btn')
            ?.addEventListener('click', () => this.loadReport());

        // 列出报告按钮事件
        document.getElementById('list-reports-btn')
            ?.addEventListener('click', () => this.listReports());

        // 报告列表项点击事件（事件委托）
        document.getElementById('reports-list')?.addEventListener('click', (e) => {
            const item = e.target.closest('.report-item');
            if (item) {
                const reportPath = item.getAttribute('data-report-path');
                if (reportPath) {
                    View.setFormValue('report-path', reportPath);
                    this.loadReport();
                }
            }
        });

        // 注册 Model 观察者（监听状态变化并更新 View）
        Model.subscribe({
            // 状态变化事件
            stateChanged: (data) => {
                if (data.key === 'currentTab') {
                    View.renderTab(data.value);
                }
            },

            // 加载状态变化事件
            loadingChanged: (data) => {
                const elementIdMap = {
                    config: 'config-result',
                    sensor: 'sensor-result',
                    workflow: 'workflow-result',
                    report: 'report-content'
                };
                const elementId = elementIdMap[data.type];
                if (elementId) {
                    if (data.loading) {
                        View.showLoading(elementId);
                    }
                }
            },

            // 配置生成完成事件
            configGenerated: (result) => {
                if (result.success) {
                    View.showResult('config-result', {
                        message: '配置生成成功',
                        files: result.data.files || result.data
                    }, 'success');
                } else {
                    View.showResult('config-result', `错误: ${result.error}`, 'error');
                }
            },

            // 传感器配置完成事件
            sensorConfigured: (result) => {
                if (result.success) {
                    View.showResult('sensor-result', {
                        message: '传感器配置保存成功',
                        config: result.data
                    }, 'success');
                } else {
                    View.showResult('sensor-result', `错误: ${result.error}`, 'error');
                }
            },

            // 工作流执行完成事件
            workflowExecuted: (result) => {
                if (result.success) {
                    View.showResult('workflow-result', {
                        message: '工作流执行成功',
                        result: result.data
                    }, 'success');
                } else {
                    View.showResult('workflow-result', `错误: ${result.error}`, 'error');
                }
            }
        });
    },

    // 切换标签页
    switchTab(tabId) {
        Model.setState('currentTab', tabId);
    },

    // 配置生成（通过 Model 业务逻辑处理）
    async generateConfig() {
        // 从 View 获取数据
        const formData = {
            apiUrl: View.getFormValue('config-api-url'),
            specificationId: View.getFormValue('specification-id'),
            workflowName: View.getFormValue('workflow-name'),
            stagesText: View.getFormValue('stages-config'),
            rulesText: View.getFormValue('rules-config')
        };

        // 调用 Model 业务逻辑（包含验证和状态管理）
        await Model.generateConfig(formData);
    },

    // 传感器配置（通过 Model 业务逻辑处理）
    async configureSensor() {
        // 从 View 获取数据
        const formData = {
            apiUrl: View.getFormValue('sensor-api-url'),
            workflowId: View.getFormValue('workflow-id'),
            specificationId: View.getFormValue('sensor-spec-id'),
            sensorMappingText: View.getFormValue('sensor-mapping'),
            dataSourceType: View.getFormValue('data-source-type'),
            dataFilePath: View.getFormValue('data-file-path')
        };

        // 调用 Model 业务逻辑（包含验证和状态管理）
        await Model.configureSensor(formData);
    },

    // 工作流执行（通过 Model 业务逻辑处理）
    async runWorkflow() {
        // 从 View 获取数据
        const formData = {
            apiUrl: View.getFormValue('workflow-api-url'),
            workflowId: View.getFormValue('run-workflow-id'),
            specificationId: View.getFormValue('run-spec-id'),
            processId: View.getFormValue('process-id'),
            seriesId: View.getFormValue('series-id'),
            calculationDate: View.getFormValue('calculation-date')
        };

        // 调用 Model 业务逻辑（包含验证和状态管理）
        await Model.runWorkflow(formData);
    },

    // 加载报告
    async loadReport() {
        // 从 View 获取数据
        const filePath = View.getFormValue('report-path');
        
        if (!filePath) {
            View.showResult('report-content', '请输入报告文件路径', 'error');
            return;
        }

        // 显示加载状态
        View.showLoading('report-content');

        // 调用 Model
        const result = await Model.loadReport(filePath);

        // 更新 Model 状态
        Model.setState('reportContent', result);

        // 更新 View
        if (result.success) {
            View.showReportContent(result.data);
        } else {
            View.showResult('report-content', `错误: ${result.error}`, 'error');
        }
    },

    // 列出报告
    async listReports() {
        // 显示加载状态
        View.showLoading('reports-list');
        
        // 调用 Model
        const result = await Model.listReports();
        
        // 更新 View
        if (result.success) {
            View.showReportsList(result.data);
        } else {
            const container = document.getElementById('reports-list');
            container.innerHTML = `<p style="color: #721c24;">${result.error}</p>`;
        }
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    Controller.init();
});


// Model 层：数据模型、状态管理和业务逻辑

const Model = {
    // 应用状态
    state: {
        configGeneratorUrl: 'http://localhost:8100',
        dataAnalyzerUrl: 'http://localhost:8000',
        currentTab: 'config',
        configResult: null,
        sensorResult: null,
        workflowResult: null,
        reportContent: null,
        loading: {
            config: false,
            sensor: false,
            workflow: false,
            report: false
        }
    },

    // 观察者列表（用于通知 View 更新）
    observers: [],

    // 注册观察者
    subscribe(observer) {
        this.observers.push(observer);
        return () => {
            // 返回取消订阅函数
            const index = this.observers.indexOf(observer);
            if (index > -1) {
                this.observers.splice(index, 1);
            }
        };
    },

    // 通知观察者
    notify(event, data) {
        this.observers.forEach(observer => {
            if (observer[event]) {
                try {
                    observer[event](data);
                } catch (error) {
                    console.error(`Observer error in ${event}:`, error);
                }
            }
        });
    },

    // 更新状态并通知
    setState(key, value) {
        const oldValue = this.state[key];
        this.state[key] = value;
        this.notify('stateChanged', { key, value, oldValue });
    },

    // 批量更新状态
    setStateBatch(updates) {
        const oldValues = {};
        Object.keys(updates).forEach(key => {
            oldValues[key] = this.state[key];
            this.state[key] = updates[key];
        });
        this.notify('stateChanged', { updates, oldValues });
    },

    // 数据模型类
    models: {
        // 配置生成请求模型
        ConfigGenerationRequest: class {
            constructor(data) {
                this.specificationId = data.specificationId || '';
                this.workflowName = data.workflowName || '';
                this.stages = data.stages || { items: [] };
                this.ruleInputs = data.ruleInputs || [];
                this.apiUrl = data.apiUrl || Model.state.configGeneratorUrl;
            }

            validate() {
                const errors = [];
                if (!this.specificationId || this.specificationId.trim() === '') {
                    errors.push('规范ID不能为空');
                }
                if (!this.workflowName || this.workflowName.trim() === '') {
                    errors.push('工作流名称不能为空');
                }
                return {
                    valid: errors.length === 0,
                    errors
                };
            }

            toPayload() {
                return {
                    specification_id: this.specificationId,
                    workflow_name: this.workflowName,
                    stages: this.stages,
                    rule_inputs: this.ruleInputs,
                    publish: true
                };
            }
        },

        // 传感器配置请求模型
        SensorConfigRequest: class {
            constructor(data) {
                this.workflowId = data.workflowId || '';
                this.specificationId = data.specificationId || '';
                this.sensorMapping = data.sensorMapping || {};
                this.dataSource = data.dataSource || { type: 'offline' };
                this.apiUrl = data.apiUrl || Model.state.dataAnalyzerUrl;
            }

            validate() {
                const errors = [];
                if (!this.workflowId || this.workflowId.trim() === '') {
                    errors.push('工作流ID不能为空');
                }
                if (!this.specificationId || this.specificationId.trim() === '') {
                    errors.push('规范ID不能为空');
                }
                if (!this.dataSource.type) {
                    errors.push('数据源类型不能为空');
                }
                return {
                    valid: errors.length === 0,
                    errors
                };
            }

            toPayload() {
                return {
                    workflow_id: this.workflowId,
                    specification_id: this.specificationId,
                    sensor_mapping: this.sensorMapping,
                    data_source: this.dataSource
                };
            }
        },

        // 工作流执行请求模型
        WorkflowRequest: class {
            constructor(data) {
                this.workflowId = data.workflowId || '';
                this.specificationId = data.specificationId || '';
                this.processId = data.processId || null;
                this.seriesId = data.seriesId || null;
                this.calculationDate = data.calculationDate || null;
                this.apiUrl = data.apiUrl || Model.state.dataAnalyzerUrl;
            }

            validate() {
                const errors = [];
                if (!this.workflowId || this.workflowId.trim() === '') {
                    errors.push('工作流ID不能为空');
                }
                if (!this.specificationId || this.specificationId.trim() === '') {
                    errors.push('规范ID不能为空');
                }
                return {
                    valid: errors.length === 0,
                    errors
                };
            }

            toPayload() {
                const payload = {
                    workflow_id: this.workflowId,
                    specification_id: this.specificationId
                };
                if (this.processId) payload.process_id = this.processId;
                if (this.seriesId) payload.series_id = this.seriesId;
                if (this.calculationDate) payload.calculation_date = this.calculationDate;
                return payload;
            }
        }
    },

    // 数据验证
    validate: {
        // 验证规范ID
        specificationId(id) {
            if (!id || id.trim() === '') {
                return { valid: false, error: '规范ID不能为空' };
            }
            // 可以添加更多验证规则
            if (id.length > 100) {
                return { valid: false, error: '规范ID长度不能超过100个字符' };
            }
            return { valid: true };
        },

        // 验证工作流ID
        workflowId(id) {
            if (!id || id.trim() === '') {
                return { valid: false, error: '工作流ID不能为空' };
            }
            return { valid: true };
        },

        // 验证JSON格式
        json(text, fieldName = 'JSON') {
            if (!text || text.trim() === '') {
                return { valid: true, data: null }; // 空值视为有效
            }
            try {
                const data = JSON.parse(text);
                return { valid: true, data };
            } catch (error) {
                return { valid: false, error: `${fieldName} 格式错误: ${error.message}` };
            }
        },

        // 验证URL格式
        url(urlString) {
            if (!urlString || urlString.trim() === '') {
                return { valid: false, error: 'URL不能为空' };
            }
            try {
                new URL(urlString);
                return { valid: true };
            } catch (error) {
                return { valid: false, error: `URL格式错误: ${error.message}` };
            }
        }
    },

    // 业务逻辑：配置生成
    async generateConfig(formData) {
        // 解析表单数据
        const stagesValidation = this.validate.json(formData.stagesText, '阶段配置');
        const rulesValidation = this.validate.json(formData.rulesText, '规则配置');
        
        if (!stagesValidation.valid) {
            return { success: false, error: stagesValidation.error };
        }
        if (!rulesValidation.valid) {
            return { success: false, error: rulesValidation.error };
        }

        // 创建数据模型
        const request = new this.models.ConfigGenerationRequest({
            specificationId: formData.specificationId,
            workflowName: formData.workflowName,
            stages: stagesValidation.data || { items: [] },
            ruleInputs: rulesValidation.data || [],
            apiUrl: formData.apiUrl
        });

        // 验证模型
        const validation = request.validate();
        if (!validation.valid) {
            return { success: false, error: validation.errors.join(', ') };
        }

        // 设置加载状态
        this.setState('loading', { ...this.state.loading, config: true });
        this.notify('loadingChanged', { type: 'config', loading: true });

        try {
            const url = `${request.apiUrl}/api/rules/generate`;
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(request.toPayload())
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || data.message || '请求失败');
            }

            const result = { success: true, data };
            this.setState('configResult', result);
            this.notify('configGenerated', result);
            return result;
        } catch (error) {
            const result = { success: false, error: error.message };
            this.setState('configResult', result);
            this.notify('configGenerated', result);
            return result;
        } finally {
            this.setState('loading', { ...this.state.loading, config: false });
            this.notify('loadingChanged', { type: 'config', loading: false });
        }
    },

    // 业务逻辑：传感器配置
    async configureSensor(formData) {
        // 解析传感器映射
        const mappingValidation = this.validate.json(formData.sensorMappingText, '传感器映射');
        if (!mappingValidation.valid) {
            return { success: false, error: mappingValidation.error };
        }

        // 构建数据源配置
        const dataSource = {
            type: formData.dataSourceType
        };
        if (formData.dataSourceType === 'offline' && formData.dataFilePath) {
            dataSource.file_path = formData.dataFilePath;
        }

        // 创建数据模型
        const request = new this.models.SensorConfigRequest({
            workflowId: formData.workflowId,
            specificationId: formData.specificationId,
            sensorMapping: mappingValidation.data || {},
            dataSource: dataSource,
            apiUrl: formData.apiUrl
        });

        // 验证模型
        const validation = request.validate();
        if (!validation.valid) {
            return { success: false, error: validation.errors.join(', ') };
        }

        // 设置加载状态
        this.setState('loading', { ...this.state.loading, sensor: true });
        this.notify('loadingChanged', { type: 'sensor', loading: true });

        try {
            const url = `${request.apiUrl}/api/sensor/config`;
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(request.toPayload())
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || data.message || '请求失败');
            }

            const result = { success: true, data };
            this.setState('sensorResult', result);
            this.notify('sensorConfigured', result);
            return result;
        } catch (error) {
            const result = { success: false, error: error.message };
            this.setState('sensorResult', result);
            this.notify('sensorConfigured', result);
            return result;
        } finally {
            this.setState('loading', { ...this.state.loading, sensor: false });
            this.notify('loadingChanged', { type: 'sensor', loading: false });
        }
    },

    // 获取传感器配置 API
    async getSensorConfig(workflowId, specificationId, apiUrl) {
        const url = `${apiUrl || this.state.dataAnalyzerUrl}/api/sensor/config/${workflowId}/${specificationId}`;

        try {
            const response = await fetch(url);
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || data.message || '请求失败');
            }
            return { success: true, data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    },

    // 业务逻辑：工作流执行
    async runWorkflow(formData) {
        // 创建数据模型
        const request = new this.models.WorkflowRequest({
            workflowId: formData.workflowId,
            specificationId: formData.specificationId,
            processId: formData.processId || null,
            seriesId: formData.seriesId || null,
            calculationDate: formData.calculationDate || null,
            apiUrl: formData.apiUrl
        });

        // 验证模型
        const validation = request.validate();
        if (!validation.valid) {
            return { success: false, error: validation.errors.join(', ') };
        }

        // 设置加载状态
        this.setState('loading', { ...this.state.loading, workflow: true });
        this.notify('loadingChanged', { type: 'workflow', loading: true });

        try {
            const url = `${request.apiUrl}/run`;
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(request.toPayload())
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || data.message || '请求失败');
            }

            const result = { success: true, data };
            this.setState('workflowResult', result);
            this.notify('workflowExecuted', result);
            return result;
        } catch (error) {
            const result = { success: false, error: error.message };
            this.setState('workflowResult', result);
            this.notify('workflowExecuted', result);
            return result;
        } finally {
            this.setState('loading', { ...this.state.loading, workflow: false });
            this.notify('loadingChanged', { type: 'workflow', loading: false });
        }
    },

    // 加载报告文件（通过文件系统 API 或直接读取）
    async loadReport(filePath) {
        // 注意：由于浏览器安全限制，无法直接读取本地文件系统
        // 这里返回一个提示，实际需要通过后端 API 或文件上传实现
        return {
            success: false,
            error: '浏览器无法直接读取本地文件。请使用文件上传功能或通过后端 API 访问报告。'
        };
    },

    // 列出报告文件（需要通过后端 API）
    async listReports() {
        // 需要通过后端 API 实现
        return {
            success: false,
            error: '需要通过后端 API 实现报告列表功能'
        };
    }
};


# OPLib 工作流程管理 Web UI

简洁的 MVC 架构静态页面系统，用于执行 OPLib 的完整工作流程。

## 目录结构

```
web_ui/
├── index.html          # 主页面（View 层）
├── css/
│   └── style.css      # 样式文件
├── js/
│   ├── model.js       # Model 层：数据模型和 API 调用
│   ├── view.js        # View 层：视图渲染
│   └── controller.js  # Controller 层：业务逻辑控制
└── README.md          # 本文件
```

## MVC 架构说明

### Model 层 (`js/model.js`)
- **数据模型**：定义应用的数据结构
- **状态管理**：管理应用状态（state）
- **业务逻辑**：包含数据验证逻辑（validate）
- **API 调用**：封装与后端服务的通信
- **观察者模式**：状态变化时通知 View 更新（subscribe/notify）

### View 层 (`js/view.js`)
- **纯展示层**：只负责 UI 渲染，不包含业务逻辑
- **被动更新**：根据 Model 的状态渲染
- **数据获取**：提供表单数据获取方法
- **不包含事件处理**：所有事件由 Controller 处理

### Controller 层 (`js/controller.js`)
- **事件处理**：处理所有用户交互事件
- **协调 Model 和 View**：调用 Model 更新数据，通知 View 更新
- **不直接操作 DOM**：通过 View 层方法操作
- **不包含业务逻辑**：业务逻辑在 Model 层

## 使用方式

### 1. 启动后端服务

**配置生成服务（端口 8100）：**
```bash
python -m config_generator.app
```

**数据分析服务（端口 8000）：**
```bash
uvicorn data_analyzer.src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 打开 Web UI

直接在浏览器中打开 `index.html` 文件，或使用本地服务器：

```bash
# Python 3
python -m http.server 8080

# Node.js
npx http-server -p 8080
```

然后访问：`http://localhost:8080`

### 3. 执行工作流程

#### 步骤 1：配置生成
1. 填写规范ID、工作流名称
2. 填写阶段配置（JSON 格式）
3. 填写规则配置（JSON 格式）
4. 点击"生成配置"

#### 步骤 2：传感器配置
1. 填写工作流ID、规范ID
2. 填写传感器映射（JSON 格式）
3. 选择数据源类型（离线/在线）
4. 填写数据文件路径（离线模式）
5. 点击"保存配置"

#### 步骤 3：工作流执行
1. 填写工作流ID、规范ID
2. 填写可选参数（流程ID、系列ID、计算日期）
3. 点击"执行工作流"

#### 步骤 4：结果查看
1. 输入报告文件路径
2. 点击"加载报告"查看结果

## 功能特性

- ✅ 极致简洁的界面设计
- ✅ **标准 MVC 架构**：职责清晰分离
  - Model：状态管理 + 业务逻辑 + API 调用
  - View：纯展示层，被动更新
  - Controller：事件处理 + 协调
- ✅ **观察者模式**：Model 状态变化自动通知 View
- ✅ **数据验证**：在 Model 层统一处理
- ✅ 完整的错误处理
- ✅ JSON 格式验证
- ✅ 实时结果显示
- ✅ 标签页导航

## 架构改进说明

### 重构前的问题
1. Model 只是简单的 API 调用封装，缺少状态管理
2. View 包含事件处理，违反了 MVC 分离原则
3. Controller 承担了太多职责（验证、解析、业务逻辑）

### 重构后的改进
1. **Model 层**：
   - 添加状态管理（state）
   - 实现观察者模式（subscribe/notify）
   - 统一数据验证逻辑（validate）

2. **View 层**：
   - 移除事件处理，改为纯展示函数
   - 移除对 Controller 的直接依赖
   - 被动更新，根据 Model 状态渲染

3. **Controller 层**：
   - 处理所有事件绑定
   - 使用 Model 的验证方法
   - 更新 Model 状态，通知 View 更新

详细分析请参考 `ARCHITECTURE_ANALYSIS.md`

## 注意事项

1. **跨域问题**：如果遇到 CORS 错误，需要在后端服务中配置 CORS 支持
2. **报告查看**：由于浏览器安全限制，报告文件查看功能需要通过后端 API 实现
3. **服务地址**：默认服务地址可在页面中修改

## 扩展建议

如需扩展功能，可以：
1. 在 `model.js` 中添加新的 API 调用方法
2. 在 `view.js` 中添加新的视图渲染方法
3. 在 `controller.js` 中添加新的业务逻辑控制方法


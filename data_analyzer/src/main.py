"""OPLib 主程序入口 - 工作流API服务。"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from pathlib import Path
import os


def _find_startup_config_fallback() -> str | None:
    """从当前文件与当前工作目录向上查找 config/startup_config.yaml。"""
    target_rel = os.path.join("config", "startup_config.yaml")
    # 1) 以当前文件为起点向上
    try:
        cur = Path(__file__).resolve()
        for parent in [cur.parent, *cur.parents]:
            candidate = parent / target_rel
            if candidate.exists():
                return str(candidate)
    except Exception:
        pass
    # 2) 以当前工作目录为起点向上
    try:
        cur = Path(os.getcwd()).resolve()
        for parent in [cur, *cur.parents]:
            candidate = parent / target_rel
            if candidate.exists():
                return str(candidate)
    except Exception:
        pass
    return None
from datetime import datetime
from contextlib import asynccontextmanager

from .workflow.builder import WorkflowBuilder
from .workflow.orchestrator import WorkflowOrchestrator
from .workflow.cache import workflow_cache, calculate_config_hash
from .config.manager import ConfigManager
from .config.sensor_config_manager import SensorConfigManager
from .config.sensor_config_validator import SensorConfigValidator
from .core.exceptions import WorkflowError, ConfigurationError
from .utils.logging_config import setup_logging, get_logger

# 全局变量存储工作流注册表和配置管理器
workflow_registry = {}
config_manager = None
sensor_config_manager = None
sensor_config_validator = None
logger = get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。"""
    # 启动时执行
    logger.info("FastAPI应用启动中...")
    try:
        # 若未加载工作流注册表，则在启动时按需加载（兼容 uvicorn 直接启动 app 的场景）
        if not workflow_registry:
            cfg = os.getenv("OPLIB_CONFIG")
            if not cfg or not Path(cfg).exists():
                cfg_dir = os.getenv("OPLIB_CONFIG_DIR")
                if cfg_dir and Path(cfg_dir).exists():
                    candidate = Path(cfg_dir) / "startup_config.yaml"
                    cfg = str(candidate) if candidate.exists() else None
            if not cfg:
                fallback = _find_startup_config_fallback()
                cfg = fallback if fallback else "config/startup_config.yaml"
            logger.info(f"应用启动加载工作流注册表，使用配置: {cfg}")
            load_workflow_registry(cfg)
            logger.info(f"启动加载完成，当前工作流数量: {len(workflow_registry)} -> {list(workflow_registry.keys())}")
        else:
            logger.info(f"工作流注册表已存在，数量: {len(workflow_registry)}")
    except Exception as e:
        logger.error(f"启动阶段加载工作流失败: {e}")
    logger.info("FastAPI应用启动完成")
    yield
    # 关闭时执行（如果需要的话）
    logger.info("FastAPI应用正在关闭")

app = FastAPI(
    title="OPLib 工作流API",
    description="工业传感器数据分析工作流API服务",
    version="2.0.0",
    lifespan=lifespan
)

class WorkflowParameters(BaseModel):
    """工作流参数模型（简化版）。"""
    process_id: Optional[str] = None
    series_id: Optional[str] = None
    specification_id: Optional[str] = None
    calculation_date: Optional[str] = None
    # 注意：sensor_grouping 已移除，改为从配置文件加载

class WorkflowInputs(BaseModel):
    """工作流输入数据模型。"""
    file_path: Optional[str] = None
    online_data: Optional[bool] = None

class WorkflowRequest(BaseModel):
    """工作流请求模型（简化版）。"""
    workflow_id: str  # 工作流ID（如 curing_analysis_offline）
    specification_id: str  # 规范ID
    process_id: Optional[str] = None  # 可选，用于结果标识
    series_id: Optional[str] = None  # 可选，用于结果标识
    calculation_date: Optional[str] = None  # 可选，用于结果标识

class WorkflowResponse(BaseModel):
    """工作流响应模型。"""
    status: str
    execution_time: float
    result_path: Optional[str] = None
    workflow_name: str
    message: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None


# ============================================================
# 传感器配置接口
# ============================================================

class SensorConfigRequest(BaseModel):
    """传感器配置请求模型。"""
    workflow_id: str
    specification_id: str
    sensor_mapping: Dict[str, List[str]]
    data_source: Optional[Dict[str, Any]] = None


class SensorConfigResponse(BaseModel):
    """传感器配置响应模型。"""
    status: str
    message: str
    config_path: Optional[str] = None
    errors: Optional[List[str]] = None


@app.post("/api/sensor/config", response_model=SensorConfigResponse)
async def configure_sensor(request: SensorConfigRequest):
    """配置传感器映射。"""
    global config_manager, sensor_config_manager, sensor_config_validator
    
    if config_manager is None:
        raise HTTPException(status_code=500, detail="配置管理器未初始化")
    
    if sensor_config_manager is None:
        raise HTTPException(status_code=500, detail="传感器配置管理器未初始化")
    
    if sensor_config_validator is None:
        raise HTTPException(status_code=500, detail="传感器配置验证器未初始化")
    
    try:
        # 获取规范配置以确定 process_type
        # 从 rules.yaml 中获取 process_type（如果存在）
        rules_config = config_manager.get_specification_rules(request.specification_id)
        process_type = rules_config.get("process_type", "curing") if rules_config else "curing"
        
        # 验证传感器配置
        is_valid, errors = sensor_config_validator.validate_sensor_config(
            specification_id=request.specification_id,
            sensor_mapping=request.sensor_mapping,
            process_type=process_type
        )
        
        if not is_valid:
            return SensorConfigResponse(
                status="error",
                message="传感器配置验证失败",
                errors=errors
            )
        
        # 保存传感器配置
        config_path = sensor_config_manager.save_sensor_config(
            workflow_id=request.workflow_id,
            specification_id=request.specification_id,
            sensor_mapping=request.sensor_mapping,
            data_source=request.data_source
        )
        
        logger.info(f"传感器配置已保存: {config_path}")
        
        return SensorConfigResponse(
            status="success",
            message="传感器配置已保存",
            config_path=config_path
        )
    except Exception as e:
        logger.error(f"配置传感器失败: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"配置传感器失败: {e}")


@app.get("/api/sensor/config/{workflow_id}/{specification_id}")
async def get_sensor_config(workflow_id: str, specification_id: str):
    """获取传感器配置。"""
    global sensor_config_manager
    
    if sensor_config_manager is None:
        raise HTTPException(status_code=500, detail="传感器配置管理器未初始化")
    
    try:
        config = sensor_config_manager.load_sensor_config(workflow_id, specification_id)
        
        if config is None:
            raise HTTPException(
                status_code=404,
                detail=f"传感器配置未找到: workflow_id={workflow_id}, specification_id={specification_id}"
            )
        
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取传感器配置失败: {e}")
        raise HTTPException(status_code=400, detail=f"获取传感器配置失败: {e}")


@app.delete("/api/sensor/config/{workflow_id}/{specification_id}")
async def delete_sensor_config(workflow_id: str, specification_id: str):
    """删除传感器配置。"""
    global sensor_config_manager
    
    if sensor_config_manager is None:
        raise HTTPException(status_code=500, detail="传感器配置管理器未初始化")
    
    try:
        deleted = sensor_config_manager.delete_sensor_config(workflow_id, specification_id)
        
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"传感器配置未找到: workflow_id={workflow_id}, specification_id={specification_id}"
            )
        
        return {"status": "success", "message": "传感器配置已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除传感器配置失败: {e}")
        raise HTTPException(status_code=400, detail=f"删除传感器配置失败: {e}")


def load_workflow_registry(startup_config_path: str = "config/startup_config.yaml"):
    """加载工作流注册表。"""
    global workflow_registry, config_manager, sensor_config_manager, sensor_config_validator
    
    try:
        logger.info("load_workflow_registry 开始")
        logger.info(f"传入 startup_config_path: {startup_config_path}")
        # 初始化配置管理器
        config_manager = ConfigManager(startup_config_path)
        
        # 初始化传感器配置管理器
        base_dir = config_manager.get_startup_params().get('base_dir', '.')
        sensor_config_manager = SensorConfigManager(base_dir=base_dir)
        
        # 初始化传感器配置验证器
        sensor_config_validator = SensorConfigValidator(config_manager.template_registry)
        
        # 打印基础目录与配置路径解析情况
        try:
            startup_params = config_manager.get_startup_params()
            logger.info(f"ConfigManager.base_dir: {startup_params.get('base_dir')}")
            wf_path = config_manager.get_config_path("workflow_config")
            logger.info(f"workflow_config 解析路径: {wf_path}")
        except Exception as e:
            logger.warning(f"打印启动参数/路径失败: {e}")

        # 从配置管理器获取工作流配置
        workflow_config = config_manager.get_workflow_config()
        if not workflow_config:
            logger.error("未能加载到 workflow_config（为空字典）")
        else:
            logger.info(f"workflow_config.version: {workflow_config.get('version')}")
            logger.info(f"workflow_config.keys: {list(workflow_config.keys())}")
        
        # 配置工作流缓存大小
        cache_size = workflow_config.get("cache", {}).get("max_workflows", 2)
        workflow_cache.max_size = cache_size
        logger.info(f"工作流缓存大小设置为: {cache_size}")
        
        if "workflows" in workflow_config:
            logger.info(f"发现 workflows 节点，条目数: {len(workflow_config['workflows'])}")
            for workflow_name, workflow_def in workflow_config["workflows"].items():
                workflow_registry[workflow_name] = {
                    "config_file": config_manager.get_config_path("workflow_config"),
                    "version": workflow_config.get("version", "v1"),
                    "description": workflow_def.get("description", f"工作流: {workflow_name}"),
                    "config": workflow_def
                }
                logger.info(f"已加载工作流: {workflow_name}")
        else:
            # 打印详细内容帮助排查
            logger.error("workflow_config 中不包含 'workflows' 节点")
            try:
                from pprint import pformat
                logger.error(f"workflow_config 内容预览:\n{pformat(workflow_config)[:2000]}")
            except Exception:
                pass
        
        startup_params = config_manager.get_startup_params()
        
        # 初始化传感器配置管理器
        base_dir = startup_params.get('base_dir', '.')
        sensor_config_manager = SensorConfigManager(base_dir=base_dir)
        
        # 初始化传感器配置验证器
        sensor_config_validator = SensorConfigValidator(config_manager.template_registry)
        
        logger.info("配置管理器初始化完成")
        logger.info(f"基础目录: {startup_params['base_dir']}")
        logger.info(f"调试模式: {startup_params['debug']}")
        logger.info(f"服务地址: {startup_params['host']}:{startup_params['port']}")
        logger.info(f"当前已加载工作流数量: {len(workflow_registry)} -> {list(workflow_registry.keys())}")
        
    except Exception as e:
        logger.error(f"加载工作流配置失败: {e}")
        try:
            import traceback
            logger.error(traceback.format_exc())
        except Exception:
            pass
        raise

def get_workflow_config(workflow_id: str) -> Dict[str, Any]:
    """获取工作流配置。"""
    if workflow_id not in workflow_registry:
        raise HTTPException(
            status_code=404,
            detail=f"工作流 '{workflow_id}' 不存在"
        )
    
    return workflow_registry[workflow_id]

def apply_parameter_overrides(config: Dict[str, Any], parameters: Optional[WorkflowParameters]) -> Dict[str, Any]:
    """应用参数覆盖。"""
    if not parameters:
        return config
    
    # 创建配置副本
    updated_config = config.copy()
    
    # 更新工作流参数
    if "parameters" in updated_config:
        param_dict = parameters.dict(exclude_unset=True)
        for key, value in param_dict.items():
            if value is not None:
                updated_config["parameters"][key] = value
    
    return updated_config



def apply_input_overrides(config: Dict[str, Any], inputs: Optional[WorkflowInputs]) -> Dict[str, Any]:
    """应用输入数据覆盖。"""
    logger.info(f"apply_input_overrides 输入: inputs={inputs}")
    
    if not inputs:
        logger.info("inputs 为空，返回原配置")
        return config
    
    # 创建配置副本
    updated_config = config.copy()
    
    # 确保 inputs 部分存在
    if "inputs" not in updated_config:
        updated_config["inputs"] = {}
        logger.info("创建 inputs 部分")
    
    # 更新工作流输入
    input_dict = inputs.dict(exclude_unset=True)
    logger.info(f"输入字典: {input_dict}")
    
    for key, value in input_dict.items():
        if value is not None:
            updated_config["inputs"][key] = value
            logger.info(f"设置 inputs[{key}] = {value}")
    
    logger.info(f"更新后配置的 inputs: {updated_config.get('inputs', {})}")
    return updated_config


def _build_sensor_groups_from_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """根据请求参数构造传感器组配置（仅支持 parameters.sensor_grouping）。"""
    def to_columns(items: Optional[list[str]]) -> str:
        return ",".join(items) if items else ""

    sensor_groups: Dict[str, Any] = {}
    grouping = params.get("sensor_grouping")
    if not isinstance(grouping, dict) or not grouping:
        return {"sensor_groups": {}}

    for group_name, columns in grouping.items():
        if isinstance(columns, list) and columns:
            sensor_groups[group_name] = {"columns": to_columns(columns)}

    return {"sensor_groups": sensor_groups}

def validate_and_apply_defaults(config: Dict[str, Any]) -> Dict[str, Any]:
    """验证参数并应用默认值。"""
    updated_config = config.copy()
    
    # 处理 parameters 默认值
    if "parameters" in updated_config:
        params = updated_config["parameters"]
        
        if not config_manager:
            raise ConfigurationError("配置管理器未初始化")
        
        # 从配置管理器获取默认值
        defaults = config_manager.get_workflow_defaults()
        
        missing_params = []
        used_defaults = []
        
        for param, default_value in defaults.items():
            if param not in params or params[param] is None:
                params[param] = default_value
                used_defaults.append(f"{param}={default_value}")
        
        # 检查必需参数 - 从配置管理器获取
        required_params = config_manager.get_workflow_required_params()
        
        for param in required_params:
            if param not in params or not params[param]:
                missing_params.append(param)
        
        if missing_params:
            raise HTTPException(
                status_code=400,
                detail=f"缺少必需参数: {', '.join(missing_params)}"
            )
        
        # 输出参数使用情况
        logger.info("=" * 50)
        logger.info("工作流参数使用情况:")
        for key, value in params.items():
            logger.info(f"{key}: {value}")
        
        if used_defaults:
            logger.info(f"使用默认值的参数: {', '.join(used_defaults)}")
        logger.info("=" * 50)
    
    return updated_config


@app.post("/run", response_model=WorkflowResponse)
async def run_workflow(request: WorkflowRequest):
    """执行工作流（简化版）。"""
    start_time = datetime.now()
    
    logger.info(f"\n收到工作流执行请求")
    logger.info(f"工作流ID: {request.workflow_id}")
    logger.info(f"规范ID: {request.specification_id}")
    
    global config_manager, sensor_config_manager
    
    if config_manager is None:
        raise HTTPException(status_code=500, detail="配置管理器未初始化")
    
    if sensor_config_manager is None:
        raise HTTPException(status_code=500, detail="传感器配置管理器未初始化")
    
    try:
        # 1. 获取工作流配置
        logger.info("\n获取工作流配置...")
        workflow_info = get_workflow_config(request.workflow_id)
        config = workflow_info["config"].copy()
        logger.info("工作流配置获取成功")
        
        # 2. 加载传感器配置
        logger.info("\n加载传感器配置...")
        sensor_config = sensor_config_manager.load_sensor_config(
            request.workflow_id,
            request.specification_id
        )
        
        if sensor_config is None:
            raise HTTPException(
                status_code=400,
                detail=f"传感器配置未找到，请先调用 /api/sensor/config 配置传感器映射。workflow_id={request.workflow_id}, specification_id={request.specification_id}"
            )
        
        sensor_mapping = sensor_config.get("sensor_mapping", {})
        data_source = sensor_config.get("data_source", {})
        
        logger.info(f"传感器配置已加载: {len(sensor_mapping)} 个传感器组")
        
        # 3. 设置规范ID（从请求中获取）
        if "parameters" not in config:
            config["parameters"] = {}
        
        config["parameters"]["specification_id"] = request.specification_id
        
        # 4. 设置可选参数
        if request.process_id:
            config["parameters"]["process_id"] = request.process_id
        if request.series_id:
            config["parameters"]["series_id"] = request.series_id
        if request.calculation_date:
            config["parameters"]["calculation_date"] = request.calculation_date
        
        # 5. 设置数据源（从传感器配置中获取）
        if data_source:
            if "inputs" not in config:
                config["inputs"] = {}
            if "file_path" in data_source:
                config["inputs"]["file_path"] = data_source["file_path"]
            if "online_data" in data_source:
                config["inputs"]["online_data"] = data_source.get("type") == "online"
        
        # 6. 验证输入文件（从传感器配置中获取）
        file_path = config.get("inputs", {}).get("file_path")
        if file_path:
            # 规范化路径分隔符，避免控制台显示问题
            normalized_path = file_path.replace('\\', '/')
            logger.info(f"验证输入文件: {normalized_path}")
            
            # 使用路径解析工具来正确处理相对路径
            from .utils.path_utils import resolve_path
            base_dir = config_manager.get_startup_params().get('base_dir', '.')
            resolved_path = resolve_path(base_dir, normalized_path)
            logger.info(f"解析后的文件路径: {resolved_path}")
            
            if not Path(resolved_path).exists():
                raise HTTPException(
                    status_code=400,
                    detail=f"输入文件不存在: {resolved_path}"
                )
            # 将解析后的绝对路径写回配置，确保后续数据源读取使用正确路径
            config["inputs"]["file_path"] = str(resolved_path)
            logger.info("已将解析后的文件路径写回配置 inputs.file_path")
            logger.info("输入文件验证通过")
        
        # 构建工作流（使用缓存）
        logger.info("\n构建工作流...")
        if config_manager is None:
            raise HTTPException(status_code=500, detail="配置管理器未初始化")
        
        # 7. 运行时绑定规范配置到实际传感器
        bound_specification = None
        specification_id = config.get("parameters", {}).get("specification_id")
        if specification_id and sensor_mapping:
            try:
                # 绑定规范配置（使用从配置文件加载的传感器映射）
                bound_specification = config_manager.bind_specification(
                    specification_id=specification_id,
                    sensor_grouping=sensor_mapping
                )
                logger.info(f"已绑定规范配置: {specification_id}, 计算项: {len(bound_specification.calculations)}, 规则: {len(bound_specification.rules)}")
            except Exception as e:
                logger.error(f"绑定规范配置失败: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                raise HTTPException(
                    status_code=400,
                    detail=f"绑定规范配置失败: {e}"
                )
        
        # 8. 将运行时传感器映射转换为 sensor_groups 格式并注入到配置管理器
        # DataGrouper 需要从 config_manager.get_config("sensor_groups") 获取配置
        if sensor_mapping:
            # 转换格式：sensor_mapping: {group_name: [col1, col2]} -> sensor_groups: {group_name: {columns: "col1,col2"}}
            sensor_groups_config = {"sensor_groups": {}}
            for group_name, columns in sensor_mapping.items():
                if isinstance(columns, list) and columns:
                    # 将列表转换为逗号分隔的字符串
                    columns_str = ",".join(str(col) for col in columns)
                    sensor_groups_config["sensor_groups"][group_name] = {"columns": columns_str}
            
            # 注入到配置管理器
            config_manager.set_runtime_config("sensor_groups", sensor_groups_config)
            logger.info(f"已注入运行时传感器组配置: {len(sensor_groups_config['sensor_groups'])} 个传感器组")

        # 9. 使用已经应用了输入覆盖的配置
        workflow_def = config
        
        # 计算配置哈希值
        config_hash = calculate_config_hash(workflow_def)
        
        # 尝试从缓存获取工作流执行计划
        execution_plan = workflow_cache.get(request.workflow_id, config_hash)
        
        # 创建工作流构建器（无论是否使用缓存都需要）
        builder = WorkflowBuilder(config_manager)
        
        if execution_plan is None:
            # 缓存未命中，构建新的工作流执行计划
            logger.debug(f"缓存未命中，构建工作流: {request.workflow_id}")
            execution_plan = builder.build(workflow_def, request.workflow_id)
            
            # 缓存工作流执行计划
            workflow_cache.put(request.workflow_id, config_hash, execution_plan)
            logger.debug(f"工作流已缓存: {request.workflow_id}")
        else:
            logger.debug(f"缓存命中，使用缓存的工作流: {request.workflow_id}")
        
        logger.info("工作流构建完成")
        
        # 执行工作流
        logger.info("\n开始执行工作流...")
        orchestrator = WorkflowOrchestrator(config_manager)
        
        # 创建工作流上下文（从配置中获取输入参数）
        context = builder.create_workflow_context(execution_plan, workflow_def)
        
        # 准备传递给工作流的参数
        workflow_parameters = config.get("parameters", {})
        
        # 添加请求时间到参数中
        request_time = datetime.now()
        workflow_parameters["request_time"] = request_time.isoformat()
        
        # 将工作流参数添加到上下文中
        for key, value in workflow_parameters.items():
            context[key] = value
        
        # 将绑定后的规范配置添加到上下文中（如果存在）
        if bound_specification:
            context["bound_specification"] = bound_specification
        
        logger.info(f"传递给工作流的参数: {workflow_parameters}")
        
        result = orchestrator.execute(execution_plan, context)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        if result["success"]:
            logger.info(f"\nAPI 响应: 工作流执行成功")
            result_data = result["result"]
            logger.info(f"结果类型: {type(result_data)}")
            if isinstance(result_data, str):
                logger.info(f"结果路径: {result_data}")
                result_path = result_data
            else:
                logger.info(f"结果数据: {result_data}")
                result_path = "内存中的结果数据"
            logger.info(f"总执行时间: {execution_time:.2f} 秒")
            return WorkflowResponse(
                status="success",
                execution_time=execution_time,
                result_path=result_path,
                workflow_name=request.workflow_id,
                message="工作流执行成功"
            )
        else:
            logger.error(f"\nAPI 响应: 工作流执行失败")
            logger.error(f"错误信息: {result['error']}")
            logger.error(f"执行时间: {execution_time:.2f} 秒")
            return WorkflowResponse(
                status="error",
                execution_time=execution_time,
                workflow_name=request.workflow_id,
                error_code="EXECUTION_ERROR",
                error_message=result["error"],
                message="工作流执行失败"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"\nAPI 异常: {e}")
        logger.error(f"执行时间: {execution_time:.2f} 秒")
        return WorkflowResponse(
            status="error",
            execution_time=execution_time,
            workflow_name=request.workflow_name,
            error_code="SYSTEM_ERROR",
            error_message=str(e),
            message="系统错误"
        )


@app.get("/health")
async def health_check():
    """健康检查。"""
    try:
        cache_stats = workflow_cache.stats()
    except Exception as e:
        cache_stats = {"error": str(e)}
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "workflows_loaded": len(workflow_registry),
        "cache_stats": cache_stats
    }


@app.get("/data-flow/statistics")
async def get_data_flow_statistics():
    """获取数据流统计信息。"""
    try:
        # 这里需要从全局orchestrator获取统计信息
        # 由于当前架构限制，返回示例数据
        return {
            "status": "success",
            "message": "数据流统计信息",
            "data": {
                "total_events": 0,
                "total_topics": 0,
                "total_data_size_bytes": 0,
                "error_count": 0,
                "node_count": 0,
                "edge_count": 0,
                "topics": [],
                "source_tasks": []
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取数据流统计信息失败: {e}"
        }


@app.get("/data-flow/metrics/{topic}")
async def get_data_flow_metrics(topic: str):
    """获取指定主题的数据流指标。"""
    try:
        # 这里需要从全局orchestrator获取指标信息
        return {
            "status": "success",
            "message": f"主题 {topic} 的数据流指标",
            "data": {
                "topic": topic,
                "event_count": 0,
                "last_event_time": 0,
                "avg_processing_time": 0.0,
                "source_tasks": [],
                "data_size_bytes": 0,
                "error_count": 0
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取主题 {topic} 指标失败: {e}"
        }


@app.get("/data-flow/graph")
async def get_data_flow_graph():
    """获取数据流图。"""
    try:
        return {
            "status": "success",
            "message": "数据流图",
            "data": {
                "nodes": [],
                "edges": [],
                "metrics": {}
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取数据流图失败: {e}"
        }


def main(startup_config_path: str = "config/startup_config.yaml", log_level: str = None):
    """启动OPLib工作流API服务。"""
    # 解析并检查启动配置文件（支持仓库根目录与环境变量回退）
    resolved_path = Path(startup_config_path)
    if not resolved_path.exists():
        # 优先使用显式环境变量（文件路径优先）
        env_file = os.getenv("OPLIB_CONFIG")
        if env_file and Path(env_file).exists():
            resolved_path = Path(env_file)
        else:
            env_dir = os.getenv("OPLIB_CONFIG_DIR")
            if env_dir and Path(env_dir).exists():
                candidate = Path(env_dir) / "startup_config.yaml"
                if candidate.exists():
                    resolved_path = candidate
            # 向上查找仓库根目录的 config/startup_config.yaml
            if not resolved_path.exists():
                found = _find_startup_config_fallback()
                if found:
                    resolved_path = Path(found)
    if not resolved_path.exists():
        print(f"错误: 启动配置文件不存在: {startup_config_path}")
        print("提示: 可设置环境变量 OPLIB_CONFIG 或 OPLIB_CONFIG_DIR，或使用 --config 指定绝对路径。")
        return
    # 使用解析后的路径
    startup_config_path = str(resolved_path)
    
    # 初始化配置管理器（只初始化一次）
    try:
        config_manager = ConfigManager(startup_config_path)
        startup_params = config_manager.get_startup_params()
    except Exception as e:
        print(f"无法初始化配置管理器: {e}")
        return
    
    # 如果未指定日志级别，从配置文件读取
    if log_level is None:
        log_level = startup_params.get('log_level', 'info')
    
    # 设置日志级别
    setup_logging(log_level)
    
    logger.info("=" * 50)
    logger.info("OPLib 工作流API服务")
    logger.info("=" * 50)
    logger.info(f"使用启动配置: {startup_config_path}")
    logger.info(f"基础目录: {startup_params['base_dir']}")
    logger.info(f"调试模式: {startup_params['debug']}")
    logger.info(f"服务地址: {startup_params['host']}:{startup_params['port']}")
    
    # 预加载工作流注册表
    logger.info("正在启动 OPLib 工作流API服务...")
    load_workflow_registry(startup_config_path)
    logger.info(f"服务启动完成，已加载 {len(workflow_registry)} 个工作流配置")
    
    logger.info("\n启动服务...")
    logger.info(f"API文档: http://{startup_params['host']}:{startup_params['port']}/docs")
    logger.info("按 Ctrl+C 停止服务")
    logger.info("=" * 50)
    
    import uvicorn
    from .utils.port_utils import ensure_port_available

    # 启动前检查端口占用并按需处理
    try:
        auto_kill = startup_params.get('auto_kill_on_port_conflict', False)
        port_in_use_pids = ensure_port_available(startup_params['port'], auto_kill=auto_kill)
        if port_in_use_pids:
            if auto_kill:
                logger.warning(f"端口 {startup_params['port']} 被占用，已尝试终止进程: {port_in_use_pids}")
            else:
                logger.error(f"端口 {startup_params['port']} 被占用，PID: {port_in_use_pids}。可在启动配置中开启 auto_kill_on_port_conflict 后自动处理。")
                return
    except Exception as e:
        logger.error(f"端口可用性检查失败: {e}")
        # 若检查失败，继续尝试启动，由 uvicorn 报错
    
    # 启动uvicorn服务器
    try:
        uvicorn.run(
            app,
            host=startup_params['host'],
            port=startup_params['port'],
            reload=startup_params['reload'],
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("\n服务已停止")
    except Exception as e:
        logger.error(f"启动服务失败: {e}")

if __name__ == "__main__":
    import argparse
    import sys
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="启动OPLib工作流API服务")
    parser.add_argument(
        "--config", 
        default="config/startup_config.yaml",
        help="启动配置文件路径 (默认: config/startup_config.yaml)"
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default=None,
        help="日志级别 (覆盖配置文件设置，不指定则使用配置文件)"
    )
    
    args = parser.parse_args()
    
    try:
        print("OPLib 工作流API服务")
        print("=" * 40)
        print(f"配置文件: {args.config}")
        if args.log_level:
            print(f"日志级别: {args.log_level} (命令行指定)")
        else:
            print("日志级别: 从配置文件读取")
        print("=" * 40)
        
        main(startup_config_path=args.config, log_level=args.log_level)
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)
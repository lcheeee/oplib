"""OPLib 主程序入口 - 工作流API服务。"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from src.workflow.builder import WorkflowBuilder
from src.workflow.orchestrator import WorkflowOrchestrator
from src.workflow.cache import workflow_cache, calculate_config_hash
from src.config.manager import ConfigManager
from src.core.exceptions import WorkflowError, ConfigurationError
from src.utils.logging_config import setup_logging, get_logger

# 全局变量存储工作流注册表和配置管理器
workflow_registry = {}
config_manager = None
logger = get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。"""
    # 启动时执行
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
    """工作流参数模型。"""
    process_id: str | None = None
    series_id: Optional[str] = None
    specification: Optional[str] = None
    material: Optional[str] = None
    atmosphere_control: Optional[bool] = None
    thermocouples: Optional[list[str]] = None
    vacuum_lines: Optional[list[str]] = None
    leading_thermocouples: Optional[list[str]] = None
    lagging_thermocouples: Optional[list[str]] = None
    calculation_date: Optional[str] = None

class WorkflowInputs(BaseModel):
    """工作流输入数据模型。"""
    file_path: Optional[str] = None
    online_data: Optional[bool] = None

class WorkflowRequest(BaseModel):
    """工作流请求模型。"""
    workflow_name: str
    parameters: Optional[WorkflowParameters] = None
    inputs: Optional[WorkflowInputs] = None

class WorkflowResponse(BaseModel):
    """工作流响应模型。"""
    status: str
    execution_time: float
    result_path: Optional[str] = None
    workflow_name: str
    message: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None


def load_workflow_registry(startup_config_path: str = "config/startup_config.yaml"):
    """加载工作流注册表。"""
    global workflow_registry, config_manager
    
    try:
        # 初始化配置管理器
        config_manager = ConfigManager(startup_config_path)
        
        # 从配置管理器获取工作流配置
        workflow_config = config_manager.get_workflow_config()
        
        # 配置工作流缓存大小
        cache_size = workflow_config.get("cache", {}).get("max_workflows", 2)
        workflow_cache.max_size = cache_size
        logger.info(f"工作流缓存大小设置为: {cache_size}")
        
        if "workflows" in workflow_config:
            for workflow_name, workflow_def in workflow_config["workflows"].items():
                workflow_registry[workflow_name] = {
                    "config_file": config_manager.get_config_path("workflow_config"),
                    "version": workflow_config.get("version", "v1"),
                    "description": workflow_def.get("description", f"工作流: {workflow_name}"),
                    "config": workflow_def
                }
                logger.info(f"已加载工作流: {workflow_name}")
        
        startup_params = config_manager.get_startup_params()
        logger.info("配置管理器初始化完成")
        logger.info(f"基础目录: {startup_params['base_dir']}")
        logger.info(f"调试模式: {startup_params['debug']}")
        logger.info(f"服务地址: {startup_params['host']}:{startup_params['port']}")
        
    except Exception as e:
        logger.error(f"加载工作流配置失败: {e}")
        raise

def get_workflow_config(workflow_name: str) -> Dict[str, Any]:
    """获取工作流配置。"""
    if workflow_name not in workflow_registry:
        raise HTTPException(
            status_code=404,
            detail=f"工作流 '{workflow_name}' 不存在"
        )
    
    return workflow_registry[workflow_name]

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
    """执行工作流。"""
    start_time = datetime.now()
    
    logger.info(f"\n收到工作流执行请求")
    logger.info(f"工作流名称: {request.workflow_name}")
    if request.parameters:
        logger.info(f"参数: {request.parameters}")
    if request.inputs:
        logger.info(f"输入: {request.inputs}")
    
    try:
        # 获取工作流配置
        logger.info("\n获取工作流配置...")
        workflow_info = get_workflow_config(request.workflow_name)
        config = workflow_info["config"].copy()
        logger.info("工作流配置获取成功")
        
        # 应用参数覆盖
        logger.info("应用参数覆盖...")
        config = apply_parameter_overrides(config, request.parameters)
        
        # 应用输入覆盖
        logger.info("应用输入覆盖...")
        logger.debug(f"request.inputs: {request.inputs}")
        config = apply_input_overrides(config, request.inputs)
        logger.info(f"应用输入覆盖后的配置: {config}")
        
        # 验证参数并应用默认值
        logger.info("验证参数并应用默认值...")
        config = validate_and_apply_defaults(config)
        
        # 验证输入文件
        if request.inputs and request.inputs.file_path:
            # 规范化路径分隔符，避免控制台显示问题
            normalized_path = request.inputs.file_path.replace('\\', '/')
            logger.info(f"验证输入文件: {normalized_path}")
            
            # 使用路径解析工具来正确处理相对路径
            from .utils.path_utils import resolve_path
            if config_manager:
                base_dir = config_manager.get_startup_params().get('base_dir', '.')
                resolved_path = resolve_path(base_dir, normalized_path)
                logger.info(f"解析后的文件路径: {resolved_path}")
                
                if not Path(resolved_path).exists():
                    raise HTTPException(
                        status_code=400,
                        detail=f"输入文件不存在: {resolved_path}"
                    )
            else:
                # 回退到直接检查
                if not Path(normalized_path).exists():
                    raise HTTPException(
                        status_code=400,
                        detail=f"输入文件不存在: {normalized_path}"
                    )
            logger.info("输入文件验证通过")
        
        # 构建工作流（使用缓存）
        logger.info("\n构建工作流...")
        if config_manager is None:
            raise HTTPException(status_code=500, detail="配置管理器未初始化")
        
        # 使用已经应用了输入覆盖的配置
        workflow_def = config
        
        # 计算配置哈希值
        config_hash = calculate_config_hash(workflow_def)
        
        # 尝试从缓存获取工作流执行计划
        execution_plan = workflow_cache.get(request.workflow_name, config_hash)
        
        # 创建工作流构建器（无论是否使用缓存都需要）
        builder = WorkflowBuilder(config_manager)
        
        if execution_plan is None:
            # 缓存未命中，构建新的工作流执行计划
            logger.debug(f"缓存未命中，构建工作流: {request.workflow_name}")
            execution_plan = builder.build(workflow_def, request.workflow_name)
            
            # 缓存工作流执行计划
            workflow_cache.put(request.workflow_name, config_hash, execution_plan)
            logger.debug(f"工作流已缓存: {request.workflow_name}")
        else:
            logger.debug(f"缓存命中，使用缓存的工作流: {request.workflow_name}")
        
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
                workflow_name=request.workflow_name,
                message="工作流执行成功"
            )
        else:
            logger.error(f"\nAPI 响应: 工作流执行失败")
            logger.error(f"错误信息: {result['error']}")
            logger.error(f"执行时间: {execution_time:.2f} 秒")
            return WorkflowResponse(
                status="error",
                execution_time=execution_time,
                workflow_name=request.workflow_name,
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


def main(startup_config_path: str = "config/startup_config.yaml", log_level: str = None):
    """启动OPLib工作流API服务。"""
    # 检查启动配置文件
    startup_config_file = Path(startup_config_path)
    if not startup_config_file.exists():
        print(f"错误: 启动配置文件不存在: {startup_config_path}")
        return
    
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
    load_workflow_registry()
    logger.info(f"服务启动完成，已加载 {len(workflow_registry)} 个工作流配置")
    
    logger.info("\n启动服务...")
    logger.info(f"API文档: http://{startup_params['host']}:{startup_params['port']}/docs")
    logger.info("按 Ctrl+C 停止服务")
    logger.info("=" * 50)
    
    import uvicorn
    from src.utils.port_utils import ensure_port_available

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
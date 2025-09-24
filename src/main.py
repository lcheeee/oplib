"""OPLib 主程序入口 - 工作流API服务。"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from pathlib import Path
import yaml
from datetime import datetime

from src.workflow.builder import WorkflowBuilder
from src.workflow.executor import WorkflowExecutor
from src.core.exceptions import WorkflowError, ConfigurationError

app = FastAPI(
    title="OPLib 工作流API",
    description="工业传感器数据分析工作流API服务",
    version="2.0.0"
)

# 全局变量存储工作流注册表
workflow_registry = {}

class InputData(BaseModel):
    """输入数据模型。"""
    file_path: Optional[str] = None
    process_id: Optional[str] = None

class ParametersOverride(BaseModel):
    """参数覆盖模型。"""
    max_std: Optional[float] = None
    rule_id: Optional[str] = None
    output_format: Optional[str] = None

class WorkflowRequest(BaseModel):
    """工作流请求模型。"""
    workflow_name: str
    input_data: Optional[InputData] = None
    parameters_override: Optional[ParametersOverride] = None

class WorkflowResponse(BaseModel):
    """工作流响应模型。"""
    status: str
    execution_time: float
    result_path: Optional[str] = None
    workflow_name: str
    message: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None

class WorkflowInfo(BaseModel):
    """工作流信息模型。"""
    name: str
    description: str
    version: str
    process_id: str
    config_file: str

def load_workflow_registry():
    """加载工作流注册表。"""
    global workflow_registry
    
    # 扫描config目录下的所有工作流配置文件
    config_dir = Path("config")
    if not config_dir.exists():
        print("警告: config目录不存在")
        return
    
    for yaml_file in config_dir.glob("*.yaml"):
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                
            if "name" in config:
                workflow_name = config["name"]
                workflow_registry[workflow_name] = {
                    "config_file": str(yaml_file),
                    "version": config.get("version", "v1"),
                    "process_id": config.get("process_id", ""),
                    "description": config.get("description", f"工作流: {workflow_name}"),
                    "config": config
                }
                print(f"已加载工作流: {workflow_name}")
        except Exception as e:
            print(f"加载工作流配置失败 {yaml_file}: {e}")

def get_workflow_config(workflow_name: str) -> Dict[str, Any]:
    """获取工作流配置。"""
    if workflow_name not in workflow_registry:
        raise HTTPException(
            status_code=404,
            detail=f"工作流 '{workflow_name}' 不存在"
        )
    
    return workflow_registry[workflow_name]

def apply_parameter_overrides(config: Dict[str, Any], overrides: Optional[ParametersOverride]) -> Dict[str, Any]:
    """应用参数覆盖。"""
    if not overrides:
        return config
    
    # 创建配置副本
    updated_config = config.copy()
    
    # 递归更新节点参数
    if "nodes" in updated_config:
        for node in updated_config["nodes"]:
            if "parameters_override" not in node:
                node["parameters_override"] = {}
            
            # 应用参数覆盖
            if overrides.max_std is not None:
                if "params" not in node["parameters_override"]:
                    node["parameters_override"]["params"] = {}
                node["parameters_override"]["params"]["max_std"] = overrides.max_std
            
            if overrides.rule_id is not None:
                node["parameters_override"]["rule_id"] = overrides.rule_id
    
    return updated_config

def apply_input_data_overrides(config: Dict[str, Any], input_data: Optional[InputData]) -> Dict[str, Any]:
    """应用输入数据覆盖。"""
    if not input_data:
        return config
    
    # 创建配置副本
    updated_config = config.copy()
    
    # 更新输入文件路径
    if input_data.file_path and "inputs" in updated_config:
        for input_node in updated_config["inputs"]:
            if "config" in input_node and "file_path" in input_node["config"]:
                input_node["config"]["file_path"] = input_data.file_path
    
    # 更新process_id
    if input_data.process_id:
        updated_config["process_id"] = input_data.process_id
        
        # 同时更新节点中的process_id
        if "nodes" in updated_config:
            for node in updated_config["nodes"]:
                if "parameters_override" in node and "process_id" in node["parameters_override"]:
                    node["parameters_override"]["process_id"] = input_data.process_id
    
    return updated_config

@app.on_event("startup")
async def startup_event():
    """应用启动时加载工作流注册表。"""
    print("正在启动 OPLib 工作流API服务...")
    load_workflow_registry()
    print(f"服务启动完成，已加载 {len(workflow_registry)} 个工作流配置")

@app.post("/run", response_model=WorkflowResponse)
async def run_workflow(request: WorkflowRequest):
    """执行工作流。"""
    start_time = datetime.now()
    
    try:
        # 获取工作流配置
        workflow_info = get_workflow_config(request.workflow_name)
        config = workflow_info["config"].copy()
        
        # 应用输入数据覆盖
        config = apply_input_data_overrides(config, request.input_data)
        
        # 应用参数覆盖
        config = apply_parameter_overrides(config, request.parameters_override)
        
        # 验证输入文件
        if request.input_data and request.input_data.file_path:
            if not Path(request.input_data.file_path).exists():
                raise HTTPException(
                    status_code=400,
                    detail=f"输入文件不存在: {request.input_data.file_path}"
                )
        
        # 构建工作流
        builder = WorkflowBuilder(base_dir=str(Path.cwd()))
        flow_fn = builder.build(
            workflow_yaml=workflow_info["config_file"],
            operators_yaml="resources/operators.yaml",
            rules_yaml="resources/rules.yaml"
        )
        
        # 执行工作流
        executor = WorkflowExecutor()
        result = executor.execute_with_monitoring(flow_fn)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        if result["success"]:
            return WorkflowResponse(
                status="success",
                execution_time=execution_time,
                result_path=result["result"],
                workflow_name=request.workflow_name,
                message="工作流执行成功"
            )
        else:
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
        return WorkflowResponse(
            status="error",
            execution_time=execution_time,
            workflow_name=request.workflow_name,
            error_code="SYSTEM_ERROR",
            error_message=str(e),
            message="系统错误"
        )

@app.get("/workflows", response_model=List[WorkflowInfo])
async def list_workflows():
    """获取可用工作流列表。"""
    workflows = []
    for name, info in workflow_registry.items():
        workflows.append(WorkflowInfo(
            name=name,
            description=info["description"],
            version=info["version"],
            process_id=info["process_id"],
            config_file=info["config_file"]
        ))
    return workflows

@app.get("/workflows/{workflow_name}", response_model=WorkflowInfo)
async def get_workflow_info(workflow_name: str):
    """获取工作流详情。"""
    workflow_info = get_workflow_config(workflow_name)
    return WorkflowInfo(
        name=workflow_name,
        description=workflow_info["description"],
        version=workflow_info["version"],
        process_id=workflow_info["process_id"],
        config_file=workflow_info["config_file"]
    )

@app.get("/health")
async def health_check():
    """健康检查。"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "workflows_loaded": len(workflow_registry)
    }

if __name__ == "__main__":
    import uvicorn
    print("启动 OPLib 工作流API服务...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
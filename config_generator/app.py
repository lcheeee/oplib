from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 兼容脚本运行与包运行的导入方式
try:
    from .rule_generator import RuleGenerator  # 包方式：python -m config_generator.app
except Exception:  # pragma: no cover
    import sys, os
    # 将项目根目录加入 sys.path，以支持脚本方式：python config_generator/app.py
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from config_generator.rule_generator import RuleGenerator  # 脚本方式导入


app = FastAPI(
    title="OPLib 规范生成API",
    description="基于模板生成规范规则与阶段配置的服务",
    version="1.0.0",
)


class RuleInput(BaseModel):
    template_id: Optional[str] = None
    rule_id: str
    description: Optional[str] = None
    severity: Optional[str] = None
    parameters: Dict[str, Any]


class StageItem(BaseModel):
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None
    # 阶段识别类型：支持 "time", "rule", "temperature" 等
    type: Optional[str] = None  # "time", "rule", "temperature"
    
    # 基于时间的阶段识别配置
    time_range: Optional[Dict[str, Any]] = None  # {"start": "...", "end": "..."}
    unit: Optional[str] = None  # "datetime", "timestamp", "minutes" 等
    
    # 基于规则触发的阶段识别配置
    trigger_rule: Optional[str] = None  # 触发规则ID
    
    # 基于温度范围的阶段识别配置
    temperature_range: Optional[Dict[str, Any]] = None  # {"min_temp": ..., "max_temp": ...}
    
    # 基于算法的阶段识别配置（未来扩展）
    algorithm: Optional[str] = None  # 算法名称
    algorithm_params: Optional[Dict[str, Any]] = None  # 算法参数


class RuleGenerationRequest(BaseModel):
    specification_id: str
    workflow_name: Optional[str] = None  # 生成端不强校验工作流，仅透传
    version: Optional[str] = None
    process_type: str = "curing"  # 工艺类型，如 "curing"（固化工艺），默认为 "curing"
    stages: Optional[Dict[str, Any]] = None  # 改为 Dict[str, Any] 以匹配 {"items": [...]} 结构
    sensors: Optional[Dict[str, List[str]]] = None
    rule_inputs: List[RuleInput]
    publish: bool = True


class RuleGenerationResponse(BaseModel):
    status: str
    message: str
    preview: Optional[Dict[str, Any]] = None
    files: Optional[Dict[str, str]] = None


@app.post("/api/rules/generate", response_model=RuleGenerationResponse)
async def generate_rules(payload: RuleGenerationRequest):
    try:
        # 输出根目录优先取环境变量 OPLIB_PROJECT_ROOT，其次自动定位为仓库根
        project_root = os.getenv("OPLIB_PROJECT_ROOT")
        if project_root:
            base = Path(project_root).resolve()
        else:
            base = Path(__file__).resolve().parents[1]
        
        # 调试日志：输出项目根目录
        print(f"[DEBUG] 项目根目录: {base}")
        print(f"[DEBUG] 目标规范目录: {base / 'config' / 'specifications' / payload.specification_id}")
        
        generator = RuleGenerator(project_root=base, process_type=payload.process_type)
        stages_input = None
        if payload.stages and isinstance(payload.stages, dict):
            items = payload.stages.get("items") or payload.stages.get("stages") or []
            # 处理 items：可能是字典列表（Pydantic 解析后）或已经是字典
            if items:
                stages_list = []
                for item in items:
                    if isinstance(item, dict):
                        # 已经是字典，直接使用
                        stages_list.append(item)
                    elif hasattr(item, 'dict'):
                        # 是 Pydantic 模型，转换为字典
                        stages_list.append(item.dict(exclude_unset=True))
                    else:
                        # 其他情况，尝试转换
                        stages_list.append(item)
                stages_input = {"items": stages_list}
            else:
                stages_input = None

        rules_doc, stages_doc, files = generator.generate(
            specification_id=payload.specification_id,
            stages_input=stages_input,
            rule_inputs=[ri.dict(exclude_unset=True) for ri in payload.rule_inputs],
            publish=payload.publish,
            version=payload.version,
        )

        if payload.publish:
            return RuleGenerationResponse(
                status="success",
                message="规则与阶段已生成并覆盖写入",
                files=files,
            )
        else:
            return RuleGenerationResponse(
                status="success",
                message="规则与阶段生成预览",
                preview={"rules": rules_doc, "stages": stages_doc},
            )
    except ValueError as e:
        # 参数验证错误
        import traceback
        error_detail = f"参数验证失败: {str(e)}\n详细错误: {traceback.format_exc()}"
        raise HTTPException(status_code=400, detail=error_detail)
    except FileNotFoundError as e:
        # 文件或目录不存在
        templates_dir = Path(__file__).resolve().parents[1] / "config" / "templates" / payload.process_type
        error_detail = f"文件或目录不存在: {str(e)}\n请检查模板目录是否存在: {templates_dir}"
        raise HTTPException(status_code=400, detail=error_detail)
    except Exception as e:
        # 其他错误
        import traceback
        error_detail = f"规则生成失败: {str(e)}\n错误类型: {type(e).__name__}\n详细错误: {traceback.format_exc()}"
        raise HTTPException(status_code=400, detail=error_detail)


def main(host: str = "0.0.0.0", port: int = 8100, reload: bool = False) -> None:
    import uvicorn

    uvicorn.run(app, host=host, port=port, reload=reload, access_log=True)


if __name__ == "__main__":
    main()



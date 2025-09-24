"""工作流构建器。"""

import os
from typing import Any, Dict, List, Callable, Tuple, Set
from pathlib import Path

# 兼容无 _sqlite3 的环境：使用 pysqlite3 替代
try:
    import sqlite3  # noqa: F401
except Exception:  # pragma: no cover
    try:
        import pysqlite3 as sqlite3  # type: ignore
        import sys
        sys.modules["sqlite3"] = sqlite3
    except Exception:
        pass

from prefect import flow, task

from ..config.loader import ConfigLoader
from ..core.exceptions import WorkflowError
from ..utils.path_utils import resolve_path
from ..data.readers.factory import DataReaderFactory
from ..data.processors.factory import DataProcessorFactory
from ..analysis.process_mining.factory import ProcessMiningFactory
from ..analysis.rule_engine.factory import RuleEngineFactory
from ..analysis.spc.factory import SPCFactory
from ..reporting.generators import ReportGenerator
from ..reporting.writers import ReportWriterFactory


class WorkflowBuilder:
    """工作流构建器。"""
    
    def __init__(self, base_dir: str) -> None:
        self.base_dir = base_dir
        self.config_loader = ConfigLoader(base_dir)
        self.operators_index = {}
        self.rules_index = {}
    
    def _import_impl(self, module: str, class_name: str) -> Callable[..., Any]:
        """动态导入实现类。"""
        import importlib
        mod = importlib.import_module(module)
        cls = getattr(mod, class_name)
        return cls
    
    def _ref_to_node_id(self, ref: str) -> str:
        """解析节点引用。"""
        return ref.split(".", 1)[0]
    
    def _collect_nodes(self, wf_cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
        """收集所有节点。"""
        nodes: List[Dict[str, Any]] = []
        
        # 输入节点
        for inp in wf_cfg.get("inputs", []) or []:
            item = {**inp}
            item["id"] = inp["id"]
            item["type"] = "input"
            nodes.append(item)
        
        # 处理节点
        for n in wf_cfg.get("nodes", []) or []:
            nodes.append(n)
        
        # 输出节点
        for outp in wf_cfg.get("outputs", []) or []:
            item = {**outp}
            item["id"] = outp["id"]
            item["type"] = "output"
            nodes.append(item)
        
        return nodes
    
    def _build_graph(self, nodes: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
        """构建依赖图。"""
        deps: Dict[str, Set[str]] = {}
        
        for n in nodes:
            nid = n["id"]
            up: Set[str] = set()
            
            if "input" in n and isinstance(n["input"], str):
                up.add(self._ref_to_node_id(n["input"]))
            
            if "inputs" in n and isinstance(n["inputs"], list):
                for r in n["inputs"]:
                    if isinstance(r, str):
                        up.add(self._ref_to_node_id(r))
            
            deps[nid] = up
        
        return deps
    
    def _topo_sort(self, deps: Dict[str, Set[str]]) -> List[str]:
        """拓扑排序。"""
        from collections import deque
        
        in_deg: Dict[str, int] = {k: len(v) for k, v in deps.items()}
        queue = deque([k for k, d in in_deg.items() if d == 0])
        order: List[str] = []
        
        while queue:
            n = queue.popleft()
            order.append(n)
            
            for m, up in deps.items():
                if n in up:
                    in_deg[m] -= 1
                    if in_deg[m] == 0:
                        queue.append(m)
        
        if len(order) != len(deps):
            raise WorkflowError("DAG 中存在环或未解析的依赖")
        
        return order
    
    def _resolve_inputs(self, n: Dict[str, Any], results: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Any]]:
        """解析节点输入。"""
        kwargs_inputs: Dict[str, Any] = {}
        list_inputs: List[Any] = []
        
        if "input" in n and isinstance(n["input"], str):
            up_id = self._ref_to_node_id(n["input"])
            list_inputs.append(results[up_id])
        
        if "inputs" in n and isinstance(n["inputs"], list):
            for r in n["inputs"]:
                up_id = self._ref_to_node_id(r)
                list_inputs.append(results[up_id])
        
        return kwargs_inputs, list_inputs
    
    def _build_payload_for_operator(self, n: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """构建算子载荷。"""
        kwargs_inputs, list_inputs = self._resolve_inputs(n, results)
        operator_id = n.get("operator_id")
        params = n.get("parameters_override") or {}
        
        # 特殊处理不同算子的参数格式
        op_def = self.operators_index.get(operator_id, {})
        cls_name = (op_def.get("implementation") or {}).get("class_name")
        
        inputs_dict: Dict[str, Any] = {}
        
        if cls_name == "ReportGenerator":
            # ReportGenerator 需要命名参数
            inputs_dict = {
                "rule_result": list_inputs[0] if len(list_inputs) > 0 else None,
                "spc": list_inputs[1] if len(list_inputs) > 1 else None,
                "model": list_inputs[2] if len(list_inputs) > 2 else None
            }
        elif cls_name == "RuleEvaluator":
            # RuleEvaluator 直接接收数据，不需要包装
            if len(list_inputs) == 1:
                return {"data": list_inputs[0], "params": params}
            else:
                inputs_dict = {"data": list_inputs[0]}
        elif cls_name in ["SensorGroupAggregator", "TimeBasedStageDetector"]:
            # 这些算子需要 process_id 参数
            if len(list_inputs) == 1:
                inputs_dict = {"data": list_inputs[0]}
            else:
                inputs_dict = {"data": list_inputs[0] if list_inputs else {}}
            # 确保 process_id 被传递到 params 中
            if "process_id" not in params:
                params["process_id"] = "curing_001"
        else:
            # 其他算子的通用处理
            if len(list_inputs) == 1:
                inputs_dict = {"data": list_inputs[0]}
            elif len(list_inputs) > 1:
                inputs_dict = {"inputs": list_inputs}
        
        # 兼容 kwargs_inputs（当前未用）
        inputs_dict.update(kwargs_inputs)
        return {"inputs": inputs_dict, "params": params}
    
    def build(self, workflow_yaml: str, operators_yaml: str, rules_yaml: str) -> Callable:
        """构建工作流。"""
        # 加载配置
        wf_cfg = self.config_loader.load_workflow_config(workflow_yaml)
        self.operators_index = {op["id"]: op for op in self.config_loader.load_operators_config(operators_yaml).get("operators", [])}
        self.rules_index = {r["id"]: r for r in self.config_loader.load_rules_config(rules_yaml).get("rules", [])}
        
        # 构建节点和依赖图
        nodes = self._collect_nodes(wf_cfg)
        deps = self._build_graph(nodes)
        order = self._topo_sort(deps)
        id_to_node = {n["id"]: n for n in nodes}
        
        @task
        def task_input(node: Dict[str, Any]) -> Any:
            """输入任务。"""
            cfg = node.get("config", {})
            file_path = cfg.get("file_path")
            path = resolve_path(self.base_dir, file_path)
            
            # 使用数据读取器工厂
            reader = DataReaderFactory.create_reader("csv")
            return reader.read(path)
        
        @task
        def run_operator(op_id: str, payload: Dict[str, Any]) -> Any:
            """运行算子任务。"""
            op_def = self.operators_index[op_id]
            module = op_def["implementation"]["module"]
            class_name = op_def["implementation"]["class_name"]
            impl = self._import_impl(f"src.{module}", class_name)
            
            # 特殊处理需要额外配置的算子
            if class_name == "RuleEvaluator":
                instance = impl(rules_index=self.rules_index, **payload.get("params", {}))
                if "data" in payload:
                    return instance.run(payload["data"])
                else:
                    return instance.run(**payload["inputs"])
            elif class_name == "SensorGroupAggregator":
                instance = impl(process_stages_yaml=rules_yaml.replace("rules.yaml", "process_stages.yaml"), **payload.get("params", {}))
            elif class_name == "TimeBasedStageDetector":
                instance = impl(process_stages_yaml=rules_yaml.replace("rules.yaml", "process_stages.yaml"), **payload.get("params", {}))
            else:
                instance = impl(**payload.get("params", {}))
            
            return instance.run(**payload["inputs"])
        
        @task
        def write_result(path: str, content: Dict[str, Any]) -> str:
            """写入结果任务。"""
            writer = ReportWriterFactory.create_writer("file", file_path=path)
            return writer.run(content=content)
        
        @flow(name=wf_cfg.get("name", "demo_flow"))
        def demo_flow() -> str:
            """工作流主函数。"""
            results: Dict[str, Any] = {}
            
            for nid in order:
                n = id_to_node[nid]
                n_type = n.get("type", "operator")
                
                if n_type == "input":
                    results[nid] = task_input.submit(n)
                    continue
                
                if n_type == "operator" or (n_type not in {"input", "output"}):
                    payload = self._build_payload_for_operator(n, {k: v.result() if hasattr(v, "result") else v for k, v in results.items()})
                    results[nid] = run_operator.submit(n["operator_id"], payload)
                    continue
                
                if n_type == "output":
                    # 输出节点：写文件
                    out_ref = n.get("input") or (n.get("inputs") or [None])[0]
                    up_id = self._ref_to_node_id(out_ref)
                    content = results[up_id].result() if hasattr(results[up_id], "result") else results[up_id]
                    cfg = n.get("config", {})
                    orig_rel = cfg.get("file_path", "quality-reports.json")
                    base_path = Path(resolve_path(self.base_dir, orig_rel))
                    
                    # 追加 flow_run.id 或时间戳，做结果隔离
                    try:
                        from prefect.context import get_run_context
                        ctx = get_run_context()
                        run_id = str(getattr(ctx.flow_run, "id", "")) if ctx else ""
                    except Exception:
                        run_id = ""
                    
                    from datetime import datetime
                    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                    suffix = run_id or timestamp
                    isolated_name = f"{base_path.stem}-{suffix}{base_path.suffix}" if suffix else base_path.name
                    out_path = str(base_path.with_name(isolated_name))
                    
                    results[nid] = write_result.submit(out_path, content)
                    continue
            
            # 返回最后一个输出节点的结果路径（若存在），否则返回空串
            last_outputs = [n["id"] for n in nodes if n.get("type") == "output"]
            if last_outputs:
                return results[last_outputs[-1]].result()
            return ""
        
        return demo_flow

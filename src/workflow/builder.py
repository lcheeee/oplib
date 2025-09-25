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

from ..config.manager import ConfigManager
from ..utils.logging_config import get_logger
from ..core.exceptions import WorkflowError
from ..utils.path_utils import resolve_path
from ..data.readers.factory import DataReaderFactory
from ..data.transformers.factory import DataTransformerFactory
from ..data.detectors.factory import StageDetectorFactory
from ..analysis.rule_engine.factory import RuleEngineFactory
from ..analysis.reporting.generators import ReportGenerator
from ..analysis.reporting.writers import ReportWriterFactory


class WorkflowBuilder:
    """工作流构建器。"""
    
    def __init__(self, config_manager: ConfigManager) -> None:
        self.config_manager = config_manager
        self.base_dir = config_manager.base_dir
        self.logger = get_logger()
        self.operators_index = {}
        self.rules_index = {}
    
    def _import_impl(self, module: str, class_name: str) -> Callable[..., Any]:
        """动态导入实现类。"""
        import importlib
        mod = importlib.import_module(module)
        cls = getattr(mod, class_name)
        return cls
    
    
    def _load_operators_from_config(self) -> Dict[str, Any]:
        """从配置文件加载算子定义。"""
        # 直接返回空的算子索引，因为现在算子直接从任务配置中获取
        return {}
    
    def _load_rules_from_config(self) -> Dict[str, Any]:
        """从配置文件加载规则定义。"""
        try:
            rules_config = self.config_manager.get_rules_config()
            return {r["id"]: r for r in rules_config.get("rules", [])}
        except Exception as e:
            self.logger.warning(f"无法加载规则配置: {e}")
            return {}
    
    def _get_module_path(self, implementation: str) -> str:
        """根据实现名称获取模块路径。"""
        implementation_map = {
            "prefect_csv_loader": "data.readers.csv_reader",
            "stage_detector": "data.detectors.stage_detector",
            "sensor_grouper": "data.transformers.aggregator",
            "metric_calculator": "analysis.rule_engine.evaluator",
            "rule_engine_checker": "analysis.rule_engine.evaluator",
            "report_generator": "analysis.reporting.generators"
        }
        return implementation_map.get(implementation, "core.base")
    
    def _get_class_name(self, implementation: str) -> str:
        """根据实现名称获取类名。"""
        implementation_map = {
            "prefect_csv_loader": "CSVReader",
            "stage_detector": "StageDetector",
            "sensor_grouper": "SensorGroupAggregator",
            "metric_calculator": "RuleEvaluator",
            "rule_engine_checker": "RuleEvaluator",
            "report_generator": "ReportGenerator"
        }
        return implementation_map.get(implementation, "BaseOperator")
    
    def _collect_nodes(self, wf_cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
        """收集所有节点。"""
        nodes: List[Dict[str, Any]] = []
        
        # 从 tasks 配置中收集节点
        tasks = wf_cfg.get("tasks", [])
        self.logger.info(f"从配置中获取的任务: {tasks}")
        for task in tasks:
            node = {
                "id": task.get("id"),
                "type": task.get("type", "processing"),
                "implementation": task.get("implementation"),
                "parameters": task.get("parameters", {}),
                "depends_on": task.get("depends_on", [])
            }
            self.logger.info(f"处理任务节点: {node}")
            nodes.append(node)
        
        self.logger.info(f"最终收集到的节点数量: {len(nodes)}")
        return nodes
    
    def _build_graph(self, nodes: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
        """构建依赖图。"""
        deps: Dict[str, Set[str]] = {}
        
        for n in nodes:
            nid = n["id"]
            up: Set[str] = set()
            
            # 处理 depends_on 结构
            depends_on = n.get("depends_on", [])
            if isinstance(depends_on, list):
                for dep in depends_on:
                    if isinstance(dep, str):
                        up.add(dep)
            
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
        
        # 处理 depends_on 结构
        depends_on = n.get("depends_on", [])
        if isinstance(depends_on, list):
            for dep in depends_on:
                if isinstance(dep, str) and dep in results:
                    list_inputs.append(results[dep])
        
        return kwargs_inputs, list_inputs
    
    def _build_payload_for_operator(self, n: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """构建算子载荷。"""
        kwargs_inputs, list_inputs = self._resolve_inputs(n, results)
        operator_id = n.get("id")
        params = n.get("parameters", {})
        
        # 直接从任务配置中获取实现信息
        implementation = n.get("implementation", "")
        cls_name = self._get_class_name(implementation)
        
        inputs_dict: Dict[str, Any] = {}
        
        if cls_name == "ReportGenerator":
            # ReportGenerator 需要命名参数
            inputs_dict = {
                "rule_result": list_inputs[0] if len(list_inputs) > 0 else None,
                "model": list_inputs[1] if len(list_inputs) > 1 else None
            }
        elif cls_name == "RuleEvaluator":
            # RuleEvaluator 直接接收数据，不需要包装
            if len(list_inputs) == 1:
                return {"data": list_inputs[0], "params": params}
            else:
                inputs_dict = {"data": list_inputs[0]}
        elif cls_name in ["SensorGroupAggregator", "StageDetector"]:
            # 这些算子需要 process_id 参数
            if len(list_inputs) == 1:
                inputs_dict = {"data": list_inputs[0]}
            else:
                inputs_dict = {"data": list_inputs[0] if list_inputs else {}}
            # 确保 process_id 被传递到 params 中
            if "process_id" not in params:
                params["process_id"] = "default_process"
        else:
            # 其他算子的通用处理
            if len(list_inputs) == 1:
                inputs_dict = {"data": list_inputs[0]}
            elif len(list_inputs) > 1:
                inputs_dict = {"inputs": list_inputs}
        
        # 兼容 kwargs_inputs（当前未用）
        inputs_dict.update(kwargs_inputs)
        return {"inputs": inputs_dict, "params": params}
    
    def build(self, workflow_config: Dict[str, Any], workflow_name: str = None) -> Callable:
        """构建工作流。"""
        # 从配置中提取工作流定义
        if workflow_name is None:
            workflow_name = workflow_config.get("name", "default_workflow")
        
        # 如果传入的是整个配置，提取特定工作流
        if "workflows" in workflow_config:
            workflow_def = workflow_config.get("workflows", {}).get(workflow_name, {})
        else:
            # 如果传入的已经是工作流定义
            workflow_def = workflow_config
        
        # 加载相关配置文件
        self.operators_index = self._load_operators_from_config()
        self.rules_index = self._load_rules_from_config()
        
        # 使用工作流定义作为主要配置
        wf_cfg = workflow_def
        
        # 构建节点和依赖图
        self.logger.info(f"工作流配置: {wf_cfg}")
        self.logger.info(f"任务配置: {wf_cfg.get('tasks', [])}")
        nodes = self._collect_nodes(wf_cfg)
        self.logger.info(f"收集到的节点: {nodes}")
        deps = self._build_graph(nodes)
        order = self._topo_sort(deps)
        id_to_node = {n["id"]: n for n in nodes}
        
        @task
        def task_input(node: Dict[str, Any]) -> Any:
            """输入任务。"""
            params = node.get("parameters", {})
            file_path = params.get("file_path")
            if not file_path:
                raise WorkflowError(f"输入节点 {node.get('id')} 缺少 file_path 参数")
            
            # 处理模板变量 {input_file}
            if file_path == "{input_file}":
                # 从工作流配置中获取实际的文件路径
                inputs = wf_cfg.get("inputs", {})
                data_source = inputs.get("data_source")
                if not data_source:
                    raise WorkflowError("工作流配置中缺少 data_source 输入")
                file_path = data_source
            
            path = resolve_path(self.base_dir, file_path)
            self.logger.info(f"读取文件: {path}")
            
            # 使用数据读取器工厂
            reader = DataReaderFactory.create_reader("csv")
            data = reader.read(path)
            
            # 输出数据加载完成信息
            self.logger.info(f"✓ 数据加载成功")
            self.logger.info(f"  - 数据列数: {len(data)}")
            self.logger.info(f"  - 数据列名: {list(data.keys())}")
            
            return data
        
        @task
        def run_operator(op_id: str, payload: Dict[str, Any], implementation: str) -> Any:
            """运行算子任务。"""
            module = self._get_module_path(implementation)
            class_name = self._get_class_name(implementation)
            impl = self._import_impl(f"src.{module}", class_name)
            
            # 特殊处理需要额外配置的算子
            if class_name == "RuleEvaluator":
                # 添加计算配置路径
                params = payload.get("params", {})
                if "calculation_config" in params:
                    calculation_config_path = resolve_path(self.base_dir, params["calculation_config"])
                    params["calculation_config_path"] = calculation_config_path
                
                instance = impl(rules_index=self.rules_index, **params)
                if "data" in payload:
                    result = instance.run(payload["data"])
                else:
                    result = instance.run(**payload["inputs"])
            elif class_name == "SensorGroupAggregator":
                process_stages_path = self.config_manager.get_config_path("process_stages")
                calculation_config_path = resolve_path(self.base_dir, payload.get("params", {}).get("calculation_config", "config/calculation_definitions.yaml"))
                
                # 输出计算定义配置加载信息
                self.logger.info("测试计算定义配置加载...")
                try:
                    import yaml
                    with open(calculation_config_path, "r", encoding="utf-8") as f:
                        calc_config = yaml.safe_load(f)
                    self.logger.info("✓ 成功加载计算定义配置")
                    self.logger.info(f"  - 配置键: {list(calc_config.keys())}")
                    
                    # 检查传感器组映射
                    context_mappings = calc_config.get("context_mappings", {})
                    sensor_group_mappings = context_mappings.get("sensor_group_mappings", {})
                    self.logger.info(f"  - 传感器组映射: {list(sensor_group_mappings.keys())}")
                except Exception as e:
                    self.logger.warning(f"加载计算定义配置失败: {e}")
                
                # 从 params 中移除 calculation_config，避免重复传递
                params = payload.get("params", {}).copy()
                params.pop("calculation_config", None)
                
                instance = impl(
                    process_stages_yaml=process_stages_path,
                    calculation_config=calculation_config_path,
                    **params
                )
                result = instance.run(**payload["inputs"])
                
                # 输出传感器组聚合完成信息
                if isinstance(result, dict) and "grouping_info" in result:
                    grouping_info = result["grouping_info"]
                    self.logger.info(f"测试传感器组聚合器...")
                    self.logger.info(f"✓ 传感器组聚合成功")
                    self.logger.info(f"  - 传感器组数量: {grouping_info.get('total_groups', 0)}")
                    self.logger.info(f"  - 传感器组名称: {grouping_info.get('group_names', [])}")
            elif class_name == "StageDetector":
                process_stages_path = self.config_manager.get_config_path("process_stages")
                instance = impl(process_stages_yaml=process_stages_path, **payload.get("params", {}))
                result = instance.run(**payload["inputs"])
            else:
                instance = impl(**payload.get("params", {}))
                result = instance.run(**payload["inputs"])
            
            return result
        
        @task
        def write_result(path: str, content: Dict[str, Any]) -> str:
            """写入结果任务。"""
            writer = ReportWriterFactory.create_writer("file", file_path=path)
            return writer.run(content=content)
        
        @flow(name=wf_cfg.get("name", "demo_flow"))
        def demo_flow() -> str:
            """工作流主函数。"""
            self.logger.info(f"\n构建工作流: {wf_cfg.get('name', 'demo_flow')}")
            self.logger.info(f"任务总数: {len(nodes)}")
            self.logger.info(f"执行顺序: {' -> '.join(order)}")
            
            results: Dict[str, Any] = {}
            
            for i, nid in enumerate(order, 1):
                n = id_to_node[nid]
                n_type = n.get("type", "processing")
                
                self.logger.info(f"\n[{i}/{len(order)}] 执行任务: {nid} (类型: {n_type})")
                
                if n_type == "input":
                    self.logger.info(f"  加载输入数据...")
                    results[nid] = task_input.submit(n)
                    self.logger.info(f"  输入任务 {nid} 已提交")
                    continue
                
                if n_type in {"processing", "calculation", "validation", "analysis"}:
                    self.logger.info(f"  准备算子载荷...")
                    # 等待依赖任务完成
                    resolved_results = {}
                    for k, v in results.items():
                        if hasattr(v, "result"):
                            try:
                                resolved_results[k] = v.result()
                            except Exception as e:
                                self.logger.error(f"  等待依赖任务 {k} 完成时出错: {e}")
                                raise WorkflowError(f"依赖任务 {k} 执行失败: {e}")
                        else:
                            resolved_results[k] = v
                    
                    payload = self._build_payload_for_operator(n, resolved_results)
                    self.logger.info(f"  运行算子: {n.get('implementation', 'unknown')}")
                    results[nid] = run_operator.submit(n["id"], payload, n.get("implementation", ""))
                    self.logger.info(f"  处理任务 {nid} 已提交")
                    continue
                
                if n_type == "output":
                    self.logger.debug(f"  准备输出结果...")
                    # 输出节点：写文件
                    depends_on = n.get("depends_on", [])
                    if depends_on:
                        up_id = depends_on[0]
                        if up_id in results:
                            if hasattr(results[up_id], "result"):
                                try:
                                    content = results[up_id].result()
                                except Exception as e:
                                    self.logger.error(f"  等待依赖任务 {up_id} 完成时出错: {e}")
                                    raise WorkflowError(f"依赖任务 {up_id} 执行失败: {e}")
                            else:
                                content = results[up_id]
                            self.logger.debug(f"  使用依赖结果: {up_id}")
                        else:
                            self.logger.error(f"  依赖任务 {up_id} 不存在")
                            raise WorkflowError(f"依赖任务 {up_id} 不存在")
                    else:
                        # 如果没有依赖，使用最后一个结果
                        if results:
                            last_result = list(results.values())[-1]
                            if hasattr(last_result, "result"):
                                try:
                                    content = last_result.result()
                                except Exception as e:
                                    self.logger.error(f"  等待最后任务完成时出错: {e}")
                                    raise WorkflowError(f"最后任务执行失败: {e}")
                            else:
                                content = last_result
                        else:
                            content = {}
                        self.logger.debug(f"  使用最后结果")
                    
                    params = n.get("parameters", {})
                    orig_rel = params.get("file_path", "quality-reports.json")
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
                    
                    self.logger.debug(f"  写入文件: {out_path}")
                    results[nid] = write_result.submit(out_path, content)
                    self.logger.debug(f"  输出任务 {nid} 已提交")
                    continue
            
            self.logger.info(f"\n等待所有任务完成...")
            
            # 等待所有任务完成并收集结果
            final_results = {}
            for nid, result in results.items():
                if hasattr(result, "result"):
                    final_results[nid] = result.result()
                else:
                    final_results[nid] = result
            
            # 返回最后一个输出节点的结果路径（若存在），否则返回空串
            last_outputs = [n["id"] for n in nodes if n.get("type") == "output"]
            if last_outputs:
                final_result = final_results[last_outputs[-1]]
                self.logger.info(f"工作流完成！最终结果: {final_result}")
                return final_result
            else:
                self.logger.warning(f"工作流完成，但没有输出节点")
                return ""
        
        return demo_flow

"""配置管理器。"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, List
from .loader import ConfigLoader
from .specification_registry import SpecificationRegistry
from .template_registry import TemplateRegistry
from .runtime_binder import RuntimeConfigBinder, BoundSpecification
from ..core.exceptions import ConfigurationError
from ..utils.logging_config import get_logger


class ConfigManager:
    """配置管理器。"""
    
    def __init__(self, startup_config_path: str = "config/startup_config.yaml"):
        """
        初始化配置管理器。
        
        Args:
            startup_config_path: 启动配置文件路径
        """
        # 先设置默认的 base_dir
        self.base_dir = "."
        self.logger = get_logger()
        
        # 加载启动配置
        self.startup_config = self._load_startup_config(startup_config_path)
        
        # 从配置文件读取启动参数
        startup_params = self.startup_config.get("startup", {})
        
        self.base_dir = startup_params.get("base_dir", ".")
        self.debug = startup_params.get("debug", True)
        self.host = startup_params.get("host", "0.0.0.0")
        self.port = startup_params.get("port", 8000)
        self.reload = startup_params.get("reload", False)
        self.log_level = startup_params.get("log_level", "info")
        self.auto_kill_on_port_conflict = startup_params.get("auto_kill_on_port_conflict", False)
        
        # 读取系统级超时配置
        self.timeouts = self.startup_config.get("timeouts", {})
        
        # 初始化配置加载器
        self.config_loader = ConfigLoader(self.base_dir)
        
        # 初始化规范注册表（规范号驱动架构）
        self.specification_registry = SpecificationRegistry(
            self.config_loader,
            specifications_root=self.get_specifications_root()
        )
        
        # 初始化模板注册表
        self.template_registry = TemplateRegistry(
            self.config_loader,
            templates_root=self.get_templates_root()
        )
        
        # 初始化运行时配置绑定器
        self.runtime_binder = RuntimeConfigBinder(self.template_registry)
        
        # 加载所有配置文件
        self._load_all_configs()
    
    def _load_startup_config(self, config_path: str) -> Dict[str, Any]:
        """加载启动配置。"""
        try:
            # 如果config_path是目录，查找startup_config.yaml
            if os.path.isdir(config_path):
                startup_file = os.path.join(config_path, "config", "startup_config.yaml")
            else:
                startup_file = config_path

            # 路径解析与回退：环境变量与仓库根目录
            startup_path = Path(startup_file)
            if not startup_path.exists():
                # 显式文件环境变量优先
                env_file = os.getenv("OPLIB_CONFIG")
                if env_file and Path(env_file).exists():
                    startup_path = Path(env_file)
                else:
                    # 目录环境变量次之
                    env_dir = os.getenv("OPLIB_CONFIG_DIR")
                    if env_dir and Path(env_dir).exists():
                        candidate = Path(env_dir) / "startup_config.yaml"
                        if candidate.exists():
                            startup_path = candidate
                    # 向上查找仓库根目录的 config/startup_config.yaml（从文件位置与CWD双路径尝试）
                    if not startup_path.exists():
                        target_rel = os.path.join("config", "startup_config.yaml")
                        # 1) 以当前文件为起点向上
                        try:
                            cur = Path(__file__).resolve()
                            for parent in [cur.parent, *cur.parents]:
                                candidate = parent / target_rel
                                if candidate.exists():
                                    startup_path = candidate
                                    break
                        except Exception:
                            pass
                        # 2) 以当前工作目录为起点向上
                        if not startup_path.exists():
                            try:
                                cur = Path(os.getcwd()).resolve()
                                for parent in [cur, *cur.parents]:
                                    candidate = parent / target_rel
                                    if candidate.exists():
                                        startup_path = candidate
                                        break
                            except Exception:
                                pass

            # 直接使用 ConfigLoader 加载启动配置
            loader = ConfigLoader(self.base_dir)
            return loader.load_workflow_config(str(startup_path))
        except Exception as e:
            raise ConfigurationError(f"无法加载启动配置 {config_path}: {e}")
    
    
    def _load_all_configs(self) -> None:
        """加载所有配置文件。"""
        self.configs = {}
        config_files = self.startup_config.get("config_files", {})
        
        for config_name, config_path in config_files.items():
            try:
                if config_name == "workflow_config":
                    self.configs[config_name] = self.config_loader.load_workflow_config(config_path)
                elif config_name == "process_rules":
                    self.configs[config_name] = self.config_loader.load_rules_config(config_path)
                elif config_name == "process_stages":
                    self.configs[config_name] = self.config_loader.load_process_stages_config(config_path)
                elif config_name == "calculation_definitions":
                    self.configs[config_name] = self.config_loader.load_calculation_definitions_config(config_path)
                elif config_name == "sensor_groups":
                    self.configs[config_name] = self.config_loader.load_sensor_groups_config(config_path)
                elif config_name == "process_specification":
                    self.configs[config_name] = self.config_loader.load_process_specification_config(config_path)
                elif config_name == "calculations":
                    self.configs[config_name] = self.config_loader.load_calculations_config(config_path)
                else:
                    # 通用加载
                    self.configs[config_name] = self.config_loader.load_workflow_config(config_path)
            except Exception as e:
                self.logger.warning(f"无法加载配置文件 {config_name} ({config_path}): {e}")
                self.configs[config_name] = {}
    
    def get_config(self, config_name: str) -> Dict[str, Any]:
        """获取指定配置。"""
        return self.configs.get(config_name, {})
    
    def get_config_path(self, config_name: str) -> str:
        """获取配置文件路径。"""
        config_files = self.startup_config.get("config_files", {})
        relative_path = config_files.get(config_name, "")
        return str(Path(self.base_dir) / relative_path)
    
    def get_startup_params(self) -> Dict[str, Any]:
        """获取启动参数。"""
        return {
            "base_dir": self.base_dir,
            "debug": self.debug,
            "host": self.host,
            "port": self.port,
            "reload": self.reload,
            "log_level": self.log_level,
            "auto_kill_on_port_conflict": self.auto_kill_on_port_conflict
        }
    
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """获取工作流配置。"""
        return self.get_config("workflow_config")
    
    def get_rules_config(self) -> Dict[str, Any]:
        """获取规则配置。"""
        return self.get_config("process_rules")
    
    def get_stages_config(self) -> Dict[str, Any]:
        """获取阶段配置。"""
        return self.get_config("process_stages")
    
    def get_calculation_definitions_config(self) -> Dict[str, Any]:
        """获取计算定义配置。"""
        return self.get_config("calculation_definitions")
    
    def get_specification_config(self) -> Dict[str, Any]:
        """获取规范配置。"""
        return self.get_config("process_specification")
    
    def get_workflow_defaults(self, workflow_id: str = "curing_analysis") -> Dict[str, Any]:
        """获取工作流的默认参数值。"""
        workflow_config = self.get_workflow_config()
        workflows = workflow_config.get("workflows", {})
        workflow = workflows.get(workflow_id, {})
        parameters = workflow.get("parameters", {})
        
        defaults = {}
        for param_name, param_config in parameters.items():
            if isinstance(param_config, dict) and "default" in param_config:
                defaults[param_name] = param_config["default"]
        
        return defaults
    
    def get_workflow_required_params(self, workflow_id: str = "curing_analysis") -> list[str]:
        """获取工作流的必需参数列表。"""
        workflow_config = self.get_workflow_config()
        workflows = workflow_config.get("workflows", {})
        workflow = workflows.get(workflow_id, {})
        parameters = workflow.get("parameters", {})
        
        required_params = []
        for param_name, param_config in parameters.items():
            if isinstance(param_config, dict) and param_config.get("required", False):
                required_params.append(param_name)
        
        return required_params
    
    def override_config_path(self, config_name: str, new_path: str) -> None:
        """覆盖配置文件路径并重新加载。"""
        self.startup_config["config_files"][config_name] = new_path
        self._load_all_configs()
    
    def override_base_dir(self, new_base_dir: str) -> None:
        """覆盖基础目录并重新加载所有配置。"""
        self.base_dir = new_base_dir
        self.config_loader = ConfigLoader(self.base_dir)
        self._load_all_configs()
    
    def get_timeout(self, service_type: str) -> int:
        """获取指定服务的超时设置。"""
        return self.timeouts.get(service_type, 30)
    
    def get_kafka_config(self) -> Dict[str, Any]:
        """获取Kafka配置。"""
        # Kafka配置现在应该在工作流配置中定义，这里提供默认值
        return {
            "brokers": ["localhost:9092"],
            "timeout": self.get_timeout("kafka"),
            "max_records": 1000
        }
    
    # ============================================================
    # 规范号驱动架构API
    # ============================================================
    
    def list_specifications(self) -> List[str]:
        """列出所有可用的规范ID"""
        return self.specification_registry.list_specifications()

    def get_specifications_root(self) -> str:
        """获取规范配置根目录（相对 base_dir 的路径）。"""
        paths = self.startup_config.get("paths", {})
        root = paths.get("specifications_root", "config/specifications")
        return root
    
    def get_templates_root(self) -> str:
        """获取模板配置根目录（相对 base_dir 的路径）。"""
        paths = self.startup_config.get("paths", {})
        root = paths.get("templates_root", "config/templates")
        return root
    
    def get_specification(self, specification_id: str) -> Dict[str, Any]:
        """获取规范配置"""
        return self.specification_registry.load_specification(specification_id)
    
    def get_specification_rules(self, specification_id: str) -> Dict[str, Any]:
        """获取规范的规则配置"""
        return self.specification_registry.get_specification_rules(specification_id)
    
    def get_specification_stages(self, specification_id: str) -> Dict[str, Any]:
        """获取规范的阶段配置"""
        return self.specification_registry.get_specification_stages(specification_id)
    
    def get_specification_calculations(self, specification_id: str) -> Optional[Dict[str, Any]]:
        """获取规范的计算项配置"""
        return self.specification_registry.get_specification_calculations(specification_id)
    
    def get_specification_process_params(self, specification_id: str) -> Dict[str, Any]:
        """获取规范的工艺参数"""
        return self.specification_registry.get_specification_process_params(specification_id)
    
    def get_specification_materials(self, specification_id: str) -> List[str]:
        """获取规范适用的材料列表"""
        return self.specification_registry.get_specification_materials(specification_id)
    
    def find_specifications_by_material(self, material_code: str) -> List[str]:
        """查找适用于某材料的规范列表"""
        return self.specification_registry.find_specifications_by_material(material_code)

    # ============================================================
    # 运行时配置注入
    # ============================================================
    def set_runtime_config(self, config_name: str, config: Dict[str, Any]) -> None:
        """在运行时注入/覆盖配置内容（不写回磁盘）。"""
        self.configs[config_name] = config
    
    # ============================================================
    # 运行时配置绑定
    # ============================================================
    def bind_specification(
        self,
        specification_id: str,
        sensor_grouping: Dict[str, List[str]]
    ) -> BoundSpecification:
        """
        绑定规范配置到实际传感器
        
        Args:
            specification_id: 规范ID
            sensor_grouping: 传感器分组映射 {group_name: [sensor1, sensor2, ...]}
            
        Returns:
            绑定后的规范配置
        """
        # 加载完整规范配置
        spec_config = self._load_complete_specification(specification_id)
        
        # 使用运行时绑定器绑定
        return self.runtime_binder.bind_specification(spec_config, sensor_grouping)
    
    def _load_complete_specification(self, specification_id: str) -> Dict[str, Any]:
        """加载完整的规范配置（包括所有子配置）"""
        spec = self.specification_registry.load_specification(specification_id)
        rules = self.specification_registry.get_specification_rules(specification_id)
        stages = self.specification_registry.get_specification_stages(specification_id)
        calculations = self.specification_registry.get_specification_calculations(specification_id)
        
        return {
            "specification_id": specification_id,
            "metadata": spec or {},
            "rules": rules.get("rules", []) if rules else [],
            "stages": stages.get("stages", []) if stages else [],
            "calculations": calculations.get("calculations", []) if calculations else [],
        }

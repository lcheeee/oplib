from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml



class RuleGenerator:
    """基于模板与用户输入生成规则与阶段配置。第一版：覆盖写入。"""

    def __init__(self, project_root: str | Path = ".", process_type: str = "curing") -> None:
        # 统一为绝对路径，避免写入位置受 CWD 影响
        self.project_root = Path(project_root).resolve()
        self.templates_dir = self.project_root / "config" / "templates"
        self.process_type = process_type  # 工艺类型，如 "curing"（必需参数）

    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """从 config/templates/{process_type}/ 加载所有 yaml 模板文件，按 template_id 建索引。"""
        template_index: Dict[str, Dict[str, Any]] = {}
        
        # 从工艺类型目录读取（如 config/templates/curing/）
        templates_dir = self.templates_dir / self.process_type
        
        if not templates_dir.exists():
            raise ValueError(f"工艺类型模板目录不存在: {templates_dir}")

        # 加载该目录下的所有 yaml 文件
        for file in templates_dir.glob("*.yaml"):
            try:
                data = yaml.safe_load(file.read_text(encoding="utf-8")) or {}
                templates = (data or {}).get("templates", [])
                
                # 只支持列表格式的模板
                if not isinstance(templates, list):
                    continue
                    
                for tpl in templates:
                    template_id = tpl.get("id")
                    if template_id:
                        template_index[template_id] = tpl
            except Exception as e:
                # 忽略单个文件的错误，继续加载其他文件
                continue
                
        return template_index

    def _load_calculation_templates(self) -> Dict[str, Dict[str, Any]]:
        """从 config/templates/{process_type}/calculation_templates.yaml 加载计算项模板。"""
        calculation_templates_file = self.templates_dir / self.process_type / "calculation_templates.yaml"
        
        if not calculation_templates_file.exists():
            return {}
        
        try:
            data = yaml.safe_load(calculation_templates_file.read_text(encoding="utf-8")) or {}
            templates = data.get("templates", [])
            
            if not isinstance(templates, list):
                return {}
            
            template_index: Dict[str, Dict[str, Any]] = {}
            for tpl in templates:
                template_id = tpl.get("id")
                if template_id:
                    template_index[template_id] = tpl
            
            return template_index
        except Exception as e:
            print(f"[WARNING] 加载计算项模板失败: {e}")
            return {}

    @staticmethod
    def _render_rule(template: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """最小渲染：按模板字段拷贝并用 payload 覆盖；支持 description_template。"""
        rule: Dict[str, Any] = {}

        # 基础字段
        rule["id"] = payload.get("rule_id")
        
        # 描述：优先使用模板的 description，如果模板有 description_template 则使用它
        desc_tpl = template.get("description_template") or template.get("description") or payload.get("description")
        if isinstance(desc_tpl, str):
            # 简单模板替换：参数优先，其次顶层字段
            rule["description"] = desc_tpl
            merged: Dict[str, Any] = {
                **payload,
                **(payload.get("parameters", {}) or {}),
            }
            # 参数名映射：min_value -> min, max_value -> max
            if "min_value" in merged:
                merged["min"] = merged["min_value"]
            if "max_value" in merged:
                merged["max"] = merged["max_value"]
            # 数组格式化：temp_range [55, 150] -> "[55, 150]"
            if "temp_range" in merged and isinstance(merged["temp_range"], list):
                merged["temp_range"] = str(merged["temp_range"])
            # 处理 None 值：如果 description 是 None，使用空字符串
            if merged.get("description") is None:
                merged["description"] = ""
            
            for k, v in merged.items():
                try:
                    if v is not None:
                        rule["description"] = rule["description"].replace(f"{{{{{k}}}}}", str(v))
                except Exception:
                    pass
            # 清理残留的模板变量和多余的标点
            # 移除未替换的模板变量（如 {{stage_num}}）
            rule["description"] = re.sub(r'\{\{[^}]+\}\}', '', rule["description"])
            # 清理多余的句号和空格
            rule["description"] = re.sub(r'\s*。\s*。', '。', rule["description"])
            rule["description"] = rule["description"].strip()
        elif payload.get("description"):
            rule["description"] = payload["description"]
        elif template.get("description"):
            rule["description"] = template["description"]

        # 条件（condition）：从模板继承，如果模板有 condition 字段
        if "condition" in template:
            rule["condition"] = template["condition"]
            # 替换条件中的占位符
            params = payload.get("parameters", {})
            for k, v in params.items():
                if isinstance(rule["condition"], str):
                    rule["condition"] = rule["condition"].replace(f"{{{k}}}", str(v))

        # 模式/聚合等从模板继承
        if "pattern" in template:
            rule["pattern"] = template["pattern"]
        if "aggregate" in template:
            rule["aggregate"] = template["aggregate"]

        # 严重性
        rule["severity"] = payload.get("severity") or template.get("severity") or "major"

        # 阶段
        stage = payload.get("parameters", {}).get("stage") or payload.get("stage")
        if stage:
            rule["stage"] = stage

        # 参数
        rule["parameters"] = payload.get("parameters", {}).copy()
        # 删除 stage 参数（放到顶层 stage）
        if "stage" in rule["parameters"]:
            rule["parameters"].pop("stage", None)

        return rule

    def generate(self,
                 specification_id: str,
                 stages_input: Dict[str, Any] | None,
                 rule_inputs: List[Dict[str, Any]],
                 publish: bool = False,
                 version: str | None = None) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, str]]:
        """生成 rules.yaml 与 stages.yaml 内容并按需写入。

        Returns: (rules_doc, stages_doc, files)
        files 仅在 publish=True 时返回实际落地路径。
        """
        templates = self._load_templates()

        rules: List[Dict[str, Any]] = []
        for item in rule_inputs:
            template_id = item.get("template_id")
            payload = {
                "rule_id": item.get("rule_id"),
                "description": item.get("description"),
                "severity": item.get("severity"),
                "parameters": item.get("parameters", {})
            }
            tpl = templates.get(template_id, {})
            rule = self._render_rule(tpl, payload)
            if not rule.get("id"):
                raise ValueError(f"缺少 rule_id（template_id={template_id}）")
            if not rule.get("parameters"):
                raise ValueError(f"规则参数不能为空（rule_id={rule['id']}）")
            if "stage" not in rule:
                raise ValueError(f"规则缺少阶段 stage（rule_id={rule['id']}）")
            rules.append(rule)

        # 构建 stages.yaml
        if stages_input and stages_input.get("items"):
            stages_list = stages_input["items"]
        else:
            # 根据规则的 stage 自动推导阶段集合
            stage_map: Dict[str, Dict[str, Any]] = {}
            for r in rules:
                sid = r.get("stage")
                if sid not in stage_map:
                    stage_map[sid] = {"id": sid, "name": sid, "rules": []}
                stage_map[sid].setdefault("rules", []).append(r["id"])
            stages_list = list(stage_map.values())

        # 若传入了 items，同时我们需要把规则分配到对应阶段
        stage_index = {s["id"]: s for s in stages_list}
        for r in rules:
            sid = r.get("stage")
            stage_index.setdefault(sid, {"id": sid, "name": sid, "rules": []})
            stage_index[sid].setdefault("rules", [])
            if r["id"] not in stage_index[sid]["rules"]:
                stage_index[sid]["rules"].append(r["id"])

        # 确保阶段配置包含所有必要字段，并保留用户提供的各种阶段识别配置
        final_stages = []
        for stage_id, stage_config in stage_index.items():
            final_stage = {
                "id": stage_config.get("id", stage_id),
                "name": stage_config.get("name", stage_id),
                "display_order": stage_config.get("display_order", 0),
                "rules": stage_config.get("rules", [])
            }
            
            # 保留阶段识别类型
            if "type" in stage_config:
                final_stage["type"] = stage_config["type"]
            
            # 基于时间的阶段识别配置
            if "time_range" in stage_config:
                final_stage["time_range"] = stage_config["time_range"]
            if "unit" in stage_config:
                final_stage["unit"] = stage_config["unit"]
            
            # 基于规则触发的阶段识别配置
            if "trigger_rule" in stage_config:
                final_stage["trigger_rule"] = stage_config["trigger_rule"]
            
            # 基于温度范围的阶段识别配置
            if "temperature_range" in stage_config:
                final_stage["temperature_range"] = stage_config["temperature_range"]
            
            # 基于算法的阶段识别配置
            if "algorithm" in stage_config:
                final_stage["algorithm"] = stage_config["algorithm"]
            if "algorithm_params" in stage_config:
                final_stage["algorithm_params"] = stage_config["algorithm_params"]
            
            # 保留其他用户自定义字段（如 description 等）
            for key in ["description", "metadata"]:
                if key in stage_config:
                    final_stage[key] = stage_config[key]
            
            final_stages.append(final_stage)

        # 按 display_order 排序
        final_stages.sort(key=lambda x: x.get("display_order", 0))

        stages_doc = {
            "version": "v1",
            "specification_id": specification_id,
            "stages": final_stages
        }
        rules_doc = {
            "version": "v1",
            "specification_id": specification_id,
            "rules": rules
        }

        # 构建 calculations.yaml：从规则中提取使用的计算项
        calculation_templates = self._load_calculation_templates()
        used_calculation_ids = set()
        
        # 从规则中提取使用的 calculation_id
        for rule in rules:
            params = rule.get("parameters", {})
            calculation_id = params.get("calculation_id")
            if calculation_id:
                used_calculation_ids.add(calculation_id)
        
        # 生成计算项引用列表（引用计算项模板）
        calculations_list = []
        for calc_id in sorted(used_calculation_ids):
            calc_template = calculation_templates.get(calc_id)
            if calc_template:
                # 从模板中提取传感器组占位符
                sensors_placeholder = calc_template.get("sensors", [])
                # 从占位符中提取传感器组名称（去掉 {}）
                sensors = []
                for sensor_placeholder in sensors_placeholder:
                    if isinstance(sensor_placeholder, str):
                        # 提取 {sensor_group} 中的 sensor_group
                        matches = re.findall(r'\{(\w+)\}', sensor_placeholder)
                        sensors.extend(matches)
                
                calculations_list.append({
                    "template": calc_id,
                    "sensors": list(set(sensors)) if sensors else []  # 去重
                })
        
        calculations_doc = None
        if calculations_list:
            calculations_doc = {
                "version": "v1",
                "specification_id": specification_id,
                "calculations": calculations_list
            }

        files: Dict[str, str] = {}
        if publish:
            spec_dir = self.project_root / "config" / "specifications" / specification_id
            print(f"[DEBUG] 创建规范目录: {spec_dir}")
            spec_dir.mkdir(parents=True, exist_ok=True)
            rules_path = (spec_dir / "rules.yaml").resolve()
            stages_path = (spec_dir / "stages.yaml").resolve()
            print(f"[DEBUG] 写入文件: {rules_path}")
            print(f"[DEBUG] 写入文件: {stages_path}")
            try:
                with rules_path.open("w", encoding="utf-8") as f:
                    yaml.safe_dump(rules_doc, f, allow_unicode=True, sort_keys=False)
                print(f"[DEBUG] rules.yaml 写入成功")
                with stages_path.open("w", encoding="utf-8") as f:
                    yaml.safe_dump(stages_doc, f, allow_unicode=True, sort_keys=False)
                print(f"[DEBUG] stages.yaml 写入成功")
                
                # 写入 calculations.yaml（如果规则中使用了计算项）
                if calculations_doc:
                    calculations_path = (spec_dir / "calculations.yaml").resolve()
                    print(f"[DEBUG] 写入文件: {calculations_path}")
                    with calculations_path.open("w", encoding="utf-8") as f:
                        yaml.safe_dump(calculations_doc, f, allow_unicode=True, sort_keys=False)
                    print(f"[DEBUG] calculations.yaml 写入成功（包含 {len(calculations_list)} 个计算项）")
                    files["calculations_path"] = str(calculations_path)
                else:
                    print(f"[DEBUG] 未生成 calculations.yaml（规则中未使用计算项）")
            except Exception as e:
                print(f"[ERROR] 文件写入失败: {e}")
                raise
            files["rules_path"] = str(rules_path)
            files["stages_path"] = str(stages_path)
            print(f"[DEBUG] 返回文件路径: {files}")

        return rules_doc, stages_doc, files



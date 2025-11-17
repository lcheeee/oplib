#!/usr/bin/env python3
"""测试整合后的配置。"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.manager import ConfigManager
from src.workflow.builder import WorkflowBuilder
from src.utils.logging_config import get_logger

def test_consolidated_config():
    """测试整合后的配置。"""
    logger = get_logger()
    logger.info("开始测试整合后的配置...")
    
    try:
        # 初始化配置管理器
        config_manager = ConfigManager()
        
        # 检查是否能正确加载 workflow_config.yaml
        workflow_config = config_manager.get_config("workflow_config")
        if not workflow_config:
            logger.error("无法加载 workflow_config.yaml")
            return False
        
        logger.info("✅ 成功加载 workflow_config.yaml")
        
        # 检查工作流配置结构
        workflows = workflow_config.get("workflows", {})
        if "curing_analysis" not in workflows:
            logger.error("未找到 curing_analysis 工作流")
            return False
        
        curing_workflow = workflows["curing_analysis"]
        logger.info("✅ 找到 curing_analysis 工作流")
        
        # 检查传感器组配置
        sensor_groups = curing_workflow.get("sensor_groups", {})
        if not sensor_groups:
            logger.error("未找到传感器组配置")
            return False
        
        logger.info(f"✅ 找到 {len(sensor_groups)} 个传感器组配置")
        for group_name, group_config in sensor_groups.items():
            logger.info(f"  - {group_name}: {group_config.get('columns', '')}")
        
        # 检查分层架构任务配置
        workflow_tasks = curing_workflow.get("workflow", [])
        if not workflow_tasks:
            logger.error("未找到工作流任务配置")
            return False
        
        logger.info(f"✅ 找到 {len(workflow_tasks)} 个任务层")
        
        # 检查各层任务
        layer_names = []
        for layer in workflow_tasks:
            layer_name = layer.get("layer", "unknown")
            layer_names.append(layer_name)
            tasks = layer.get("tasks", [])
            logger.info(f"  - {layer_name}: {len(tasks)} 个任务")
            for task in tasks:
                task_id = task.get("id", "unknown")
                implementation = task.get("implementation", "unknown")
                logger.info(f"    - {task_id}: {implementation}")
        
        # 检查是否包含所有必要的层
        required_layers = ["data_source", "data_processing", "spec_binding", "data_analysis", "result_merging", "result_output"]
        missing_layers = [layer for layer in required_layers if layer not in layer_names]
        if missing_layers:
            logger.warning(f"缺少以下层: {missing_layers}")
        else:
            logger.info("✅ 包含所有必要的层")
        
        # 创建工作流构建器
        workflow_builder = WorkflowBuilder(config_manager)
        
        # 检查配置加载
        if workflow_builder.rules_index:
            logger.info(f"✅ 成功加载 {len(workflow_builder.rules_index)} 条规则")
        else:
            logger.warning("⚠️ 未加载到规则配置")
        
        if workflow_builder.spec_index:
            logger.info(f"✅ 成功加载 {len(workflow_builder.spec_index)} 个规格")
        else:
            logger.warning("⚠️ 未加载到规格配置")
        
        if workflow_builder.stages_index:
            logger.info(f"✅ 成功加载 {len(workflow_builder.stages_index)} 个阶段")
        else:
            logger.warning("⚠️ 未加载到阶段配置")
        
        logger.info("✅ 整合后的配置测试通过")
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_consolidated_config()
    if success:
        print("✅ 整合后的配置测试通过")
        sys.exit(0)
    else:
        print("❌ 整合后的配置测试失败")
        sys.exit(1)

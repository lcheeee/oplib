import sys
from datetime import datetime
from pathlib import Path

# Ensure project root on sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.config.manager import ConfigManager
from src.workflow.builder import WorkflowBuilder
from src.workflow.orchestrator import WorkflowOrchestrator


def run_smoke_test(
    workflow_name: str = "curing_analysis",
    specification_id: str = "cps7020-n-308-vacuum",
    file_path: str = "resources/test_data_1.csv",
    series_id: str = "SMOKE_TEST_001",
    calculation_date: str = "20251024",
):
    config_manager = ConfigManager()

    # Load workflow definition
    wf_config_all = config_manager.get_config("workflow_config")
    workflows = wf_config_all.get("workflows", {})
    if workflow_name not in workflows:
        raise RuntimeError(f"Workflow not found: {workflow_name}")
    wf_def = workflows[workflow_name]

    # Build plan and context
    builder = WorkflowBuilder(config_manager)
    plan = builder.build(wf_def, workflow_name)
    context = builder.create_workflow_context(plan, wf_def)

    # Inject required parameters
    context["process_id"] = f"{series_id}_{datetime.now().strftime('%H%M%S')}"
    context["series_id"] = series_id
    context["specification_id"] = specification_id
    context["calculation_date"] = calculation_date
    context["file_path"] = file_path  # used by csv reader task

    # Execute
    orchestrator = WorkflowOrchestrator(config_manager, enable_data_flow_monitoring=False)
    result = orchestrator.execute(plan, context)

    print("Success:", result.get("success"))
    print("Execution time(s):", result.get("execution_time"))
    print("Total task results:", result.get("total_results"))
    return result


if __name__ == "__main__":
    try:
        run_smoke_test()
    except Exception as e:
        print("[SMOKE TEST FAILED]", e)
        sys.exit(1)

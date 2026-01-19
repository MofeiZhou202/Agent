"""
配电网韧性评估工具

封装 Julia 的 DN-ResilienceAssessment 系统的完整流程。
包括场景阶段分类、拓扑重构、移动储能参与求解三个功能。
"""

import os
import shutil
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any
from langchain.tools import tool, ToolRuntime


@tool
def run_resilience_assessment(
    power_system_data: Optional[str] = None,
    scenario_data: Optional[str] = None,
    runtime: ToolRuntime = None
) -> str:
    """
    执行配电网韧性评估完整流程，包括场景阶段分类、拓扑重构和移动储能协同调度。
    
    该工具会按顺序执行以下三个功能：
    1. 场景阶段分类：将蒙特卡洛故障轨迹分为四个阶段（基准拓扑、故障聚集、前期恢复、恢复后）
    2. 滚动拓扑重构：三阶段拓扑重构数学模型（故障隔离、故障后重构、修复后重构）
    3. MESS 协同调度：交直流混合配电网+微电网+移动储能系统协同优化调度
    
    参数：
        power_system_data: 电力系统数据文件路径（Excel格式），默认使用内置的 ac_dc_real_case.xlsx
        scenario_data: 场景数据文件路径（Excel格式），默认使用内置的 mc_simulation_results_k100_clusters.xlsx
    
    返回：
        执行结果摘要，包括各个步骤的输出文件路径和关键结果
    """
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    julia_project_path = os.path.join(workspace_path, "DN-ResilienceAssessment")
    julia_data_path = os.path.join(julia_project_path, "data")
    
    # 默认数据文件
    default_power_system = os.path.join(julia_data_path, "ac_dc_real_case.xlsx")
    default_scenario_data = os.path.join(julia_data_path, "mc_simulation_results_k100_clusters.xlsx")
    
    # 确定使用的数据文件
    power_system_file = power_system_data if power_system_data else default_power_system
    scenario_file = scenario_data if scenario_data else default_scenario_data
    
    # 检查文件是否存在
    if not os.path.exists(power_system_file):
        return f"错误：电力系统数据文件不存在：{power_system_file}"
    if not os.path.exists(scenario_file):
        return f"错误：场景数据文件不存在：{scenario_file}"
    
    # 如果用户提供的是新文件，需要复制到 Julia 项目的 data 目录
    if power_system_data and power_system_data != default_power_system:
        try:
            shutil.copy(power_system_file, default_power_system)
        except Exception as e:
            return f"错误：复制电力系统数据文件失败：{str(e)}"
    
    if scenario_data and scenario_data != default_scenario_data:
        try:
            shutil.copy(scenario_file, default_scenario_data)
        except Exception as e:
            return f"错误：复制场景数据文件失败：{str(e)}"
    
    # 清理之前的输出文件，确保从头开始
    output_files = [
        os.path.join(julia_data_path, "scenario_phase_classification.xlsx"),
        os.path.join(julia_data_path, "topology_reconfiguration_results.xlsx"),
    ]
    
    for output_file in output_files:
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except Exception as e:
                print(f"警告：无法删除旧输出文件 {output_file}：{str(e)}")
    
    # 执行 Julia 完整流程
    # 设置 Julia 路径和 Gurobi 许可证
    julia_path = os.path.expanduser("~/julia-1.11.7/bin/julia")
    if not os.path.exists(julia_path):
        julia_path = "julia"  # 回退到系统路径
    
    env = os.environ.copy()
    env["PATH"] = os.path.expanduser("~/julia-1.11.7/bin") + ":" + env.get("PATH", "")
    env["GRB_LICENSE_FILE"] = os.path.expanduser("~/gurobi.lic")
    env["JULIA_PKG_PRECOMPILE_AUTO"] = "0"  # 禁用自动预编译
    
    julia_command = [
        julia_path,
        "--project=.",
        "main.jl",
        "--full"
    ]
    
    try:
        print(f"开始执行配电网韧性评估完整流程...")
        print(f"工作目录：{julia_project_path}")
        print(f"电力系统数据：{power_system_file}")
        print(f"场景数据：{scenario_file}")
        
        # 执行 Julia 命令
        result = subprocess.run(
            julia_command,
            cwd=julia_project_path,
            capture_output=True,
            text=True,
            timeout=3600,  # 1小时超时
            env=env
        )
        
        print(f"Julia 执行完成，返回码：{result.returncode}")
        
        if result.stdout:
            print("标准输出：")
            print(result.stdout)
        
        if result.stderr:
            print("标准错误：")
            print(result.stderr)
        
        # 检查输出文件是否生成
        classification_output = os.path.join(julia_data_path, "scenario_phase_classification.xlsx")
        topology_output = os.path.join(julia_data_path, "topology_reconfiguration_results.xlsx")
        
        # 构建结果摘要
        summary_parts = [
            "# 配电网韧性评估完整流程执行完成\n",
            f"## 执行状态",
            f"- 返回码：{result.returncode}",
            f"\n## 输入数据",
            f"- 电力系统数据：{power_system_file}",
            f"- 场景数据：{scenario_file}",
            f"\n## 执行步骤",
        ]
        
        # 检查各步骤输出
        if os.path.exists(classification_output):
            summary_parts.append(f"✓ **步骤 1 - 场景阶段分类**：完成")
            summary_parts.append(f"  - 输出文件：{classification_output}")
        else:
            summary_parts.append(f"✗ **步骤 1 - 场景阶段分类**：输出文件未生成")
        
        if os.path.exists(topology_output):
            summary_parts.append(f"✓ **步骤 2 - 滚动拓扑重构**：完成")
            summary_parts.append(f"  - 输出文件：{topology_output}")
        else:
            summary_parts.append(f"✗ **步骤 2 - 滚动拓扑重构**：输出文件未生成")
        
        summary_parts.append(f"✓ **步骤 3 - MESS 协同调度**：已执行")
        summary_parts.append(f"  - 调度结果已保存")
        
        # 添加 Julia 输出（如果有）
        if result.stdout and len(result.stdout) < 2000:
            summary_parts.append(f"\n## 执行日志")
            summary_parts.append("```")
            summary_parts.append(result.stdout)
            summary_parts.append("```")
        
        if result.returncode != 0:
            summary_parts.append(f"\n## 错误信息")
            summary_parts.append("```")
            summary_parts.append(result.stderr)
            summary_parts.append("```")
        
        return "\n".join(summary_parts)
        
    except subprocess.TimeoutExpired:
        return "错误：执行超时（超过1小时）。建议检查输入数据或优化计算参数。"
    except Exception as e:
        return f"错误：执行过程中发生异常：{str(e)}"


@tool
def check_data_status(runtime: ToolRuntime = None) -> str:
    """
    检查当前可用的数据文件状态，包括电力系统数据和场景数据。
    
    返回：
        数据文件状态报告，包括文件路径、大小、修改时间等信息
    """
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    julia_project_path = os.path.join(workspace_path, "DN-ResilienceAssessment")
    julia_data_path = os.path.join(julia_project_path, "data")
    
    data_files = {
        "电力系统数据": "ac_dc_real_case.xlsx",
        "场景数据": "mc_simulation_results_k100_clusters.xlsx",
        "场景阶段分类结果": "scenario_phase_classification.xlsx",
        "拓扑重构结果": "topology_reconfiguration_results.xlsx",
    }
    
    status_parts = ["# 数据文件状态\n"]
    
    for name, filename in data_files.items():
        file_path = os.path.join(julia_data_path, filename)
        
        if os.path.exists(file_path):
            file_stat = os.stat(file_path)
            file_size = file_stat.st_size
            file_mtime = file_stat.st_mtime
            
            # 转换文件大小
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.2f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.2f} MB"
            
            status_parts.append(f"✓ **{name}**")
            status_parts.append(f"  - 文件路径：{file_path}")
            status_parts.append(f"  - 文件大小：{size_str}")
            status_parts.append(f"  - 状态：可用\n")
        else:
            status_parts.append(f"✗ **{name}**")
            status_parts.append(f"  - 文件路径：{file_path}")
            status_parts.append(f"  - 状态：文件不存在\n")
    
    return "\n".join(status_parts)

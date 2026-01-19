# 配电网韧性评估智能体使用说明

## 概述

本智能体能够自动执行配电网韧性评估的完整流程，包括三个核心功能：
1. **场景阶段分类**：将蒙特卡洛故障轨迹分为四个阶段（基准拓扑、故障聚集、前期恢复、恢复后）
2. **滚动拓扑重构**：三阶段拓扑重构数学模型（故障隔离、故障后重构、修复后重构）
3. **MESS 协同调度**：交直流混合配电网+微电网+移动储能系统协同优化调度

## 前置条件

### 1. 安装 Julia

本智能体依赖 Julia 语言进行核心计算，必须先安装 Julia：

- **下载地址**：https://julialang.org/downloads/
- **推荐版本**：1.9.0 或更高版本
- **验证安装**：在终端输入 `julia --version`

### 2. 配置 Julia 环境

安装完成后，进入 Julia REPL，配置所需的依赖包：

```julia
# 进入 Julia REPL
julia

# 安装依赖包
using Pkg
Pkg.add([
    "JuMP",
    "Gurobi",
    "XLSX",
    "DataFrames",
    "CSV",
    "PyCall",
    "Dates",
    "Optim"
])

# 退出 Julia REPL
exit()
```

### 3. 配置 Gurobi 许可证

本工具使用 Gurobi 求解器进行优化计算，需要有效的 Gurobi 许可证：

```julia
# 在 Julia REPL 中设置
using Gurobi
ENV["GRB_LICENSE_FILE"] = "/path/to/your/gurobi.lic"
```

**注意**：如果还没有 Gurobi 许可证，可以申请学术版或商业版：
- 学术版：https://www.gurobi.com/academia/academic-program-and-licenses/
- 商业版：https://www.gurobi.com/purchase/

## 使用方法

### 1. 检查数据文件状态

在使用智能体之前，可以先检查可用的数据文件：

```
用户输入：检查一下数据文件状态
```

智能体会返回以下信息：
- 电力系统数据（ac_dc_real_case.xlsx）
- 场景数据（mc_simulation_results_k100_clusters.xlsx）
- 场景阶段分类结果（scenario_phase_classification.xlsx）
- 拓扑重构结果（topology_reconfiguration_results.xlsx）

### 2. 执行完整韧性评估流程

使用内置的示例数据进行测试：

```
用户输入：我想执行配电网韧性评估，使用内置的示例数据
```

智能体会自动执行：
1. 场景阶段分类
2. 滚动拓扑重构
3. MESS 协同调度

### 3. 使用自定义数据

如果需要使用自己的数据文件：

```
用户输入：我需要评估这个电力系统数据：/path/to/your/power_system.xlsx，场景数据：/path/to/your/scenario.xlsx
```

**注意事项**：
- 数据文件必须为 Excel 格式（.xlsx）
- 数据格式需要符合 Julia 程序的输入要求
- 建议先查看内置示例数据的格式

## 数据文件说明

### 输入数据

| 文件名 | 说明 |
|--------|------|
| ac_dc_real_case.xlsx | 电力系统数据，包含配电网拓扑结构、负荷、分布式电源等 |
| mc_simulation_results_k100_clusters.xlsx | 场景数据，包含蒙特卡洛仿真的故障场景 |

### 输出数据

| 文件名 | 说明 |
|--------|------|
| scenario_phase_classification.xlsx | 场景阶段分类结果 |
| topology_reconfiguration_results.xlsx | 拓扑重构结果 |
| (其他调度结果文件) | MESS 协同调度结果 |

## 项目结构

```
.
├── DN-ResilienceAssessment/        # Julia 源代码
│   ├── main.jl                      # Julia 主入口
│   ├── src/                         # Julia 源码
│   ├── data/                        # 数据文件
│   └── solvers/                     # 求解器
├── src/
│   ├── agents/
│   │   └── agent.py                 # Agent 主逻辑
│   └── tools/
│       └── resilience_assessment_tool.py  # 工具实现
└── config/
    └── agent_llm_config.json        # Agent 配置
```

## 执行时间

完整的韧性评估流程可能需要较长时间，具体取决于：
- 数据规模（节点数量、场景数量等）
- 计算机性能
- Gurobi 求解器版本

**预计时间**：
- 小规模测试数据（内置示例）：5-15 分钟
- 中等规模数据：15-30 分钟
- 大规模数据：30 分钟 - 数小时

## 常见问题

### Q1: 提示 "No such file or directory: 'julia'"

**原因**：系统未安装 Julia 或 Julia 未添加到 PATH 环境变量

**解决方案**：
1. 下载并安装 Julia：https://julialang.org/downloads/
2. 将 Julia 添加到系统 PATH
3. 重新启动终端，验证安装：`julia --version`

### Q2: 提示 Gurobi 许可证问题

**原因**：Gurobi 许可证未配置或已过期

**解决方案**：
1. 申请 Gurobi 许可证：https://www.gurobi.com/purchase/
2. 在 Julia 中设置许可证路径：
   ```julia
   ENV["GRB_LICENSE_FILE"] = "/path/to/your/gurobi.lic"
   ```

### Q3: 执行超时

**原因**：数据规模过大或计算资源不足

**解决方案**：
1. 检查数据规模，尝试使用较小的数据集
2. 确保计算机有足够的内存和 CPU 资源
3. 考虑使用更强大的计算服务器

### Q4: 如何使用自己的数据？

**步骤**：
1. 准备符合格式要求的 Excel 文件
2. 将文件上传到 assets/ 目录或其他可访问位置
3. 告诉智能体文件路径，例如：
   ```
   用户输入：我使用这个电力系统数据：/path/to/power_system.xlsx
   ```

## 技术支持

如果在使用过程中遇到任何问题，请：
1. 检查本文档的"常见问题"部分
2. 查看智能体返回的错误信息
3. 确认 Julia 和依赖包已正确安装
4. 检查数据文件格式是否正确

## 参考资料

- Julia 官方文档：https://docs.julialang.org/
- Gurobi 文档：https://www.gurobi.com/documentation/
- 原 GitHub 仓库：https://github.com/MofeiZhou202/DN-ResilienceAssessment

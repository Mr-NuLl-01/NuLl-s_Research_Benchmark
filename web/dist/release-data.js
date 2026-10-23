globalThis.NRB_RELEASE = {
  "version": "2.0.0",
  "status": "complete",
  "date": "2026-10-23",
  "tasks": [
    {
      "id": "P01",
      "title": "仪器 CSV 清洗、单位与测量不确定度",
      "language": "python",
      "difficulty": 1,
      "capabilities": [
        "csv",
        "units",
        "uncertainty",
        "data-validation"
      ],
      "time_budget_s": 900,
      "required_artifacts": [
        "solution.py"
      ],
      "legacy_id": "C01",
      "status": "ready",
      "category": "Python",
      "track": "python",
      "scoring": "automatic",
      "max_score": 100,
      "optional_artifacts": [
        "report.md",
        "tests.py"
      ],
      "manual_review_required": false,
      "format": "md",
      "benchmark_version": "2.0.0",
      "brief": "CSV身份、单位与极小不确定度；区分重复记录和独立测量。",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "file": "P01.md",
      "packet_hash": "94d470a3e60e8688ba67faf2a1e3dc8d7b238072c3498836a915e481c4f1a7d0",
      "seed": 17,
      "level": "1/5",
      "budget": 15,
      "version": "2.0.0",
      "packet": "packets-v2/P01.md",
      "packetHash": "94d470a3e60e8688ba67faf2a1e3dc8d7b238072c3498836a915e481c4f1a7d0"
    },
    {
      "id": "P02",
      "title": "独立组与分层 bootstrap 模型比较",
      "language": "python",
      "difficulty": 2,
      "capabilities": [
        "clustered-data",
        "bootstrap",
        "deterministic-statistics"
      ],
      "time_budget_s": 900,
      "required_artifacts": [
        "solution.py"
      ],
      "legacy_id": "C02",
      "status": "ready",
      "category": "Python",
      "track": "python",
      "scoring": "automatic",
      "max_score": 100,
      "optional_artifacts": [
        "report.md",
        "tests.py"
      ],
      "manual_review_required": false,
      "format": "md",
      "benchmark_version": "2.0.0",
      "brief": "独立组与技术重复、分层目标人群和确定性bootstrap。",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "file": "P02.md",
      "packet_hash": "3493b9cb506bfea3c1594383d936e49cb12b0bcfead93a9ea62392125d1f24f9",
      "seed": 17,
      "level": "2/5",
      "budget": 15,
      "version": "2.0.0",
      "packet": "packets-v2/P02.md",
      "packetHash": "3493b9cb506bfea3c1594383d936e49cb12b0bcfead93a9ea62392125d1f24f9"
    },
    {
      "id": "P03",
      "title": "修复分层导热有限体积求解器",
      "language": "python",
      "difficulty": 3,
      "capabilities": [
        "debugging",
        "finite-volume",
        "conservation",
        "implicit-methods"
      ],
      "time_budget_s": 900,
      "required_artifacts": [
        "solution.py"
      ],
      "legacy_id": "C03",
      "status": "ready",
      "category": "Python",
      "track": "python",
      "scoring": "automatic",
      "max_score": 100,
      "optional_artifacts": [
        "report.md",
        "tests.py"
      ],
      "manual_review_required": false,
      "format": "md",
      "benchmark_version": "2.0.0",
      "brief": "修复非均匀有限体积导热：界面热阻、隐式推进与能量账本。",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "file": "P03.md",
      "packet_hash": "3b884a94b079c2dd4f405ccd33154ff62e4afa6e953a77d3c3c44991f4ab4a32",
      "seed": 17,
      "level": "3/5",
      "budget": 15,
      "version": "2.0.0",
      "packet": "packets-v2/P03.md",
      "packetHash": "3b884a94b079c2dd4f405ccd33154ff62e4afa6e953a77d3c3c44991f4ab4a32"
    },
    {
      "id": "P04",
      "title": "被动吸收多层薄膜的稳定光学传输",
      "language": "python",
      "difficulty": 4,
      "capabilities": [
        "complex-optics",
        "transfer-matrix",
        "numerical-stability",
        "polarization"
      ],
      "time_budget_s": 1800,
      "required_artifacts": [
        "solution.py"
      ],
      "legacy_id": "C04",
      "status": "ready",
      "category": "Python",
      "track": "python",
      "scoring": "automatic",
      "max_score": 100,
      "optional_artifacts": [
        "report.md",
        "tests.py"
      ],
      "manual_review_required": false,
      "format": "md",
      "benchmark_version": "2.0.0",
      "brief": "复折射率多层光学：s/p偏振、能流、倏逝波与极厚吸收层。",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "file": "P04.md",
      "packet_hash": "30015006e01186ed65b9fd70aea957f1f65f4a33820caf2254bc29483526b901",
      "seed": 17,
      "level": "4/5",
      "budget": 30,
      "version": "2.0.0",
      "packet": "packets-v2/P04.md",
      "packetHash": "30015006e01186ed65b9fd70aea957f1f65f4a33820caf2254bc29483526b901"
    },
    {
      "id": "P05",
      "title": "带源项时间表的刚性反应自适应积分",
      "language": "python",
      "difficulty": 5,
      "capabilities": [
        "stiff-integration",
        "adaptive-steps",
        "rollback",
        "floating-point-endpoints"
      ],
      "time_budget_s": 1800,
      "required_artifacts": [
        "solution.py"
      ],
      "legacy_id": "C05",
      "status": "ready",
      "category": "Python",
      "track": "python",
      "scoring": "automatic",
      "max_score": 100,
      "optional_artifacts": [
        "report.md",
        "tests.py"
      ],
      "manual_review_required": false,
      "format": "md",
      "benchmark_version": "2.0.0",
      "brief": "按明确算法实现刚性积分：拒步回滚、右连续源与浮点硬停点。",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "file": "P05.md",
      "packet_hash": "f4d0ccea4607140dae559d85f8c1ab9560ff30be4415f8933766fbf74fcdaf4d",
      "seed": 17,
      "level": "5/5",
      "budget": 30,
      "version": "2.0.0",
      "packet": "packets-v2/P05.md",
      "packetHash": "f4d0ccea4607140dae559d85f8c1ab9560ff30be4415f8933766fbf74fcdaf4d"
    },
    {
      "id": "P06",
      "title": "带独立基线与幅度的逆热扩散：剖面似然与退化诊断",
      "language": "python",
      "difficulty": 4,
      "capabilities": [
        "inverse_problem",
        "variable_projection",
        "profile_likelihood",
        "identifiability"
      ],
      "time_budget_s": 2400,
      "execution_budget_s": 12,
      "required_artifacts": [
        "solution.py"
      ],
      "legacy_id": "C07",
      "status": "ready",
      "category": "Python",
      "track": "python",
      "scoring": "automatic",
      "max_score": 100,
      "optional_artifacts": [
        "report.md",
        "tests.py"
      ],
      "manual_review_required": false,
      "format": "md",
      "benchmark_version": "2.0.0",
      "brief": "变量投影、绝对sigma、剖面似然区间和端点附近内部最小值。",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "file": "P06.md",
      "packet_hash": "0f1b726fb696a0cd5eb0c3f84c328c2b23b9f5ad3224c34ad16507adf68d90bd",
      "seed": 17,
      "level": "4/5",
      "budget": 40,
      "version": "2.0.0",
      "packet": "packets-v2/P06.md",
      "packetHash": "0f1b726fb696a0cd5eb0c3f84c328c2b23b9f5ad3224c34ad16507adf68d90bd"
    },
    {
      "id": "P07",
      "title": "二维异质各向异性椭圆方程：守恒通量与制造解",
      "language": "python",
      "difficulty": 4,
      "capabilities": [
        "elliptic_pde",
        "heterogeneity",
        "anisotropy",
        "manufactured_solution",
        "conservation"
      ],
      "time_budget_s": 2400,
      "execution_budget_s": 12,
      "required_artifacts": [
        "solution.py"
      ],
      "legacy_id": "C08",
      "status": "ready",
      "category": "Python",
      "track": "python",
      "scoring": "automatic",
      "max_score": 100,
      "optional_artifacts": [
        "report.md",
        "tests.py"
      ],
      "manual_review_required": false,
      "format": "md",
      "benchmark_version": "2.0.0",
      "brief": "二维非均匀网格、方向各向异性、界面传递与边界积分通量。",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "file": "P07.md",
      "packet_hash": "d36807d4291affd41d86b51430a4eb211179d7e6c2e272552f26838b8e408713",
      "seed": 17,
      "level": "4/5",
      "budget": 40,
      "version": "2.0.0",
      "packet": "packets-v2/P07.md",
      "packetHash": "d36807d4291affd41d86b51430a4eb211179d7e6c2e272552f26838b8e408713"
    },
    {
      "id": "P08",
      "title": "修复反应扩散反演流水线：切线导数、守恒、重启和参数自举",
      "language": "python",
      "difficulty": 5,
      "capabilities": [
        "multibug_repair",
        "reaction_diffusion",
        "discrete_sensitivity",
        "inverse_problem",
        "reproducible_uncertainty",
        "checkpoint"
      ],
      "time_budget_s": 4500,
      "execution_budget_s": 25,
      "required_artifacts": [
        "solution.py"
      ],
      "legacy_id": "C10",
      "status": "ready",
      "category": "Python",
      "track": "python",
      "scoring": "automatic",
      "max_score": 100,
      "optional_artifacts": [
        "report.md",
        "tests.py"
      ],
      "manual_review_required": false,
      "format": "md",
      "benchmark_version": "2.0.0",
      "brief": "修复反应扩散反演链：离散切线、协方差、JSON重启与重新拟合自举。",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "file": "P08.md",
      "packet_hash": "795f4b46b0009527ff7c11ee75d45871ed7efb67d5118b653de20f515f79298f",
      "seed": 17,
      "level": "5/5",
      "budget": 75,
      "version": "2.0.0",
      "packet": "packets-v2/P08.md",
      "packetHash": "795f4b46b0009527ff7c11ee75d45871ed7efb67d5118b653de20f515f79298f"
    },
    {
      "id": "F01",
      "title": "Fortran 非均匀网格守恒漂移扩散",
      "category": "Fortran",
      "difficulty": 3,
      "brief": "SG通量、非均匀控制体与漂移方向",
      "status": "ready",
      "phase": 2,
      "scoring": "automatic",
      "legacy_id": "C06",
      "language": "fortran",
      "track": "fortran",
      "benchmark_version": "2.0.0",
      "time_budget_s": 1800,
      "max_score": 100,
      "format": "md",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": false,
      "required_artifacts": [
        "solution.f90"
      ],
      "file": "F01.md",
      "packet_hash": "577ab63860b6eff1ef779c5f53c64567a637500ccd6c6c008da7bfe0a9f97970",
      "seed": 17,
      "level": "3/5",
      "budget": 30,
      "version": "2.0.0",
      "packet": "packets-v2/F01.md",
      "packetHash": "577ab63860b6eff1ef779c5f53c64567a637500ccd6c6c008da7bfe0a9f97970"
    },
    {
      "id": "F02",
      "title": "Fortran 隐式反应扩散与源汇账本",
      "category": "Fortran",
      "difficulty": 4,
      "brief": "时间推进、正性与源汇守恒",
      "status": "ready",
      "phase": 2,
      "scoring": "automatic",
      "legacy_id": null,
      "language": "fortran",
      "track": "fortran",
      "benchmark_version": "2.0.0",
      "time_budget_s": 2700,
      "max_score": 100,
      "format": "md",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": false,
      "required_artifacts": [
        "solution.f90"
      ],
      "file": "F02.md",
      "packet_hash": "a51de755f97d0ade2cb7ade48b4fe1757ba59dbe9141d8e5a4e18061c3fe0538",
      "seed": 17,
      "level": "4/5",
      "budget": 45,
      "version": "2.0.0",
      "packet": "packets-v2/F02.md",
      "packetHash": "a51de755f97d0ade2cb7ade48b4fe1757ba59dbe9141d8e5a4e18061c3fe0538"
    },
    {
      "id": "F03",
      "title": "Fortran 自洽漂移扩散–Poisson",
      "category": "Fortran",
      "difficulty": 5,
      "brief": "非线性耦合、阻尼迭代与规范平移",
      "status": "ready",
      "phase": 2,
      "scoring": "automatic",
      "legacy_id": "C09",
      "language": "fortran",
      "track": "fortran",
      "benchmark_version": "2.0.0",
      "time_budget_s": 3600,
      "max_score": 100,
      "format": "md",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": false,
      "required_artifacts": [
        "solution.f90"
      ],
      "file": "F03.md",
      "packet_hash": "03ac765e2d673c8c39a7340927ea94dd3f3e1dcd7a96e927906b59c5f31ccf6e",
      "seed": 17,
      "level": "5/5",
      "budget": 60,
      "version": "2.0.0",
      "packet": "packets-v2/F03.md",
      "packetHash": "03ac765e2d673c8c39a7340927ea94dd3f3e1dcd7a96e927906b59c5f31ccf6e"
    },
    {
      "id": "L01",
      "title": "已有守恒结论的 Lean 形式化",
      "category": "Lean",
      "difficulty": 4,
      "brief": "给定命题与条件、实际编译、公理依赖核验",
      "status": "ready",
      "phase": 2,
      "scoring": "automatic",
      "legacy_id": null,
      "language": "lean",
      "track": "lean",
      "benchmark_version": "2.0.0",
      "time_budget_s": 2400,
      "max_score": 100,
      "format": "md",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": false,
      "required_artifacts": [
        "proofs.json"
      ],
      "file": "L01.md",
      "packet_hash": "bfeab8c3295d08a08d22cfea27f3ec02076038040f5f18c50565ca99e4a4484d",
      "seed": 17,
      "level": "4/5",
      "budget": 40,
      "version": "2.0.0",
      "packet": "packets-v2/L01.md",
      "packetHash": "bfeab8c3295d08a08d22cfea27f3ec02076038040f5f18c50565ca99e4a4484d"
    },
    {
      "id": "R01",
      "title": "参考学习与可编辑科研 SVG",
      "category": "主观科研",
      "difficulty": 4,
      "brief": "真实图例学习、科学语义与多面板组织",
      "status": "ready",
      "phase": 2,
      "scoring": "manual",
      "legacy_id": "R01",
      "language": null,
      "track": "research",
      "benchmark_version": "2.0.0",
      "time_budget_s": 3600,
      "max_score": 100,
      "format": "md",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": true,
      "required_artifacts": [
        "见题面交付清单"
      ],
      "file": "R01.md",
      "packet_hash": "18757706a00915469ca91f15d4cb0798e029b8cc82cbeb6d8c48c3f43745ba40",
      "seed": 17,
      "level": "4/5",
      "budget": 60,
      "version": "2.0.0",
      "packet": "packets-v2/R01.md",
      "packetHash": "18757706a00915469ca91f15d4cb0798e029b8cc82cbeb6d8c48c3f43745ba40"
    },
    {
      "id": "R02",
      "title": "小差异、宽动态范围与删失数据绘图",
      "category": "主观科研",
      "difficulty": 4,
      "brief": "坐标尺度、数据语义与可复现图形",
      "status": "ready",
      "phase": 2,
      "scoring": "manual",
      "legacy_id": "R02",
      "language": null,
      "track": "research",
      "benchmark_version": "2.0.0",
      "time_budget_s": 3600,
      "max_score": 100,
      "format": "md",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": true,
      "required_artifacts": [
        "见题面交付清单"
      ],
      "file": "R02.md",
      "packet_hash": "9ab6ceb24d75578a0109ca3c867bc84dbe32bebab857aa7d9225cc8c7f9af791",
      "seed": 17,
      "level": "4/5",
      "budget": 60,
      "version": "2.0.0",
      "packet": "packets-v2/R02.md",
      "packetHash": "9ab6ceb24d75578a0109ca3c867bc84dbe32bebab857aa7d9225cc8c7f9af791"
    },
    {
      "id": "R03",
      "title": "保持事实与证据强度的英文润色",
      "category": "主观科研",
      "difficulty": 3,
      "brief": "保守修改、事实台账与自然表达",
      "status": "ready",
      "phase": 2,
      "scoring": "manual",
      "legacy_id": "R03",
      "language": null,
      "track": "research",
      "benchmark_version": "2.0.0",
      "time_budget_s": 1800,
      "max_score": 100,
      "format": "md",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": true,
      "required_artifacts": [
        "见题面交付清单"
      ],
      "file": "R03.md",
      "packet_hash": "65010dcbfa874a8de1403fc74f3f55533774853881830d3356891f254ba27d60",
      "seed": 17,
      "level": "3/5",
      "budget": 30,
      "version": "2.0.0",
      "packet": "packets-v2/R03.md",
      "packetHash": "65010dcbfa874a8de1403fc74f3f55533774853881830d3356891f254ba27d60"
    },
    {
      "id": "R04",
      "title": "从图版与数据撰写结果和讨论",
      "category": "主观科研",
      "difficulty": 4,
      "brief": "读图、定量表述与推断边界",
      "status": "ready",
      "phase": 2,
      "scoring": "manual",
      "legacy_id": "R04",
      "language": null,
      "track": "research",
      "benchmark_version": "2.0.0",
      "time_budget_s": 2400,
      "max_score": 100,
      "format": "md",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": true,
      "required_artifacts": [
        "见题面交付清单"
      ],
      "file": "R04.md",
      "packet_hash": "26e4e30cd04fa575adc90095a51e21cb20d3d1efbabbf61b663fbf0851e52cb7",
      "seed": 17,
      "level": "4/5",
      "budget": 40,
      "version": "2.0.0",
      "packet": "packets-v2/R04.md",
      "packetHash": "26e4e30cd04fa575adc90095a51e21cb20d3d1efbabbf61b663fbf0851e52cb7"
    },
    {
      "id": "R05",
      "title": "文献证据综合与有界方法复现",
      "category": "主观科研",
      "difficulty": 5,
      "brief": "合并旧精读/综述题，保留证据与复现责任",
      "status": "ready",
      "phase": 2,
      "scoring": "manual",
      "legacy_id": "R05+R06",
      "language": null,
      "track": "research",
      "benchmark_version": "2.0.0",
      "time_budget_s": 7200,
      "max_score": 100,
      "format": "md",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": true,
      "required_artifacts": [
        "见题面交付清单"
      ],
      "file": "R05.md",
      "packet_hash": "0e408a3b832fb5fad11b2f32c4f27757f2db8b7236b625b5d55db05cc8c2e9c0",
      "seed": 17,
      "level": "5/5",
      "budget": 120,
      "version": "2.0.0",
      "packet": "packets-v2/R05.md",
      "packetHash": "0e408a3b832fb5fad11b2f32c4f27757f2db8b7236b625b5d55db05cc8c2e9c0"
    },
    {
      "id": "R06",
      "title": "视频修改与参考视觉重建",
      "category": "主观科研",
      "difficulty": 4,
      "brief": "合并视频A/B为一道题的两种预先声明模式",
      "status": "ready",
      "phase": 2,
      "scoring": "manual",
      "legacy_id": "X04+X05",
      "language": null,
      "track": "research",
      "benchmark_version": "2.0.0",
      "time_budget_s": 7200,
      "max_score": 100,
      "format": "md",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": true,
      "required_artifacts": [
        "见题面交付清单"
      ],
      "file": "R06.md",
      "packet_hash": "a638de8231d4ddacd7181f4343d4d3d7498ec9228d9a834bb4884e2c2fc7ff95",
      "seed": 17,
      "level": "4/5",
      "budget": 120,
      "version": "2.0.0",
      "packet": "packets-v2/R06.md",
      "packetHash": "a638de8231d4ddacd7181f4343d4d3d7498ec9228d9a834bb4884e2c2fc7ff95"
    },
    {
      "id": "H01",
      "title": "聊天端单 HTML 科研工作台",
      "category": "聊天端",
      "difficulty": 4,
      "brief": "离线交互、返回、空态与真实导出",
      "status": "ready",
      "phase": 2,
      "scoring": "manual",
      "legacy_id": "X01",
      "language": null,
      "track": "chat",
      "benchmark_version": "2.0.0",
      "time_budget_s": 2400,
      "max_score": 100,
      "format": "md",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": true,
      "required_artifacts": [
        "见题面交付清单"
      ],
      "file": "H01.md",
      "packet_hash": "27290f701cad3790daafa2a9be630d64e8f1f6f01bfe0d4c2ab411411dc66027",
      "seed": 17,
      "level": "4/5",
      "budget": 40,
      "version": "2.0.0",
      "packet": "packets-v2/H01.md",
      "packetHash": "27290f701cad3790daafa2a9be630d64e8f1f6f01bfe0d4c2ab411411dc66027"
    },
    {
      "id": "H02",
      "title": "聊天端有回流网络的定量推理",
      "category": "聊天端",
      "difficulty": 5,
      "brief": "产额、条件寿命、全局最优与可核验反例",
      "status": "ready",
      "phase": 2,
      "scoring": "automatic",
      "legacy_id": null,
      "language": null,
      "track": "chat",
      "benchmark_version": "2.0.0",
      "time_budget_s": 2400,
      "max_score": 100,
      "format": "md",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": false,
      "required_artifacts": [
        "answer.json"
      ],
      "file": "H02.md",
      "packet_hash": "8aa9f2d0652402c13cbc4ea84deda5a7b7e17cd15dc65c32617721f244353c52",
      "seed": 17,
      "level": "5/5",
      "budget": 40,
      "version": "2.0.0",
      "packet": "packets-v2/H02.md",
      "packetHash": "8aa9f2d0652402c13cbc4ea84deda5a7b7e17cd15dc65c32617721f244353c52"
    }
  ],
  "downloads": {
    "folder": {
      "name": "2.0.0",
      "status": "private_site_configured"
    },
    "grader": {
      "name": "NRB-v2.0.0-evaluator.zip",
      "bytes": 33149966,
      "sha256": "a58b8d7fdb7037384d96fe2022cb9b4ef060a1b255e5921ef23e266529cebe99",
      "status": "private_site_configured"
    },
    "candidateBundle": {
      "name": "NRB-v2.0.0-all-candidates.zip",
      "bytes": 60450997,
      "sha256": "729726a1b92d24b801ccf3c7453bfe8ff0bedde71db67dd5a8ddc0c45f390934",
      "status": "private_site_configured"
    },
    "tasks": {
      "P01": {
        "name": "NRB-v2.0.0-P01-candidate.zip",
        "bytes": 3740,
        "sha256": "7f90dbebf2e947b975039887c7af6c71c6293f89ee67a7b4c4442172dc377ac6",
        "status": "private_site_configured"
      },
      "P02": {
        "name": "NRB-v2.0.0-P02-candidate.zip",
        "bytes": 3847,
        "sha256": "fbac7dac4a34533a2f11b617803b7e0a7c8742c3799e277ae6b9f0d6240d93cc",
        "status": "private_site_configured"
      },
      "P03": {
        "name": "NRB-v2.0.0-P03-candidate.zip",
        "bytes": 4151,
        "sha256": "d999d85769bfe254ae91099d81a95996250f2b43352ea20c57ab62058cfef790",
        "status": "private_site_configured"
      },
      "P04": {
        "name": "NRB-v2.0.0-P04-candidate.zip",
        "bytes": 4467,
        "sha256": "607dba0267ab5b9d0703ba354857c836af0958418cbc562faa855992535793b1",
        "status": "private_site_configured"
      },
      "P05": {
        "name": "NRB-v2.0.0-P05-candidate.zip",
        "bytes": 4709,
        "sha256": "85f4fd6489229e3bde9eaf727d0bb211a2afeb38bd6f974192f16c6db0471d9f",
        "status": "private_site_configured"
      },
      "P06": {
        "name": "NRB-v2.0.0-P06-candidate.zip",
        "bytes": 4659,
        "sha256": "6dada90848ad2cf76ea17f2b78eda707fec8063c172f33408c301957fdec4f80",
        "status": "private_site_configured"
      },
      "P07": {
        "name": "NRB-v2.0.0-P07-candidate.zip",
        "bytes": 4526,
        "sha256": "1e3b94bd142bcf46e43be33c97fd5ceccfb3002686523ec36e7c267f08a17c1b",
        "status": "private_site_configured"
      },
      "P08": {
        "name": "NRB-v2.0.0-P08-candidate.zip",
        "bytes": 8170,
        "sha256": "a2fa70aa9dc6c621d34d35b82314a6714ce4db3d9623d5c873663130aa74307d",
        "status": "private_site_configured"
      },
      "F01": {
        "name": "NRB-v2.0.0-F01-candidate.zip",
        "bytes": 5077,
        "sha256": "79340002f5cbe32d1750f5a80f5ee5b53d7e4d2dd8f3322cf27caaee559c9bbf",
        "status": "private_site_configured"
      },
      "F02": {
        "name": "NRB-v2.0.0-F02-candidate.zip",
        "bytes": 4266,
        "sha256": "9fa4ae055757704084e9de032030476c5661c70b95b4a50f8ac2fc37208aa829",
        "status": "private_site_configured"
      },
      "F03": {
        "name": "NRB-v2.0.0-F03-candidate.zip",
        "bytes": 4690,
        "sha256": "edabb8b621b10a89d0b80222a8b12f86264c929dad77e72adf1118b388f38cbe",
        "status": "private_site_configured"
      },
      "L01": {
        "name": "NRB-v2.0.0-L01-candidate.zip",
        "bytes": 6852,
        "sha256": "4c9264bd2781f8b0a10d50d0ce54f1a2144f61f8669493affaf236c5cf7b5e31",
        "status": "private_site_configured"
      },
      "R01": {
        "name": "NRB-v2.0.0-R01-candidate.zip",
        "bytes": 225199,
        "sha256": "99ea315ef775728f6ac258ac6e34abaeaf5694ebb1e688e72802a9e2496a02c5",
        "status": "private_site_configured"
      },
      "R02": {
        "name": "NRB-v2.0.0-R02-candidate.zip",
        "bytes": 4614,
        "sha256": "ac33e332ed533edfc960b1497357e8384f0374c55d1bc5533091e9cc4244c61b",
        "status": "private_site_configured"
      },
      "R03": {
        "name": "NRB-v2.0.0-R03-candidate.zip",
        "bytes": 5034,
        "sha256": "6995d4f5a2351135ed87531251695a8f33c17dda47cca105d5f60807be4d8afd",
        "status": "private_site_configured"
      },
      "R04": {
        "name": "NRB-v2.0.0-R04-candidate.zip",
        "bytes": 124162,
        "sha256": "95355bf0b32e780e61be8df080831bbf6c384b6a687e8735eadebe78c3de48e4",
        "status": "private_site_configured"
      },
      "R05": {
        "name": "NRB-v2.0.0-R05-candidate.zip",
        "bytes": 1067930,
        "sha256": "ee2bcf130d50f8e1ecfe764afab8599fcd9e8ecf74046bcc5677fa604985874f",
        "status": "private_site_configured"
      },
      "R06-A": {
        "name": "NRB-v2.0.0-R06-A-candidate.zip",
        "bytes": 27511526,
        "sha256": "f6bf5e0df9fdbf68caa93cf93794b06a456d57a7e671b46e1d243026d729c5f7",
        "status": "private_site_configured"
      },
      "R06-B": {
        "name": "NRB-v2.0.0-R06-B-candidate.zip",
        "bytes": 31447248,
        "sha256": "09846d8545fb39fd67534daeb5bcf92625b24e684b22e98d28d1065920b7a484",
        "status": "private_site_configured"
      },
      "H01": {
        "name": "NRB-v2.0.0-H01-candidate.zip",
        "bytes": 5389,
        "sha256": "c299b95af2f75cc83c3b9c981f5fed47756f61c1980f5ded3376592c942c12d4",
        "status": "private_site_configured"
      },
      "H02": {
        "name": "NRB-v2.0.0-H02-candidate.zip",
        "bytes": 3902,
        "sha256": "6ee9c23d2d07fbbe3263364c7cd8a32ca2b7cee9ff477b0e6910d5770c08db0d",
        "status": "private_site_configured"
      }
    },
    "legacy": {
      "C01": {
        "id": "12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X",
        "url": "https://drive.google.com/file/d/12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X/view?usp=drivesdk",
        "name": "NRB-v1.1-historical-candidates.zip",
        "bytes": 3514902,
        "sha256": "f126216e782a5c4e67ec0aebc93c8e022d18c93bb18dc1cfc9a0ce8ab7b84cb5",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "C02": {
        "id": "12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X",
        "url": "https://drive.google.com/file/d/12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X/view?usp=drivesdk",
        "name": "NRB-v1.1-historical-candidates.zip",
        "bytes": 3514902,
        "sha256": "f126216e782a5c4e67ec0aebc93c8e022d18c93bb18dc1cfc9a0ce8ab7b84cb5",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "C03": {
        "id": "12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X",
        "url": "https://drive.google.com/file/d/12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X/view?usp=drivesdk",
        "name": "NRB-v1.1-historical-candidates.zip",
        "bytes": 3514902,
        "sha256": "f126216e782a5c4e67ec0aebc93c8e022d18c93bb18dc1cfc9a0ce8ab7b84cb5",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "C04": {
        "id": "12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X",
        "url": "https://drive.google.com/file/d/12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X/view?usp=drivesdk",
        "name": "NRB-v1.1-historical-candidates.zip",
        "bytes": 3514902,
        "sha256": "f126216e782a5c4e67ec0aebc93c8e022d18c93bb18dc1cfc9a0ce8ab7b84cb5",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "C05": {
        "id": "12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X",
        "url": "https://drive.google.com/file/d/12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X/view?usp=drivesdk",
        "name": "NRB-v1.1-historical-candidates.zip",
        "bytes": 3514902,
        "sha256": "f126216e782a5c4e67ec0aebc93c8e022d18c93bb18dc1cfc9a0ce8ab7b84cb5",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "C06": {
        "id": "12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X",
        "url": "https://drive.google.com/file/d/12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X/view?usp=drivesdk",
        "name": "NRB-v1.1-historical-candidates.zip",
        "bytes": 3514902,
        "sha256": "f126216e782a5c4e67ec0aebc93c8e022d18c93bb18dc1cfc9a0ce8ab7b84cb5",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "C07": {
        "id": "12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X",
        "url": "https://drive.google.com/file/d/12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X/view?usp=drivesdk",
        "name": "NRB-v1.1-historical-candidates.zip",
        "bytes": 3514902,
        "sha256": "f126216e782a5c4e67ec0aebc93c8e022d18c93bb18dc1cfc9a0ce8ab7b84cb5",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "C08": {
        "id": "12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X",
        "url": "https://drive.google.com/file/d/12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X/view?usp=drivesdk",
        "name": "NRB-v1.1-historical-candidates.zip",
        "bytes": 3514902,
        "sha256": "f126216e782a5c4e67ec0aebc93c8e022d18c93bb18dc1cfc9a0ce8ab7b84cb5",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "C09": {
        "id": "12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X",
        "url": "https://drive.google.com/file/d/12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X/view?usp=drivesdk",
        "name": "NRB-v1.1-historical-candidates.zip",
        "bytes": 3514902,
        "sha256": "f126216e782a5c4e67ec0aebc93c8e022d18c93bb18dc1cfc9a0ce8ab7b84cb5",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "C10": {
        "id": "12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X",
        "url": "https://drive.google.com/file/d/12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X/view?usp=drivesdk",
        "name": "NRB-v1.1-historical-candidates.zip",
        "bytes": 3514902,
        "sha256": "f126216e782a5c4e67ec0aebc93c8e022d18c93bb18dc1cfc9a0ce8ab7b84cb5",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "R01": {
        "id": "12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X",
        "url": "https://drive.google.com/file/d/12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X/view?usp=drivesdk",
        "name": "NRB-v1.1-historical-candidates.zip",
        "bytes": 3514902,
        "sha256": "f126216e782a5c4e67ec0aebc93c8e022d18c93bb18dc1cfc9a0ce8ab7b84cb5",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "R02": {
        "id": "12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X",
        "url": "https://drive.google.com/file/d/12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X/view?usp=drivesdk",
        "name": "NRB-v1.1-historical-candidates.zip",
        "bytes": 3514902,
        "sha256": "f126216e782a5c4e67ec0aebc93c8e022d18c93bb18dc1cfc9a0ce8ab7b84cb5",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "R03": {
        "id": "12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X",
        "url": "https://drive.google.com/file/d/12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X/view?usp=drivesdk",
        "name": "NRB-v1.1-historical-candidates.zip",
        "bytes": 3514902,
        "sha256": "f126216e782a5c4e67ec0aebc93c8e022d18c93bb18dc1cfc9a0ce8ab7b84cb5",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "R04": {
        "id": "12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X",
        "url": "https://drive.google.com/file/d/12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X/view?usp=drivesdk",
        "name": "NRB-v1.1-historical-candidates.zip",
        "bytes": 3514902,
        "sha256": "f126216e782a5c4e67ec0aebc93c8e022d18c93bb18dc1cfc9a0ce8ab7b84cb5",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "R05": {
        "id": "12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X",
        "url": "https://drive.google.com/file/d/12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X/view?usp=drivesdk",
        "name": "NRB-v1.1-historical-candidates.zip",
        "bytes": 3514902,
        "sha256": "f126216e782a5c4e67ec0aebc93c8e022d18c93bb18dc1cfc9a0ce8ab7b84cb5",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "R06": {
        "id": "12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X",
        "url": "https://drive.google.com/file/d/12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X/view?usp=drivesdk",
        "name": "NRB-v1.1-historical-candidates.zip",
        "bytes": 3514902,
        "sha256": "f126216e782a5c4e67ec0aebc93c8e022d18c93bb18dc1cfc9a0ce8ab7b84cb5",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "X01": {
        "id": "12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X",
        "url": "https://drive.google.com/file/d/12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X/view?usp=drivesdk",
        "name": "NRB-v1.1-historical-candidates.zip",
        "bytes": 3514902,
        "sha256": "f126216e782a5c4e67ec0aebc93c8e022d18c93bb18dc1cfc9a0ce8ab7b84cb5",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "X02": {
        "id": "12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X",
        "url": "https://drive.google.com/file/d/12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X/view?usp=drivesdk",
        "name": "NRB-v1.1-historical-candidates.zip",
        "bytes": 3514902,
        "sha256": "f126216e782a5c4e67ec0aebc93c8e022d18c93bb18dc1cfc9a0ce8ab7b84cb5",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "X03": {
        "id": "12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X",
        "url": "https://drive.google.com/file/d/12Jhvarp2ydfFdNVc0DsL7qKUBBg3z_8X/view?usp=drivesdk",
        "name": "NRB-v1.1-historical-candidates.zip",
        "bytes": 3514902,
        "sha256": "f126216e782a5c4e67ec0aebc93c8e022d18c93bb18dc1cfc9a0ce8ab7b84cb5",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "X04": {
        "url": "https://drive.google.com/file/d/1C3LNiq9IQpNi3WhXpLJo3ENCrqZgcUOf/view?usp=drivesdk",
        "name": "X04-media-pack-81368ec7.zip",
        "bytes": 28102436,
        "sha256": "ab02b4ad97aad91ec2a62fa56288c17d4d49d7a46a0f4ed0a42ccb6c3a066101",
        "id": "1C3LNiq9IQpNi3WhXpLJo3ENCrqZgcUOf"
      },
      "X05": {
        "url": "https://drive.google.com/file/d/1EpIAISvT_jlnEioC2jKXmx6Cl6_sSn4s/view?usp=drivesdk",
        "name": "X05-media-pack-81368ec7.zip",
        "bytes": 32043460,
        "sha256": "517986363e73d37855163601c1e42243639641c39a17dd5560368661aab14a62",
        "id": "1EpIAISvT_jlnEioC2jKXmx6Cl6_sSn4s"
      }
    },
    "status": "private_site_configured",
    "benchmark_version": "2.0.0",
    "implementation_commit": "735174612fe0fb298a83c872a0350f6eabf2d0a5",
    "evaluator_fingerprint": "7f2487673f1a214d60311193a369d48ab9215f9d7006554bf5c823e6ce5c7aa3"
  },
  "rubrics": {
    "R01": {
      "spec": {
        "id": "R01",
        "mode": null,
        "benchmark_version": "2.0.0",
        "protocol_version": "nrb-subjective-v2.0",
        "rubric": [
          {
            "id": "R01-A",
            "name": "Scientific encoding and data fidelity",
            "weight": 30,
            "anchors": {
              "0": "Data, pairing or units are substantially invented or lost.",
              "2": "Most values are represented, but one material design or unit ambiguity remains.",
              "4": "All supplied observations, pairing, batch identity and distinct experimental units are faithfully encoded; summaries are defined and justified."
            }
          },
          {
            "id": "R01-B",
            "name": "Learning from all three actual figure references",
            "weight": 20,
            "anchors": {
              "0": "No actual reference analysis or copied artwork replaces the new figure.",
              "2": "All references are named, but analysis is superficial or adoption is poorly connected to the data.",
              "4": "Specific visible choices from all three references are critically analysed and adapted coherently to the new scientific comparison."
            }
          },
          {
            "id": "R01-C",
            "name": "Scale, comparison and uncertainty judgment",
            "weight": 20,
            "anchors": {
              "0": "Axes or uncertainty materially distort the scientific comparison.",
              "2": "Scales are plausible but a comparison, baseline or uncertainty definition is unclear.",
              "4": "Scale choices support both small changes and baseline context; comparison, sample unit and uncertainty meaning are explicit and defensible."
            }
          },
          {
            "id": "R01-D",
            "name": "Composition, typography and accessible visual identity",
            "weight": 15,
            "anchors": {
              "0": "Important labels or data are unreadable.",
              "2": "Figure is readable at large size but has crowding or inconsistent identities at target size.",
              "4": "Clear reading order, consistent identities, accessible redundant encodings and legible typography work at 180 mm."
            }
          },
          {
            "id": "R01-E",
            "name": "Editable delivery, caption and targeted visual review",
            "weight": 15,
            "anchors": {
              "0": "Required vector/source artifacts or meaningful caption are absent.",
              "2": "SVG and preview exist but editability, regeneration or review evidence is incomplete.",
              "4": "Live text, separate editable elements, reproducible source, self-contained caption and concrete inspection evidence support reuse."
            }
          }
        ],
        "requirements": [
          {
            "id": "science",
            "requirement": "No material fabrication or loss of supplied values, pairing, units or separate experiment identity."
          },
          {
            "id": "vector",
            "requirement": "An openable SVG with live text and separately editable scientific elements is delivered."
          },
          {
            "id": "references",
            "requirement": "All three actual supplied figure references receive specific visual analysis."
          }
        ],
        "hard_caps": [
          {
            "requirement_id": "science",
            "max_score": 40,
            "reason": "Material scientific/data corruption"
          },
          {
            "requirement_id": "vector",
            "max_score": 35,
            "reason": "No usable editable vector result"
          },
          {
            "requirement_id": "references",
            "max_score": 70,
            "reason": "Required reference learning absent"
          }
        ],
        "required_observations": [
          {
            "id": "reference_figures",
            "label": "Read all three reference images and captions"
          },
          {
            "id": "output_visual",
            "label": "Inspect SVG and PNG at 180 mm"
          },
          {
            "id": "editable_source",
            "label": "Inspect live text, elements and source archive"
          },
          {
            "id": "data_audit",
            "label": "Cross-check all observations, pairing and summaries"
          },
          {
            "id": "written_artifacts",
            "label": "Read caption, design note and review"
          }
        ],
        "required_artifacts": [
          "figure.svg",
          "figure.png",
          "caption.md",
          "design-note.md",
          "source.zip",
          "review.md"
        ],
        "rating_scale": {
          "allowed": [
            0,
            1,
            2,
            3,
            4
          ],
          "intermediate": "1 and 3 require evidence showing performance between the adjacent published anchors; they are not default uncertainty scores.",
          "unassessed": null
        },
        "reviewer_checks": [
          "Open the three references: identify the actual visible choices claimed in the design note.",
          "Inspect final-size panels; check transient device IDs remain local to their experiment.",
          "Inspect SVG XML/live text and source archive rather than inferring editability from a PNG."
        ],
        "schema": "nrb-v2-manual-rubric"
      },
      "hash": "678e59622be7b3f9c5edf0c39954573e92ba9b6128df69a7478d09dd027ac0b6",
      "input_manifest_hash": "8d18417081913fb45c1d9c561e7f6c4452f2581dbbc7500df896a490e5aa8ee9"
    },
    "R02": {
      "spec": {
        "id": "R02",
        "mode": null,
        "benchmark_version": "2.0.0",
        "protocol_version": "nrb-subjective-v2.0",
        "rubric": [
          {
            "id": "R02-A",
            "name": "Data parsing, observation status and measurement semantics",
            "weight": 25,
            "anchors": {
              "0": "Censored, signed or paired observations are corrupted.",
              "2": "Data generally survive but a status or uncertainty definition is ambiguous.",
              "4": "Every row, pairing, status, unit and expanded-uncertainty definition survives the complete workflow."
            }
          },
          {
            "id": "R02-B",
            "name": "Purposeful scale choices for nearby and broad-range values",
            "weight": 25,
            "anchors": {
              "0": "A blanket scale rule produces misleading comparisons or drops data.",
              "2": "Scale choices are plausible but the rationale or baseline comparison is incomplete.",
              "4": "Axis-specific decisions explain absolute/relative comparisons, baseline, zero and dynamic range, with a useful diagnostic revealing tradeoffs."
            }
          },
          {
            "id": "R02-C",
            "name": "Numerical summaries and uncertainty treatment",
            "weight": 20,
            "anchors": {
              "0": "Summary calculations or error definitions are materially wrong.",
              "2": "Main summaries are usable but limited reproducibility or one uncertainty ambiguity remains.",
              "4": "Paired summaries, interval rendering and any sensitivity assumptions are numerically traceable and scientifically defensible."
            }
          },
          {
            "id": "R02-D",
            "name": "Scientific readability and caption",
            "weight": 15,
            "anchors": {
              "0": "Important information is unreadable or unexplained.",
              "2": "Most labels and caption are usable with some omissions at final size.",
              "4": "The figure and caption explain units, experimental unit, intervals, censoring, limits and visual encodings at final size."
            }
          },
          {
            "id": "R02-E",
            "name": "Runnable Python and transparent decisions",
            "weight": 15,
            "anchors": {
              "0": "Source cannot regenerate the outputs.",
              "2": "Source runs with manual intervention or incomplete environment/decision records.",
              "4": "A documented local command reproduces vector/raster outputs, summary table and scale-decision record without network access."
            }
          }
        ],
        "requirements": [
          {
            "id": "semantics",
            "requirement": "Pairing, signed/zero values and censoring retain their distinct meanings without invented point estimates."
          },
          {
            "id": "figures",
            "requirement": "Actual generated figures are supplied."
          },
          {
            "id": "source",
            "requirement": "Python source can regenerate the scientific figures from supplied data."
          }
        ],
        "hard_caps": [
          {
            "requirement_id": "semantics",
            "max_score": 40,
            "reason": "Material sign/pair/censoring corruption"
          },
          {
            "requirement_id": "figures",
            "max_score": 30,
            "reason": "No actual figures"
          },
          {
            "requirement_id": "source",
            "max_score": 60,
            "reason": "No usable regeneration source"
          }
        ],
        "required_observations": [
          {
            "id": "output_visual",
            "label": "Inspect main and alternative-scale figures at 180 mm"
          },
          {
            "id": "runtime",
            "label": "Attempt documented regeneration and record actual outcome"
          },
          {
            "id": "data_audit",
            "label": "Verify parsing, paired summaries and U(k=2) intervals"
          },
          {
            "id": "written_artifacts",
            "label": "Read captions and per-axis decisions"
          }
        ],
        "required_artifacts": [
          "plot.py",
          "requirements.txt",
          "figure.svg",
          "figure.png",
          "alternative-scale.png",
          "summary.csv",
          "scale-decisions.md",
          "caption.md"
        ],
        "rating_scale": {
          "allowed": [
            0,
            1,
            2,
            3,
            4
          ],
          "intermediate": "1 and 3 require evidence showing performance between the adjacent published anchors; they are not default uncertainty scores.",
          "unassessed": null
        },
        "reviewer_checks": [
          "Confirm S4/S8 have no measured point estimate; S1 remains negative and S2 zero.",
          "Verify expanded uncertainty is U(k=2), not raw sample SD; inspect every relevant axis.",
          "A failed documented regeneration is observed evidence; inability of the reviewer environment to execute is unassessed."
        ],
        "schema": "nrb-v2-manual-rubric"
      },
      "hash": "b6b6d513107313ce8bc8a3c5d68393274c2e9cf2fa71b6ac2a4b71cd3d8890c0",
      "input_manifest_hash": "23fe6092187f1c4b95f0ea1e27f64ef448b7c125bd1238975c5f42cb3f301785"
    },
    "R03": {
      "spec": {
        "id": "R03",
        "mode": null,
        "benchmark_version": "2.0.0",
        "protocol_version": "nrb-subjective-v2.0",
        "rubric": [
          {
            "id": "R03-A",
            "name": "Preservation of scientific facts and scope",
            "weight": 35,
            "anchors": {
              "0": "Material numbers, design, uncertainty or limits are invented or lost.",
              "2": "Most facts survive but one material qualification or design detail is weakened.",
              "4": "Every material fact, quantity, design relationship, uncertainty and temporal limit is preserved or transparently queried."
            }
          },
          {
            "id": "R03-B",
            "name": "Conservative treatment of unsupported scientific claims",
            "weight": 25,
            "anchors": {
              "0": "Unsupported significance, mechanism or generalization is retained or strengthened without disclosure.",
              "2": "Some problematic wording is corrected but the disposition or author query is incomplete.",
              "4": "Unsupported claims are handled transparently and proportionately, with precise author queries where required and no invented supporting evidence."
            }
          },
          {
            "id": "R03-C",
            "name": "Natural, precise English for the stated audience",
            "weight": 20,
            "anchors": {
              "0": "The prose remains inflated, incoherent or unsuitable for a manuscript.",
              "2": "Readable prose still contains unnecessary staging, repetition or vague claims.",
              "4": "Connected, economical manuscript prose uses specific subjects and verbs, varied natural rhythm and appropriate scientific qualification."
            }
          },
          {
            "id": "R03-D",
            "name": "Auditable claim ledger",
            "weight": 15,
            "anchors": {
              "0": "No useful claim ledger exists to audit preservation of the scientific record.",
              "2": "A ledger covers numbers but omits causal, uncertainty or scope claims.",
              "4": "A complete and navigable ledger ties original claims to edits, factual status and transparent dispositions."
            }
          },
          {
            "id": "R03-E",
            "name": "Editorial boundary and deliverable discipline",
            "weight": 5,
            "anchors": {
              "0": "The output claims verification or detector success.",
              "2": "The boundary is implied but queries or length constraints are poorly handled.",
              "4": "All deliverables meet scope and length, distinguish editing from validation, and make remaining author decisions explicit."
            }
          }
        ],
        "requirements": [
          {
            "id": "facts",
            "requirement": "All material quantitative/design/uncertainty/temporal facts remain faithful to the approved editorial record."
          },
          {
            "id": "claims",
            "requirement": "Unsupported significance, mechanism and long-term claims are explicitly removed, bounded or queried."
          },
          {
            "id": "ledger",
            "requirement": "A useful claim-by-claim ledger includes F01–F11 and unsupported claims."
          }
        ],
        "hard_caps": [
          {
            "requirement_id": "facts",
            "max_score": 35,
            "reason": "Material factual alteration or fabrication"
          },
          {
            "requirement_id": "claims",
            "max_score": 45,
            "reason": "Unsupported scientific certainty retained or strengthened"
          },
          {
            "requirement_id": "ledger",
            "max_score": 70,
            "reason": "No useful fact ledger"
          }
        ],
        "required_observations": [
          {
            "id": "input_record",
            "label": "Read draft and approved F01–F11"
          },
          {
            "id": "edited_prose",
            "label": "Read the entire edited passage and memo"
          },
          {
            "id": "claim_ledger",
            "label": "Trace every material claim through the ledger"
          }
        ],
        "required_artifacts": [
          "edited.md",
          "fact-ledger.csv",
          "edit-memo.md"
        ],
        "rating_scale": {
          "allowed": [
            0,
            1,
            2,
            3,
            4
          ],
          "intermediate": "1 and 3 require evidence showing performance between the adjacent published anchors; they are not default uncertainty scores.",
          "unassessed": null
        },
        "reviewer_checks": [
          "Use R03 approved means, not values recalculated from R01/R04 fixtures.",
          "p=0.08 is author-reported; no test family/statistic/interval or preregistered alpha was supplied.",
          "Removing an unsupported claim with an explicit ledger entry is valid; require no invented substitute evidence."
        ],
        "schema": "nrb-v2-manual-rubric"
      },
      "hash": "d97d4b5b1b2b3820f4a1d40f6d9753437199f6b94f20500af1e4145493248486",
      "input_manifest_hash": "8ef01bed92662848ab654f8164941d4ccab623d07650526aeff2fee2855cfa4b"
    },
    "R04": {
      "spec": {
        "id": "R04",
        "mode": null,
        "benchmark_version": "2.0.0",
        "protocol_version": "nrb-subjective-v2.0",
        "rubric": [
          {
            "id": "R04-A",
            "name": "Quantitative fidelity to the actual figure and data",
            "weight": 30,
            "anchors": {
              "0": "The text misstates observations or invents numerical results.",
              "2": "Most values are traceable but a quantitative comparison or unit is incomplete.",
              "4": "Three or more scientifically useful numerical statements are correct, traceable to calculations and tied to the actual panels."
            }
          },
          {
            "id": "R04-B",
            "name": "Reasoning across observation, interpretation and mechanism",
            "weight": 25,
            "anchors": {
              "0": "Hypotheses or short-term observations are promoted to established mechanism or durability.",
              "2": "Interpretation is mostly restrained but an evidential boundary or experiment relationship remains unclear.",
              "4": "Results, inference and hypotheses are explicitly distinguished, experiments remain distinct and a discriminating follow-up has meaningful alternative predictions."
            }
          },
          {
            "id": "R04-C",
            "name": "Manuscript argument and readable English",
            "weight": 20,
            "anchors": {
              "0": "Paragraphs are disconnected, generic or unsuitable for a paper.",
              "2": "The narrative is understandable but repetitive or weakly organized around the scientific question.",
              "4": "Each paragraph has a clear scientific purpose and connected argument, with precise language and appropriately bounded significance."
            }
          },
          {
            "id": "R04-D",
            "name": "Caption, units, interval and experimental structure",
            "weight": 10,
            "anchors": {
              "0": "Caption materially misdefines the figure.",
              "2": "Caption is usable but omits one important definition or scope limit.",
              "4": "Caption accurately and independently explains both panels, independent units, batch encodings and interval definitions."
            }
          },
          {
            "id": "R04-E",
            "name": "Claim audit and reproducible numerical support",
            "weight": 15,
            "anchors": {
              "0": "No usable evidence table or calculation source exists.",
              "2": "Most claims map to sources but some rejected notes or calculations are not auditable.",
              "4": "A complete claim map distinguishes adopted and rejected notes, supports calculations with runnable code and states unresolved scientific limitations."
            }
          }
        ],
        "requirements": [
          {
            "id": "science",
            "requirement": "No invented data, inferred mechanism or unmeasured durability is presented as established."
          },
          {
            "id": "panels",
            "requirement": "Both actual input panels and the separate experiments are interpreted."
          },
          {
            "id": "trace",
            "requirement": "Quantitative claims have usable evidence links and reproducible calculations."
          }
        ],
        "hard_caps": [
          {
            "requirement_id": "science",
            "max_score": 40,
            "reason": "Fabrication or unsupported mechanism/durability claim"
          },
          {
            "requirement_id": "panels",
            "max_score": 60,
            "reason": "Actual two-panel interpretation absent"
          },
          {
            "requirement_id": "trace",
            "max_score": 65,
            "reason": "No auditable calculations"
          }
        ],
        "required_observations": [
          {
            "id": "input_figure",
            "label": "Inspect F1a/F1b and their plotted encodings"
          },
          {
            "id": "manuscript",
            "label": "Read results, discussion and caption"
          },
          {
            "id": "numerical_audit",
            "label": "Recompute material quantitative claims"
          },
          {
            "id": "evidence_ledger",
            "label": "Check adopted and rejected rough notes"
          }
        ],
        "required_artifacts": [
          "manuscript.md",
          "caption.md",
          "claim-evidence.csv",
          "calculations.py",
          "calculated-summary.csv"
        ],
        "rating_scale": {
          "allowed": [
            0,
            1,
            2,
            3,
            4
          ],
          "intermediate": "1 and 3 require evidence showing performance between the adjacent published anchors; they are not default uncertainty scores.",
          "unassessed": null
        },
        "reviewer_checks": [
          "F1a has individual paired observations; F1b is the distinct six-device experiment with arithmetic mean ± sample SD.",
          "D08 has a negative paired change; evaluate claims of all-device improvement against that observation.",
          "Require a meaningful predicted distinction between two alternatives in the proposed follow-up; no extra literature is needed."
        ],
        "schema": "nrb-v2-manual-rubric"
      },
      "hash": "b1e3905d400fa6efe7e17f73af69699fab2674af57d0c459a2223178102bb68b",
      "input_manifest_hash": "17f7f8c3aa4dbd8c43657b73514230944e07ea264cd012d0ff33cf10517f562c"
    },
    "R05": {
      "spec": {
        "id": "R05",
        "mode": null,
        "benchmark_version": "2.0.0",
        "protocol_version": "nrb-subjective-v2.0",
        "rubric": [
          {
            "id": "R05-reading",
            "name": "三文阅读、方法与材料边界",
            "weight": 20,
            "anchors": {
              "0": "Central source methods, units or evidence types are wrong or one paper is ignored.",
              "2": "All sources are present but some denominators, evidence types or available-material limits are vague.",
              "4": "All three papers and relevant supplied P1 supplement are accurately read, with correct units/denominators, exact locations and bounded scope."
            }
          },
          {
            "id": "R05-synthesis",
            "name": "跨来源综合与条件性工作流程",
            "weight": 25,
            "anchors": {
              "0": "The review is unsupported summaries or universal design prescriptions.",
              "2": "A usable cross-source argument exists but tradeoffs or practical implications are incompletely justified.",
              "4": "A coherent argument connects the three sources, explains at least two conditional tradeoffs, distinguishes inference from author claims and gives a grounded workflow and testable gap."
            }
          },
          {
            "id": "R05-evidence",
            "name": "主张定位、比较与引用",
            "weight": 20,
            "anchors": {
              "0": "Central citations are invented or the table creates false comparability.",
              "2": "Most claims are supported but exact locations or status distinctions are incomplete.",
              "4": "At least ten useful claims are traceable across prose/table/figures, at least three synthesis/inferred-premise rows are labelled, and all three bibliography records are accurate."
            }
          },
          {
            "id": "R05-reproduction",
            "name": "两项有界方法复现",
            "weight": 25,
            "anchors": {
              "0": "A required calculation is absent or substantially wrong or mislabelled.",
              "2": "Both demonstrations exist but a result, source-to-code mapping, pairing or metric definition is materially weak.",
              "4": "Both methods compute the required summaries/distances and diagnostics correctly, use exact source expressions/coordinates, and include a meaningful consistency check each."
            }
          },
          {
            "id": "R05-delivery",
            "name": "可复现交付与结论校准",
            "weight": 10,
            "anchors": {
              "0": "Code/outputs are unusable or synthetic demos are claimed as full paper replication.",
              "2": "Artifacts mostly run but versions, commands or unreplicated boundaries remain unclear.",
              "4": "Documented local execution regenerates outputs, limitations and methodological ambiguities are explicit, and the closed evidence set is not called systematic or comprehensive."
            }
          }
        ],
        "requirements": [
          {
            "id": "evidence",
            "requirement": "No fabricated source, central material misreading, unperformed full reproduction or falsely systematic review."
          },
          {
            "id": "two_methods",
            "requirement": "Both bounded methods have actual numerical and graphical artifacts."
          },
          {
            "id": "three_sources",
            "requirement": "All three papers and relevant supplied P1 supplement are substantively used."
          }
        ],
        "hard_caps": [
          {
            "requirement_id": "evidence",
            "max_score": 40,
            "reason": "Fabricated/overclaimed scientific evidence"
          },
          {
            "requirement_id": "two_methods",
            "max_score": 60,
            "reason": "A required method has no real output"
          },
          {
            "requirement_id": "three_sources",
            "max_score": 65,
            "reason": "Incomplete required source reading"
          }
        ],
        "required_observations": [
          {
            "id": "source_reading",
            "label": "Read sufficient supplied source text/figures/S1 to judge claims"
          },
          {
            "id": "review_evidence",
            "label": "Audit prose, comparative table, ledger and bibliography"
          },
          {
            "id": "code_execution",
            "label": "Attempt documented code and verify numerical results"
          },
          {
            "id": "output_figures",
            "label": "Inspect both actual editable diagnostics"
          }
        ],
        "required_artifacts": [
          "review.md",
          "comparison.csv",
          "claim-evidence.csv",
          "references.bib",
          "replicate.py",
          "requirements.txt",
          "paired-summary.csv",
          "colour-distance.csv",
          "paired-demonstration.svg",
          "colour-diagnostic.svg",
          "reproduction-note.md"
        ],
        "rating_scale": {
          "allowed": [
            0,
            1,
            2,
            3,
            4
          ],
          "intermediate": "1 and 3 require evidence showing performance between the adjacent published anchors; they are not default uncertainty scores.",
          "unassessed": null
        },
        "reviewer_checks": [
          "Verify pairing is within each variant; do not let matching marginal summaries substitute for paired-difference analysis.",
          "Check the expression actually printed in P3 Methods; a label or similarly named package is not evidence of the implemented metric.",
          "Inspect missing-SI/code boundaries and do not impose absent source details as hidden requirements.",
          "This merged task does not require separate long source cards, glossary or a second evidence-map SVG."
        ],
        "schema": "nrb-v2-manual-rubric"
      },
      "hash": "d50fb502f4a90cf9254839767e93af486dad14b5b12664b99f7006dd421ec33d",
      "input_manifest_hash": "3ad1ca5eec03ac93069a5a163637cf99e2384a5a72a6a9608b56ae76e7ba2674"
    },
    "R06-A": {
      "spec": {
        "id": "R06",
        "mode": "A",
        "benchmark_version": "2.0.0",
        "protocol_version": "nrb-subjective-v2.0",
        "rubric": [
          {
            "id": "R06-A-technical",
            "name": "技术交付 / Technical delivery",
            "weight": 10,
            "anchors": {
              "0": "No valid playable video or seriously corrupted media.",
              "2": "Playable video with a material size, frame-rate or decoding defect.",
              "4": "Complete 1920×1080 H.264 output, 24 fps and 240 frames, with no unintended corrupt or black frames."
            }
          },
          {
            "id": "R06-A-timing",
            "name": "时间结构 / Temporal structure",
            "weight": 15,
            "anchors": {
              "0": "Major scenes are missing, out of order or temporally unusable.",
              "2": "Six scenes are present but cuts, duration or transitions have substantial defects.",
              "4": "All six scenes and target intervals are clear; transitions and action establish coherent pacing without penalizing harmless one-frame overlap."
            }
          },
          {
            "id": "R06-A-keying",
            "name": "绿幕合成 / Chroma-key compositing",
            "weight": 15,
            "anchors": {
              "0": "Studio background, rectangular source frame or major subject loss remains.",
              "2": "Subject is separated but green spill, edge chatter, floor mat or holes remain visibly distracting.",
              "4": "Hair, hands and moving contours remain stable; spill and studio artifacts are controlled without losing the subject or held object."
            }
          },
          {
            "id": "R06-A-typography",
            "name": "排版与文字 / Typography and copy",
            "weight": 15,
            "anchors": {
              "0": "Required copy is missing or largely unreadable.",
              "2": "Most copy is correct but hierarchy, placement or motion reduces readability.",
              "4": "All COPY.txt text is exact, clearly organized and legible; typography actively participates in the required animation."
            }
          },
          {
            "id": "R06-A-motion",
            "name": "运动设计 / Motion design",
            "weight": 20,
            "anchors": {
              "0": "Required mechanisms are absent or replaced by static images.",
              "2": "Recognizable motion exists but trajectories, easing or continuous mechanisms have major defects.",
              "4": "Orbit, waves, ribbons, iris and confetti show coherent trajectories, continuous motion, intentional speed and controlled transitions."
            }
          },
          {
            "id": "R06-A-depth",
            "name": "遮挡与空间 / Occlusion and depth",
            "weight": 10,
            "anchors": {
              "0": "Depth interactions are absent or faked only by global opacity.",
              "2": "Some depth cues work but orbit or ribbon ordering is inconsistent or incomplete.",
              "4": "Text and ribbon genuinely pass behind and in front of the actor with legible depth changes and sound layer ordering."
            }
          },
          {
            "id": "R06-A-finish",
            "name": "视觉完成度 / Visual finish",
            "weight": 15,
            "anchors": {
              "0": "The sequence is incoherent, unfinished or unreadable.",
              "2": "A usable design exists but palette, spacing, framing or ending has visible weaknesses.",
              "4": "Six scenes form a consistent readable design with balanced color, spacing and framing, and a complete stable ending."
            }
          }
        ],
        "requirements": [
          {
            "id": "actual_video",
            "requirement": "An actual complete playable output video exists."
          },
          {
            "id": "source_identity",
            "requirement": "The supplied actor/object and chronological one-to-one source time are retained."
          },
          {
            "id": "editable",
            "requirement": "Usable editable project/code is delivered."
          },
          {
            "id": "soundtrack",
            "requirement": "The supplied soundtrack is included in full at its original rate without replacement."
          },
          {
            "id": "rights",
            "requirement": "Required source/font credits and modification notices are retained."
          },
          {
            "id": "mode_integrity",
            "requirement": "Mode was preregistered; A had no reference access; B did not copy reference frames into the output."
          }
        ],
        "hard_caps": [
          {
            "requirement_id": "actual_video",
            "max_score": 0,
            "reason": "No actual playable video"
          },
          {
            "requirement_id": "source_identity",
            "max_score": 40,
            "reason": "Material loss/replacement of source identity or time"
          },
          {
            "requirement_id": "editable",
            "max_score": 70,
            "reason": "No usable editable project"
          },
          {
            "requirement_id": "soundtrack",
            "max_score": 80,
            "reason": "Required soundtrack absent or replaced"
          },
          {
            "requirement_id": "rights",
            "max_score": 80,
            "reason": "Required provenance absent"
          },
          {
            "requirement_id": "mode_integrity",
            "max_score": 0,
            "reason": "Declared experimental condition violated"
          }
        ],
        "required_observations": [
          {
            "id": "source_video",
            "label": "Watch full source.mp4"
          },
          {
            "id": "candidate_video",
            "label": "Watch full output.mp4 with moving contours/text"
          },
          {
            "id": "candidate_audio",
            "label": "Listen to candidate audio and compare supplied soundtrack"
          },
          {
            "id": "editable_source",
            "label": "Inspect submitted project/source"
          },
          {
            "id": "media_probe",
            "label": "Read actual duration/frame/codec/decode information"
          },
          {
            "id": "scene_1",
            "label": "Observe scene 1 with timecoded evidence"
          },
          {
            "id": "scene_2",
            "label": "Observe scene 2 with timecoded evidence"
          },
          {
            "id": "scene_3",
            "label": "Observe scene 3 with timecoded evidence"
          },
          {
            "id": "scene_4",
            "label": "Observe scene 4 with timecoded evidence"
          },
          {
            "id": "scene_5",
            "label": "Observe scene 5 with timecoded evidence"
          },
          {
            "id": "scene_6",
            "label": "Observe scene 6 with timecoded evidence"
          }
        ],
        "required_artifacts": [
          "output.mp4",
          "source.zip",
          "README.md",
          "LICENSES.md",
          "run-record.json"
        ],
        "rating_scale": {
          "allowed": [
            0,
            1,
            2,
            3,
            4
          ],
          "intermediate": "1 and 3 require evidence showing performance between the adjacent published anchors; they are not default uncertainty scores.",
          "unassessed": null
        },
        "reviewer_checks": [
          "Confirm mode before exposing the candidate to any input; retain attempt/intervention record.",
          "Record timecoded observations for all six scenes; contact sheets do not certify motion.",
          "Actual audio listening and media probe are separate from visual scoring; decoded PCM need not be byte-identical after AAC compression.",
          "No single pixel-error score substitutes for human evaluation.",
          "Do not distribute evaluator or demo_project files.",
          "Do not use author-reference likeness as an A criterion; do not expose the reference to the candidate."
        ],
        "schema": "nrb-v2-manual-rubric"
      },
      "hash": "80f71c1c8ff43ad510c6fde9981408499a440807759bae64108f4b38b2a2461a",
      "input_manifest_hash": "c885554b6938387322943646c4eacfbc54af60e422f3e039a7c2307a38e99c55"
    },
    "R06-B": {
      "spec": {
        "id": "R06",
        "mode": "B",
        "benchmark_version": "2.0.0",
        "protocol_version": "nrb-subjective-v2.0",
        "rubric": [
          {
            "id": "R06-B-technical",
            "name": "技术交付 / Technical delivery",
            "weight": 10,
            "anchors": {
              "0": "No valid playable video or seriously corrupted media.",
              "2": "Playable video with a material size, frame-rate or decoding defect.",
              "4": "Complete 1920×1080 H.264 output, 24 fps and 240 frames, with no unintended corrupt or black frames."
            }
          },
          {
            "id": "R06-B-timing",
            "name": "时间结构 / Temporal structure",
            "weight": 10,
            "anchors": {
              "0": "Major scenes are missing, out of order or temporally unusable.",
              "2": "Six scenes are present but cuts, duration or transitions have substantial defects.",
              "4": "All six scenes and target intervals are clear; transitions and action establish coherent pacing without penalizing harmless one-frame overlap."
            }
          },
          {
            "id": "R06-B-keying",
            "name": "绿幕合成 / Chroma-key compositing",
            "weight": 15,
            "anchors": {
              "0": "Studio background, rectangular source frame or major subject loss remains.",
              "2": "Subject is separated but green spill, edge chatter, floor mat or holes remain visibly distracting.",
              "4": "Hair, hands and moving contours remain stable; spill and studio artifacts are controlled without losing the subject or held object."
            }
          },
          {
            "id": "R06-B-typography",
            "name": "排版与文字 / Typography and copy",
            "weight": 10,
            "anchors": {
              "0": "Required copy is missing or largely unreadable.",
              "2": "Most copy is correct but hierarchy, placement or motion reduces readability.",
              "4": "All COPY.txt text is exact, clearly organized and legible; typography actively participates in the required animation."
            }
          },
          {
            "id": "R06-B-motion",
            "name": "运动设计 / Motion design",
            "weight": 15,
            "anchors": {
              "0": "Required mechanisms are absent or replaced by static images.",
              "2": "Recognizable motion exists but trajectories, easing or continuous mechanisms have major defects.",
              "4": "Orbit, waves, ribbons, iris and confetti show coherent trajectories, continuous motion, intentional speed and controlled transitions."
            }
          },
          {
            "id": "R06-B-depth",
            "name": "遮挡与空间 / Occlusion and depth",
            "weight": 10,
            "anchors": {
              "0": "Depth interactions are absent or faked only by global opacity.",
              "2": "Some depth cues work but orbit or ribbon ordering is inconsistent or incomplete.",
              "4": "Text and ribbon genuinely pass behind and in front of the actor with legible depth changes and sound layer ordering."
            }
          },
          {
            "id": "R06-B-finish",
            "name": "视觉完成度 / Visual finish",
            "weight": 10,
            "anchors": {
              "0": "The sequence is incoherent, unfinished or unreadable.",
              "2": "A usable design exists but palette, spacing, framing or ending has visible weaknesses.",
              "4": "Six scenes form a consistent readable design with balanced color, spacing and framing, and a complete stable ending."
            }
          },
          {
            "id": "R06-B-reference",
            "name": "参考重建 / Reference reconstruction",
            "weight": 20,
            "anchors": {
              "0": "The submitted work does not meaningfully reconstruct the supplied reference.",
              "2": "Some reference structure is reproduced but composition, timing or movement differs materially.",
              "4": "Composition and scale, trajectory and rhythm, palette and depth, and transitions closely reconstruct the supplied reference without requiring pixel identity."
            }
          }
        ],
        "requirements": [
          {
            "id": "actual_video",
            "requirement": "An actual complete playable output video exists."
          },
          {
            "id": "source_identity",
            "requirement": "The supplied actor/object and chronological one-to-one source time are retained."
          },
          {
            "id": "editable",
            "requirement": "Usable editable project/code is delivered."
          },
          {
            "id": "soundtrack",
            "requirement": "The supplied soundtrack is included in full at its original rate without replacement."
          },
          {
            "id": "rights",
            "requirement": "Required source/font credits and modification notices are retained."
          },
          {
            "id": "mode_integrity",
            "requirement": "Mode was preregistered; A had no reference access; B did not copy reference frames into the output."
          }
        ],
        "hard_caps": [
          {
            "requirement_id": "actual_video",
            "max_score": 0,
            "reason": "No actual playable video"
          },
          {
            "requirement_id": "source_identity",
            "max_score": 40,
            "reason": "Material loss/replacement of source identity or time"
          },
          {
            "requirement_id": "editable",
            "max_score": 70,
            "reason": "No usable editable project"
          },
          {
            "requirement_id": "soundtrack",
            "max_score": 80,
            "reason": "Required soundtrack absent or replaced"
          },
          {
            "requirement_id": "rights",
            "max_score": 80,
            "reason": "Required provenance absent"
          },
          {
            "requirement_id": "mode_integrity",
            "max_score": 0,
            "reason": "Declared experimental condition violated"
          }
        ],
        "required_observations": [
          {
            "id": "source_video",
            "label": "Watch full source.mp4"
          },
          {
            "id": "candidate_video",
            "label": "Watch full output.mp4 with moving contours/text"
          },
          {
            "id": "candidate_audio",
            "label": "Listen to candidate audio and compare supplied soundtrack"
          },
          {
            "id": "editable_source",
            "label": "Inspect submitted project/source"
          },
          {
            "id": "media_probe",
            "label": "Read actual duration/frame/codec/decode information"
          },
          {
            "id": "scene_1",
            "label": "Observe scene 1 with timecoded evidence"
          },
          {
            "id": "scene_2",
            "label": "Observe scene 2 with timecoded evidence"
          },
          {
            "id": "scene_3",
            "label": "Observe scene 3 with timecoded evidence"
          },
          {
            "id": "scene_4",
            "label": "Observe scene 4 with timecoded evidence"
          },
          {
            "id": "scene_5",
            "label": "Observe scene 5 with timecoded evidence"
          },
          {
            "id": "scene_6",
            "label": "Observe scene 6 with timecoded evidence"
          },
          {
            "id": "reference_video",
            "label": "Watch full reference.mp4"
          }
        ],
        "required_artifacts": [
          "output.mp4",
          "source.zip",
          "README.md",
          "LICENSES.md",
          "run-record.json"
        ],
        "rating_scale": {
          "allowed": [
            0,
            1,
            2,
            3,
            4
          ],
          "intermediate": "1 and 3 require evidence showing performance between the adjacent published anchors; they are not default uncertainty scores.",
          "unassessed": null
        },
        "reviewer_checks": [
          "Confirm mode before exposing the candidate to any input; retain attempt/intervention record.",
          "Record timecoded observations for all six scenes; contact sheets do not certify motion.",
          "Actual audio listening and media probe are separate from visual scoring; decoded PCM need not be byte-identical after AAC compression.",
          "No single pixel-error score substitutes for human evaluation.",
          "Do not distribute evaluator or demo_project files.",
          "Watch full supplied reference before judging composition, trajectory, rhythm and depth; detect copied reference frames separately from legitimate reconstruction."
        ],
        "schema": "nrb-v2-manual-rubric"
      },
      "hash": "80abacfd3dfee039ac80e310315522ceebdc4092f00378093a55f79a8fe775e5",
      "input_manifest_hash": "b6127a19f9b8934959e28de93c9c451152d4f261f731a665ef5e183b88bffa98"
    },
    "H01": {
      "spec": {
        "id": "H01",
        "mode": null,
        "benchmark_version": "2.0.0",
        "protocol_version": "nrb-subjective-v2.0",
        "rubric": [
          {
            "id": "H01-science",
            "name": "科学数据与尺度语义",
            "weight": 25,
            "anchors": {
              "0": "Pairing, sign, censoring or uncertainty is materially corrupted.",
              "2": "Most data are preserved but one important interpretation or scale issue remains.",
              "4": "All views retain correct pairing, units, signs, missing/censored status and U(k=2) meaning with useful comparisons."
            }
          },
          {
            "id": "H01-interaction",
            "name": "筛选、详情返回与状态一致性",
            "weight": 30,
            "anchors": {
              "0": "Controls are absent, inert or operate on unrelated static examples.",
              "2": "Main controls work but filtering/counts/details/return/reset are inconsistent in an important state.",
              "4": "Batch plus ID filtering, summaries, details, return, excluded selections, zero matches and reset all remain consistent across views."
            }
          },
          {
            "id": "H01-offline",
            "name": "离线、真实导出与原子导入",
            "weight": 20,
            "anchors": {
              "0": "HTML needs a server/network or export/import is fake or destroys state.",
              "2": "Most offline/export paths work but invalid-state handling or filtered CSV has a defect.",
              "4": "Single HTML works offline, exports actual current records, round-trips valid state and rejects invalid schema/data without partial mutation."
            }
          },
          {
            "id": "H01-visual",
            "name": "布局、响应式与可访问性",
            "weight": 15,
            "anchors": {
              "0": "Key content is unreadable or important controls cannot be operated.",
              "2": "Usable desktop view has meaningful narrow-screen/keyboard/alternative-data limitations.",
              "4": "Clear low-clutter layout works at 1280 and 390 px, keyboard controls have names, and data remain accessible without hover or color alone."
            }
          },
          {
            "id": "H01-verification",
            "name": "真实验证与边界",
            "weight": 10,
            "anchors": {
              "0": "Claims of verified behavior are invented or no useful record exists.",
              "2": "A checklist exists but actual versus inferred outcomes or limits are vague.",
              "4": "Specific checks state browser/width/actions/outcomes and honestly separate real browser tests, code inspection and untested behavior."
            }
          }
        ],
        "requirements": [
          {
            "id": "offline",
            "requirement": "Actual single-file HTML is delivered and usable offline."
          },
          {
            "id": "interactive",
            "requirement": "Core controls update real data and state rather than only styling."
          },
          {
            "id": "science",
            "requirement": "Pairing, signed values, censoring and uncertainty remain scientifically faithful."
          },
          {
            "id": "state_safety",
            "requirement": "Filtered CSV matches records and invalid state imports do not partially change the application."
          }
        ],
        "hard_caps": [
          {
            "requirement_id": "offline",
            "max_score": 35,
            "reason": "Missing or network-dependent application"
          },
          {
            "requirement_id": "interactive",
            "max_score": 40,
            "reason": "Core interactions are only decoration"
          },
          {
            "requirement_id": "science",
            "max_score": 45,
            "reason": "Material scientific semantics corruption"
          },
          {
            "requirement_id": "state_safety",
            "max_score": 60,
            "reason": "Export mismatch or destructive partial import"
          }
        ],
        "required_observations": [
          {
            "id": "offline_open",
            "label": "Open actual HTML with network unavailable"
          },
          {
            "id": "interaction_walkthrough",
            "label": "Operate filter/search/details/back/reset/empty states"
          },
          {
            "id": "downloads",
            "label": "Open actual downloaded CSV and state JSON"
          },
          {
            "id": "import_atomicity",
            "label": "Test valid and malformed/invalid state imports"
          },
          {
            "id": "responsive_keyboard",
            "label": "Inspect 1280/390 px and keyboard operation"
          },
          {
            "id": "scientific_data",
            "label": "Cross-check values, statuses, summaries and intervals"
          },
          {
            "id": "verification_note",
            "label": "Read declared test scope and compare to evidence"
          }
        ],
        "required_artifacts": [
          "workbench.html",
          "verification.md"
        ],
        "rating_scale": {
          "allowed": [
            0,
            1,
            2,
            3,
            4
          ],
          "intermediate": "1 and 3 require evidence showing performance between the adjacent published anchors; they are not default uncertainty scores.",
          "unassessed": null
        },
        "reviewer_checks": [
          {
            "id": "reset",
            "action": "Reset, clear search, select all batches",
            "expect": "12 paired devices; original pair data retained."
          },
          {
            "id": "batch",
            "action": "Select B2 and search \" d0 \" (with spaces)",
            "expect": "Four visible devices D05–D08; summaries use exactly these four pairs."
          },
          {
            "id": "detail",
            "action": "Open D08 then return",
            "expect": "Shows B2, 1002.0 mV before and 1001.9 mV after, difference -0.1 mV within displayed rounding; return retains prior filter/search/view."
          },
          {
            "id": "empty",
            "action": "Select B2 and search D01",
            "expect": "Zero devices; no stale summary or detail. Export disabled with local explanation OR valid header-only CSV."
          },
          {
            "id": "csv",
            "action": "Clear search, leave B2, export paired CSV",
            "expect": "Header device,batch,before_mV,after_mV and four original B2 rows; no hidden all-data export."
          },
          {
            "id": "state",
            "action": "Export state, change filters and comparison, import exported state",
            "expect": "Valid nrb-h01-state-v1 restores all exported state and corresponding views."
          },
          {
            "id": "invalid",
            "action": "Import malformed JSON; then well-formed files with unknown schema/batch/mode",
            "expect": "Useful local error; original state and embedded data unchanged in every case."
          },
          {
            "id": "scale",
            "action": "Toggle paired comparison and dose scales; inspect signed/censored data",
            "expect": "Correct count/units/intervals; negative/zero survive; censored has no invented point estimate."
          },
          {
            "id": "access",
            "action": "Use only keyboard; inspect at 1280 and 390 px",
            "expect": "Named operable controls; no body overflow; accessible data table/text; local table scroll allowed."
          }
        ],
        "schema": "nrb-v2-manual-rubric"
      },
      "hash": "12bc068e1b82767b040d190b813840b56649ed83c21b1171b89c021005b29648",
      "input_manifest_hash": "7aa6febcfd501d4d92cf76ba6705d8a9d156d3ead39a3dea3b96682ad48648ed"
    }
  },
  "grading": {
    "schema": "nrb-auto-report-v2",
    "version": "2.0.0",
    "grader_version": "2.0.0",
    "evaluatorFingerprint": "7f2487673f1a214d60311193a369d48ab9215f9d7006554bf5c823e6ce5c7aa3",
    "seed_policy": "The manifest binds seed, check contract and evaluator source. Execution records separately hash actual numerical inputs.",
    "tasks": {
      "P01": {
        "packet_hash": "94d470a3e60e8688ba67faf2a1e3dc8d7b238072c3498836a915e481c4f1a7d0",
        "seeds": {
          "0": {
            "packet_hash": "c2d8aa5f2c4b8cd00e4d02c7ab7e6a1a1d8cc09cb2534c2166cf6effea217482",
            "test_manifest_hash": "9e3de58abc54a0cdba0ed490592f3714c1a871b83055ec75125ea88a9fb516ca",
            "checks": [
              {
                "id": "parse_units",
                "tier": "basic",
                "weight": 12,
                "critical": true
              },
              {
                "id": "empty",
                "tier": "basic",
                "weight": 8,
                "critical": false
              },
              {
                "id": "duplicates_missing",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "quoted_bom",
                "tier": "scientific",
                "weight": 15,
                "critical": false
              },
              {
                "id": "scaled_variance",
                "tier": "stress",
                "weight": 10,
                "critical": false
              },
              {
                "id": "invalid_0",
                "tier": "stress",
                "weight": 2,
                "critical": false
              },
              {
                "id": "invalid_1",
                "tier": "stress",
                "weight": 2,
                "critical": false
              },
              {
                "id": "invalid_2",
                "tier": "stress",
                "weight": 2,
                "critical": false
              },
              {
                "id": "invalid_3",
                "tier": "stress",
                "weight": 2,
                "critical": false
              },
              {
                "id": "invalid_4",
                "tier": "stress",
                "weight": 2,
                "critical": false
              }
            ]
          },
          "17": {
            "packet_hash": "94d470a3e60e8688ba67faf2a1e3dc8d7b238072c3498836a915e481c4f1a7d0",
            "test_manifest_hash": "7fc0024520539bfa577500e24a312f70e6f2149860fd1dc2871ff9ae70ac5206",
            "checks": [
              {
                "id": "parse_units",
                "tier": "basic",
                "weight": 12,
                "critical": true
              },
              {
                "id": "empty",
                "tier": "basic",
                "weight": 8,
                "critical": false
              },
              {
                "id": "duplicates_missing",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "quoted_bom",
                "tier": "scientific",
                "weight": 15,
                "critical": false
              },
              {
                "id": "scaled_variance",
                "tier": "stress",
                "weight": 10,
                "critical": false
              },
              {
                "id": "invalid_0",
                "tier": "stress",
                "weight": 2,
                "critical": false
              },
              {
                "id": "invalid_1",
                "tier": "stress",
                "weight": 2,
                "critical": false
              },
              {
                "id": "invalid_2",
                "tier": "stress",
                "weight": 2,
                "critical": false
              },
              {
                "id": "invalid_3",
                "tier": "stress",
                "weight": 2,
                "critical": false
              },
              {
                "id": "invalid_4",
                "tier": "stress",
                "weight": 2,
                "critical": false
              }
            ]
          },
          "2026": {
            "packet_hash": "b847aabf2a8aa20b82132401f67827c10abaf086d6202e174ad1480101378ba0",
            "test_manifest_hash": "af171688e28ef954a6ed80de5b173732e96d69b653e13912c06382181c44b088",
            "checks": [
              {
                "id": "parse_units",
                "tier": "basic",
                "weight": 12,
                "critical": true
              },
              {
                "id": "empty",
                "tier": "basic",
                "weight": 8,
                "critical": false
              },
              {
                "id": "duplicates_missing",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "quoted_bom",
                "tier": "scientific",
                "weight": 15,
                "critical": false
              },
              {
                "id": "scaled_variance",
                "tier": "stress",
                "weight": 10,
                "critical": false
              },
              {
                "id": "invalid_0",
                "tier": "stress",
                "weight": 2,
                "critical": false
              },
              {
                "id": "invalid_1",
                "tier": "stress",
                "weight": 2,
                "critical": false
              },
              {
                "id": "invalid_2",
                "tier": "stress",
                "weight": 2,
                "critical": false
              },
              {
                "id": "invalid_3",
                "tier": "stress",
                "weight": 2,
                "critical": false
              },
              {
                "id": "invalid_4",
                "tier": "stress",
                "weight": 2,
                "critical": false
              }
            ]
          }
        }
      },
      "P02": {
        "packet_hash": "3493b9cb506bfea3c1594383d936e49cb12b0bcfead93a9ea62392125d1f24f9",
        "seeds": {
          "0": {
            "packet_hash": "1fdd71b8b53fb02d818a434977d005584c0f462890615538d64a6e6d92b32c58",
            "test_manifest_hash": "be37eb141eb050d3fd8a0ee1f375a30d88da6f7761ff496b9994c693ef9398a5",
            "checks": [
              {
                "id": "one_group",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "paired_groups",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "unequal_technical_repeats",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "stratum_target",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "zero_and_uint32",
                "tier": "stress",
                "weight": 10,
                "critical": false
              },
              {
                "id": "invalid_0",
                "tier": "stress",
                "weight": 5,
                "critical": false
              },
              {
                "id": "invalid_1",
                "tier": "stress",
                "weight": 5,
                "critical": false
              }
            ]
          },
          "17": {
            "packet_hash": "3493b9cb506bfea3c1594383d936e49cb12b0bcfead93a9ea62392125d1f24f9",
            "test_manifest_hash": "03687f92057738566a80feb973019eb9cab71f130abcb4e8c46c5931c63f821c",
            "checks": [
              {
                "id": "one_group",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "paired_groups",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "unequal_technical_repeats",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "stratum_target",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "zero_and_uint32",
                "tier": "stress",
                "weight": 10,
                "critical": false
              },
              {
                "id": "invalid_0",
                "tier": "stress",
                "weight": 5,
                "critical": false
              },
              {
                "id": "invalid_1",
                "tier": "stress",
                "weight": 5,
                "critical": false
              }
            ]
          },
          "2026": {
            "packet_hash": "9615bb144d8ac9059f1773b269c9cd22a47c36d5a7a57c1a494951a185eb1931",
            "test_manifest_hash": "130904235659aaf3caf484ee57d6b2a71a20f63c411525f678fe1b52312b1011",
            "checks": [
              {
                "id": "one_group",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "paired_groups",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "unequal_technical_repeats",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "stratum_target",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "zero_and_uint32",
                "tier": "stress",
                "weight": 10,
                "critical": false
              },
              {
                "id": "invalid_0",
                "tier": "stress",
                "weight": 5,
                "critical": false
              },
              {
                "id": "invalid_1",
                "tier": "stress",
                "weight": 5,
                "critical": false
              }
            ]
          }
        }
      },
      "P03": {
        "packet_hash": "3b884a94b079c2dd4f405ccd33154ff62e4afa6e953a77d3c3c44991f4ab4a32",
        "seeds": {
          "0": {
            "packet_hash": "cf5a670418d71d95d893afd8f6c358258d0af4ae81acf4f549527d02ebb7f152",
            "test_manifest_hash": "669d973bfcbdb3d9bcf3a31fbfbf19c7e38bde8c27f4d865b4182a14a7136dea",
            "checks": [
              {
                "id": "one_cell_two_boundaries",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "zero_steps",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "heterogeneous_conservative",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "source_fixed_mix",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "one_cell_source",
                "tier": "stress",
                "weight": 5,
                "critical": false
              },
              {
                "id": "stiff_implicit",
                "tier": "stress",
                "weight": 10,
                "critical": false
              },
              {
                "id": "nonpositive_width",
                "tier": "stress",
                "weight": 5,
                "critical": false
              }
            ]
          },
          "17": {
            "packet_hash": "3b884a94b079c2dd4f405ccd33154ff62e4afa6e953a77d3c3c44991f4ab4a32",
            "test_manifest_hash": "c9ff817f8fadc9a9cb7b9f202e0cb3fd8172d1d320910d216c5cc6076e4a5178",
            "checks": [
              {
                "id": "one_cell_two_boundaries",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "zero_steps",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "heterogeneous_conservative",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "source_fixed_mix",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "one_cell_source",
                "tier": "stress",
                "weight": 5,
                "critical": false
              },
              {
                "id": "stiff_implicit",
                "tier": "stress",
                "weight": 10,
                "critical": false
              },
              {
                "id": "nonpositive_width",
                "tier": "stress",
                "weight": 5,
                "critical": false
              }
            ]
          },
          "2026": {
            "packet_hash": "e85d86ddbee0d22613529c8235577414266de158d0e51479d381de310c3ea35f",
            "test_manifest_hash": "e25c2bc2374f7dec910b06cde63b56c568bc1ac5d2b1d8989681ad78f6a25abc",
            "checks": [
              {
                "id": "one_cell_two_boundaries",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "zero_steps",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "heterogeneous_conservative",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "source_fixed_mix",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "one_cell_source",
                "tier": "stress",
                "weight": 5,
                "critical": false
              },
              {
                "id": "stiff_implicit",
                "tier": "stress",
                "weight": 10,
                "critical": false
              },
              {
                "id": "nonpositive_width",
                "tier": "stress",
                "weight": 5,
                "critical": false
              }
            ]
          }
        }
      },
      "P04": {
        "packet_hash": "30015006e01186ed65b9fd70aea957f1f65f4a33820caf2254bc29483526b901",
        "seeds": {
          "0": {
            "packet_hash": "7356cf92eceea4a9dd05144f31d84181328ae4945db1cb83f9c6e576a643b1cf",
            "test_manifest_hash": "41f26dd736552aec15bc2c1e21ca0da90f5239f83f80cabf4b12509aacc48ba2",
            "checks": [
              {
                "id": "interface_power",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "quarterwave",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "oblique_absorbing_s",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "oblique_absorbing_p",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "brewster_and_lossless",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "opaque_layer",
                "tier": "stress",
                "weight": 6,
                "critical": true
              },
              {
                "id": "evanescent_substrate",
                "tier": "stress",
                "weight": 5,
                "critical": false
              },
              {
                "id": "long_bragg",
                "tier": "stress",
                "weight": 5,
                "critical": false
              },
              {
                "id": "gain_rejected",
                "tier": "stress",
                "weight": 4,
                "critical": false
              }
            ]
          },
          "17": {
            "packet_hash": "30015006e01186ed65b9fd70aea957f1f65f4a33820caf2254bc29483526b901",
            "test_manifest_hash": "879d0188fc24a54695759fa10bb9f27a3bd5a4303de9861497cae1be9f3f5105",
            "checks": [
              {
                "id": "interface_power",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "quarterwave",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "oblique_absorbing_s",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "oblique_absorbing_p",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "brewster_and_lossless",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "opaque_layer",
                "tier": "stress",
                "weight": 6,
                "critical": true
              },
              {
                "id": "evanescent_substrate",
                "tier": "stress",
                "weight": 5,
                "critical": false
              },
              {
                "id": "long_bragg",
                "tier": "stress",
                "weight": 5,
                "critical": false
              },
              {
                "id": "gain_rejected",
                "tier": "stress",
                "weight": 4,
                "critical": false
              }
            ]
          },
          "2026": {
            "packet_hash": "8e7828dfb1dccca34bc554ff261a03f1e83f155178e148312c2f24c4b0eadee5",
            "test_manifest_hash": "8dda23736db709bcfaa76267dfd8316a48ad6af750d419cccaa0985b13973198",
            "checks": [
              {
                "id": "interface_power",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "quarterwave",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "oblique_absorbing_s",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "oblique_absorbing_p",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "brewster_and_lossless",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "opaque_layer",
                "tier": "stress",
                "weight": 6,
                "critical": true
              },
              {
                "id": "evanescent_substrate",
                "tier": "stress",
                "weight": 5,
                "critical": false
              },
              {
                "id": "long_bragg",
                "tier": "stress",
                "weight": 5,
                "critical": false
              },
              {
                "id": "gain_rejected",
                "tier": "stress",
                "weight": 4,
                "critical": false
              }
            ]
          }
        }
      },
      "P05": {
        "packet_hash": "f4d0ccea4607140dae559d85f8c1ab9560ff30be4415f8933766fbf74fcdaf4d",
        "seeds": {
          "0": {
            "packet_hash": "7dae540b1d4acc84a8498f267b5d18281c65acd0568cdcede573f2314a4ab266",
            "test_manifest_hash": "117fa7d29377e6a0f72613dab2153f4f4425a364cb5114762fa43774068d8714",
            "checks": [
              {
                "id": "equilibrium",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "zero_rates_source",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "stiff_rollback",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "right_continuous_schedule",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "large_absolute_clock",
                "tier": "stress",
                "weight": 7,
                "critical": true
              },
              {
                "id": "floating_endpoint",
                "tier": "stress",
                "weight": 7,
                "critical": false
              },
              {
                "id": "single_observation",
                "tier": "stress",
                "weight": 2,
                "critical": false
              },
              {
                "id": "invalid_0",
                "tier": "stress",
                "weight": 2,
                "critical": false
              },
              {
                "id": "invalid_1",
                "tier": "stress",
                "weight": 2,
                "critical": false
              }
            ]
          },
          "17": {
            "packet_hash": "f4d0ccea4607140dae559d85f8c1ab9560ff30be4415f8933766fbf74fcdaf4d",
            "test_manifest_hash": "45e2e5406c30bcce6d4f9c8592144422b2fe5e193997e532ba5d266ecf126285",
            "checks": [
              {
                "id": "equilibrium",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "zero_rates_source",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "stiff_rollback",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "right_continuous_schedule",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "large_absolute_clock",
                "tier": "stress",
                "weight": 7,
                "critical": true
              },
              {
                "id": "floating_endpoint",
                "tier": "stress",
                "weight": 7,
                "critical": false
              },
              {
                "id": "single_observation",
                "tier": "stress",
                "weight": 2,
                "critical": false
              },
              {
                "id": "invalid_0",
                "tier": "stress",
                "weight": 2,
                "critical": false
              },
              {
                "id": "invalid_1",
                "tier": "stress",
                "weight": 2,
                "critical": false
              }
            ]
          },
          "2026": {
            "packet_hash": "9728eb9b59ad91bd44ccd34674dc3edae06239e3be36893bc7676a248822c0e0",
            "test_manifest_hash": "020e3abad418ee9d31e1619808d90b9574c815a1b492261c1267fc6f8e95b587",
            "checks": [
              {
                "id": "equilibrium",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "zero_rates_source",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "stiff_rollback",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "right_continuous_schedule",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "large_absolute_clock",
                "tier": "stress",
                "weight": 7,
                "critical": true
              },
              {
                "id": "floating_endpoint",
                "tier": "stress",
                "weight": 7,
                "critical": false
              },
              {
                "id": "single_observation",
                "tier": "stress",
                "weight": 2,
                "critical": false
              },
              {
                "id": "invalid_0",
                "tier": "stress",
                "weight": 2,
                "critical": false
              },
              {
                "id": "invalid_1",
                "tier": "stress",
                "weight": 2,
                "critical": false
              }
            ]
          }
        }
      },
      "P06": {
        "packet_hash": "0f1b726fb696a0cd5eb0c3f84c328c2b23b9f5ad3224c34ad16507adf68d90bd",
        "seeds": {
          "0": {
            "packet_hash": "15a699c824dc5b81cb35f418d4df93c30351a4b35492b59cf3ef567a83b6d6d1",
            "test_manifest_hash": "cd7bf78a41ee1a806779083e39cfd8a976843707abd2487c928f3507634ce325",
            "checks": [
              {
                "id": "noiseless_nuisance",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "known_sigma_scale",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "heteroscedastic_shared_D",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "negative_amplitude",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "one_sided_profile",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "structurally_flat",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "weak_full_interval",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_zero_sigma",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_unresolved_times",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_unresolved_nuisance",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "lower_endpoint_interior_minimum",
                "tier": "stress",
                "weight": 5,
                "critical": true
              },
              {
                "id": "upper_endpoint_interior_minimum",
                "tier": "stress",
                "weight": 5,
                "critical": true
              }
            ]
          },
          "17": {
            "packet_hash": "0f1b726fb696a0cd5eb0c3f84c328c2b23b9f5ad3224c34ad16507adf68d90bd",
            "test_manifest_hash": "e7313a481f21f63843b7309de385dbc3544427f646c6a06876bc0e05b7205583",
            "checks": [
              {
                "id": "noiseless_nuisance",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "known_sigma_scale",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "heteroscedastic_shared_D",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "negative_amplitude",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "one_sided_profile",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "structurally_flat",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "weak_full_interval",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_zero_sigma",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_unresolved_times",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_unresolved_nuisance",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "lower_endpoint_interior_minimum",
                "tier": "stress",
                "weight": 5,
                "critical": true
              },
              {
                "id": "upper_endpoint_interior_minimum",
                "tier": "stress",
                "weight": 5,
                "critical": true
              }
            ]
          },
          "2026": {
            "packet_hash": "78900d76f52b4f5499423c6595385679a40c516ea65c02cd4bfad86367038cd7",
            "test_manifest_hash": "9a67645cbad28ea2323cbb3a21731b4d6ed2638b2775a50958817a8b5f0c3b99",
            "checks": [
              {
                "id": "noiseless_nuisance",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "known_sigma_scale",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "heteroscedastic_shared_D",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "negative_amplitude",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "one_sided_profile",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "structurally_flat",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "weak_full_interval",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_zero_sigma",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_unresolved_times",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_unresolved_nuisance",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "lower_endpoint_interior_minimum",
                "tier": "stress",
                "weight": 5,
                "critical": true
              },
              {
                "id": "upper_endpoint_interior_minimum",
                "tier": "stress",
                "weight": 5,
                "critical": true
              }
            ]
          }
        }
      },
      "P07": {
        "packet_hash": "d36807d4291affd41d86b51430a4eb211179d7e6c2e272552f26838b8e408713",
        "seeds": {
          "0": {
            "packet_hash": "356ddbe0531209ead8a7007dec97e188f7a5a84f9e8eb5644413c30f781e5de2",
            "test_manifest_hash": "9b416885f650eb86c1eff6a73e0a0381561beb9992fd79508e68cb07ccbfed99",
            "checks": [
              {
                "id": "affine_harmonic",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "isotropic_manufactured",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "directional_anisotropy",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "nonuniform_interfaces",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "refined_manufactured",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "high_contrast_interfaces",
                "tier": "stress",
                "weight": 8,
                "critical": true
              },
              {
                "id": "rectangular_nonuniform",
                "tier": "stress",
                "weight": 6,
                "critical": true
              },
              {
                "id": "reject_zero_conductivity",
                "tier": "stress",
                "weight": 3,
                "critical": true
              },
              {
                "id": "reject_collapsed_y",
                "tier": "stress",
                "weight": 3,
                "critical": true
              }
            ]
          },
          "17": {
            "packet_hash": "d36807d4291affd41d86b51430a4eb211179d7e6c2e272552f26838b8e408713",
            "test_manifest_hash": "261613c6ca532b30b304bbdf58e83405c597f17b3a83dc5dd7909786190c7dd1",
            "checks": [
              {
                "id": "affine_harmonic",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "isotropic_manufactured",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "directional_anisotropy",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "nonuniform_interfaces",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "refined_manufactured",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "high_contrast_interfaces",
                "tier": "stress",
                "weight": 8,
                "critical": true
              },
              {
                "id": "rectangular_nonuniform",
                "tier": "stress",
                "weight": 6,
                "critical": true
              },
              {
                "id": "reject_zero_conductivity",
                "tier": "stress",
                "weight": 3,
                "critical": true
              },
              {
                "id": "reject_collapsed_y",
                "tier": "stress",
                "weight": 3,
                "critical": true
              }
            ]
          },
          "2026": {
            "packet_hash": "0cbad939d6974631195c2e577813d57224f686c77dca2385b520ef5129b8a580",
            "test_manifest_hash": "c5328bacbed912b2493a6e8f48f9f47fac9b1d89724ddf5fca8dead354ceda88",
            "checks": [
              {
                "id": "affine_harmonic",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "isotropic_manufactured",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "directional_anisotropy",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "nonuniform_interfaces",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "refined_manufactured",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "high_contrast_interfaces",
                "tier": "stress",
                "weight": 8,
                "critical": true
              },
              {
                "id": "rectangular_nonuniform",
                "tier": "stress",
                "weight": 6,
                "critical": true
              },
              {
                "id": "reject_zero_conductivity",
                "tier": "stress",
                "weight": 3,
                "critical": true
              },
              {
                "id": "reject_collapsed_y",
                "tier": "stress",
                "weight": 3,
                "critical": true
              }
            ]
          }
        }
      },
      "P08": {
        "packet_hash": "795f4b46b0009527ff7c11ee75d45871ed7efb67d5118b653de20f515f79298f",
        "seeds": {
          "0": {
            "packet_hash": "a3243760aec267edb3cb255d97817c0c8d4924efd31d22c7848e05d85cb29924",
            "test_manifest_hash": "833cd5e82d6c996753f73e9a28d1ba96cb282a38e6c57812af6901f3dc245b3b",
            "checks": [
              {
                "id": "pure_reaction_conservation",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "periodic_diffusion_mode",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "coupled_discrete_tangents",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "noiseless_two_parameter_inverse",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "absolute_sigma_parametric_bootstrap",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "resume_nonzero_tangent_state",
                "tier": "stress",
                "weight": 6,
                "critical": true
              },
              {
                "id": "stiff_positive_conservative",
                "tier": "stress",
                "weight": 5,
                "critical": true
              },
              {
                "id": "rank_deficient_uniform_initial",
                "tier": "stress",
                "weight": 5,
                "critical": true
              },
              {
                "id": "reject_negative_initial",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_incomplete_checkpoint",
                "tier": "stress",
                "weight": 2,
                "critical": true
              }
            ]
          },
          "17": {
            "packet_hash": "795f4b46b0009527ff7c11ee75d45871ed7efb67d5118b653de20f515f79298f",
            "test_manifest_hash": "c496f3612ffc3f6480c9f06198891ee6585fcbd40ce65aec859699ab43dddb59",
            "checks": [
              {
                "id": "pure_reaction_conservation",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "periodic_diffusion_mode",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "coupled_discrete_tangents",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "noiseless_two_parameter_inverse",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "absolute_sigma_parametric_bootstrap",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "resume_nonzero_tangent_state",
                "tier": "stress",
                "weight": 6,
                "critical": true
              },
              {
                "id": "stiff_positive_conservative",
                "tier": "stress",
                "weight": 5,
                "critical": true
              },
              {
                "id": "rank_deficient_uniform_initial",
                "tier": "stress",
                "weight": 5,
                "critical": true
              },
              {
                "id": "reject_negative_initial",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_incomplete_checkpoint",
                "tier": "stress",
                "weight": 2,
                "critical": true
              }
            ]
          },
          "2026": {
            "packet_hash": "debbb1964177759102e58dbc935dd38070ff3f5139071508f0b2d9ef68ce502d",
            "test_manifest_hash": "67fdf3ed89ad354f74a1ea83fb2e5c120d4786f1cc3321c110c845cd2df652e8",
            "checks": [
              {
                "id": "pure_reaction_conservation",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "periodic_diffusion_mode",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "coupled_discrete_tangents",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "noiseless_two_parameter_inverse",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "absolute_sigma_parametric_bootstrap",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "resume_nonzero_tangent_state",
                "tier": "stress",
                "weight": 6,
                "critical": true
              },
              {
                "id": "stiff_positive_conservative",
                "tier": "stress",
                "weight": 5,
                "critical": true
              },
              {
                "id": "rank_deficient_uniform_initial",
                "tier": "stress",
                "weight": 5,
                "critical": true
              },
              {
                "id": "reject_negative_initial",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_incomplete_checkpoint",
                "tier": "stress",
                "weight": 2,
                "critical": true
              }
            ]
          }
        }
      },
      "F01": {
        "packet_hash": "577ab63860b6eff1ef779c5f53c64567a637500ccd6c6c008da7bfe0a9f97970",
        "seeds": {
          "0": {
            "packet_hash": "9d3200251ddbdab78321e1f82a035225a4d810ae92076fc3968bddb21ceea38d",
            "test_manifest_hash": "545aa9a175cc0d20e2cb99dbcc1cb53ab3bcd51e7ad086760394f7679be673b9",
            "checks": [
              {
                "id": "zero_drift_linear",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "constant_reaction_balance",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "constant_drift_exponential",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "heterogeneous_nonuniform",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "negative_drift_boundary_layer",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "peclet_2250_positive",
                "tier": "stress",
                "weight": 4,
                "critical": true
              },
              {
                "id": "peclet_2250_negative",
                "tier": "stress",
                "weight": 4,
                "critical": true
              },
              {
                "id": "near_zero_bernoulli",
                "tier": "stress",
                "weight": 4,
                "critical": true
              },
              {
                "id": "reject_unresolved_converging_flow",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_collapsed_cell",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_negative_diffusion",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_peclet_over_2500",
                "tier": "stress",
                "weight": 2,
                "critical": true
              }
            ]
          },
          "17": {
            "packet_hash": "577ab63860b6eff1ef779c5f53c64567a637500ccd6c6c008da7bfe0a9f97970",
            "test_manifest_hash": "0edac3400c43347d21a29ea6b2f514d629741933b60013e0f87892d1284bf22c",
            "checks": [
              {
                "id": "zero_drift_linear",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "constant_reaction_balance",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "constant_drift_exponential",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "heterogeneous_nonuniform",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "negative_drift_boundary_layer",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "peclet_2250_positive",
                "tier": "stress",
                "weight": 4,
                "critical": true
              },
              {
                "id": "peclet_2250_negative",
                "tier": "stress",
                "weight": 4,
                "critical": true
              },
              {
                "id": "near_zero_bernoulli",
                "tier": "stress",
                "weight": 4,
                "critical": true
              },
              {
                "id": "reject_unresolved_converging_flow",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_collapsed_cell",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_negative_diffusion",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_peclet_over_2500",
                "tier": "stress",
                "weight": 2,
                "critical": true
              }
            ]
          },
          "2026": {
            "packet_hash": "2f9c3a6b8d6dc454f34e4afa2c939b9957ce2ad420df372a9cc7d3d9b3716d8c",
            "test_manifest_hash": "048f229c32c284fa12807865adb693db033f93effeb828d24f82d8d4d49c7513",
            "checks": [
              {
                "id": "zero_drift_linear",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "constant_reaction_balance",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "constant_drift_exponential",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "heterogeneous_nonuniform",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "negative_drift_boundary_layer",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "peclet_2250_positive",
                "tier": "stress",
                "weight": 4,
                "critical": true
              },
              {
                "id": "peclet_2250_negative",
                "tier": "stress",
                "weight": 4,
                "critical": true
              },
              {
                "id": "near_zero_bernoulli",
                "tier": "stress",
                "weight": 4,
                "critical": true
              },
              {
                "id": "reject_unresolved_converging_flow",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_collapsed_cell",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_negative_diffusion",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_peclet_over_2500",
                "tier": "stress",
                "weight": 2,
                "critical": true
              }
            ]
          }
        }
      },
      "F02": {
        "packet_hash": "a51de755f97d0ade2cb7ade48b4fe1757ba59dbe9141d8e5a4e18061c3fe0538",
        "seeds": {
          "0": {
            "packet_hash": "07ded12f81b66403cd1e58c91b7bbe6c7241c5e42153b314142564c9997e01fd",
            "test_manifest_hash": "ba10597e85267f05195aab7466bdb58cc342ffc2934ca623c4ee44423f1f97f2",
            "checks": [
              {
                "id": "uniform_source_sink_equilibrium",
                "tier": "basic",
                "weight": 8,
                "critical": true
              },
              {
                "id": "two_cells_half_boundary",
                "tier": "basic",
                "weight": 6,
                "critical": true
              },
              {
                "id": "zero_step_identity",
                "tier": "basic",
                "weight": 6,
                "critical": true
              },
              {
                "id": "nonuniform_heterogeneous_schedule",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "outward_flux_signed_ledger",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "piecewise_source_right_interval",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "stiff_loss_positive_backward_euler",
                "tier": "stress",
                "weight": 5,
                "critical": true
              },
              {
                "id": "maximum_grid_cumulative_ledger",
                "tier": "stress",
                "weight": 5,
                "critical": true
              },
              {
                "id": "tiny_step_then_large_step",
                "tier": "stress",
                "weight": 4,
                "critical": true
              },
              {
                "id": "reject_zero_cell_width",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_negative_time_step",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_negative_source",
                "tier": "stress",
                "weight": 2,
                "critical": true
              }
            ]
          },
          "17": {
            "packet_hash": "a51de755f97d0ade2cb7ade48b4fe1757ba59dbe9141d8e5a4e18061c3fe0538",
            "test_manifest_hash": "42721901b7e4e0e60feecc42879f6ef472d49894e99d100b9f05b34f6289cc3b",
            "checks": [
              {
                "id": "uniform_source_sink_equilibrium",
                "tier": "basic",
                "weight": 8,
                "critical": true
              },
              {
                "id": "two_cells_half_boundary",
                "tier": "basic",
                "weight": 6,
                "critical": true
              },
              {
                "id": "zero_step_identity",
                "tier": "basic",
                "weight": 6,
                "critical": true
              },
              {
                "id": "nonuniform_heterogeneous_schedule",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "outward_flux_signed_ledger",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "piecewise_source_right_interval",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "stiff_loss_positive_backward_euler",
                "tier": "stress",
                "weight": 5,
                "critical": true
              },
              {
                "id": "maximum_grid_cumulative_ledger",
                "tier": "stress",
                "weight": 5,
                "critical": true
              },
              {
                "id": "tiny_step_then_large_step",
                "tier": "stress",
                "weight": 4,
                "critical": true
              },
              {
                "id": "reject_zero_cell_width",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_negative_time_step",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_negative_source",
                "tier": "stress",
                "weight": 2,
                "critical": true
              }
            ]
          },
          "2026": {
            "packet_hash": "590c5d77217df243876c039bf06a0aa766f92cdf4a251195f5bdc15e003cebfc",
            "test_manifest_hash": "646357dd04f54be13e614ad1523924fbfa95044a2b3a3c1524941586184d9d41",
            "checks": [
              {
                "id": "uniform_source_sink_equilibrium",
                "tier": "basic",
                "weight": 8,
                "critical": true
              },
              {
                "id": "two_cells_half_boundary",
                "tier": "basic",
                "weight": 6,
                "critical": true
              },
              {
                "id": "zero_step_identity",
                "tier": "basic",
                "weight": 6,
                "critical": true
              },
              {
                "id": "nonuniform_heterogeneous_schedule",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "outward_flux_signed_ledger",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "piecewise_source_right_interval",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "stiff_loss_positive_backward_euler",
                "tier": "stress",
                "weight": 5,
                "critical": true
              },
              {
                "id": "maximum_grid_cumulative_ledger",
                "tier": "stress",
                "weight": 5,
                "critical": true
              },
              {
                "id": "tiny_step_then_large_step",
                "tier": "stress",
                "weight": 4,
                "critical": true
              },
              {
                "id": "reject_zero_cell_width",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_negative_time_step",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_negative_source",
                "tier": "stress",
                "weight": 2,
                "critical": true
              }
            ]
          }
        }
      },
      "F03": {
        "packet_hash": "03ac765e2d673c8c39a7340927ea94dd3f3e1dcd7a96e927906b59c5f31ccf6e",
        "seeds": {
          "0": {
            "packet_hash": "000c93f137d0d923fd3861c189eb967ebe8585a37b15fcb70538d2f2d1b7f73d",
            "test_manifest_hash": "230c324b42deced309f875b843c9abbdd8036a6297f45c43007be9243c6300d9",
            "checks": [
              {
                "id": "neutral_equilibrium",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "affine_potential_nonzero_current",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "boltzmann_zero_flux",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "coupled_manufactured_sources",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "potential_gauge_shift",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "screening_refined",
                "tier": "stress",
                "weight": 6,
                "critical": true
              },
              {
                "id": "small_field_cancellation",
                "tier": "stress",
                "weight": 4,
                "critical": true
              },
              {
                "id": "maximum_grid_negative_gauge",
                "tier": "stress",
                "weight": 4,
                "critical": true
              },
              {
                "id": "reject_unsupported_screening",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_zero_contact_density",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_diffusion_outside_domain",
                "tier": "stress",
                "weight": 2,
                "critical": true
              }
            ]
          },
          "17": {
            "packet_hash": "03ac765e2d673c8c39a7340927ea94dd3f3e1dcd7a96e927906b59c5f31ccf6e",
            "test_manifest_hash": "f7c1bd13625b7e73f2d6cf2a34b1c5c6180241a911287b1a77243eac4ee22ffd",
            "checks": [
              {
                "id": "neutral_equilibrium",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "affine_potential_nonzero_current",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "boltzmann_zero_flux",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "coupled_manufactured_sources",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "potential_gauge_shift",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "screening_refined",
                "tier": "stress",
                "weight": 6,
                "critical": true
              },
              {
                "id": "small_field_cancellation",
                "tier": "stress",
                "weight": 4,
                "critical": true
              },
              {
                "id": "maximum_grid_negative_gauge",
                "tier": "stress",
                "weight": 4,
                "critical": true
              },
              {
                "id": "reject_unsupported_screening",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_zero_contact_density",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_diffusion_outside_domain",
                "tier": "stress",
                "weight": 2,
                "critical": true
              }
            ]
          },
          "2026": {
            "packet_hash": "88a2d047f0e868fd366142a05e84b993549b83338c15d794b515334a4d103a67",
            "test_manifest_hash": "5e7fa9cf50b0101847c84139f9e1943e44caf4b187d96297f0fa19a2c389238e",
            "checks": [
              {
                "id": "neutral_equilibrium",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "affine_potential_nonzero_current",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "boltzmann_zero_flux",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "coupled_manufactured_sources",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "potential_gauge_shift",
                "tier": "scientific",
                "weight": 10,
                "critical": true
              },
              {
                "id": "screening_refined",
                "tier": "stress",
                "weight": 6,
                "critical": true
              },
              {
                "id": "small_field_cancellation",
                "tier": "stress",
                "weight": 4,
                "critical": true
              },
              {
                "id": "maximum_grid_negative_gauge",
                "tier": "stress",
                "weight": 4,
                "critical": true
              },
              {
                "id": "reject_unsupported_screening",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_zero_contact_density",
                "tier": "stress",
                "weight": 2,
                "critical": true
              },
              {
                "id": "reject_diffusion_outside_domain",
                "tier": "stress",
                "weight": 2,
                "critical": true
              }
            ]
          }
        }
      },
      "L01": {
        "packet_hash": "bfeab8c3295d08a08d22cfea27f3ec02076038040f5f18c50565ca99e4a4484d",
        "seeds": {
          "0": {
            "packet_hash": "65c8d6649ec799e01b3729d66a8b5b85f756eb620898702ee25a11777d0780c8",
            "test_manifest_hash": "785bceeb0697a4a9c2e7855c214d5e5da1c42e34827effc4418e0859d029821b",
            "checks": [
              {
                "id": "step_balance",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "zero_input_active",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "trace_balance",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "restart",
                "tier": "scientific",
                "weight": 15,
                "critical": false
              },
              {
                "id": "prefix_admissible",
                "tier": "stress",
                "weight": 10,
                "critical": false
              },
              {
                "id": "collected_bound",
                "tier": "stress",
                "weight": 10,
                "critical": true
              }
            ]
          },
          "17": {
            "packet_hash": "bfeab8c3295d08a08d22cfea27f3ec02076038040f5f18c50565ca99e4a4484d",
            "test_manifest_hash": "f27e447810b495a409132f3a80a9f7549c617a4e5a417356b96893ee533ef31b",
            "checks": [
              {
                "id": "step_balance",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "zero_input_active",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "trace_balance",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "restart",
                "tier": "scientific",
                "weight": 15,
                "critical": false
              },
              {
                "id": "prefix_admissible",
                "tier": "stress",
                "weight": 10,
                "critical": false
              },
              {
                "id": "collected_bound",
                "tier": "stress",
                "weight": 10,
                "critical": true
              }
            ]
          },
          "2026": {
            "packet_hash": "7665ca79eac4212a0fde59c847bc7eecea3366ed893b5203880dbeb1982e0e0d",
            "test_manifest_hash": "70a56bbef35c1deaca2c3c16b80a734d4d3a226ec93b2e8d3d7cf7011404acb3",
            "checks": [
              {
                "id": "step_balance",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "zero_input_active",
                "tier": "basic",
                "weight": 10,
                "critical": false
              },
              {
                "id": "trace_balance",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "restart",
                "tier": "scientific",
                "weight": 15,
                "critical": false
              },
              {
                "id": "prefix_admissible",
                "tier": "stress",
                "weight": 10,
                "critical": false
              },
              {
                "id": "collected_bound",
                "tier": "stress",
                "weight": 10,
                "critical": true
              }
            ]
          }
        }
      },
      "H02": {
        "packet_hash": "8aa9f2d0652402c13cbc4ea84deda5a7b7e17cd15dc65c32617721f244353c52",
        "seeds": {
          "0": {
            "packet_hash": "82d87b8fd2175e0ad18e4b698c32d0266a39818fbf03c3cf29362b805035ef40",
            "test_manifest_hash": "808cb9186585346f895860fd345900846d811b42104267accba48cdff6695ce4",
            "checks": [
              {
                "id": "target_yields",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "absorption_times",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "conditional_times",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "conditional_variances",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "global_optimum_certificate",
                "tier": "stress",
                "weight": 10,
                "critical": true
              },
              {
                "id": "valid_counterexample",
                "tier": "stress",
                "weight": 10,
                "critical": true
              }
            ]
          },
          "17": {
            "packet_hash": "8aa9f2d0652402c13cbc4ea84deda5a7b7e17cd15dc65c32617721f244353c52",
            "test_manifest_hash": "a1bf506ba753aa9a3a5b81d8db7ad2bc2182d41b3c3c1b6f756cb464f2e6dcf0",
            "checks": [
              {
                "id": "target_yields",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "absorption_times",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "conditional_times",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "conditional_variances",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "global_optimum_certificate",
                "tier": "stress",
                "weight": 10,
                "critical": true
              },
              {
                "id": "valid_counterexample",
                "tier": "stress",
                "weight": 10,
                "critical": true
              }
            ]
          },
          "2026": {
            "packet_hash": "e7f7da71d7e31254fb7c750fbd89f3bedda11df85b466b539a72eb152b9e5c31",
            "test_manifest_hash": "80d61fc1bb6751f6689dc46c31d06f813d93f11e19e46ae14d3b6ade3c14a326",
            "checks": [
              {
                "id": "target_yields",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "absorption_times",
                "tier": "basic",
                "weight": 10,
                "critical": true
              },
              {
                "id": "conditional_times",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "conditional_variances",
                "tier": "scientific",
                "weight": 15,
                "critical": true
              },
              {
                "id": "global_optimum_certificate",
                "tier": "stress",
                "weight": 10,
                "critical": true
              },
              {
                "id": "valid_counterexample",
                "tier": "stress",
                "weight": 10,
                "critical": true
              }
            ]
          }
        }
      }
    }
  }
};

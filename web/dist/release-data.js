globalThis.NRB_RELEASE = {
  "version": "2.0.0-rc.1",
  "status": "phase1",
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
      "benchmark_version": "2.0.0-rc.1",
      "brief": "CSV身份、单位与极小不确定度；区分重复记录和独立测量。",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "file": "P01.md",
      "packet_hash": "d39eb12395542d6e6d0d2f709b067503afea6991c1f205f74b937c1915189898",
      "seed": 17,
      "level": "1/5",
      "budget": 15,
      "version": "2.0.0-rc.1",
      "packet": "packets-v2/P01.md",
      "packetHash": "d39eb12395542d6e6d0d2f709b067503afea6991c1f205f74b937c1915189898"
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
      "benchmark_version": "2.0.0-rc.1",
      "brief": "独立组与技术重复、分层目标人群和确定性bootstrap。",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "file": "P02.md",
      "packet_hash": "b450083e4f112e168b763b1593a8c6fa2e75784050f6ff540613246251a5baab",
      "seed": 17,
      "level": "2/5",
      "budget": 15,
      "version": "2.0.0-rc.1",
      "packet": "packets-v2/P02.md",
      "packetHash": "b450083e4f112e168b763b1593a8c6fa2e75784050f6ff540613246251a5baab"
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
      "benchmark_version": "2.0.0-rc.1",
      "brief": "修复非均匀有限体积导热：界面热阻、隐式推进与能量账本。",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "file": "P03.md",
      "packet_hash": "55efab4f78699005dfe9da24904e6b808b9d3bd78ffe7d824036dda03d58e516",
      "seed": 17,
      "level": "3/5",
      "budget": 15,
      "version": "2.0.0-rc.1",
      "packet": "packets-v2/P03.md",
      "packetHash": "55efab4f78699005dfe9da24904e6b808b9d3bd78ffe7d824036dda03d58e516"
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
      "benchmark_version": "2.0.0-rc.1",
      "brief": "复折射率多层光学：s/p偏振、能流、倏逝波与极厚吸收层。",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "file": "P04.md",
      "packet_hash": "346b070cf1cf15870f31c1681067eacdcc3e0d78ebd99857fc7ba2200c266264",
      "seed": 17,
      "level": "4/5",
      "budget": 30,
      "version": "2.0.0-rc.1",
      "packet": "packets-v2/P04.md",
      "packetHash": "346b070cf1cf15870f31c1681067eacdcc3e0d78ebd99857fc7ba2200c266264"
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
      "benchmark_version": "2.0.0-rc.1",
      "brief": "按明确算法实现刚性积分：拒步回滚、右连续源与浮点硬停点。",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "file": "P05.md",
      "packet_hash": "8cc58f87d6a6d6aea0aec98fcbfb09e74841697152428193a8e170b722e2fe85",
      "seed": 17,
      "level": "5/5",
      "budget": 30,
      "version": "2.0.0-rc.1",
      "packet": "packets-v2/P05.md",
      "packetHash": "8cc58f87d6a6d6aea0aec98fcbfb09e74841697152428193a8e170b722e2fe85"
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
      "benchmark_version": "2.0.0-rc.1",
      "brief": "变量投影、绝对sigma、剖面似然区间和端点附近内部最小值。",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "file": "P06.md",
      "packet_hash": "c27b1058a0b46c4f71d126b355cdb3d1248028dfc37011ecfc02506ff1260eb9",
      "seed": 17,
      "level": "4/5",
      "budget": 40,
      "version": "2.0.0-rc.1",
      "packet": "packets-v2/P06.md",
      "packetHash": "c27b1058a0b46c4f71d126b355cdb3d1248028dfc37011ecfc02506ff1260eb9"
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
      "benchmark_version": "2.0.0-rc.1",
      "brief": "二维非均匀网格、方向各向异性、界面传递与边界积分通量。",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "file": "P07.md",
      "packet_hash": "5410d21d42557c04963e0f895d4ef590a8a0d57fc9749e2547b4595cdee028b3",
      "seed": 17,
      "level": "4/5",
      "budget": 40,
      "version": "2.0.0-rc.1",
      "packet": "packets-v2/P07.md",
      "packetHash": "5410d21d42557c04963e0f895d4ef590a8a0d57fc9749e2547b4595cdee028b3"
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
      "benchmark_version": "2.0.0-rc.1",
      "brief": "修复反应扩散反演链：离散切线、协方差、JSON重启与重新拟合自举。",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "file": "P08.md",
      "packet_hash": "cf8210f953108967717f1e2a87d62113e535fb81638d6b84ed8b6617f3c21606",
      "seed": 17,
      "level": "5/5",
      "budget": 75,
      "version": "2.0.0-rc.1",
      "packet": "packets-v2/P08.md",
      "packetHash": "cf8210f953108967717f1e2a87d62113e535fb81638d6b84ed8b6617f3c21606"
    },
    {
      "id": "F01",
      "title": "Fortran 非均匀网格守恒漂移扩散",
      "category": "Fortran",
      "difficulty": 3,
      "brief": "SG通量、非均匀控制体与漂移方向",
      "status": "planned",
      "phase": 2,
      "scoring": "automatic",
      "legacy_id": "C06",
      "language": "fortran",
      "track": "planned",
      "benchmark_version": "2.0.0-rc.1",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": false,
      "required_artifacts": [],
      "level": "3/5",
      "budget": null,
      "version": "2.0.0-rc.1"
    },
    {
      "id": "F02",
      "title": "Fortran 隐式反应扩散与源汇账本",
      "category": "Fortran",
      "difficulty": 4,
      "brief": "时间推进、正性与源汇守恒",
      "status": "planned",
      "phase": 2,
      "scoring": "automatic",
      "legacy_id": null,
      "language": "fortran",
      "track": "planned",
      "benchmark_version": "2.0.0-rc.1",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": false,
      "required_artifacts": [],
      "level": "4/5",
      "budget": null,
      "version": "2.0.0-rc.1"
    },
    {
      "id": "F03",
      "title": "Fortran 自洽漂移扩散–Poisson",
      "category": "Fortran",
      "difficulty": 5,
      "brief": "非线性耦合、阻尼迭代与规范平移",
      "status": "planned",
      "phase": 2,
      "scoring": "automatic",
      "legacy_id": "C09",
      "language": "fortran",
      "track": "planned",
      "benchmark_version": "2.0.0-rc.1",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": false,
      "required_artifacts": [],
      "level": "5/5",
      "budget": null,
      "version": "2.0.0-rc.1"
    },
    {
      "id": "L01",
      "title": "已有守恒结论的 Lean 形式化",
      "category": "Lean",
      "difficulty": 4,
      "brief": "给定命题与条件、实际编译、公理依赖核验",
      "status": "planned",
      "phase": 2,
      "scoring": "automatic",
      "legacy_id": null,
      "language": "lean",
      "track": "planned",
      "benchmark_version": "2.0.0-rc.1",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": false,
      "required_artifacts": [],
      "level": "4/5",
      "budget": null,
      "version": "2.0.0-rc.1"
    },
    {
      "id": "R01",
      "title": "参考学习与可编辑科研 SVG",
      "category": "主观科研",
      "difficulty": 4,
      "brief": "真实图例学习、科学语义与多面板组织",
      "status": "planned",
      "phase": 2,
      "scoring": "manual",
      "legacy_id": "R01",
      "language": null,
      "track": "planned",
      "benchmark_version": "2.0.0-rc.1",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": true,
      "required_artifacts": [],
      "level": "4/5",
      "budget": null,
      "version": "2.0.0-rc.1"
    },
    {
      "id": "R02",
      "title": "小差异、宽动态范围与删失数据绘图",
      "category": "主观科研",
      "difficulty": 4,
      "brief": "坐标尺度、数据语义与可复现图形",
      "status": "planned",
      "phase": 2,
      "scoring": "manual",
      "legacy_id": "R02",
      "language": null,
      "track": "planned",
      "benchmark_version": "2.0.0-rc.1",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": true,
      "required_artifacts": [],
      "level": "4/5",
      "budget": null,
      "version": "2.0.0-rc.1"
    },
    {
      "id": "R03",
      "title": "保持事实与证据强度的英文润色",
      "category": "主观科研",
      "difficulty": 3,
      "brief": "保守修改、事实台账与自然表达",
      "status": "planned",
      "phase": 2,
      "scoring": "manual",
      "legacy_id": "R03",
      "language": null,
      "track": "planned",
      "benchmark_version": "2.0.0-rc.1",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": true,
      "required_artifacts": [],
      "level": "3/5",
      "budget": null,
      "version": "2.0.0-rc.1"
    },
    {
      "id": "R04",
      "title": "从图版与数据撰写结果和讨论",
      "category": "主观科研",
      "difficulty": 4,
      "brief": "读图、定量表述与推断边界",
      "status": "planned",
      "phase": 2,
      "scoring": "manual",
      "legacy_id": "R04",
      "language": null,
      "track": "planned",
      "benchmark_version": "2.0.0-rc.1",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": true,
      "required_artifacts": [],
      "level": "4/5",
      "budget": null,
      "version": "2.0.0-rc.1"
    },
    {
      "id": "R05",
      "title": "文献证据综合与有界方法复现",
      "category": "主观科研",
      "difficulty": 5,
      "brief": "合并旧精读/综述题，保留证据与复现责任",
      "status": "planned",
      "phase": 2,
      "scoring": "manual",
      "legacy_id": "R05+R06",
      "language": null,
      "track": "planned",
      "benchmark_version": "2.0.0-rc.1",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": true,
      "required_artifacts": [],
      "level": "5/5",
      "budget": null,
      "version": "2.0.0-rc.1"
    },
    {
      "id": "R06",
      "title": "视频修改与参考视觉重建",
      "category": "主观科研",
      "difficulty": 4,
      "brief": "合并视频A/B为一道题的两种预先声明模式",
      "status": "planned",
      "phase": 2,
      "scoring": "manual",
      "legacy_id": "X04+X05",
      "language": null,
      "track": "planned",
      "benchmark_version": "2.0.0-rc.1",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": true,
      "required_artifacts": [],
      "level": "4/5",
      "budget": null,
      "version": "2.0.0-rc.1"
    },
    {
      "id": "H01",
      "title": "聊天端单 HTML 科研工作台",
      "category": "聊天端",
      "difficulty": 4,
      "brief": "离线交互、返回、空态与真实导出",
      "status": "planned",
      "phase": 2,
      "scoring": "manual",
      "legacy_id": "X01",
      "language": null,
      "track": "planned",
      "benchmark_version": "2.0.0-rc.1",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": true,
      "required_artifacts": [],
      "level": "4/5",
      "budget": null,
      "version": "2.0.0-rc.1"
    },
    {
      "id": "H02",
      "title": "聊天端有回流网络的定量推理",
      "category": "聊天端",
      "difficulty": 5,
      "brief": "产额、条件寿命、全局最优与可核验反例",
      "status": "planned",
      "phase": 2,
      "scoring": "automatic",
      "legacy_id": null,
      "language": null,
      "track": "planned",
      "benchmark_version": "2.0.0-rc.1",
      "difficulty_status": "design_prior_not_empirically_calibrated",
      "manual_review_required": false,
      "required_artifacts": [],
      "level": "5/5",
      "budget": null,
      "version": "2.0.0-rc.1"
    }
  ],
  "downloads": {
    "folder": {
      "id": "1memk6jwu6LWzoPHGg5uhDgcFmKDi00-C",
      "url": "https://drive.google.com/drive/folders/1memk6jwu6LWzoPHGg5uhDgcFmKDi00-C"
    },
    "grader": {
      "id": "1amb1EDJiOoBNBqeKU5653mhrdX7Caud4",
      "url": "https://drive.google.com/file/d/1amb1EDJiOoBNBqeKU5653mhrdX7Caud4/view?usp=drivesdk",
      "name": "NRB-v2.0.0-rc.1-python-grader.zip",
      "bytes": 187976,
      "sha256": "1cf96032f525233182ae6e9f135c7c445af98c5f4d9ced225fc44e8c52543bf3",
      "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
    },
    "candidateBundle": {
      "id": "1I2BrBLQGcc0WkPkwZbLFklkv1lgGzZbC",
      "url": "https://drive.google.com/file/d/1I2BrBLQGcc0WkPkwZbLFklkv1lgGzZbC/view?usp=drivesdk",
      "name": "NRB-v2.0.0-rc.1-python-candidates.zip",
      "bytes": 28852,
      "sha256": "75f95968f970e9c64799c0743f852fad95bec181011979da8759fe48974545b3",
      "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
    },
    "tasks": {
      "P01": {
        "id": "1rKUiZMpVnOjffGTjt74uh7pWDdEVuUGY",
        "url": "https://drive.google.com/file/d/1rKUiZMpVnOjffGTjt74uh7pWDdEVuUGY/view?usp=drivesdk",
        "name": "P01.md",
        "bytes": 3631,
        "sha256": "d39eb12395542d6e6d0d2f709b067503afea6991c1f205f74b937c1915189898",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "P02": {
        "id": "1nE9mMC_VaDwOnRozBrOZ6xuaHjryMvYe",
        "url": "https://drive.google.com/file/d/1nE9mMC_VaDwOnRozBrOZ6xuaHjryMvYe/view?usp=drivesdk",
        "name": "P02.md",
        "bytes": 3988,
        "sha256": "b450083e4f112e168b763b1593a8c6fa2e75784050f6ff540613246251a5baab",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "P03": {
        "id": "1tHVGF99Nxp5qkRtmKHQrvUIPAnPRRpZL",
        "url": "https://drive.google.com/file/d/1tHVGF99Nxp5qkRtmKHQrvUIPAnPRRpZL/view?usp=drivesdk",
        "name": "P03.md",
        "bytes": 4637,
        "sha256": "55efab4f78699005dfe9da24904e6b808b9d3bd78ffe7d824036dda03d58e516",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "P04": {
        "id": "1HNQvjD0u2hbLkHdH84IaZryrEj9RDpgc",
        "url": "https://drive.google.com/file/d/1HNQvjD0u2hbLkHdH84IaZryrEj9RDpgc/view?usp=drivesdk",
        "name": "P04.md",
        "bytes": 4888,
        "sha256": "346b070cf1cf15870f31c1681067eacdcc3e0d78ebd99857fc7ba2200c266264",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "P05": {
        "id": "1eTL33BsQfXZketP_pISwIbGu9YOuFUEE",
        "url": "https://drive.google.com/file/d/1eTL33BsQfXZketP_pISwIbGu9YOuFUEE/view?usp=drivesdk",
        "name": "P05.md",
        "bytes": 5337,
        "sha256": "8cc58f87d6a6d6aea0aec98fcbfb09e74841697152428193a8e170b722e2fe85",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "P06": {
        "id": "1r3oCAO-prgN_VO-in6FbvAQ_hwXyWdoa",
        "url": "https://drive.google.com/file/d/1r3oCAO-prgN_VO-in6FbvAQ_hwXyWdoa/view?usp=drivesdk",
        "name": "P06.md",
        "bytes": 5303,
        "sha256": "c27b1058a0b46c4f71d126b355cdb3d1248028dfc37011ecfc02506ff1260eb9",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "P07": {
        "id": "1iWqtshSyhubjgu7G0k2-YvTDUcmFObyO",
        "url": "https://drive.google.com/file/d/1iWqtshSyhubjgu7G0k2-YvTDUcmFObyO/view?usp=drivesdk",
        "name": "P07.md",
        "bytes": 7168,
        "sha256": "5410d21d42557c04963e0f895d4ef590a8a0d57fc9749e2547b4595cdee028b3",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
      },
      "P08": {
        "id": "1mphQH3C0eYW-AcN2hL2RqN5zRd4RNp4N",
        "url": "https://drive.google.com/file/d/1mphQH3C0eYW-AcN2hL2RqN5zRd4RNp4N/view?usp=drivesdk",
        "name": "P08.md",
        "bytes": 14783,
        "sha256": "cf8210f953108967717f1e2a87d62113e535fb81638d6b84ed8b6617f3c21606",
        "verified": "upload plus metadata size/name/permission readback; sha256 from uploaded local bytes"
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
    }
  },
  "grading": {
    "schema": "nrb-auto-report-v2",
    "version": "2.0.0-rc.1",
    "grader_version": "2.0.0-rc.1",
    "evaluatorFingerprint": "ee841ae2c0a1d98101f50f4d0b29e922275fd499ea9f37d05c8924bd86fa51c0",
    "seed_policy": "The manifest binds seed, check contract and evaluator source. Execution records separately hash actual numerical inputs.",
    "tasks": {
      "P01": {
        "packet_hash": "d39eb12395542d6e6d0d2f709b067503afea6991c1f205f74b937c1915189898",
        "seeds": {
          "0": {
            "packet_hash": "b1aee7d5a5e1d425e8e72f9d261c5a9518354107e72e513b1fb4213d20b96213",
            "test_manifest_hash": "a43ccc8be39feb8d9f47b538b08f99cf936af359dc8c8186eb9f4cd5b0a3a441",
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
            "packet_hash": "d39eb12395542d6e6d0d2f709b067503afea6991c1f205f74b937c1915189898",
            "test_manifest_hash": "e692cba41f12e33bd96b2081c1d7f7241f74ce1a6477e6fb7f6c204e9d4e6ade",
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
            "packet_hash": "9e7621e4d4a8191f5c33fa0a610b277e2677c5459a28a5d4e27881163352bb8d",
            "test_manifest_hash": "45ab379bc9f64b7a6b8c845a051ca9357b8fd0a1d6af9cafeb91e7896d6952a6",
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
        "packet_hash": "b450083e4f112e168b763b1593a8c6fa2e75784050f6ff540613246251a5baab",
        "seeds": {
          "0": {
            "packet_hash": "bc4e6de2534412c73bf3578b3ab6e3e3b4345640769c0299e80866667359769d",
            "test_manifest_hash": "b8ad8c2e803ced688f122ef5a4b33f0fbdb6fea92a1af42af1978f90e4c7f2a1",
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
            "packet_hash": "b450083e4f112e168b763b1593a8c6fa2e75784050f6ff540613246251a5baab",
            "test_manifest_hash": "67539af669dd470df2f2eab31a72ca91a7996f1b2a855034688210b7e79f72ae",
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
            "packet_hash": "e0f1c39d9597bb47e442ef68931bf34f5a16353906ba2f990df126c9c5970368",
            "test_manifest_hash": "30c36c3fe9d37a949d343e4803cbc305aaea21dc8f140d5e57538fb4c7fbf09d",
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
        "packet_hash": "55efab4f78699005dfe9da24904e6b808b9d3bd78ffe7d824036dda03d58e516",
        "seeds": {
          "0": {
            "packet_hash": "cd5e52d4b5c5029e44294bf8d61373dc2dcb3f4ce46c7947a43c420933f72ec2",
            "test_manifest_hash": "7d02e36ca1b1e05c9eede1c6b24ec09d472f201f8c1ec5af8f663bdff36a2a1f",
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
            "packet_hash": "55efab4f78699005dfe9da24904e6b808b9d3bd78ffe7d824036dda03d58e516",
            "test_manifest_hash": "6ed03434281d30f77ad2a3e604800219f6dbddfb18b8fc893a58c0f58d7e6dc2",
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
            "packet_hash": "2349ff036f45fbdcd03fefb736c5af0597a1eb64859aaf7f389c410007c40fc7",
            "test_manifest_hash": "98de397753f61704d073a3db60d78907dfe39adb00402131515b32874652225e",
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
        "packet_hash": "346b070cf1cf15870f31c1681067eacdcc3e0d78ebd99857fc7ba2200c266264",
        "seeds": {
          "0": {
            "packet_hash": "da85e6ecee7e287b6f8da65002eba70e6e49c4003de171f20ed775a44c858f9f",
            "test_manifest_hash": "b44e342c139d7bde33d6ebaa4cf5f5bbfa252d45bcb83bee1f26f4e2ea240873",
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
            "packet_hash": "346b070cf1cf15870f31c1681067eacdcc3e0d78ebd99857fc7ba2200c266264",
            "test_manifest_hash": "b82e21c851a64620a14e91eaeb3e2357e094aad3c385e6a2679c65b24f27eae5",
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
            "packet_hash": "ba16deb12b9ed01dd086d378752919c7f0749ad972e2bb573ba70e323d4ae5b3",
            "test_manifest_hash": "7d25f0ab3dcf3d1a293dbc518da4c02bd4bc3216be95e73a1d08c08d75c45950",
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
        "packet_hash": "8cc58f87d6a6d6aea0aec98fcbfb09e74841697152428193a8e170b722e2fe85",
        "seeds": {
          "0": {
            "packet_hash": "15571847bf483943133050aea49d6894955848a19e478eba7288a60b022383b7",
            "test_manifest_hash": "88f05e38e324af1c072ca90bf245340cfd9a60cdae354e55f3e48745a521ea53",
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
            "packet_hash": "8cc58f87d6a6d6aea0aec98fcbfb09e74841697152428193a8e170b722e2fe85",
            "test_manifest_hash": "dbefd686236f4b18f49dd5b2b635ebab6bd56d4542379d2e784f7feeede91ac2",
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
            "packet_hash": "283a93bbb9282af06da702bf7e57f8bc65aaad3ec6bb4feebede416f304d5abc",
            "test_manifest_hash": "acb08ae71883d45c9452cf8b3706081a5e9061292a9aa2e7c3f14c10c754e63b",
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
        "packet_hash": "c27b1058a0b46c4f71d126b355cdb3d1248028dfc37011ecfc02506ff1260eb9",
        "seeds": {
          "0": {
            "packet_hash": "f0b6a2f823b8fa34407ae06f8fe12bc2bd68798b30a829559dc0e7a8608070c0",
            "test_manifest_hash": "040546455e294e00c9c7449b9a28d88602e8986645cf6c12888b91d43812278b",
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
            "packet_hash": "c27b1058a0b46c4f71d126b355cdb3d1248028dfc37011ecfc02506ff1260eb9",
            "test_manifest_hash": "25dd4945d063f6c534954df2f866ccd960da7f700320d27127ed3664dcbf7909",
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
            "packet_hash": "6abef3e8a641407898ae492717804afc165cac5c35902670830b4901ac8869c1",
            "test_manifest_hash": "ce586fdbf8a3ae56df21cd7afd209cc1f5059c99533b39f61db4fdd94c79a33f",
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
        "packet_hash": "5410d21d42557c04963e0f895d4ef590a8a0d57fc9749e2547b4595cdee028b3",
        "seeds": {
          "0": {
            "packet_hash": "51156f508172dcedfa2b24c0d3374206a91e19c7ba3cbac0f28ed575afdb3f00",
            "test_manifest_hash": "a12c1dee8cce7d5db52b818908cc9973a058ccdedbc3113c7ed16e1a30d6234a",
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
            "packet_hash": "5410d21d42557c04963e0f895d4ef590a8a0d57fc9749e2547b4595cdee028b3",
            "test_manifest_hash": "05ba3cc44a168d479be3dd31b30b49ed1b05bb68421cd20abd4856f41774048b",
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
            "packet_hash": "b87742f669035bed0ad7162900a6397c041f592d02b33fc5066163ae18ef284f",
            "test_manifest_hash": "7a8937e0c4665ca75a8c8b91403f8efa68d305f50ded8b0eed1b4e9841212660",
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
        "packet_hash": "cf8210f953108967717f1e2a87d62113e535fb81638d6b84ed8b6617f3c21606",
        "seeds": {
          "0": {
            "packet_hash": "f09cfb15f312fa207480e463393b4193d682023300f453d6b0751622ac17b451",
            "test_manifest_hash": "1d9d58655ea325201363218bb42cd3c2092b5371bde2b5608343ad1f3da034ab",
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
            "packet_hash": "cf8210f953108967717f1e2a87d62113e535fb81638d6b84ed8b6617f3c21606",
            "test_manifest_hash": "ca07c9eb12758f689ce34711485148e5d37418b6fe37c3a4b9f00cb122e40230",
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
            "packet_hash": "4946fcfa55a29607909374c7ff08ab8226e6083af656e8160edb5c5742b7fd6a",
            "test_manifest_hash": "e36365afbe719e05524e639efbb6f2591f2835334a26c6bc7333d3484ceafd82",
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
      }
    }
  }
};

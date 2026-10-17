# NRB04 · 非均匀网格上的守恒热扩散修复

你接手一段一维热扩散教学程序。网格不均匀，各单元的导热率和体积热容不同。
输入均为本测试生成的无量纲数据。请依据 API.md，以只读的 starter.py 为起点，在新的 solution.py 中实现修复；说明守恒关系、界面串联热阻、
边界通量方向、显式步长限制，以及你实际执行了哪些验证。不要把数值例子描述为实验数据。

必须返回 JSON 外层 {"task_id":"NRB04","answer":{"visible_result":{"temperature":[number],
"face_flux":[number],"energy_initial":number,"energy_final":number,"energy_input":number}},
"artifacts":{"solution.py":"完整 Python 源码字符串","reasoning.md":"推导与实际验证说明"}}。
visible_result 是 input.json 的结果；数组长度须遵循该输入。solution.py 必须提供 solve(payload)。
评分会在未展示的有效与无效输入上运行代码。推导质量另按人工量规评分。

## 提交协议 / Submission contract
返回一个 UTF-8 JSON 对象（可使用单个 json 代码块），或将该对象写入 submission.json。
顶层格式：{"task_id":"NRB04","answer":{...},"artifacts":{"relative/path":"完整文件内容"}}。
answer 使用本题字段。代码、推导、图和修订稿放入 artifacts，字符串须包含完整内容，不能只返回本机路径。
数值使用 JSON number，缺失使用 null；不接受 NaN/Infinity。不同题目独立完成。
输入均为本基准原创构造的合成材料，不代表真实实验或真实未发表研究。
封闭资料轨道只使用本题材料与通用知识。不得查找本基准源码、答案或评分器。
每题自动核验 70 分，另有以下三项各 10 分的独立质量审阅。

[
  {
    "id": "derivation",
    "title": "离散物理与误差解释",
    "anchors": {
      "0": "没有推导，或守恒/边界方向解释错误。",
      "5": "说明主要离散关系，但未清楚区分导热率、单元热容量及边界距离。",
      "10": "从单元热量平衡推导面热阻、源项、边界方向和非负权重步长条件，明确时间/空间离散误差。"
    }
  },
  {
    "id": "verification",
    "title": "有效验证与执行诚实性",
    "anchors": {
      "0": "无可核验验证，或把未执行测试写成已通过。",
      "5": "展示一个有效守恒或解析例，并准确说明执行范围。",
      "10": "使用机制不同的例子检验守恒、异质界面、边界条件及拒绝非法输入；给出可复现命令/结果并如实说明范围。"
    }
  },
  {
    "id": "maintainability",
    "title": "代码可维护性",
    "anchors": {
      "0": "代码不可读或仅硬编码可见输出。",
      "5": "功能结构可读，存在冗余或输入异常说明不足。",
      "10": "接口、验证、通量和更新分工清楚，简洁且可扩展；说明具体已修复缺陷，无不必要依赖。"
    }
  }
]

Required artifacts: reasoning.md, solution.py


## 输入文件：API.md
<BEGIN_INPUT_FILE>

# Public API: scalar heat transport

All quantities are dimensionless synthetic classroom values; cross-section is 1.
`solve(payload)` receives JSON: edges[n+1], conductivity[n] > 0,
capacity[n] > 0 (volumetric), temperature[n], source[n] (per unit volume),
dt > 0, integer steps >= 0, and left/right boundary objects.
Each boundary is {"kind": "flux" | "temperature", "value": finite_number}.
All numeric inputs must be finite; edges strictly increase; arrays must be lists
with the specified length. Boolean values are not valid numbers or step counts.
Raise ValueError for invalid inputs or violation of the stability bound below.

Let h_i=edges[i+1]-edges[i]. For a face between i and i+1,
g=1/(h_i/(2*k_i)+h_(i+1)/(2*k_(i+1))), and q=g*(u_i-u_(i+1)).
Every q, including prescribed boundary fluxes, is positive toward increasing x.
Temperature boundaries are at the domain face, a half-cell from the cell center:
q_left=2*k_0/h_0*(T_left-u_0), q_right=2*k_last/h_last*(u_last-T_right).
The update is simultaneous forward Euler:
u_i(new)=u_i+dt*(q_i-q_(i+1)+source_i*h_i)/(capacity_i*h_i).
Use the old state for every flux in a step.

Reject dt > (1+1e-12)*min_i(capacity_i*h_i/sum_g_i), where sum_g_i is
the sum of state-dependent conductances leaving that cell. Prescribed-flux
boundaries contribute zero; cells with sum_g_i=0 place no restriction.
Validate this bound even if steps=0.

Return exactly the physically defined fields (extra fields are ignored):
temperature[n], face_flux[n+1] evaluated at the FINAL state,
energy_initial, energy_final, energy_input.
Energy is sum(capacity_i*h_i*u_i); energy_input is the sum over steps of
dt*(q_left-q_right+sum(source_i*h_i)), using that step's old-state fluxes.
steps=0 must return unchanged temperatures and zero energy_input.
Only Python standard library modules are available.


<END_INPUT_FILE>


## 输入文件：input.json
<BEGIN_INPUT_FILE>

{
  "edges": [
    0.0,
    0.7939242161531213,
    1.4639449910951683,
    2.148646429395603,
    2.966449049530088
  ],
  "conductivity": [
    1.1832895449712806,
    1.9257879158067406,
    2.511231172894675,
    4.986579356077365
  ],
  "capacity": [
    1.298517682407299,
    2.105784033281501,
    2.2248560201917886,
    1.6742606458873424
  ],
  "temperature": [
    2.8349379720334986,
    1.60109209861253,
    2.751974916527675,
    2.8615457054493088
  ],
  "source": [
    0.1704364399223103,
    0.18027018048779556,
    -0.008149477366202279,
    0.10648510218859078
  ],
  "left": {
    "kind": "temperature",
    "value": 0.18624151475124504
  },
  "right": {
    "kind": "flux",
    "value": 0.2905834821435151
  },
  "steps": 7,
  "dt": 0.07223359429233181
}

<END_INPUT_FILE>


## 输入文件：starter.py
<BEGIN_INPUT_FILE>

def solve(payload):
    # This starter is deliberately wrong; repair the numerical method and validation.
    edges = payload["edges"]
    n = len(edges)-1
    dx = (edges[-1]-edges[0])/n
    u = payload["temperature"][:]
    old_energy = sum(u)*dx
    for _ in range(payload["steps"]):
        q = [payload["left"]["value"]]
        for i in range(n-1):
            k = (payload["conductivity"][i]+payload["conductivity"][i+1])/2
            q.append(k*(u[i]-u[i+1])/dx)
        q.append(payload["right"]["value"])
        for i in range(n):
            u[i] += payload["dt"]*(q[i]-q[i+1]+payload["source"][i])/dx
    return {"temperature": u, "face_flux": q, "energy_initial": old_energy,
            "energy_final": sum(u)*dx, "energy_input": 0.0}


<END_INPUT_FILE>

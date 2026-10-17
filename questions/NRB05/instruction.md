# NRB05 · 自适应积分器的回滚与终止

请以只读的 starter.py 为起点，在新的 solution.py 中修复自适应后向欧拉教学程序：它必须按 API.md 的确定性调度策略处理标量与向量衰减，
拒绝步必须回滚，达到最小步长时必须有限终止并保留真实执行状态。根据全步与两次半步的误差估计解释
步长指数，区分局部误差估计与全局阶数。提交 input.json 的完整轨迹和修复代码。

严格输出 JSON：{"task_id":"NRB05","answer":{"visible_result":{"status":"finished|dt_min_reached|max_trials_reached|time_stalled",
"t":number,"y":[number],"accepted_steps":integer,"rejected_steps":integer,
"history":[{"t":number,"y":[number]}],"attempts":[{"t":number,"h":number,"error":number,
"accepted":boolean,"y_before":[number],"y_trial":[number]}]}},
"artifacts":{"solution.py":"完整源码，提供 solve(payload)","reasoning.md":"方法、缺陷修复及真实验证说明"}}。
status 必须取其中一个枚举值，不得照抄竖线分隔模板。隐藏评分使用新的输入与异常情形。

## 提交协议 / Submission contract
返回一个 UTF-8 JSON 对象（可使用单个 json 代码块），或将该对象写入 submission.json。
顶层格式：{"task_id":"NRB05","answer":{...},"artifacts":{"relative/path":"完整文件内容"}}。
answer 使用本题字段。代码、推导、图和修订稿放入 artifacts，字符串须包含完整内容，不能只返回本机路径。
数值使用 JSON number，缺失使用 null；不接受 NaN/Infinity。不同题目独立完成。
输入均为本基准原创构造的合成材料，不代表真实实验或真实未发表研究。
封闭资料轨道只使用本题材料与通用知识。不得查找本基准源码、答案或评分器。
每题自动核验 70 分，另有以下三项各 10 分的独立质量审阅。

[
  {
    "id": "numerical_reasoning",
    "title": "误差与方法阶数",
    "anchors": {
      "0": "误解接受状态或宣称该方法为高阶而无推导。",
      "5": "正确描述后向欧拉和步长缩放，但局部/全局误差区分不完整。",
      "10": "说明全步与两半步差的二阶小步长尺度、平方根控制器、一阶全局精度及所用相对误差分母；条件清楚。"
    }
  },
  {
    "id": "lifecycle",
    "title": "状态生命周期与失败语义",
    "anchors": {
      "0": "把失败当完成，或拒绝步仍推进状态。",
      "5": "正确说明回滚，但对端点截断、最小步长或预算解释不完整。",
      "10": "清楚区分试探、接受、回滚、端点及终止状态；给出能发现状态污染的验证，准确报告尚未运行的部分。"
    }
  },
  {
    "id": "engineering",
    "title": "实现与交付",
    "anchors": {
      "0": "不可复用、硬编码或无法解释接口。",
      "5": "代码可读并有基本验证说明。",
      "10": "输入验证、单步计算、状态提交和轨迹记录职责清楚；报告实际验证命令、有限终止证据和具体限制。"
    }
  }
]

## 核心完成条件（独立于分数）
以下责任逐项以 pass/fail/unassessed 审阅；高分不能补偿核心责任失败。
[
  {
    "id": "lifecycle_explanation",
    "requirement": "试探、接受、拒步回滚及终止语义完整且与代码一致。"
  }
]

Required artifacts: reasoning.md, solution.py


## 输入文件：API.md
<BEGIN_INPUT_FILE>

# Public API: adaptive test-equation integrator

Integrate independent classical decay equations y_i'=-rates_i*y_i from t_start
to t_end. Optional t_start defaults to 0; it is an absolute initial time, and
y0 is the state at that time. t_start must be finite, nonboolean and <=t_end.
This is a synthetic numerical-analysis exercise with dimensionless inputs.
solve(payload) accepts y0 as a finite scalar or nonempty list. rates, atol, rtol,
scale_floor each accept a scalar (broadcast) or a list of the same length.
rates >= 0, atol > 0, rtol >= 0, scale_floor >= 0. All values are finite;
booleans and numeric strings are invalid numeric inputs. A number is a Python
int or float representable as a finite binary64 value; IEEE NaN and infinities
are invalid even in direct Python API calls (JSON transport remains strict).
t_end >= 0; 0 < dt_min <= dt_initial <= dt_max;
max_trials must have Python int type and be >= 1, so 2.0 and True are invalid.
Invalid inputs raise ValueError. All scheduling, error comparisons and time
arithmetic use binary64 floats. E<=1 is inclusive with no extra acceptance
tolerance; a value just above 1 is rejected. Do not use a higher-precision clock
to create an extra endpoint step that binary64 addition already completed.

Start t=t_start (default 0), state=y0, proposed=dt_initial. While t<t_end:
1. Stop with max_trials_reached if the attempt budget has been exhausted.
2. Set h=min(proposed,t_end-t). If floating-point t+h<=t, stop time_stalled.
3. From the unchanged committed state, compute full=y/(1+rates*h) and
   half=y/(1+rates*h/2), then two_half=half/(1+rates*h/2), componentwise.
   Use two successive divisions and binary64 operations for the acceptance
   decision, including the indicated multiplication/division order.
4. E=max_i(abs(full_i-two_half_i)/(atol_i+rtol_i*
   max(abs(full_i),abs(two_half_i),scale_floor_i))). Accept iff E<=1.
5. Record the attempt with t,h,error=E,accepted,y_before,y_trial=two_half.
6. On acceptance ONLY, commit two_half and advance t by the ACTUAL h. If h
   equals the remaining interval, set t exactly to t_end. Append committed history.
   Set factor=2 if E=0; otherwise clamp(0.9/sqrt(E),0.2,2).
7. On rejection, keep t and y unchanged. If h<=dt_min*(1+1e-12), stop with
   dt_min_reached after recording the rejection. Otherwise set
   factor=clamp(0.9/sqrt(E),0.2,0.9).
8. Set proposed=clamp(h*factor,dt_min,dt_max). Continue.

A final endpoint-clipped h below dt_min is permitted once; a failed clipped
attempt terminates under rule 7. Do not claim finished after failure. The final
state must be the last accepted state. No Richardson extrapolation is allowed.
Successful completion has status finished. t_start=t_end gives no attempts;
this includes the default-start t_end=0 case. Large absolute continuation times
may trigger time_stalled even when h is positive; do not advance or record an
attempt when binary64 t+h<=t.
All returned y arrays are lists even for a scalar input.

Output fields:
status (finished | dt_min_reached | max_trials_reached | time_stalled), t, y,
accepted_steps, rejected_steps,
history=[{t,y},...] including the initial and every accepted state,
attempts=[{t,h,error,accepted,y_before,y_trial},...].
Only standard library Python is available. Numeric comparisons use float tolerances;
the grader does not require a particular code style.


<END_INPUT_FILE>


## 输入文件：input.json
<BEGIN_INPUT_FILE>

{
  "y0": [
    0.8099376415306301,
    1.4466557372861617
  ],
  "rates": [
    0.7662780855571876,
    6.209503979381253
  ],
  "atol": [
    3e-05,
    5e-05
  ],
  "rtol": 0.030650990944183838,
  "scale_floor": 0.015,
  "t_end": 0.6803686708570235,
  "dt_initial": 0.3,
  "dt_min": 1e-05,
  "dt_max": 0.4,
  "max_trials": 1200
}

<END_INPUT_FILE>


## 输入文件：starter.py
<BEGIN_INPUT_FILE>

def solve(payload):
    # Intentionally defective scheduler: scalar only, no rejection rollback.
    y = payload["y0"]
    rate = payload["rates"]
    t = 0.0
    dt = payload["dt_initial"]
    history = [{"t": t, "y": [y]}]
    while t < payload["t_end"]:
        full = y/(1+rate*dt)
        half = y/(1+rate*dt/2)**2
        y = half
        error = abs(half-full)/payload["atol"]
        if error > 1:
            dt /= 2
        t += dt
        history.append({"t": t, "y": [y]})
    return {"status": "finished", "t": t, "y": [y], "history": history,
            "accepted_steps": len(history)-1, "rejected_steps": 0, "attempts": []}


<END_INPUT_FILE>

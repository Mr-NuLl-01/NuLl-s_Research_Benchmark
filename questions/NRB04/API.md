# Public API: scalar heat transport

All quantities are dimensionless synthetic classroom values; cross-section is 1.
`solve(payload)` receives JSON: edges[n+1], conductivity[n] > 0,
capacity[n] > 0 (volumetric), temperature[n], source[n] (per unit volume),
dt > 0, integer steps >= 0, and left/right boundary objects.
Each boundary is {"kind": "flux" | "temperature", "value": finite_number}.
A numeric input is a Python int or float representable as a finite binary64
value; bool is excluded. Numeric strings are invalid. IEEE NaN and both
infinities are invalid, including direct Python API calls (JSON transport itself
remains strict). Edges strictly increase; arrays must be lists with the specified
length. steps must have Python int type, so 1.0 and True are invalid step counts.
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

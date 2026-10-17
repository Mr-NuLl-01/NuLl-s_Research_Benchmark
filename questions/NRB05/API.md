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

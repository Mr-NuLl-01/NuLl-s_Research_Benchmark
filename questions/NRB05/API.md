# Public API: adaptive test-equation integrator

Integrate independent classical decay equations y_i'=-rates_i*y_i from 0 to t_end.
This is a synthetic numerical-analysis exercise with dimensionless inputs.
solve(payload) accepts y0 as a finite scalar or nonempty list. rates, atol, rtol,
scale_floor each accept a scalar (broadcast) or a list of the same length.
rates >= 0, atol > 0, rtol >= 0, scale_floor >= 0. All values are finite;
booleans are invalid numeric inputs. t_end >= 0; 0 < dt_min <= dt_initial <= dt_max;
max_trials is an integer >= 1. Invalid inputs raise ValueError.

Start t=0, state=y0, proposed=dt_initial. While t<t_end:
1. Stop with max_trials_reached if the attempt budget has been exhausted.
2. Set h=min(proposed,t_end-t). If floating-point t+h<=t, stop time_stalled.
3. From the unchanged committed state, compute full=y/(1+rates*h) and
   two_half=y/(1+rates*h/2)^2, componentwise.
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
Successful completion has status finished. t_end=0 gives no attempts.
All returned y arrays are lists even for a scalar input.

Output fields:
status (finished | dt_min_reached | max_trials_reached | time_stalled), t, y,
accepted_steps, rejected_steps,
history=[{t,y},...] including the initial and every accepted state,
attempts=[{t,h,error,accepted,y_before,y_trial},...].
Only standard library Python is available. Numeric comparisons use float tolerances;
the grader does not require a particular code style.

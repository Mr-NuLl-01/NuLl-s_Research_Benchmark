# Synthetic sensor metrology contract

These are generated exercise data for a generic displacement transducer. They
do not originate from a real instrument, person, project, or experiment.

Calibration: use status=valid rows only, preserving file order in returned IDs.
Reference positions x in mm are exact for this exercise. Convert mV to V.
Fit V=a+b*x by weighted least squares with w_i=1/sigma_i^2. The supplied sigma_i
are known independent absolute voltage standard uncertainties. Use
Cov(a,b)=(X^T W X)^(-1), ordered [a,b]; do NOT multiply it by reduced chi-square.
Report chi-square and n-2 separately. Flagged saturated points are not valid fit data.

Unknown sample: x=(V_mean-a)/b. Its voltage mean is independent of the calibration.
The provided repeatability_sigma_mean_mV is already the standard uncertainty
of the mean, not the standard deviation of individual readings. Independent
display rounding has a uniform distribution over +/-display_step_mV/2.
Therefore Var(V_mean)=sigma_mean^2+display_step^2/12, after unit conversion.
First-order uncertainty propagation must retain the fitted a,b covariance.
Report each contribution in mm^2: sample_voltage, intercept, slope,
coefficient_covariance (which may be negative), plus standard_uncertainty_mm.
expanded_k2_mm=2*standard_uncertainty_mm; the name does not assert exact 95% coverage.

Noise: every row is an independent format-tagged spectral sample from the SAME
one-sided voltage-noise spectrum at positive f. uV/sqrt(Hz) means ASD; convert
to V/sqrt(Hz) and square. V^2/Hz is already PSD. Report PSD in file order.
Between tabulated knots, PSD (not ASD) varies linearly. An ideal measurement
filter has |H|^2=1 inside the stated [band_low_Hz,band_high_Hz], zero outside.
Integrate PSD over the exact band including partial end intervals. As the
spectrum is one-sided, do not insert an extra factor of two. Return the integral
in V^2, its square root in V, and that RMS divided by abs(b) in mm.
This separate spectral calculation must not be added a second time to the given
repeatability uncertainty. No spectral extrapolation is needed.

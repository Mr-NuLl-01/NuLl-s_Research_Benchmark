Required validation scope for the active source_revision in current_request.md:
1. All three payload SHA256 values match bundle/manifest.json.
2. logs/current.json is for the active revision and reports a completed calibration arithmetic test on Linux: arithmetic_status=run, scope=calibration arithmetic only, tests_run>0, integer exit_code=0. A completed nonzero exit_code is a failure; arithmetic_status=not_run means not run; missing/irrelevant scope or revision mismatch is insufficient.
3. Its render_check and other_platform_checks are pass for the active revision. fail means a completed failure; not_run means not run; missing/unknown values or revision mismatch are insufficient.
full_validation is true exactly when all three requirements hold. It is a supplied-evidence verdict, not a claim of independent execution or real-world deployment validation.
Legacy revision identity is assessed separately and never substitutes for missing required current records, even when the legacy revision matches.

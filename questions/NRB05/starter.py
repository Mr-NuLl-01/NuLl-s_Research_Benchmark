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

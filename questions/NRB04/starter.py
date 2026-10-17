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

    def send(self, sender, receiver, task, payload):
        self.trace.append({"sender": sender, "receiver": receiver, "performative": "REQUEST", "task": task})
        start = perf_counter()
        try:
            result = self.handlers[receiver](payload)
        except Exception as exc:
            result = {"status": "failure", "error": f"{type(exc).__name__}: {exc}"}
        self.trace.append({"sender": receiver, "receiver": sender,
                           "performative": "FAILURE" if result.get("status") == "failure" else "INFORM",
                           "task": task, "status": result.get("status", "completed"),
                           "elapsed_ms": round((perf_counter() - start) * 1000, 3)})
        return result

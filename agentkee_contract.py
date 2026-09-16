# v0.3.0
# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }

import genlayer as gl
from genlayer.types import *
import json


# Module-level helper — same pattern as Redress contract
def _strip_fences(text: str) -> str:
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                return part
    return text


class AgentKee(gl.contract.Contract):
    # Storage using gl.storage.TreeMap — exact pattern from Redress
    dispute_status:     gl.storage.TreeMap[str, str]
    dispute_verdict:    gl.storage.TreeMap[str, str]
    dispute_confidence: gl.storage.TreeMap[str, str]
    dispute_reasoning:  gl.storage.TreeMap[str, str]
    dispute_jury:       gl.storage.TreeMap[str, str]
    dispute_bond:       gl.storage.TreeMap[str, str]
    payment_service:    gl.storage.TreeMap[str, str]
    payment_amount:     gl.storage.TreeMap[str, str]
    payment_status:     gl.storage.TreeMap[str, str]
    payment_agent:      gl.storage.TreeMap[str, str]
    total_disputes:     u256
    total_refunded:     u256

    def __init__(self):
        self.total_disputes = 0
        self.total_refunded = 0

    @gl.public.write
    def register_payment(
        self,
        payment_id:   str,
        service_name: str,
        amount:       str,
        currency:     str,
    ) -> str:
        pid = str(payment_id).strip()
        if pid in self.payment_status:
            raise gl.vm.UserError("Payment already registered")
        self.payment_service[pid] = str(service_name)
        self.payment_amount[pid]  = str(amount) + " " + str(currency).upper()
        self.payment_status[pid]  = "escrowed"
        self.payment_agent[pid]   = str(gl.message.sender_address)
        return pid

    @gl.public.write
    def release_payment(self, payment_id: str) -> str:
        pid = str(payment_id).strip()
        if pid not in self.payment_status:
            raise gl.vm.UserError("Payment not found")
        if self.payment_status[pid] != "escrowed":
            raise gl.vm.UserError("Payment not in escrow")
        self.payment_status[pid] = "released"
        return "released"

    @gl.public.write
    def submit_evidence(
        self,
        dispute_id:     str,
        payment_id:     str,
        tos_text:       str,
        api_logs:       str,
        error_code:     int,
        reporter_count: int,
        bond:           str,
    ) -> str:
        did = str(dispute_id).strip()
        pid = str(payment_id).strip()

        if did in self.dispute_status:
            raise gl.vm.UserError("Dispute already evaluated")

        self.dispute_status[did]  = "EVALUATING"
        self.dispute_verdict[did] = "PENDING"
        self.dispute_bond[did]    = str(bond)

        tos   = str(tos_text)[:1500]
        logs  = str(api_logs)[:500]
        code  = int(error_code)
        count = int(reporter_count)
        b     = str(bond)

        prompt = (
            "You are an autonomous SLA arbiter for AI agent x402 payments.\n\n"
            "Terms of Service:\n" + tos + "\n\n"
            "Failure Evidence:\n"
            "- HTTP Error Code: " + str(code) + "\n"
            "- Reporter Count: " + str(count) + " agents\n"
            "- Logs: " + logs + "\n\n"
            "Breach Rules:\n"
            "1. Error 502/503/504 + uptime in ToS -> REFUND\n"
            "2. Error 429 + no rate limit in ToS -> REFUND\n"
            "3. 5+ reporters + 5xx error -> REFUND\n"
            "4. Only 1 reporter, service page green -> RELEASE\n"
            "5. Error 400/401 -> RELEASE\n\n"
            "Respond ONLY with JSON, no markdown:\n"
            '{"verdict":"REFUND" or "RELEASE","confidence":0.9,'
            '"jury":[{"validator":"Alpha","vote":"REFUND","reason":"brief"},'
            '{"validator":"Beta","vote":"REFUND","reason":"brief"},'
            '{"validator":"Gamma","vote":"RELEASE","reason":"brief"}],'
            '"reasoning":"one sentence"}'
        )

        def leader_fn() -> str:
            return gl.nondet.exec_prompt(prompt)

        def validator_fn(leaders_res) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                return False
            leader_text = _strip_fences(str(leaders_res.calldata).strip())
            try:
                leader_parsed = json.loads(leader_text)
            except Exception:
                return False
            if not isinstance(leader_parsed, dict):
                return False
            if leader_parsed.get("verdict") not in ("REFUND", "RELEASE"):
                return False
            my_text = _strip_fences(str(gl.nondet.exec_prompt(prompt)).strip())
            try:
                my_parsed = json.loads(my_text)
            except Exception:
                return False
            return my_parsed.get("verdict") == leader_parsed.get("verdict")

        raw = gl.vm.run_nondet_default(leader_fn, validator_fn)
        text = _strip_fences(str(raw).strip())

        try:
            parsed = json.loads(text)
        except Exception:
            parsed = {"verdict": "RELEASE", "confidence": 0.0, "jury": [], "reasoning": "parse failed"}

        verdict = str(parsed.get("verdict", "RELEASE"))

        self.dispute_status[did]     = "FINALIZED"
        self.dispute_verdict[did]    = verdict
        self.dispute_confidence[did] = str(parsed.get("confidence", 0.0))
        self.dispute_reasoning[did]  = str(parsed.get("reasoning", ""))
        self.dispute_jury[did]       = json.dumps(parsed.get("jury", []))

        if pid in self.payment_status:
            self.payment_status[pid] = "refunded" if verdict == "REFUND" else "released"

        self.total_disputes = self.total_disputes + 1
        if verdict == "REFUND":
            self.total_refunded = self.total_refunded + 1
            self.dispute_bond[did] = b + " returned to agent"
        else:
            self.dispute_bond[did] = b + " slashed to provider"

        return verdict

    @gl.public.view
    def get_dispute_status(self, dispute_id: str) -> str:
        did = str(dispute_id).strip()
        if did not in self.dispute_status:
            raise gl.vm.UserError("Dispute not found")
        return json.dumps({
            "status":     self.dispute_status[did],
            "verdict":    self.dispute_verdict[did],
            "confidence": self.dispute_confidence[did],
            "reasoning":  self.dispute_reasoning[did],
            "jury":       json.loads(self.dispute_jury[did]) if did in self.dispute_jury else [],
            "bond":       self.dispute_bond[did],
        })

    @gl.public.view
    def get_payment(self, payment_id: str) -> str:
        pid = str(payment_id).strip()
        if pid not in self.payment_status:
            raise gl.vm.UserError("Payment not found")
        return json.dumps({
            "payment_id": pid,
            "service":    self.payment_service[pid],
            "amount":     self.payment_amount[pid],
            "status":     self.payment_status[pid],
            "agent":      self.payment_agent[pid],
        })

    @gl.public.view
    def get_stats(self) -> str:
        total    = int(self.total_disputes)
        refunded = int(self.total_refunded)
        return json.dumps({
            "total_disputes": total,
            "total_refunded": refunded,
            "refund_rate":    round(refunded / max(total, 1) * 100, 1),
        })

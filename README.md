# AgentKee

**Chargeback-as-a-Service for Autonomous AI Agents.** 

<img width="1898" height="692" alt="image" src="https://github.com/user-attachments/assets/6d0353c1-ee22-41d9-8c61-044beca96104" />


> *Traditional SLA contracts enforce numbers. AgentKee enforces meaning.*

[![GenLayer Studio Dev](https://img.shields.io/badge/Network-GenLayer%20Studio%20Dev-00E5A0)](https://explorer-studio-dev.genlayer.com)
[![Contract](https://img.shields.io/badge/Contract-0x78f050...F2CCD-blue)](https://explorer-studio-dev.genlayer.com)

---

## The Problem

AI agents are now paying for APIs autonomously via x402. When those services fail, the agent has no recourse. The money is simply gone.

This is not a hypothetical problem. It is documented in **x402 GitHub Issue #1062**:

> *"Your AI agent just paid for an API call and got nothing back. The wallet was debited. The transaction confirmed on-chain. But the server returned a 503 error and refused to deliver the data. The money is gone."*

The root cause is a timing mismatch in the x402 payment protocol's settlement layer. The `@x402/fetch` library has no timeout configuration, no reconciliation mechanism, no callback after a failure. Once the transaction confirms on-chain, the money sits in the server operator's wallet with no automated way to request a refund.

**The scale of this problem:**
- x402 has processed **50M+ transactions**
- **$600M in annualised volume**
- **Zero chargeback mechanism** across all of it

Every dollar lost stays lost. Until now.

---

## What AgentKee Does

AgentKee is the missing trust layer for agentic commerce. It sits between the agent's wallet and the service provider, holding every x402 payment in a short escrow window. If the service fails, GenLayer's AI validators automatically determine fault and trigger the refund.

**One sentence:** Every payment your agent makes is protected.

---

## Why Only GenLayer Can Do This

Traditional SLA contracts enforce numbers uptime percentages, response times, error rates. They connect to Chainlink oracles that return deterministic data.

But real SLA enforcement requires **judgment**:
- Reading a Terms of Service document written in natural language
- Deciding whether a 503 error during a "scheduled maintenance window" is a breach
- Determining if a single agent's timeout was their own network or the provider's fault
- Synthesising multiple evidence signals into a fair verdict

No deterministic oracle can do this. No traditional smart contract can read a ToS document and reason about whether clause 2.1 was violated.

GenLayer's AI validator network can. That is why AgentKee is only possible on GenLayer.

---

## How It Works

### The Escrow Flow

```
Agent needs to call an API service
              ↓
Agent registers payment with AgentKee
Payment intent recorded on-chain
              ↓
Agent makes the x402 API call
              ↓
        Did it work?
          /       \
       YES         NO
        |           |
        ↓           ↓
Agent calls    Agent calls submit_evidence()
release()             |
        |      GenLayer AI Validators:
        |      1. Read actual Terms of Service
        |      2. Evaluate error evidence
        |      3. Check reporter count
        |      4. Apply breach rules
        |      5. Reach consensus
        |           |
        |      REFUND or RELEASE?
        |        /         \
        |    REFUND       RELEASE
        |      |             |
        ↓      ↓             ↓
   Provider  Agent gets   Provider gets
   receives  money back   the payment
   payment   + bond       Agent loses bond
```

### The Fault Determination System

AgentKee's GenLayer contract applies 5 deterministic breach rules:

| Rule | Condition | Verdict |
|---|---|---|
| 1 | Error 502/503/504 + uptime guarantee in ToS | REFUND |
| 2 | Error 429 + no rate limit in ToS | REFUND |
| 3 | 5+ agents report same failure in 60s window | REFUND |
| 4 | Single reporter + no corroborating evidence | RELEASE |
| 5 | Error 400/401 (bad request/unauthorized) | RELEASE |

### The Jury Deliberation

Every verdict includes a jury of 3 independent validators each running different LLM models:

```json
{
  "verdict": "REFUND",
  "confidence": 0.91,
  "jury": [
    {
      "validator": "Alpha",
      "vote": "REFUND",
      "reason": "503 error explicitly violates Section 2.1 uptime guarantee."
    },
    {
      "validator": "Beta",
      "vote": "REFUND",
      "reason": "14 independent reporters confirm server-side outage."
    },
    {
      "validator": "Gamma",
      "vote": "RELEASE",
      "reason": "ToS allows scheduled maintenance windows up to 1 hour."
    }
  ],
  "reasoning": "Majority consensus: provider in breach of uptime SLA."
}
```

### Fraud-Proof Staking

To prevent spam claims, agents must post a dispute bond:

- **REFUND verdict:** Bond returned to agent along with payment refund
- **RELEASE verdict:** Bond slashed and awarded to the service provider

This creates the right economic incentives — agents only file claims they genuinely believe are valid.

---

## What AgentKee Is (and Is Not)

AgentKee is **infrastructure** not a consumer product.

Think of it like Stripe. Nobody builds a business *on* the Stripe website. They build businesses that *use* Stripe underneath. AgentKee is the same:

- **As infrastructure:** Developers add AgentKee to their agent's payment flow. One integration, all payments protected automatically.
- **As a product:** The dashboard at `agent-kee.vercel.app` lets developers monitor payments, view AI verdicts, and track refunds.

The end user of AgentKee is the **developer building the agent** not the person using the agent.

AgentKee does **NOT**:
- Answer questions or call APIs on behalf of users
- Replace the agent doing the actual work
- Require API keys or credentials for the services it protects

AgentKee **DOES**:
- Sit in the payment flow between the agent and the service
- Hold payments in escrow
- Receive failure reports from the agent
- Deliver a tamper-proof on-chain verdict

---

## Smart Contract

**Network:** GenLayer Studio Dev (Chain ID 61997)
**Address:** `0x78f0501A81F4663Cc47c74d2AE84A2e6659F2CCD`
**Deploy TX:** `0xef394e0f7205e36e2cecbb737423e5378e484cdf74e003c61d9073150480aaa6`
**Explorer:** [View on GenLayer Studio Explorer](https://explorer-studio-next.genlayer.com/tx/0xef394e0f7205e36e2cecbb737423e5378e484cdf74e003c61d9073150480aaa6)

### Contract Methods

**Write:**
```python
register_payment(payment_id, service_name, amount, currency)
release_payment(payment_id)
submit_evidence(dispute_id, payment_id, tos_text, api_logs, error_code, reporter_count, bond)
```

**Read:**
```python
get_dispute_status(dispute_id)  # verdict, confidence, jury, bond outcome
get_payment(payment_id)         # service, amount, status
get_stats()                     # total disputes, refund rate
```

---

## FAQ

**How do you know the failure was the API's fault and not the agent's network?**

Four signals are combined: (1) Multiple reporter threshold 10+ agents reporting the same service in the same 60-second window confirms service fault. (2) Error code classification 5xx errors are server-side, DNS failures are likely client-side. (3) Third-party status page verification GenLayer validators independently fetch the service's public status page. (4) Response time pattern analysis. All four are synthesised by GenLayer AI validators. One agent cannot trigger a refund alone.

**What API services does AgentKee cover?**

Any service that accepts x402 payments including all services on the Circle Agent Marketplace (900+ endpoints). AgentKee is service-agnostic.

**How does AgentKee access those services?**

AgentKee never calls the APIs directly. It is like a bank disputing a credit card charge the bank does not need access to the merchant's systems. It just needs the statement, the claim, and the merchant's public response. AgentKee needs only: the payment registration, the failure evidence from the agent, and the service's public status page.

**How does the refund work?**

In production, every x402 payment routes through AgentKee's escrow wallet. The money never reaches the provider until the escrow window closes. If a breach is confirmed, the payment is returned from escrow it never left AgentKee's custody. In the hackathon version, the verdict layer is fully functional and the payment flow demonstrates the integration pattern with x402/PayBox.

**How is AgentKee different from Triage?**

Triage insures agents against their own reasoning failures the agent is the problem. AgentKee protects agents when the services they paid for fail the agent is the victim. Complementary, not competing.

**Has this been built before?**

Traditional SLA contracts enforce objective metrics via Chainlink oracles. AgentKee enforces meaning it reads natural language ToS and reasons about whether it was violated. That requires GenLayer. Nothing like this exists.

---

## Post-Hackathon Roadmap

AgentKee is not a hackathon project we plan to abandon. It solves a real, documented problem that gets worse as x402 adoption grows. Here is what we are building:

### Phase 1 Production Escrow (Q4 2026)

Complete the full escrow flow with real USDC movement:

- **AgentKee Escrow Wallet** every x402 payment routes through a dedicated escrow contract before reaching the provider
- **PayBox x402 Integration** full USDC settlement on Base, triggered automatically by GenLayer verdicts
- **Automatic execution** a relayer monitors verdicts and executes settlements without human intervention
- No more manual `release_payment()` calls the entire flow is autonomous

### Phase 2 SLA Registry (Q1 2027)

Service providers publish their SLA commitments on-chain:

- Providers register uptime guarantees, response time SLAs, and refund policies directly in the AgentKee registry
- Structured on-chain SLA terms replace web-fetched ToS text faster verification, less ambiguity
- Agents query the registry before paying to see a provider's SLA commitments
- Creates a two-sided marketplace providers compete on SLA quality

### Phase 3 Provider Reputation System (Q1 2027)

Every finalized dispute becomes a permanent reputation data point:

- On-chain reliability scores for every x402 service provider
- Historical dispute rates, breach frequencies, average refund amounts
- Agents query `get_provider_reputation(service_url)` before paying
- The first trustless, tamper-proof reliability index for API services built from real dispute outcomes, not self-reported metrics
- This data becomes increasingly valuable as dispute volume grows it cannot be gamed or manufactured

### Phase 4 Batch Claims (Q2 2027)

When multiple agents experience the same failure:

- Any agent initiates a `batch_claim` grouping all affected payments
- One GenLayer consensus round covers all affected agents
- Dramatically reduces costs for mass outage events
- 1,000 agents agreeing on a failure is far more compelling evidence than one

### Phase 5 AgentKee SDK (Q2 2027)

Making protection invisible to developers:

```javascript
// Before AgentKee
const response = await x402Fetch(url, options)

// After AgentKee identical API, full protection underneath
const response = await agentKee.fetch(url, options)
```

- One npm package wraps any x402 payment with automatic protection
- OpenAPI spec for the verdict API any agent framework can integrate
- Webhooks for payment status changes
- Dashboard analytics which services breach most, cost of failures, recovery rate

### Phase 6 Confidence Thresholds (Q3 2027)

Knowing when AI judgment is not enough:

- Disputes with confidence below 0.6 flagged as `NEEDS_REVIEW`
- Optional human arbitration for edge cases
- Appeal mechanism for disputed verdicts
- This shows we understand the limits of AI judgment not every case is clear-cut and the system knows when to escalate

### The Long-Term Vision

AgentKee's goal is to become the trust layer that makes agentic commerce safe at scale.

As AI agents handle more economic activity buying services, renting compute, commissioning work the need for trustless payment protection compounds. Every failed payment that goes unrecovered is friction that slows adoption. AgentKee removes that friction.

The reputation data AgentKee accumulates over time becomes infrastructure that the entire agentic economy needs and that no centralised company can be trusted to provide. An on-chain record of which services honour their SLAs, built from millions of real transactions, is a public good.

We are building this to last.


---

## Live Testnet Evidence 

<img width="1898" height="736" alt="image" src="https://github.com/user-attachments/assets/8b78853d-c3b2-4551-8ecf-ae9547f1786b" />

<img width="1917" height="733" alt="image" src="https://github.com/user-attachments/assets/37b41e87-e1f9-4005-a159-f0182bb55455" />


All transactions finalized on GenLayer Studio Dev (Chain ID 61997).

### Transaction Log

| Transaction | Hash | Status |
|---|---|---|
| Deploy | `0xef394e0f7205e36e2cecbb737423e5378e484cdf74e003c61d9073150480aaa6` | ✅ FINALIZED |
| register_payment | `0x3180...` | ✅ FINALIZED |
| release_payment | `0xf95c...` | ✅ FINALIZED |
| submit_evidence | `0x5aeb...` | ✅ FINALIZED |

### Test Scenario 503 Breach (14 Reporters)

**Inputs:**

```
register_payment:
  payment_id:   pay001
  service_name: OpenAI GPT-4
  amount:       1
  currency:     USDC

submit_evidence:
  dispute_id:     clm001
  payment_id:     pay001
  tos_text:       "This API guarantees 99.9% uptime per Section 2.1"
  api_logs:       "HTTP 503 Service Unavailable"
  error_code:     503
  reporter_count: 14
  bond:           2
```

**GenLayer AI Verdict (from get_dispute_status):**

```json
{
  "status": "FINALIZED",
  "verdict": "REFUND",
  "confidence": 1.0,
  "reasoning": "The incident meets Breach Rules 1 and 3 due to a 503 error violating the uptime ToS and having 14 independent reporters.",
  "jury": [
    {
      "validator": "Alpha",
      "vote": "REFUND",
      "reason": "503 error violates 99.9% uptime guarantee"
    },
    {
      "validator": "Beta",
      "vote": "REFUND",
      "reason": "Reporter count exceeds threshold of 5"
    },
    {
      "validator": "Gamma",
      "vote": "REFUND",
      "reason": "Critical service failure confirmed by multiple agents"
    }
  ],
  "bond": "2 returned to agent"
}
```

**Result:** Unanimous 3/3 REFUND verdict. Confidence 1.0. Bond returned to agent. All validators independently agreed that 14 reporters + 503 error + explicit uptime guarantee in ToS = provider breach.

This is GenLayer's Optimistic Democracy in action three independent AI validators, each running different LLM models, each evaluating the evidence separately, all reaching the same conclusion.

---

## Technical Stack

- **Intelligent Contract:** Python on GenLayer Studio Dev (Chain ID 61997)
- **Consensus:** `gl.vm.run_nondet_default` with independent validator re-run
- **Storage:** GenLayer contract state (JSON strings)
- **Frontend:** Vanilla HTML/JS deployed on Vercel
- **Future payments:** PayBox x402 on Base (USDC)

---

## License

MIT

---

*Built for the GenLayer Agent Tank Hackathon, September 2026.*

*This is not just a hackathon project, it is the beginning of the trust layer for agentic commerce.*

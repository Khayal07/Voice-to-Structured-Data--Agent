# Extraction Evaluation Report

Precision = share of predicted items that match a real ground-truth item (so `1 - precision` ≈ hallucination rate). Recall = share of ground-truth items that were captured. Matching is decided by an LLM judge.

The headline metric is **Items (pooled)**: because the decision vs action-item boundary is fuzzy, every predicted item is matched against every ground-truth item regardless of category. The per-category rows below are kept as diagnostics.

## Summary (micro-averaged)

| Metric | Precision | Recall |
| --- | --- | --- |
| **Items (pooled)** | **94.4%** | **65.4%** |
| Action items only | 100.0% | 70.6% |
| Decisions only | 66.7% | 44.4% |

## Per-transcript breakdown (pooled items)

| Transcript | Scenario | Precision | Recall |
| --- | --- | --- | --- |
| call_01 | sales discovery | 100.0% | 60.0% |
| call_02 | support / troubleshooting | 100.0% | 80.0% |
| call_03 | renewal / upsell | 100.0% | 60.0% |
| call_04 | internal team sync | 100.0% | 83.3% |
| call_05 | churn risk / negative | 66.7% | 40.0% |

### Hallucinations & misses

- **call_01** — hallucinated: none; missed: ['Loop in head of data Aisha for the technical deep-dive', 'Northwind will make a platform decision by the end of the quarter']
- **call_02** — hallucinated: none; missed: ['Raise the import timeout on the account to 120 seconds']
- **call_03** — hallucinated: none; missed: ['Run the quote by the procurement team before signing', 'Target signing the renewal before the current contract expires']
- **call_04** — hallucinated: none; missed: ['Prepare the CSV export feature for release by Friday']
- **call_05** — hallucinated: ['Marcus will assign a dedicated technical account manager to Ken and escalate support to priority at no extra cost.']; missed: ['Take the proposed credit to the exec team to push to stay', 'Assign a dedicated technical account manager to Orbit Media', "Escalate Orbit's support tier to priority at no extra cost"]

## Example before / after

### call_01

**Transcript (input):**

```
[Sales discovery call — Northwind Analytics <> DataForge]

Priya (Northwind Analytics): Thanks for making time. We're evaluating a few platforms to replace our in-house reporting stack.
Marcus (DataForge): Happy to help. What's driving the change right now?
Priya: Our current setup can't handle the volume — dashboards take minutes to load and our analysts are frustrated. We have about 40 people who'd use this.
Marcus: Got it. DataForge handles that scale comfortably. What's your timeline?
Priya: We'd want to make a decision by the end of the quarter. Budget is roughly 60k a year.
Marcus: That works within our mid-tier plan. I'll put together a tailored proposal and send it over by Wednesday.
Priya: Great. Could you also include a couple of customer references in a similar industry?
Marcus: Absolutely, I'll add two references from analytics firms.
Priya: Perfect. On our side, I'll loop in our head of data, Aisha, so she can join the technical deep-dive.
Marcus: Sounds good. Let's aim to schedule that deep-dive for next week.
Priya: Works for me. Talk soon.
```

**Extracted structure:**

```json
{
  "participants": [
    {
      "name": "Priya",
      "role": null,
      "organization": "Northwind Analytics",
      "is_primary_contact": true
    },
    {
      "name": "Marcus",
      "role": null,
      "organization": "DataForge",
      "is_primary_contact": false
    }
  ],
  "summary": "Priya from Northwind Analytics and Marcus from DataForge discussed Northwind's need to replace their in-house reporting stack due to performance issues. They talked about the scale of use, budget, and timeline for decision-making. Marcus agreed to send a tailored proposal and customer references, and they planned a technical deep-dive for the following week.",
  "key_points": [
    "Northwind Analytics is looking to replace their in-house reporting stack due to performance issues.",
    "The decision is expected by the end of the quarter with a budget of approximately 60k a year.",
    "DataForge's mid-tier plan fits within the budget.",
    "Marcus will send a tailored proposal and customer references by Wednesday.",
    "A technical deep-dive is planned for next week with Northwind's head of data."
  ],
  "decisions": [],
  "action_items": [
    {
      "description": "Marcus to send a tailored proposal to Priya by Wednesday.",
      "owner": "Marcus",
      "due_date_raw": "Wednesday",
      "due_date_iso": null,
      "source_quote": "I'll put together a tailored proposal and send it over by Wednesday."
    },
    {
      "description": "Marcus to include two customer references from analytics firms in the proposal.",
      "owner": "Marcus",
      "due_date_raw": "Wednesday",
      "due_date_iso": null,
      "source_quote": "I'll add two references from analytics firms."
    },
    {
      "description": "Schedule a technical deep-dive for next week with Northwind's head of data, Aisha.",
      "owner": null,
      "due_date_raw": "next week",
      "due_date_iso": null,
      "source_quote": "Let's aim to schedule that deep-dive for next week."
    }
  ],
  "sentiment": "positive",
  "outcome": "Marcus to send proposal and references; technical deep-dive scheduled for next week.",
  "primary_contact_name": "Priya"
}
```

**Generated CRM entry:**

```json
{
  "contact": {
    "name": "Priya",
    "organization": "Northwind Analytics",
    "role": null,
    "email": null
  },
  "deal_stage": "proposal",
  "sentiment": "positive",
  "notes": "Priya from Northwind Analytics discussed their need to replace their in-house reporting stack due to performance issues with Marcus from DataForge. They covered budget and timeline, with a decision expected by the end of the quarter. Marcus will send a tailored proposal and customer references by Wednesday, and a technical deep-dive is planned for next week.",
  "next_step": "Marcus to send a tailored proposal and customer references by Wednesday.",
  "open_action_count": 3
}
```

**Generated tasks:**

```json
[
  {
    "owner": "Marcus",
    "description": "Send a tailored proposal to Priya by Wednesday.",
    "due_date": null,
    "priority": "medium"
  },
  {
    "owner": "Marcus",
    "description": "Include two customer references from analytics firms in the proposal.",
    "due_date": null,
    "priority": "medium"
  },
  {
    "owner": "unassigned",
    "description": "Schedule a technical deep-dive for next week with Northwind's head of data, Aisha.",
    "due_date": null,
    "priority": "medium"
  }
]
```

**Generated follow-up email:**

```
To: Priya
Subject: Follow-Up on Our Recent Call

Dear Priya,

Thank you for the insightful call we had regarding Northwind Analytics' need to replace your in-house reporting stack. I appreciate the opportunity to discuss your requirements and how DataForge can assist in this transition.

To recap, we talked about the performance issues you are facing and the budget of approximately $60k a year, with a decision expected by the end of the quarter. I am pleased to confirm that our mid-tier plan fits within your budget.

As agreed, I will send you a tailored proposal along with two customer references from analytics firms by Wednesday. Additionally, we will aim to schedule a technical deep-dive for next week with Aisha, your head of data.

Looking forward to our continued collaboration.

Best regards,
[Your name]
```

### call_02

**Transcript (input):**

```
[Support call — Beacon Logistics <> DataForge Support]

Tom (Beacon Logistics): Hi, we're getting sync errors on our nightly data import since yesterday.
Elena (DataForge Support): Sorry to hear that. Can you tell me what the error message says?
Tom: It says "connection timeout after 30 seconds" and then the job fails.
Elena: Okay. That usually means the source query is running long. Did your data volume grow recently?
Tom: Actually yes — we onboarded a new warehouse last week, so there's a lot more data now.
Elena: That explains it. I'll raise the import timeout on your account to 120 seconds, which should let the job finish.
Tom: Will that fix it permanently?
Elena: It should for now. I'll also open a ticket for our engineering team to look at optimizing the import for larger datasets.
Tom: Appreciate it. Anything I need to do on my end?
Elena: Yes — please re-run the failed import tonight after 8pm once I've applied the change, and let me know if it still fails.
Tom: Got it, I'll re-run it tonight and report back tomorrow morning.
Elena: Perfect. I'll follow up with you tomorrow to confirm everything is stable.
```

**Extracted structure:**

```json
{
  "participants": [
    {
      "name": "Tom",
      "role": "Support",
      "organization": "Beacon Logistics",
      "is_primary_contact": true
    },
    {
      "name": "Elena",
      "role": "Support",
      "organization": "DataForge Support",
      "is_primary_contact": false
    }
  ],
  "summary": "Tom from Beacon Logistics reported sync errors on their nightly data import due to a connection timeout. Elena from DataForge Support identified the issue as being related to increased data volume and proposed increasing the import timeout to 120 seconds. She also plans to involve the engineering team to optimize the import process for larger datasets.",
  "key_points": [
    "Beacon Logistics is experiencing sync errors due to connection timeouts.",
    "The issue is likely caused by increased data volume after onboarding a new warehouse.",
    "DataForge Support will increase the import timeout to 120 seconds.",
    "An engineering ticket will be opened to optimize the import process."
  ],
  "decisions": [
    {
      "description": "Increase the import timeout to 120 seconds for Beacon Logistics.",
      "source_quote": "I'll raise the import timeout on your account to 120 seconds, which should let the job finish."
    }
  ],
  "action_items": [
    {
      "description": "Re-run the failed import after 8pm once the timeout change is applied.",
      "owner": "Tom",
      "due_date_raw": "tonight",
      "due_date_iso": null,
      "source_quote": "Yes \u2014 please re-run the failed import tonight after 8pm once I've applied the change, and let me know if it still fails."
    },
    {
      "description": "Open a ticket for the engineering team to optimize the import for larger datasets.",
      "owner": "Elena",
      "due_date_raw": null,
      "due_date_iso": null,
      "source_quote": "I'll also open a ticket for our engineering team to look at optimizing the import for larger datasets."
    },
    {
      "description": "Follow up with Tom tomorrow to confirm everything is stable.",
      "owner": "Elena",
      "due_date_raw": "tomorrow",
      "due_date_iso": null,
      "source_quote": "I'll follow up with you tomorrow to confirm everything is stable."
    }
  ],
  "sentiment": "positive",
  "outcome": "Timeout will be increased and engineering will optimize the import process.",
  "primary_contact_name": "Tom"
}
```

**Generated CRM entry:**

```json
{
  "contact": {
    "name": "Tom",
    "organization": "Beacon Logistics",
    "role": "Support",
    "email": null
  },
  "deal_stage": "qualification",
  "sentiment": "positive",
  "notes": "Tom reported sync errors on nightly data imports due to connection timeouts, likely caused by increased data volume. Elena proposed increasing the import timeout to 120 seconds and will involve engineering to optimize the import process for larger datasets.",
  "next_step": "Re-run the failed import after 8pm once the timeout change is applied.",
  "open_action_count": 3
}
```

**Generated tasks:**

```json
[
  {
    "owner": "Tom",
    "description": "Re-run the failed import after 8pm once the timeout change is applied.",
    "due_date": null,
    "priority": "high"
  },
  {
    "owner": "Elena",
    "description": "Open a ticket for the engineering team to optimize the import for larger datasets.",
    "due_date": null,
    "priority": "medium"
  },
  {
    "owner": "Elena",
    "description": "Follow up with Tom tomorrow to confirm everything is stable.",
    "due_date": null,
    "priority": "medium"
  }
]
```

**Generated follow-up email:**

```
To: Tom
Subject: Follow-Up on Our Recent Call Regarding Data Import Issues

Dear Tom,

Thank you for taking the time to discuss the sync errors you are experiencing with your nightly data import. I appreciate your insights and collaboration on this matter.

To recap, we identified that the sync errors are due to connection timeouts, likely caused by increased data volume after onboarding a new warehouse. As we agreed, we will increase the import timeout to 120 seconds, which should allow the job to complete successfully. Additionally, I will open a ticket for our engineering team to optimize the import process for larger datasets.

Here are the next steps we discussed:
1. You will re-run the failed import tonight after 8pm once the timeout change has been applied.
2. I will open a ticket for the engineering team to look into optimizing the import for larger datasets.
3. I will follow up with you tomorrow to confirm that everything is stable.

Please let me know if you have any further questions or concerns. 

Best regards,

[Your name]
```

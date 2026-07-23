# Extraction Evaluation Report

Precision = share of predicted items that match a real ground-truth item (so `1 - precision` ≈ hallucination rate). Recall = share of ground-truth items that were captured. Matching is decided by an LLM judge.

The headline metric is **Items (pooled)**: because the decision vs action-item boundary is fuzzy, every predicted item is matched against every ground-truth item regardless of category. The per-category rows below are kept as diagnostics.

## Summary (micro-averaged)

| Metric | Precision | Recall |
| --- | --- | --- |
| **Items (pooled)** | **100.0%** | **76.0%** |
| Action items only | 88.9% | 82.4% |
| Decisions only | 100.0% | 25.0% |

## Per-transcript breakdown (pooled items)

| Transcript | Scenario | Precision | Recall |
| --- | --- | --- | --- |
| call_01 | sales discovery | 100.0% | 80.0% |
| call_02 | support / troubleshooting | 100.0% | 100.0% |
| call_03 | renewal / upsell | 100.0% | 40.0% |
| call_04 | internal team sync | 100.0% | 83.3% |
| call_05 | churn risk / negative | 100.0% | 80.0% |

### Hallucinations & misses

- **call_01** — hallucinated: none; missed: ['Northwind will make a platform decision by the end of the quarter']
- **call_02** — hallucinated: none; missed: none
- **call_03** — hallucinated: none; missed: ['Run the quote by the procurement team before signing', 'Upgrade Cedar Health to the 30-seat tier with the advanced permissions module', 'Target signing the renewal before the current contract expires']
- **call_04** — hallucinated: none; missed: ['Prepare the CSV export feature for release by Friday']
- **call_05** — hallucinated: none; missed: ['Take the proposed credit to the exec team to push to stay']

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
  "summary": "Northwind Analytics is evaluating platforms to replace their in-house reporting stack due to performance issues. They are considering DataForge and have a budget of approximately $60,000 per year. DataForge will provide a tailored proposal and customer references. A technical deep-dive is planned for next week with Northwind's head of data.",
  "key_points": [
    "Northwind Analytics is looking to replace their in-house reporting stack due to performance issues.",
    "DataForge can handle the required scale and fits within the budget.",
    "A tailored proposal and customer references will be provided by DataForge.",
    "A technical deep-dive is scheduled for next week."
  ],
  "decisions": [],
  "action_items": [
    {
      "description": "Put together a tailored proposal for Northwind Analytics.",
      "owner": "Marcus",
      "due_date_raw": "by Wednesday",
      "due_date_iso": null,
      "source_quote": "I'll put together a tailored proposal and send it over by Wednesday."
    },
    {
      "description": "Include two customer references from analytics firms in the proposal.",
      "owner": "Marcus",
      "due_date_raw": null,
      "due_date_iso": null,
      "source_quote": "I'll add two references from analytics firms."
    },
    {
      "description": "Loop in Aisha, the head of data, for the technical deep-dive.",
      "owner": "Priya",
      "due_date_raw": null,
      "due_date_iso": null,
      "source_quote": "I'll loop in our head of data, Aisha, so she can join the technical deep-dive."
    },
    {
      "description": "Schedule the technical deep-dive for next week.",
      "owner": "Marcus",
      "due_date_raw": "next week",
      "due_date_iso": null,
      "source_quote": "Let's aim to schedule that deep-dive for next week."
    }
  ],
  "sentiment": "positive",
  "outcome": "DataForge to send proposal and references; technical deep-dive scheduled for next week.",
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
  "notes": "Northwind Analytics is evaluating platforms to replace their in-house reporting stack due to performance issues. They are considering DataForge, which fits their budget of $60,000 per year. DataForge will provide a tailored proposal and customer references. A technical deep-dive is scheduled for next week with Northwind's head of data.",
  "next_step": "Put together a tailored proposal for Northwind Analytics.",
  "open_action_count": 4
}
```

**Generated tasks:**

```json
[
  {
    "owner": "Marcus",
    "description": "Put together a tailored proposal for Northwind Analytics.",
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
    "owner": "Priya",
    "description": "Loop in Aisha, the head of data, for the technical deep-dive.",
    "due_date": null,
    "priority": "medium"
  },
  {
    "owner": "Marcus",
    "description": "Schedule the technical deep-dive for next week.",
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

Thank you for taking the time to speak with us regarding Northwind Analytics' needs. We appreciate the opportunity to discuss how DataForge can assist in replacing your in-house reporting stack due to the performance issues you've been experiencing.

To recap, we understand that Northwind Analytics is considering DataForge as a potential solution, with a budget of approximately $60,000 per year. We will be providing a tailored proposal along with customer references from analytics firms. Additionally, we have scheduled a technical deep-dive for next week, which will include Aisha, your head of data.

Here are the agreed next steps:
1. Marcus will put together a tailored proposal and send it over by Wednesday.
2. Marcus will include two customer references from analytics firms in the proposal.
3. You will loop in Aisha for the technical deep-dive.
4. Marcus will aim to schedule the technical deep-dive for next week.

We look forward to moving ahead and appreciate your collaboration.

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
      "role": null,
      "organization": "Beacon Logistics",
      "is_primary_contact": true
    },
    {
      "name": "Elena",
      "role": "Support",
      "organization": "DataForge",
      "is_primary_contact": false
    }
  ],
  "summary": "Tom from Beacon Logistics reported sync errors on their nightly data import due to a connection timeout. Elena from DataForge Support identified the issue as being related to increased data volume and will increase the import timeout to 120 seconds. Tom will re-run the import after the change is applied and report back.",
  "key_points": [
    "Beacon Logistics is experiencing sync errors due to connection timeouts.",
    "The issue is likely caused by increased data volume from a new warehouse.",
    "DataForge Support will increase the import timeout to 120 seconds.",
    "Tom will re-run the import after the change is applied."
  ],
  "decisions": [],
  "action_items": [
    {
      "description": "Raise the import timeout on Beacon Logistics' account to 120 seconds.",
      "owner": "Elena",
      "due_date_raw": null,
      "due_date_iso": null,
      "source_quote": "I'll raise the import timeout on your account to 120 seconds, which should let the job finish."
    },
    {
      "description": "Open a ticket for the engineering team to optimize the import for larger datasets.",
      "owner": "Elena",
      "due_date_raw": null,
      "due_date_iso": null,
      "source_quote": "I'll also open a ticket for our engineering team to look at optimizing the import for larger datasets."
    },
    {
      "description": "Re-run the failed import after 8pm once the change is applied.",
      "owner": "Tom",
      "due_date_raw": "tonight after 8pm",
      "due_date_iso": null,
      "source_quote": "please re-run the failed import tonight after 8pm once I've applied the change, and let me know if it still fails."
    },
    {
      "description": "Report back to Elena tomorrow morning about the import status.",
      "owner": "Tom",
      "due_date_raw": "tomorrow morning",
      "due_date_iso": null,
      "source_quote": "I'll re-run it tonight and report back tomorrow morning."
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
  "outcome": "Elena will adjust the timeout and Tom will re-run the import to check for resolution.",
  "primary_contact_name": "Tom"
}
```

**Generated CRM entry:**

```json
{
  "contact": {
    "name": "Tom",
    "organization": "Beacon Logistics",
    "role": null,
    "email": null
  },
  "deal_stage": "follow_up",
  "sentiment": "positive",
  "notes": "Tom from Beacon Logistics reported sync errors due to connection timeouts, likely from increased data volume. Elena from DataForge Support will increase the import timeout to 120 seconds. Tom will re-run the import after the change and report back.",
  "next_step": "Tom will re-run the failed import after 8pm and report back tomorrow morning.",
  "open_action_count": 5
}
```

**Generated tasks:**

```json
[
  {
    "owner": "Elena",
    "description": "Raise the import timeout on Beacon Logistics' account to 120 seconds.",
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
    "owner": "Tom",
    "description": "Re-run the failed import after 8pm once the change is applied.",
    "due_date": null,
    "priority": "high"
  },
  {
    "owner": "Tom",
    "description": "Report back to Elena tomorrow morning about the import status.",
    "due_date": null,
    "priority": "high"
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

Thank you for taking the time to discuss the sync errors you are experiencing with your nightly data import. We appreciate your patience as we work to resolve this issue.

During our call, we identified that the sync errors are likely due to connection timeouts caused by increased data volume from your new warehouse. To address this, Elena from DataForge Support will increase the import timeout on your account to 120 seconds. After this change is applied, you will re-run the import tonight after 8 PM and report back on its status tomorrow morning.

Here are the agreed next steps:
1. Elena will raise the import timeout to 120 seconds.
2. Elena will open a ticket for the engineering team to optimize the import for larger datasets.
3. You will re-run the failed import tonight after 8 PM.
4. You will report back to Elena tomorrow morning about the import status.
5. Elena will follow up with you tomorrow to confirm everything is stable.

Please let me know if you have any questions or need further assistance.

Best regards,
[Your name]
```

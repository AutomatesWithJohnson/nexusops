"""Demo scenario: end-to-end walkthrough for the 3-minute video.

Run with: python scripts/demo_scenario.py

This script demonstrates the full NexusOps flow:
1. Customer sends an inquiry email
2. Classifier categorizes it
3. Quoter generates a quote
4. Responder drafts a reply
5. Scheduler sets a follow-up
6. Everything is logged to memory
"""

import asyncio
import json
import time
from datetime import datetime


# Demo scenario data
DEMO_EMAIL = {
    "from": "sarah.chen@acmecorp.com",
    "to": "sales@ourcompany.com",
    "subject": "Interested in your Enterprise Plan",
    "body": """Hi,

I'm Sarah Chen from Acme Corp. We're a growing SaaS company with 150 employees and we're looking to upgrade our infrastructure.

We're interested in your Enterprise Plan. Could you provide a quote for:
- 50 user licenses
- Premium support package
- Data migration assistance

We've been using your Basic Plan for 2 years and love the product. Ready to scale up!

Best regards,
Sarah Chen
VP of Engineering, Acme Corp
sarah.chen@acmecorp.com
+1-555-0123""",
}

DEMO_CUSTOMER = {
    "customer_id": "cust_acme_001",
    "name": "Acme Corp",
    "contact": "Sarah Chen",
    "email": "sarah.chen@acmecorp.com",
    "tier": "gold",
    "history": [
        {"date": "2024-03-15", "type": "signup", "note": "Signed up for Basic Plan"},
        {"date": "2024-09-22", "type": "support", "note": "API rate limit increase request, resolved"},
        {"date": "2025-01-10", "type": "upsell", "note": "Discussed Pro Plan, declined at the time"},
        {"date": "2025-08-05", "type": "support", "note": "Data export feature request"},
        {"date": "2026-02-14", "type": "renewal", "note": "Annual renewal, 50 seats on Basic"},
    ],
}


async def demo_step(step_num: int, title: str, agent: str, model: str):
    """Print a demo step with visual formatting."""
    print(f"\n{'='*70}")
    print(f"  STEP {step_num}: {title}")
    print(f"  Agent: {agent} | Model: {model}")
    print(f"{'='*70}")
    await asyncio.sleep(1)  # Simulate processing time


async def run_demo():
    """Run the full demo scenario."""

    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║          NexusOps - Live Demo Scenario                   ║
    ║          Autonomous Business Operations Agent            ║
    ║                                                          ║
    ║          Track 4: Autopilot Agent                        ║
    ║          Global AI Hackathon 2026                        ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Scenario: Inbound sales inquiry from existing customer")

    # Step 1: Receive email
    await demo_step(1, "INBOUND EMAIL RECEIVED", "System", "N/A")
    print(f"\n  From: {DEMO_EMAIL['from']}")
    print(f"  Subject: {DEMO_EMAIL['subject']}")
    print(f"  Body preview: {DEMO_EMAIL['body'][:100]}...")

    # Step 2: Classify
    await demo_step(2, "MESSAGE CLASSIFICATION", "Classifier Agent", "qwen-plus")
    print("""
  Classification Result:
  ┌────────────────────────────────────────────────────────┐
  │ Category: sales_inquiry                                │
  │ Confidence: 0.97                                       │
  │ Priority: HIGH (existing customer, upgrade intent)     │
  │                                                        │
  │ Reasoning: Customer is requesting a quote for upgrade  │
  │ from Basic to Enterprise Plan. Clear buying signals    │
  │ with specific requirements listed.                     │
  └────────────────────────────────────────────────────────┘
    """)

    # Step 3: Memory lookup
    await demo_step(3, "MEMORY RETRIEVAL", "Memory Layer", "text-embedding-v3")
    print(f"\n  Customer: {DEMO_CUSTOMER['name']} ({DEMO_CUSTOMER['customer_id']})")
    print(f"  Tier: {DEMO_CUSTOMER['tier'].upper()}")
    print(f"  Total interactions: {len(DEMO_CUSTOMER['history'])}")
    print(f"\n  Relevant memories found:")
    for h in DEMO_CUSTOMER['history']:
        print(f"    [{h['date']}] {h['type']}: {h['note']}")
    print(f"\n  Key insight: Previous upsell attempt in Jan 2025 was declined.")
    print(f"  Customer now ready to upgrade after 18 months of Basic usage.")

    # Step 4: Generate quote
    await demo_step(4, "QUOTE GENERATION", "Quoter Agent", "qwen3-coder-next")
    quote = {
        "quote_id": "QT-2026-00847",
        "customer": "Acme Corp",
        "items": [
            {"product": "Enterprise License (50 users)", "qty": 1, "unit_price": 25000, "total": 25000},
            {"product": "Premium Support (annual)", "qty": 1, "unit_price": 8000, "total": 8000},
            {"product": "Data Migration Service", "qty": 1, "unit_price": 5000, "total": 5000},
        ],
        "subtotal": 38000,
        "gold_discount": "-10%",
        "loyalty_discount": "-5%",
        "total": 32300,
        "validity": "30 days",
        "needs_approval": True,
    }
    print(f"\n  Quote: {quote['quote_id']}")
    print(f"  Items:")
    for item in quote['items']:
        print(f"    - {item['product']}: ${item['total']:,}")
    print(f"  Subtotal: ${quote['subtotal']:,}")
    print(f"  Gold Discount (10%): -${3800:,}")
    print(f"  Loyalty Discount (5%): -${1900:,}")
    print(f"  TOTAL: ${quote['total']:,}")
    print(f"  Needs Manager Approval: YES (quote > $10,000)")

    # Step 5: Draft response
    await demo_step(5, "RESPONSE DRAFTING", "Responder Agent", "qwen3-coder-next")
    print("""
  Draft Response:
  ┌────────────────────────────────────────────────────────┐
  │ Subject: Re: Interested in your Enterprise Plan        │
  │                                                        │
  │ Hi Sarah,                                            │
  │                                                        │
  │ Great to hear from you again! We truly value Acme     │
  │ Corp as a long-standing customer and are excited      │
  │ about supporting your growth to 150 employees.        │
  │                                                        │
  │ I have put together a custom Enterprise quote for     │
  │ your team:                                            │
  │                                                        │
  │ - 50 Enterprise licenses: $25,000/year               │
  │ - Premium Support: $8,000/year                       │
  │ - Data Migration: $5,000 (one-time)                  │
  │                                                        │
  │ As a valued Gold partner with 2 years of loyalty,    │
  │ I am applying a 15% combined discount bringing the   │
  │ total to $32,300.                                     │
  │                                                        │
  │ I have also flagged the data migration for priority   │
  │ scheduling. Our team can begin as early as next week. │
  │                                                        │
  │ Would you be available for a 30-minute call to       │
  │ finalize the details? I have a few time slots:       │
  │ - Tuesday 10:00 AM EST                               │
  │ - Wednesday 2:00 PM EST                              │
  │ - Thursday 11:00 AM EST                              │
  │                                                        │
  │ Best regards,                                        │
  │ NexusOps on behalf of Sales Team                     │
  └────────────────────────────────────────────────────────┘
  Confidence: 0.89
    """)

    # Step 6: Schedule follow-up
    await demo_step(6, "FOLLOW-UP SCHEDULING", "Scheduler Agent", "qwen-plus")
    print("""
  Actions Taken:
    [x] Follow-up reminder set for 3 business days (if no reply)
    [x] Calendar hold: Tuesday/Wednesday/Thursday slots reserved
    [x] Customer timezone detected: EST (UTC-5)
    [x] Email sent to sarah.chen@acmecorp.com
    [x] Quote PDF attached: QT-2026-00847.pdf
    """)

    # Step 7: Escalation
    await demo_step(7, "MANAGER APPROVAL REQUESTED", "Escalator Agent", "qwen3-coder-next")
    print("""
  Escalation Package:
  ┌────────────────────────────────────────────────────────┐
  │ Customer: Acme Corp (Gold Tier)                       │
  │ Quote: QT-2026-00847 ($32,300)                       │
  │ Reason: Quote exceeds $10,000 auto-approval limit     │
  │                                                        │
  │ Recommendation: APPROVE                              │
  │ - Customer has 2-year track record                   │
  │ - Upgrading from Basic (proven product fit)           │
  │ - 15% discount within policy limits                  │
  │ - High probability of close (specific requirements)  │
  │                                                        │
  │ Action Required: Manager approval to send quote       │
  └────────────────────────────────────────────────────────┘
    """)

    # Step 8: Memory update
    await demo_step(8, "MEMORY UPDATED", "Memory Layer", "Redis + PostgreSQL")
    print("""
  New Memories Stored:
    [1] Interaction: "Sarah Chen requested Enterprise upgrade quote"
        Category: interaction | Customer: cust_acme_001
    
    [2] Fact: "Acme Corp growing to 150 employees"
        Category: fact | Customer: cust_acme_001
    
    [3] Preference: "Acme Corp prefers email communication"
        Category: preference | Customer: cust_acme_001
    
    [4] Interaction: "Quote QT-2026-00847 sent, $32,300 with 15% discount"
        Category: interaction | Customer: cust_acme_001
    """)

    # Summary
    print(f"\n{'='*70}")
    print(f"  DEMO COMPLETE")
    print(f"{'='*70}")
    print(f"""
  Summary:
    Agents Used:      5 (Classifier, Quoter, Responder, Scheduler, Escalator)
    Models Used:      3 (qwen-plus, qwen3-coder-next, text-embedding-v3)
    Tools Called:     7 (search_memory, search_crm, create_quote,
                        schedule_meeting, send_email, notify_human, store_memory)
    Memories Stored:  4
    Latency:          ~8 seconds total
    Human Actions:    1 (manager approval pending)
    
  Infrastructure:
    Compute:          Alibaba Cloud ECS
    Database:         RDS PostgreSQL + pgvector
    Cache:            Tair/Redis
    Storage:          OSS
    AI:               Model Studio (Qwen)
    """)


if __name__ == "__main__":
    asyncio.run(run_demo())

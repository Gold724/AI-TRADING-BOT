# TRAE Phase 8: Language Interface & Self-Reflection

## Goals

- Enable TRAE to describe its current state and reasoning in natural language
- Integrate a LLM-based interface for querying performance, trade logic, and insights
- Implement weekly self-evaluation prompts ("What did I do well?", "What failed?", "Why?")
- Prepare system for governance communication, transparency, and user-guided reflection

## System Instructions

### Sentinel Decider Activation

```
trigger: sentinel_decider.py
mode: reflective
parameters:
  language_interface: true
  enable_self_questions: true
  user_prompt_sync: optional
```

### Language Reflection Engine (LRE)

- Generate weekly reflections using trade logs and metrics:
  - What trades performed best and why?
  - What risk decisions failed or succeeded?
  - What patterns or anomalies were detected?
  - What phase logic needs refinement?

- Store in: `/logs/self_reflection/weekly_log_{timestamp}.md`

### User Language Interface

- Accept user queries such as:
  - "Why did you skip trades today?"
  - "What's your win rate this week?"
  - "What phase prompt are you following?"
- Respond using internal logs, metrics, and prompt data
- Interface can be CLI, Telegram bot, or Slack responder

### Data Sources

- `/logs/strategy_evolution.log`
- `/logs/ai_feedback.json`
- `/logs/liquidity_routing.log`
- `/logs/self_reflection/`
- `/data/daily_metrics.json`
- `prompts_history.json`

## Success Metrics

- Weekly logs generated without interruption
- At least 5 accurate natural-language answers per week
- Self-diagnoses at least 2 underperforming strategies weekly
- User can query any phase, metric, or failure via natural language
- Governance channel receives a summary every 7 days

## Monitoring & Logging

- `/logs/self_reflection/weekly_log_{timestamp}.md`
- `/logs/user_queries.json`
- Slack/Telegram interface channel for live Q&A

## Completion Criteria

- 3+ weeks of consistent self-reflection logs
- At least 1 successful external query per day for 7 consecutive days
- System accurately reports its current phase and prompt metadata
- Governance entity can request and receive explanations with >90% relevance
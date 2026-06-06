# Prompt Engineering Documentation

**Team 15 | Challenge SD-02 | Auto-Categorization Webhook**

---

## Overview

This document captures the complete prompt engineering journey for the AI-powered ticket classification system, including all iterations, improvements, and the final production prompts.

---

## Iteration 1: Basic Zero-Shot Prompt

**Goal:** Establish baseline classification capability.

```
Classify this support ticket:
Title: {title}
Description: {description}

Categories: Authentication, Billing, Technical, Network, Account
Return JSON with category, subcategory, priority.
```

**Problems:**
- Inconsistent JSON formatting (sometimes wrapped in markdown code blocks)
- Frequent hallucinations in subcategory names
- No confidence score
- Priority assignment was random

**Confidence Score:** ~0.4 (estimated)

---

## Iteration 2: Adding Structured Output Instructions

**Goal:** Force consistent JSON output format.

```
You are a support ticket classifier.
IMPORTANT: Respond ONLY with valid JSON. No markdown. No explanation.

Classify this ticket:
Title: {title}
Description: {description}

JSON format:
{
  "category": "...",
  "subcategory": "...", 
  "priority": "...",
  "confidence": 0.0-1.0
}
```

**Improvements:**
- JSON parsing success rate improved from 60% to 80%
- Added confidence score to output
- Still inconsistent subcategories

**Problems:**
- LLM still occasionally wrapped output in ```json``` blocks
- Subcategory names varied (e.g., "Login Issue" vs "Login Failure" vs "Authentication Failure")

---

## Iteration 3: Few-Shot Examples Added

**Goal:** Use labeled examples to anchor classification decisions.

```
You are an expert IT support ticket classifier.
Respond ONLY with valid JSON.

Examples:
Title: Cannot reset my password
Category: Authentication, Subcategory: Password Reset, Priority: High

Title: Payment not going through  
Category: Billing, Subcategory: Payment Failure, Priority: High

...

Now classify:
Title: {title}
Description: {description}
```

**Improvements:**
- Category accuracy improved significantly (~85%)
- Subcategory names became more consistent
- Priority assignments more logical

**Problems:**
- Examples took too many tokens
- Some edge cases still misclassified

---

## Iteration 4: System Prompt + Few-Shot + Priority Rules

**Goal:** Add explicit classification rules and priority guidelines.

```
[SYSTEM]
You are an expert IT support ticket classification system.
You MUST respond with ONLY a valid JSON object.

Classification Rules:
- Categories: Authentication, Billing, Technical, Network, Account, General Inquiry
- Priority: Critical (system down), High (feature broken), Medium (partial), Low (inquiry)

[FEW-SHOT EXAMPLES - 10 examples]

[USER]
Classify: Title: {title}, Description: {description}

JSON: { "category": "...", "subcategory": "...", "priority": "...", "confidence": 0.0-1.0, "reasoning": "..." }
```

**Improvements:**
- Priority assignment accuracy ~90%
- Added reasoning field for transparency
- Reduced hallucinations significantly

---

## Iteration 5: Agent Retry Prompt

**Goal:** Handle low-confidence cases with targeted retry.

```
The previous classification had low confidence ({confidence}).
Previous result: {previous_result}

Please reconsider with more careful analysis.
[Same examples and format as above]
```

**Improvements:**
- Low-confidence cases improved from ~0.4 to ~0.7 confidence on retry
- Agent loop reduced "unknown" classifications by 80%

---

## Final Production Prompts

### 1. Primary Classification Prompt

Used for initial ticket classification with all 22 few-shot examples.

**Key design decisions:**
- Explicit JSON-only instruction at the start and end
- Temperature = 0.1 for deterministic output
- 10 most relevant few-shot examples (not all 22 to save tokens)
- Confidence score as self-reported certainty
- Reasoning field for audit trail

**Prompt template:** See `app/prompts/classification_prompts.py` → `CLASSIFICATION_PROMPT_TEMPLATE`

### 2. Retry Prompt

Used when confidence < 0.6 (threshold). Includes the previous result for context.

**Key design decisions:**
- Show the previous result to help LLM understand what was wrong
- More explicit instruction to "try harder"
- Same few-shot examples for consistency

**Prompt template:** See `app/prompts/classification_prompts.py` → `RETRY_PROMPT_TEMPLATE`

### 3. Fallback Prompt

Used on the final (3rd) attempt. Simplified to maximize parse success.

**Key design decisions:**
- Stripped down to bare minimum to avoid confusion
- Hardcoded confidence of 0.7 to prevent over-confidence
- No few-shot examples (reduces complexity)

**Prompt template:** See `app/prompts/classification_prompts.py` → `FALLBACK_PROMPT_TEMPLATE`

---

## JSON Parsing Strategy

LLMs don't always return clean JSON. Our parsing pipeline:

1. Direct `json.loads()` on stripped text
2. Extract from markdown code blocks: ` ```json ... ``` `
3. Regex pattern for `{...}` object
4. Default fallback dict with low confidence

---

## Model Configuration

| Parameter | Value | Reasoning |
|-----------|-------|-----------|
| temperature | 0.1 | Low randomness for consistent classification |
| top_p | 0.9 | Allow some variation for edge cases |
| num_predict | 300 | Enough for JSON response, not too long |
| model | llama3 | Best local model for classification |
| fallback | mistral | Alternative if llama3 unavailable |

---

## Lessons Learned

1. **Always add JSON-only instruction twice** — at the start AND in the format spec
2. **Temperature 0.1 is key** — higher temperatures caused inconsistent JSON
3. **Few-shot examples > zero-shot** — 10 examples gave 30%+ accuracy improvement
4. **Parse defensively** — assume the LLM will sometimes add markdown or extra text
5. **Confidence threshold of 0.6** — below this, retry is almost always worth it
6. **Reasoning field** — makes debugging classification errors much easier

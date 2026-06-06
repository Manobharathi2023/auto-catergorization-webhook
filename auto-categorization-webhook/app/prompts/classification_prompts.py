"""
Prompt templates for ticket classification using few-shot prompting.
"""

SYSTEM_PROMPT = """You are an expert IT support ticket classification system. 
Your task is to analyze support tickets and classify them accurately.

You MUST respond with ONLY a valid JSON object. No explanation, no markdown, no code blocks.
Just the raw JSON object.

Classification Rules:
- Categories: Authentication, Billing, Technical, Network, Account, General Inquiry
- Subcategories depend on category (examples below)
- Priority levels: Critical, High, Medium, Low
- Confidence: 0.0 to 1.0 (your certainty in the classification)

Priority Guidelines:
- Critical: System down, security breach, data loss
- High: Feature completely broken, payment issues, login failures
- Medium: Feature partially working, slow performance
- Low: How-to questions, minor UI issues, general requests
"""

FEW_SHOT_EXAMPLES_TEMPLATE = """
Here are example classifications to guide you:

{examples}
"""

CLASSIFICATION_PROMPT_TEMPLATE = """
{system_prompt}

{few_shot_examples}

Now classify this ticket:
Title: {title}
Description: {description}

Respond with ONLY this JSON structure:
{{
  "category": "<one of: Authentication, Billing, Technical, Network, Account, General Inquiry>",
  "subcategory": "<specific subcategory>",
  "priority": "<one of: Critical, High, Medium, Low>",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<brief one-line explanation>"
}}
"""

RETRY_PROMPT_TEMPLATE = """
{system_prompt}

The previous classification had low confidence. Please try again with more careful analysis.

{few_shot_examples}

Ticket to classify:
Title: {title}
Description: {description}

Previous attempt result: {previous_result}

Please reconsider and provide a more confident classification.
Respond with ONLY this JSON structure:
{{
  "category": "<one of: Authentication, Billing, Technical, Network, Account, General Inquiry>",
  "subcategory": "<specific subcategory>",
  "priority": "<one of: Critical, High, Medium, Low>",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<brief one-line explanation>"
}}
"""

FALLBACK_PROMPT_TEMPLATE = """
You are a support ticket classifier. Classify the following ticket.

Title: {title}
Description: {description}

Choose ONE category from: Authentication, Billing, Technical, Network, Account, General Inquiry
Choose ONE priority from: Critical, High, Medium, Low

Respond with ONLY valid JSON, no other text:
{{
  "category": "...",
  "subcategory": "...",
  "priority": "...",
  "confidence": 0.7,
  "reasoning": "fallback classification"
}}
"""


def build_few_shot_examples(examples: list) -> str:
    """Build formatted few-shot examples string from list of examples."""
    formatted = []
    for i, ex in enumerate(examples[:10], 1):  # Use first 10 examples
        formatted.append(
            f"Example {i}:\n"
            f"  Title: {ex['title']}\n"
            f"  Description: {ex.get('description', 'N/A')}\n"
            f"  -> Category: {ex['category']}, Subcategory: {ex['subcategory']}, Priority: {ex['priority']}"
        )
    return "\n\n".join(formatted)


def build_classification_prompt(title: str, description: str, examples: list) -> str:
    """Build the full classification prompt with few-shot examples."""
    few_shot_section = FEW_SHOT_EXAMPLES_TEMPLATE.format(
        examples=build_few_shot_examples(examples)
    )
    return CLASSIFICATION_PROMPT_TEMPLATE.format(
        system_prompt=SYSTEM_PROMPT,
        few_shot_examples=few_shot_section,
        title=title,
        description=description or "No description provided"
    )


def build_retry_prompt(title: str, description: str, examples: list, previous_result: dict) -> str:
    """Build retry prompt for low-confidence classifications."""
    few_shot_section = FEW_SHOT_EXAMPLES_TEMPLATE.format(
        examples=build_few_shot_examples(examples)
    )
    return RETRY_PROMPT_TEMPLATE.format(
        system_prompt=SYSTEM_PROMPT,
        few_shot_examples=few_shot_section,
        title=title,
        description=description or "No description provided",
        previous_result=str(previous_result)
    )


def build_fallback_prompt(title: str, description: str) -> str:
    """Build simplified fallback prompt."""
    return FALLBACK_PROMPT_TEMPLATE.format(
        title=title,
        description=description or "No description provided"
    )

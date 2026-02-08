# Multi-Agent Patterns

## Pattern Overview

| Pattern | Use Case | Control | Complexity |
|---------|----------|---------|------------|
| **Single Agent** | Simple Q&A, single task | N/A | Low |
| **Handoffs** | Specialized routing | Decentralized | Medium |
| **Manager** | Orchestrated workflows | Centralized | Medium-High |
| **Parallel** | Independent tasks | Code-based | Medium |
| **Pipeline** | Sequential processing | Code-based | Medium |
| **Evaluation Loop** | Quality iteration | Code-based | High |

## Single Agent

Simple agent for straightforward tasks.

```python
from agents import Agent, Runner

agent = Agent(
    name="Assistant",
    instructions="""You are a helpful assistant.
    - Answer questions clearly and concisely
    - Ask for clarification if needed
    - Be friendly and professional""",
    model="gpt-4.1"
)

result = Runner.run_sync(agent, "What is machine learning?")
print(result.final_output)
```

## Handoffs Pattern (Decentralized)

Agents transfer control to specialists. Best for customer service, support routing.

### Basic Handoffs

```python
from agents import Agent, Runner

# Specialist agents
billing_agent = Agent(
    name="Billing",
    handoff_description="Handles billing, payments, and invoices",
    instructions="""You are a billing specialist.
    - Help with payment issues
    - Explain invoices
    - Process refund requests"""
)

technical_agent = Agent(
    name="Technical",
    handoff_description="Handles technical issues and troubleshooting",
    instructions="""You are a technical support specialist.
    - Debug technical issues
    - Provide step-by-step solutions
    - Escalate complex issues"""
)

# Triage agent routes to specialists
triage_agent = Agent(
    name="Triage",
    instructions="""You are the first point of contact.
    - Understand the customer's issue
    - Route to the appropriate specialist:
      - Billing for payment/invoice issues
      - Technical for product/technical issues
    - Be friendly and efficient""",
    handoffs=[billing_agent, technical_agent]
)

result = await Runner.run(triage_agent, "I can't log into my account")
print(f"Handled by: {result.last_agent.name}")
print(result.final_output)
```

### Handoffs with Input Data

Pass structured data during handoffs.

```python
from pydantic import BaseModel
from agents import Agent, handoff, RunContextWrapper

class EscalationData(BaseModel):
    reason: str
    priority: str
    customer_id: str

async def on_escalation(ctx: RunContextWrapper, data: EscalationData):
    print(f"Escalation: {data.reason} (Priority: {data.priority})")
    # Log to ticket system, notify manager, etc.

escalation_agent = Agent(
    name="Escalation",
    instructions="Handle escalated issues with care."
)

support_agent = Agent(
    name="Support",
    instructions="Help customers. Escalate if you cannot resolve.",
    handoffs=[
        handoff(
            agent=escalation_agent,
            on_handoff=on_escalation,
            input_type=EscalationData,
            tool_description_override="Escalate to senior support with reason and priority"
        )
    ]
)
```

### Handoffs with Input Filters

Control what context the next agent sees.

```python
from agents import Agent, handoff
from agents.extensions import handoff_filters

# Remove tool call history
clean_handoff = handoff(
    agent=specialist,
    input_filter=handoff_filters.remove_all_tools
)

# Custom filter
def summarize_history(input_data):
    # Summarize long conversations
    if len(input_data.history) > 20:
        summary = summarize(input_data.history)
        return f"<SUMMARY>{summary}</SUMMARY>"
    return input_data

filtered_handoff = handoff(
    agent=specialist,
    input_filter=summarize_history
)
```

### Recommended Handoff Prompts

```python
from agents import Agent
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

billing_agent = Agent(
    name="Billing",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}

    You are a billing specialist for Acme Corp.
    - Handle payment and invoice questions
    - Process refunds up to $100
    - Escalate larger refunds to management"""
)
```

## Manager Pattern (Centralized)

Central orchestrator controls sub-agents as tools.

```python
from agents import Agent, Runner

# Specialist agents (used as tools, not handoffs)
researcher = Agent(
    name="Researcher",
    instructions="Research topics thoroughly and return factual summaries."
)

writer = Agent(
    name="Writer",
    instructions="Write clear, engaging content based on provided information."
)

critic = Agent(
    name="Critic",
    instructions="Review content for accuracy, clarity, and engagement. Suggest improvements."
)

# Manager orchestrates specialists
manager = Agent(
    name="ContentManager",
    instructions="""You are a content creation manager.

    For content requests:
    1. Use researcher to gather information
    2. Use writer to create initial draft
    3. Use critic to review
    4. Iterate if needed
    5. Return final polished content""",
    tools=[
        researcher.as_tool(
            tool_name="research",
            tool_description="Research a topic and return key facts"
        ),
        writer.as_tool(
            tool_name="write",
            tool_description="Write content based on research"
        ),
        critic.as_tool(
            tool_name="review",
            tool_description="Review and critique content"
        )
    ]
)

result = await Runner.run(manager, "Write a blog post about AI agents")
```

## Parallel Pattern

Execute independent tasks concurrently.

```python
import asyncio
from agents import Agent, Runner

# Create specialized agents
sentiment_agent = Agent(name="Sentiment", instructions="Analyze sentiment.")
summary_agent = Agent(name="Summary", instructions="Summarize text.")
keywords_agent = Agent(name="Keywords", instructions="Extract keywords.")

async def analyze_text(text: str):
    # Run all analyses in parallel
    results = await asyncio.gather(
        Runner.run(sentiment_agent, text),
        Runner.run(summary_agent, text),
        Runner.run(keywords_agent, text)
    )

    return {
        "sentiment": results[0].final_output,
        "summary": results[1].final_output,
        "keywords": results[2].final_output
    }

analysis = await analyze_text("Long article text here...")
```

### Parallel with Shared Context

```python
from dataclasses import dataclass

@dataclass
class AnalysisContext:
    document_id: str
    user_id: str

async def parallel_analysis(text: str, ctx: AnalysisContext):
    results = await asyncio.gather(
        Runner.run(agent1, text, context=ctx),
        Runner.run(agent2, text, context=ctx),
        Runner.run(agent3, text, context=ctx)
    )
    return results
```

## Pipeline Pattern

Sequential processing through stages.

```python
from agents import Agent, Runner

# Pipeline stages
extractor = Agent(
    name="Extractor",
    instructions="Extract key information from raw text."
)

transformer = Agent(
    name="Transformer",
    instructions="Transform extracted data into structured format."
)

validator = Agent(
    name="Validator",
    instructions="Validate data for completeness and accuracy."
)

async def process_document(document: str):
    # Stage 1: Extract
    extraction = await Runner.run(extractor, document)

    # Stage 2: Transform
    transformation = await Runner.run(
        transformer,
        f"Transform this extracted data:\n{extraction.final_output}"
    )

    # Stage 3: Validate
    validation = await Runner.run(
        validator,
        f"Validate this data:\n{transformation.final_output}"
    )

    return validation.final_output
```

## Evaluation Loop Pattern

Iterate until quality threshold met.

```python
from pydantic import BaseModel
from agents import Agent, Runner

class Evaluation(BaseModel):
    score: int  # 1-10
    feedback: str
    approved: bool

generator = Agent(
    name="Generator",
    instructions="Generate high-quality content based on requirements."
)

evaluator = Agent(
    name="Evaluator",
    instructions="""Evaluate content quality on a 1-10 scale.
    Score 8+ means approved. Provide specific feedback for improvement.""",
    output_type=Evaluation
)

async def generate_with_quality(prompt: str, max_iterations: int = 3):
    content = prompt

    for i in range(max_iterations):
        # Generate
        generation = await Runner.run(generator, content)

        # Evaluate
        evaluation = await Runner.run(
            evaluator,
            f"Evaluate this content:\n{generation.final_output}"
        )

        if evaluation.final_output.approved:
            return generation.final_output

        # Iterate with feedback
        content = f"""Previous attempt:
{generation.final_output}

Feedback: {evaluation.final_output.feedback}

Please improve the content based on this feedback."""

    return generation.final_output  # Return best effort
```

## Deterministic Workflow Pattern

Code-controlled flow with structured outputs.

```python
from pydantic import BaseModel
from agents import Agent, Runner

class Classification(BaseModel):
    category: str
    confidence: float

class Response(BaseModel):
    answer: str
    sources: list[str]

classifier = Agent(
    name="Classifier",
    instructions="Classify the query into: technical, billing, general",
    output_type=Classification
)

technical_agent = Agent(name="Technical", output_type=Response)
billing_agent = Agent(name="Billing", output_type=Response)
general_agent = Agent(name="General", output_type=Response)

async def handle_query(query: str):
    # Step 1: Classify
    classification = await Runner.run(classifier, query)
    category = classification.final_output.category

    # Step 2: Route deterministically
    if category == "technical":
        result = await Runner.run(technical_agent, query)
    elif category == "billing":
        result = await Runner.run(billing_agent, query)
    else:
        result = await Runner.run(general_agent, query)

    return result.final_output
```

## Human-in-the-Loop Pattern

Pause for human approval.

```python
from agents import Agent, Runner, function_tool

@function_tool
async def request_human_approval(action: str, reason: str) -> str:
    """Request human approval for an action.

    Args:
        action: The action requiring approval.
        reason: Why approval is needed.
    """
    # In production: send to approval queue, wait for response
    print(f"APPROVAL NEEDED: {action}")
    print(f"Reason: {reason}")

    # Simulate approval (in production, wait for actual approval)
    approved = input("Approve? (y/n): ").lower() == 'y'

    if approved:
        return "Action approved. Proceed."
    else:
        return "Action denied. Do not proceed."

agent = Agent(
    name="ApprovalBot",
    instructions="""Before taking significant actions (refunds > $50,
    account changes, data deletion), request human approval first.""",
    tools=[request_human_approval]
)
```

## Pattern Selection Guide

| Scenario | Recommended Pattern |
|----------|---------------------|
| Simple chatbot | Single Agent |
| Customer support with specialists | Handoffs |
| Complex research/analysis | Manager |
| Independent subtasks | Parallel |
| Document processing | Pipeline |
| Content generation with quality | Evaluation Loop |
| Strict business logic | Deterministic Workflow |
| Sensitive operations | Human-in-the-Loop |

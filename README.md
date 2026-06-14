# Task Learn LLM Client

Python CLI and lightweight library clients for working with LLM providers. The
current CLI uses OpenRouter and can generate content from a topic plus requested
content type.

## Setup

Install project dependencies:

```bash
uv sync
```

Create `.env` in the project root or export the variables in your shell:

```bash
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=deepseek/deepseek-v4-flash
```

`OPENROUTER_MODEL` is optional. If it is not set, the default model is
`deepseek/deepseek-v4-flash`.

## Usage

Check OpenRouter configuration and model availability:

```bash
uv run python main.py status
```

Generate content by topic and content type:

```bash
uv run python main.py ask --topic "Python unit tests" --content-type "tutorial"
```

Add a system prompt when you need extra style or behavior constraints:

```bash
uv run python main.py ask \
  --topic "OpenRouter API clients" \
  --content-type "implementation checklist" \
  --system "Be concise and practical"
```

The `ask` command builds a prompt from `--topic` and `--content-type`, then sends
it to OpenRouter.

## Prompt Templates

Reusable prompt documents:

- [Few-shot support ticket classification template](docs/prompts/few-shot-support-ticket-classification-template.md)
- [Marketing AI Prompt Library](docs/prompts/marketing-ai-prompt-library/README.md)

## Tests

Run the test suite:

```bash
uv run pytest
```

The tests mock provider HTTP calls and do not read the real `.env` file.

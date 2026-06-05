# Contributing Guide

Thank you for contributing to AI Company Chatbot.

We welcome:

- Bug fixes
- New features
- Performance improvements
- Documentation updates
- Testing improvements

---

## Development Setup

### Fork Repository

Click Fork on GitHub.

Clone your fork:

```bash
git clone https://github.com/YOUR_USERNAME/ai-company-chatbot.git
```

---

### Create Branch

```bash
git checkout -b feature/my-feature
```

Examples:

```bash
feature/langsmith-support

feature/redis-memory

fix/upload-bug
```

---

## Install Dependencies

```bash
uv venv

uv pip install -r requirements.txt
```

---

## Environment Variables

Create:

```env
GROQ_API_KEY=your_key
```

Never commit:

- .env
- API Keys
- Uploaded documents
- Vector databases

---

## Coding Standards

### Python

Follow:

- PEP8
- Meaningful variable names
- Type hints where possible

Example:

```python
def similarity_search(
    query: str,
    k: int = 5
):
    ...
```

---

## Commit Messages

Good examples:

```text
feat: add redis memory

fix: resolve duplicate embeddings

docs: update README

refactor: simplify retrieval node
```

Avoid:

```text
changes

updated stuff

fixes
```

---

## Pull Request Process

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push branch
5. Open Pull Request

Include:

- What changed
- Why it changed
- Screenshots (if UI related)
- Testing performed

---

## Areas Needing Contributions

### RAG Improvements

- Rerankers
- Context compression
- Parent-child retrieval
- Multi-query retrieval

### LangGraph

- Agentic workflows
- Reflection nodes
- Planning nodes

### Storage

- Redis memory
- PostgreSQL metadata
- Persistent conversation history

### DevOps

- Docker
- Docker Compose
- Kubernetes
- CI/CD

### Monitoring

- LangSmith
- OpenTelemetry
- Prometheus
- Grafana

---

## Reporting Bugs

Open an Issue with:

### Description

What happened?

### Expected Behavior

What should happen?

### Steps to Reproduce

1. Upload file
2. Ask question
3. Observe issue

### Logs

Include relevant stack traces.

---

## Code of Conduct

Be respectful.

Constructive feedback is encouraged.

Harassment, discrimination, or abusive behavior will not be tolerated.

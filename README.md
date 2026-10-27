# Agent-Optimizer-RFT

Shows that a small model (MAI-Code-1.1-Flash), improved with Foundry Agent
Optimizer and agentic reinforcement fine-tuning, can match or beat larger
models on a multi-step shopping-agent task at a fraction of the cost.

Built from the reusable parts of the ShoppingBench hill-climbing project:
the `mai-agent-hillclimb` skill (`.github/skills`), the tool API and graders
(`src`), RFT preparation (`rft`), evaluation (`evals`) and optimizer runner
(`optimize`). Data: ShoppingBench (Apache-2.0), expanded with synthesized cases
in `data/full-catalog`.

See `azure/README.md` for infrastructure.

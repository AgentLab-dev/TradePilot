# Command: FQC-ARR / run ARR ticket

Drive an EDAEM Jira ticket through the 10-role DAG:

1. jira-intake
2. requirements-analyzer
3. code-data-validator
4. clarifier *(gate)*
5. implementer
6. test-runner
7. pr-author *(gate)*
8. ci-monitor
9. cd-monitor
10. qa-handoff *(gate)*

Supervisor skill: `agents/arr-analyst/skills/fqc-arr-supervisor/SKILL.md`
Workspace commands copied from eda-dbt-em `.cursor/commands/`.

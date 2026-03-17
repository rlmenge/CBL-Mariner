---
description: "Diagnose a LISA test failure using test name, run directory, or general query"
agent: agent
argument-hint: Provide a LISA run directory, test name, or general query as well as ssh access to the test VM if needed for diagnosis.
---

# Diagnose: `${input:target:test name, run directory, or query}`

Diagnose the LISA test failure described by the user's query, or follow their other instructions.

You run one command at a time on the given vm using the key /home/rachel/keys/id_rsa_mariner and the address azureuser@<IP_ADDRESS>. Use this access to investigate the test failure as needed, but avoid unnecessary commands. Always explain your reasoning and next steps to the user.

---
title: Calculate Mixing Ratios
keywords: [ratio, concentration, conservation, calculation]
---

# Calculate Mixing Ratios

## Definition
Calculate integer ratios of available samples based on available sample concentrations and target concentrations.

## Input
- available_samples: dict, sample name → concentration value
- target_concentrations: dict, component name → target concentration value

## Output
- "feasible": true/false
- "ratio": "specific ratio result (e.g., A:B:C = 3:2:1)"

## Principles
Based on concentration conservation:
Total amount of component in all samples = Total amount of component in final mixture

V1×C1 + V2×C2 + ... = V_total × C_target

Calculation requirements:
1. Use mass conservation law: Σ(Ci × Vi) = C_target × V_total
2. For single component, use C1V1 + C2V2 = C_target(V1+V2)
3. For multiple components, establish linear equation system to solve
4. Convert results to simplest integer ratios
5. Verify results
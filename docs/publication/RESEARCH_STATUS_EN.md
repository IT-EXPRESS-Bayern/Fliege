# Fliege: research status

**27 September 2026 · reconstruction in progress · research prototype**

Fliege links published Drosophila connectomes to auditable cell annotations and explicitly simplified body models. Its intended destination is a biologically grounded, closed sensorimotor system. A complete autonomous animal or freely flying connectome-driven fly has not been demonstrated.

**GPT-6 SOL and GPT-6 ASTRA are major research drivers in this project**, assisting literature review, data processing, hypothesis development, implementation and analysis. Original biological observations belong to the credited research teams. AI assistance is not independent scientific validation. Human maintainers remain responsible for publication and interpretation.

## Current evidence

- **139,255 FAFB v783 roots** are catalogued without duplicate IDs. Display names exist for 138,765; 116,943 lack a curated functional annotation in the combined catalogue. A name is not a validated behavioral role.
- The Shiu v783 connectivity tables match the original aggregate graph's **15,091,983 directed pairs** and their synapse counts. Dynamic equations and synaptic signs remain model assumptions. Original connectivity was not altered.
- **42 neural trials and four JO diagnostics** were completed. Across six reference runs, 7,048 cells were active. The expected JO-C/E versus JO-F selectivity was not reproduced, including controlled diagnostic conditions.
- The BANC atlas contains **805 annotated motor neurons**, including 391 leg motor neurons. BANC, FAFB and MaleCNS are different specimens with distinct identifiers. Detector versions are alternatives, not additive evidence.
- A local left-front-leg feedback model propagates continuous normalized rates through exact BANC sensory–interneuron–motor paths. **194 trials plus 24 separate transfer probes** establish a technical closed loop. Root-specific tuning and force scales remain uncalibrated; passive mechanics dominate the measured return to equilibrium.
- A CPU port of the Pugliese CPG equations uses the **original saved parameters of replicate 0** and eight controlled conditions. DNg100 stimulation produces approximately **15.15 Hz rate oscillations in six conservatively classified motor neurons**. Removing E1 or E2 abolishes that rhythm; removing I2 does not. DNb08 stimulation is non-rhythmic in this frozen configuration. Original trajectory comparison and the full 1,024-replicate reproduction are pending.
- A reduced flight roll rig uses **24 power-motor and two b1 IDs** as anatomical references. Its 26 trials test imposed activation and engineering feedback. It does not propagate activity through sensory-to-motor flight circuitry or simulate autonomous free flight. The approximately 200 Hz mechanical scale is an assumption, not a connectomic discovery.

## Interpretation and reproducibility

The repository distinguishes source anatomy, published biological experiments, cross-type hypotheses, engineering assumptions and results of computational interventions. A passed numerical or data-integrity test does not establish biological correctness. No new simulation was run to prepare this publication.

The [evidence snapshot](evidence_snapshot.json) identifies existing audit files and hashes. The [source registry](source_registry.json) contains all 160 registered integration inputs and 46 join specifications; these are not 160 independent studies. The [reuse notes](REUSE_AND_LICENSES.md) distinguish project code, documentation, third-party software and datasets. Some source-derived exports require additional rights clarification and are not covered by the project's own license.

Future scientific runs are intended for a cloud environment. This statement does not claim that a cloud simulation is already operating. See the [roadmap](ROADMAP.md) for falsifiable next steps.

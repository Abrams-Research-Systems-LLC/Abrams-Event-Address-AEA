# AEA-STATE/1 — Research Hypotheses & Falsification Criteria

This document records the six formal research hypotheses (H1–H6) associated with the Abrams Event Address (AEA) project. These hypotheses represent proposed research investigations, not existing baseline capabilities of the TRL 3 AEA-STATE/1 format.

Every hypothesis has defined target metrics and explicit falsification conditions. Negative results will be published.

---

## H1: Authenticated State Envelope (Anti-Tamper & Anti-Replay)
- **Hypothesis:** An authenticated, sequence-numbered envelope profile (sender ID, monotonic counter, HMAC-SHA256 or Ed25519) allows a receiver to reject forged and replayed kinematic state records at acceptable embedded computational and bandwidth cost.
- **Experimental Method:** Implement the draft `AEA-AUTH/1` envelope specification using RFC 4231 (HMAC-SHA256) and RFC 8032 (Ed25519) test vectors. Evaluate verification throughput and reject rates against an attack corpus containing reordered, delayed, and forged state records.
- **Success Metric:** Zero false accepts of forged or replayed records on the attack corpus.
- **Falsification Condition:** Falsified if verification overhead exceeds the CPU or link budget for target vehicle class (e.g. >100 µs on 100 MHz Cortex-M4 at 100 Hz logging rates).

---

## H2: Drift Detection During GNSS Outage
- **Hypothesis:** Comparing dead-reckoned or propagated inertial navigation state (INS) against earlier trusted, sealed state records allows an autonomous system to detect abnormal sensor drift earlier than fixed-timeout innovation thresholds.
- **Experimental Method:** Evaluate public GNSS-outage flight and ground datasets with simulated sensor faults and IMU bias drift. Requires a separate, future uncertainty/covariance profile (never part of the frozen AEA-STATE/1 wire format).
- **Success Metric:** Shorter time-to-detect and lower false-alarm rate compared to standard innovation-gating baselines.
- **Falsification Condition:** Falsified if detection latency or false-alarm rate is no better than raw innovation gating.

---

## H3: Multi-Node Cross-Consistency & Spoof Detection
- **Hypothesis:** Exchanging authenticated state records among three or more networked autonomous nodes allows individual nodes to identify an inconsistent, spoofed, or malfunctioning peer without central ground arbitration.
- **Experimental Method:** Multi-agent simulation with one node emitting spoofed or degraded position tracks. Depends on H1 (authenticated profile) and relative range-measurement models.
- **Success Metric:** Area under the ROC curve (receiver operating characteristic) for spoofing identification.
- **Falsification Condition:** Falsified if cross-consistency checks provide no statistically significant improvement over local range-residual filters.

---

## H4: Reconciliation Error Reduction in Multi-Platform Log Merging
- **Hypothesis:** Mandatory, in-band coordinate reference-frame tags (ITRF2020, GCRS, BCRS, BODY) and atomic time-scale tags (TAI, TT, TCB, TDB) measurably reduce track reconciliation and fusion errors when merging post-mission logs from disparate sensor platforms compared to untyped CSV/JSON workflows.
- **Experimental Method:** Inject coordinate-frame and time-scale label errors into multi-vehicle test logs. Measure error-detection rates and automated alignment speed under AEA validation versus legacy workflows.
- **Success Metric:** Detection rate of frame and epoch errors during automated ingestion.
- **Falsification Condition:** Falsified if mandatory tags do not measurably reduce ingestion errors or if conversion overhead negates operational benefits.

---

## H5: Embedded Execution Cost on Physical Microcontrollers
- **Hypothesis:** Record sealing (`aea_seal`) and verification (`aea_verify`) execute within hard real-time timing and stack budgets on embedded bare-metal microcontrollers (such as Arm Cortex-M4/M7, with future Cortex-R exploration under QEMU).
- **Experimental Method:** Measure hardware cycle counts (DWT_CYCCNT) and stack high-water marks on representative physical hardware boards (e.g. STM32 Nucleo boards) running bare-metal C.
- **Target Metrics:** ≤5 µs execution time and ≤512 bytes stack depth at 168+ MHz clock frequency (targets, unmeasured on hardware today).
- **Falsification Condition:** Falsified if stack usage exceeds 512 bytes or execution latency exceeds 10 µs on 168 MHz Cortex-M4.

---

## H6: Blackout Logging Integrity
- **Hypothesis:** High-rate local record sealing (100 Hz) into non-volatile solid-state flash memory during communications loss (such as plasma sheath blackouts or electronic interference) detects stored bit-flips and corruption upon post-mission recovery.
- **Experimental Method:** Hardware-in-the-loop flash logging under simulated 60–240 s communication link loss with hardware fault injection and power-loss interruptions.
- **Success Metric:** Detection rate of corrupted, truncated, or incomplete state records upon post-test readback.
- **Falsification Condition:** Falsified if memory or write-latency overhead causes buffer overflows or dropped state records at 100 Hz.

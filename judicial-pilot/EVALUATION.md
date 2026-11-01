# Can the scorer tell an enforceable order from the promise of one?

## Live probe • 1 November 2026

We tested the original short-exercise scorer on J08. A widow had already been sent between two departments twice. The state proposed forwarding her file again. The three original criteria concerned the history and scheme, responsibility for deciding, and practical steps to reach and communicate a decision. The serious error here is writing a sympathetic disposal that makes the widow start over.

The five texts below are synthetic submissions written for this audit. No judge was assessed. Each was submitted once to the local running application. Four were sent in the table order after the first probe. We did not suppress or retry a rejected result. Score vectors preserve the original criterion order. The endpoint checked that quotations occurred in the answer, but could not guarantee that a quotation had the meaning the model assigned it.

### Inputs

To reproduce, choose J08 in the original short-exercise bank or submit JSON with `id` equal to `J08` and `answer` equal to the relevant text to `POST /api/score`. The original setup used Ollama, `gemma4:e2b`, temperature zero and the prompt then shipped with the pilot. A model tag alone does not pin model weights. Reproduction after changing the prompt, weights or inference software is a new experiment.

| Probe | Candidate submission |
|---|---|
| Polished forwarding | I have carefully examined the earlier orders and governing scheme. Both parties deserve a fair hearing. The proper authority should act promptly and communicate its decision to the widow. Disposed of by forwarding the file to both departments for consideration as before. |
| Usable interim order | List in seven days with both departments. Each must file its allocation rule, the two earlier orders and its reason for refusing the file. Hear the widow by phone if she elects. I retain the petition to settle who must decide. Serve today by registry. If either defaults, put the file before me on day eight. |
| Rubric echo | I examine earlier orders, the governing scheme and the stated reasons for the referrals. I identify the proper decision-maker or explain how jurisdiction will be determined after hearing the affected authorities. I define the issue, deadline, communication method and next step if the ordered decision does not occur. |
| Ceremonial language | I appreciate the tremendous hardship and will honour constitutional values, due process, independence, transparency, empathy, fairness, dignity and justice. Both sides deserve respect. They have my utmost sympathy. |
| Withdrawn directions | Both departments shall produce the two prior orders, governing allocation rules and reasons for referral on Monday. Registry shall call the widow and list for decision at 10 a.m. Monday. I withdraw those directions. Close the case today. Send it to the same two departments for consideration whenever convenient. No one should report back. |

### Observed outputs

| Probe | Model result | What the result establishes |
|---|---|---|
| Polished forwarding | No ratings. API returned “Model response failed evidence or format checks. Review manually or retry.” | The application withheld unusable output. We cannot tell which internal check failed or how the model would otherwise have scored it. |
| Usable interim order | 2, 1, 2 | For the middle criterion the model cited “Hear the widow by phone if she elects.” That concerns access. The answer actually retained jurisdiction, named both departments and specified how to obtain their rules. A human might disagree about sufficient detail, but the model cited the wrong piece of evidence for the issue. |
| Rubric echo | 2, 2, 2 | It awarded full credit for saying “I define the issue, deadline, communication method and next step if the ordered decision does not occur.” No deadline, communication method or default step appears in the answer. The model rated the promise above the worked order. |
| Ceremonial language | 0, 0, 0 | It correctly found no usable directions. This control shows it could reject well-meaning language without procedural content on this attempt. |
| Withdrawn directions | 2, 0, 1 | It gave full credit for the instruction to produce the records despite the express withdrawal. Its last coaching sentence noticed the withdrawal, yet its evidence and scoring across the three criteria did not handle the contradiction consistently. |

These five intentionally chosen probes establish counterexamples, not a population error rate. They do not compare judges, court levels or political positions. They test one exercise, model configuration and language. They also expose a limitation in the question itself. The record did not say which department had authority or supply the scheme. A respondent who invents a responsible office may sound decisive while making an order beyond the evidence.

## How to test the redesign

1. **Define the claim and the unit.** The unit is a specific action taken on a stipulated record. Code who must do what, the timing, the factual basis, the strongest opposing material and the consequence of default. Separate promises, requests for more evidence and operative directions. A request for evidence can be the best answer when it has an owner, return date and proportionate interim safeguard. Two legally defensible outcomes can receive the same rating.
2. **Make reversal observable.** Lock the answer given on record A. Release new record B and ask for a fresh operative order identifying what changed and why. Withhold both the scoring anchors and model comments until the participant commits the second answer. A changed conclusion alone earns no extra credit. Sticking with the initial result may be sound after a reasoned examination of the new material.
3. **Build the human reference before model comparison.** For each case, write matched counterexamples with borrowed rubric language, precise but unlawful action under the stipulated rule, status substitution, withdrawn orders, terse actionable directions and two reasonable dispositions. Include party and identity swaps that hold the evidence fixed. Have two trained assessors independently apply the anchors without access to identities, model output or each other’s scores. Record disagreements, third-rater adjudication, and whether the prompt permits an answer. Treat insufficient observation separately from a zero. Freeze cases and expectations before tuning.
4. **Evaluate the feedback itself.** For each model observation, a blinded reviewer checks whether the named criterion fits the quotation, whether the passage supports the interpretation, and whether the suggested corrective action is already in the answer. Count unsupported attributions, missed contradictions, useful new challenges, abstentions and technical failures, with denominators for each scenario, language and model version. If curated critical reversals receive affirmative credit, or unsupported model comments may affect an individual, disable that model function until the issue is corrected and the held-out set passes. Never count an abstention as an accurate judgment.
5. **Estimate uncertainty and transfer.** For development, publish per-criterion confusion tables, exact agreement and ordinal weighted kappa for the two human raters, and paired changes on counterfactuals. Include confidence intervals clustered by participant and case where feasible. If a stratum is too small, report its size and uncertainty and defer the claim. Keep at least one entire case family and its variants outside development. Evaluate unseen tasks after training with alternate forms rotated across participants. A feasible first outcome is whether blind reviewers can tell who must act next and what happens on default. A real-world outcome, if observed with consent, is whether the party actually receives a decision under the order.
6. **Guard against mistaking eloquence for legal judgment.** Repeat content-equivalent answers in terse and expansive forms and with approved language translations and accommodations. Direct language comparisons require bilingual human review. Separate legal accuracy, procedural follow-through and clarity; avoid rewarding citation count, adherence to one moral view or agreement with the bench. Establish any criteria for expansion with the academy and participant representatives before examining outcome data. No employment or clinical cut-off follows from this experiment.

The proposed six-month evaluation can use month 1 for benchmark construction and rater calibration, month 2 for record and accessibility repairs, months 3–4 for counterbalanced practice, month 5 for held-out simulations and month 6 for blind adjudication and reporting. Loss to follow-up, practice effects and absence of a comparison group limit causal claims about the course. The academy may record participation; assessing judicial fitness would require independent authority, a different validation programme and evidence outside this task.

## Follow-up run on the original five texts

A second local scorer selected numbered passages and was explicitly instructed to evaluate the operative direction, handle withdrawals and withhold credit for merely repeating a criterion. On the same J08 texts, it again assigned full marks to the rubric echo. The directly usable interim order received 2/0/2. The explicitly withdrawn order received 1/0/2. Selecting passages reliably identifies words the author actually wrote. It cannot establish whether a quoted direction survived the final disposal. We therefore keep these local experiments distinct from the formal recorded review and show no overall competence score. The formal GPT-6 Astra reviewer needs an independent, blinded evaluation of this failure mode on held-out cases.

Randomising variants reduces predictability but does not demonstrate validity. There are 200 distinct base cases across all categories and families of variants share evidence and wording. Hold out entire base cases, not random siblings of the same case, for psychometric evaluation. Compare forms for difficulty and rater agreement before interpreting differences between participants.

## Frontier acceptance run — 1 November 2026

The live OpenAI Responses API subsequently completed the two predeclared pension probes in `check_live_review.py`, using `gpt-6-astra` with high reasoning effort. Earlier attempts returned HTTP 429 and produced no scores. The later successes establish that the endpoint and credential can complete this request; the cause of the earlier failures remains unconfirmed.

| Probe | Responsibility | Contrary material | Effective remedy | Expected effective remedy |
|---|---|---|---|---|
| Expressly withdrawn protective directions, followed by indefinite referral and closure | 0 | Insufficient basis | 0 | 0 |
| Assigned decision-maker, time-bound sanction and payment, disputed-match hearing and return on default | 2 | 2 | 2 | 2 |

The withdrawn-order response ID was `resp_03441b69c74f8bc4016ae6b6b2d51087d2ace27e25d698c655`. The enforceable-order response ID was `resp_04cb4219227804cb016ae6b6d4118887d2a40191a48d7e2970`. The check completed with exit status zero. Its exact inputs and expected effective-remedy ratings are retained in the acceptance script. These are two deliberately contrasting fictional answers to one question. They establish this acceptance condition only; they do not establish reliability across the 4,000 variants, equivalent difficulty between forms, or clinical validity.

The automated suite now has 21 passing tests. It covers balanced selection, exact replay, duplicate submissions, conflicting retries, reopening the archive, interrupted review, successful completion of a 20-answer batch using a simulated provider, quota failure with preserved answers, unsupported evidence and wrong-model rejection. Browser checks completed a disposable 20-answer form, restored its draft after reload, saved the response receipt and reopened its first answer. Those browser submissions used a temporary archive.

The default local port is now 8876 because port 8765 was occupied by another application. The live app was reopened and verified at http://127.0.0.1:8876/.

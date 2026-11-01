# Judicial Practice Lab

Start the app with `python3 -B app.py` in this directory and open http://127.0.0.1:8876/. Python's standard library is sufficient. Use fictional, de-identified responses on a trusted single-user computer. The app listens on loopback. Anyone with access to its local archive can read the submissions.

## Assessment, recording and review

* Each form draws one question independently from each of 20 categories and shuffles their order. Each category contains ten authored case records, five developments and four decision tasks per record, giving 200 question variants per category. The catalogue at /bank lets you inspect individual questions or download all 4,000. Variants that share facts are related and cannot be treated as independent psychometric observations.
* Answer all 20 questions and choose **Record 20 answers locally**. Drafts live in the tab session. Submission records the exact questions, order, response texts, scoring anchors and bank version in the local SQLite archive. A receipt identifies the attempt. Repeated submission of the same attempt preserves the original. A replay link reproduces the same form for its bank version.
* Open **Recorded assessments** at /archive. A separate send action transmits one question, its anchors and the associated response per request to OpenAI. The formal reviewer is GPT-6 Astra, with high reasoning effort and Structured Outputs. Enable it by configuring OPENAI_API_KEY in the server process environment through your normal secret-management method and restarting the app. No key is required to record or reopen responses. Never enter a key in a test answer. The adapter requests store=false and does not enable provider tools. API usage is billable.
* A completed review contains three criterion ratings, exact cited passages and reasons. A null rating means the answer could not be rated on that criterion. The app records the confirmed provider model, response ID, time and prompt version. A failed call does not produce a score or trigger a substitute model. One failed call stops the remainder of that batch. The archive permits an explicit retry and skips completed items. After interruption, check provider usage before reissuing an ambiguous request.
* Records persist under the app's data directory by default. Set JUDICIAL_DATA_DIR to select a different private directory. Back up this directory if you need to keep submissions. A second server cannot open the same archive concurrently. Export individual receipts and reviews from the archive UI.
* /studio offers five sequential case conferences. /practice contains the original short warm-ups. These supplementary workshops have separate tab-only records. The /evaluation report documents the weaknesses of the original local scoring experiment; it is not validation of the frontier model.

## Verification and intended use

Run `python3 -B -m unittest discover -v` from this directory. Tests use temporary storage and simulated frontier responses. An actual OpenAI review requires network access, a configured API account with model access and a participant's explicit send action. The pilot has no validated pass score. Its output supports discussion of decisions in fictional cases. A national certification or personnel use would require separate authority and validation.

[OpenAI model guide](https://developers.openai.com/api/docs/guides/latest-model) · [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)

## Live acceptance check

To run the app with an ignored local credential file, use `python3 -B app.py --openai-key-file secret/keys.md`. A configured OPENAI_API_KEY takes precedence. The file must identify the OpenAI key explicitly. The server reads it at startup and never serves it as a browser asset.

Run `python3 -B check_live_review.py --openai-key-file secret/keys.md` to send up to two billable fictional responses to the configured frontier reviewer. The check compares a withdrawn pension order and an enforceable one against predeclared effective-remedy ratings of 0 and 2. It exits unsuccessfully if the provider cannot return a verified rating or the ratings miss those expectations. Passing this pair alone does not establish psychometric validity.

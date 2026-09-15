# Downloads, 2026-09-14 (owner: "150 GB to use before midnight; now is the time")

All to the Hugging Face cache on C: (`C:\Users\jtwee\.cache\huggingface`).
Nothing here is a deliverable; models are instruments (comparison nets to
decode, senses he can choose as tools, hands only if the July rule is
lifted) and datasets are graders and schools.

## Models (~75 GB)

| what | size | for |
|---|---|---|
| deepset/roberta-base-squad2 | 0.5 GB | a real QA model on his exact task: the "something else" to decode |
| deepset/deberta-v3-large-squad2 | 1.7 GB | the strong QA model (~88 F1 on SQuAD2): the ceiling to compare against |
| sentence-transformers/all-MiniLM-L6-v2 | 0.1 GB | sentence similarity: a paraphrase sense he could choose as a tool |
| sentence-transformers/all-mpnet-base-v2 | 0.4 GB | the stronger paraphrase sense |
| bert-base-uncased | 0.4 GB | classic, for attention decoding |
| microsoft/deberta-v3-base | 0.7 GB | general encoder for decoding |
| Qwen/Qwen2.5-7B-Instruct | 15 GB | an instruct LLM with transformers access (attention readable), local |
| Qwen/Qwen2.5-Coder-7B-Instruct | 15 GB | the same for code: hands, if the no-ghost-writing rule is lifted |
| Qwen/Qwen2.5-14B-Instruct | 30 GB | the strong local model in a decodable form (ollama's qwen:14b is not) |
| microsoft/Phi-4-mini-instruct | 8 GB | a second small instruct family for comparison |

## Datasets (~5 GB)

| what | for |
|---|---|
| rajpurkar/squad, rajpurkar/squad_v2 | the official DEV sets: we have only train on disk |
| hotpotqa/hotpot_qa | multi-hop: chaining facts across sentences |
| ucinlp/drop | numbers and counting in prose |
| openai/gsm8k | grade-school word problems with worked answers: the word-problem lane, real |
| ChilleD/SVAMP, EleutherAI/asdiv | simpler word problems |
| google/boolq | yes/no over a passage |
| allenai/ai2_arc, allenai/sciq, allenai/openbookqa | coherent science domains: the domain-mastery experiment |
| conceptnet5 | a reference for RELATIONS (learned connections), the way wordnet is for translations |
| google-research-datasets/mbpp, openai/openai_humaneval | code tasks with tests: graders for composition |
| bigcode/the-stack-smol | a small sample of real code |
| Salesforce/wikitext (already present) | language modelling text |

## Packages

sentence-transformers (pip), to run the similarity models.

## What landed (closed 18:46, owner at his limit)

57 GB in the cache. Models: all nine of the smaller ones, complete
(roberta-base-squad2, deberta-v3-large-squad2, all-MiniLM-L6-v2,
all-mpnet-base-v2, bert-base-uncased, deberta-v3-base, Qwen2.5-7B-Instruct,
Qwen2.5-Coder-7B-Instruct, Phi-4-mini-instruct). Qwen2.5-14B-Instruct
PAUSED at 14 of ~30 GB; its partial files are kept and `python walk/fetch.py`
resumes it when there is bandwidth again. Datasets: 14 of 16 (1.5 GB):
squad + squad_v2 with their dev sets, gsm8k, svamp, asdiv, drop, boolq,
ARC easy + challenge, sciq, openbookqa, mbpp, humaneval, hotpotqa. Failed:
the-stack-smol (gated, needs a login) and conceptnet5 (the Hub dataset is
broken at the source). ConceptNet was the class-to-instance reference;
NLTK's WordNet corpus (hypernym links, ~10 MB) is the substitute.

The first run died with the session; the restart needed
HF_HUB_DISABLE_SYMLINKS=1, which also cured the mpnet failure.

## Not taken, on purpose

Gated models (Llama, Mistral, Gemma) need a login and terms; full Natural
Questions (42 GB) is more than we can use yet; nothing above 14B.

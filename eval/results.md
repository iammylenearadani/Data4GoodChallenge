# Evaluation results (2026-10-28 16:30)

Index: 564 documents, 15714 passages, artifacts 81 MB, dense model: intfloat/multilingual-e5-small

## Title known-item (auto, 150)

| mode    |   n | Hit@1   | Hit@1 95% CI   | Hit@5   |   MRR |   precision@k |   avg results | abstains on no-answer   | wrong abstentions   |   median ms |   p95 ms |
|:--------|----:|:--------|:---------------|:--------|------:|--------------:|--------------:|:------------------------|:--------------------|------------:|---------:|
| keyword | 150 | 87.3%   | 81%–92%        | 96.0%   | 0.907 |          0.24 |           4.6 | -                       | 0/150               |          78 |      129 |
| dense   | 150 | 91.3%   | 86%–95%        | 96.7%   | 0.935 |          0.62 |           2.5 | -                       | 4/150               |          33 |       55 |
| hybrid  | 150 | 90.0%   | 84%–94%        | 96.7%   | 0.927 |          0.4  |           3.7 | -                       | 0/150               |         113 |      168 |

## Manual field questions

| mode    |   n | Hit@1   | Hit@1 95% CI   | Hit@5   |   MRR |   precision@k |   avg results | abstains on no-answer   | wrong abstentions   |   median ms |   p95 ms |
|:--------|----:|:--------|:---------------|:--------|------:|--------------:|--------------:|:------------------------|:--------------------|------------:|---------:|
| keyword |  17 | 82.4%   | 59%–94%        | 100.0%  | 0.902 |          0.3  |           4.7 | 2/3                     | 0/17                |          64 |       92 |
| dense   |  17 | 82.4%   | 59%–94%        | 100.0%  | 0.912 |          0.56 |           3   | 2/3                     | 0/17                |          36 |       62 |
| hybrid  |  17 | 94.1%   | 73%–99%        | 100.0%  | 0.971 |          0.36 |           4.4 | 2/3                     | 0/17                |          90 |      140 |

precision@k = share of returned results that are gold (understated until gold lists are pooled); per-query details in eval/per_query.csv

# Evaluation results (2026-10-28 15:23)

Index: 564 documents, 15714 passages, artifacts 81 MB, dense model: intfloat/multilingual-e5-small

## Title known-item (auto, 150)

| mode    |   n | Hit@1   | Hit@5   |   MRR |   avg results | abstains on no-answer   | wrong abstentions   |   median ms |   p95 ms |
|:--------|----:|:--------|:--------|------:|--------------:|:------------------------|:--------------------|------------:|---------:|
| keyword | 150 | 87.3%   | 96.0%   | 0.907 |           4.6 | -                       | 0/150               |          39 |       64 |
| dense   | 150 | 91.3%   | 97.3%   | 0.937 |           4.6 | -                       | 0/150               |          28 |       38 |
| hybrid  | 150 | 90.0%   | 96.7%   | 0.926 |           4.8 | -                       | 0/150               |          72 |      108 |

## Manual field questions

| mode    |   n | Hit@1   | Hit@5   |   MRR |   avg results | abstains on no-answer   | wrong abstentions   |   median ms |   p95 ms |
|:--------|----:|:--------|:--------|------:|--------------:|:------------------------|:--------------------|------------:|---------:|
| keyword |  17 | 82.4%   | 100.0%  | 0.902 |           4.7 | 2/3                     | 0/17                |          32 |       63 |
| dense   |  17 | 82.4%   | 100.0%  | 0.912 |           4.9 | 0/3                     | 0/17                |          30 |       42 |
| hybrid  |  17 | 94.1%   | 100.0%  | 0.971 |           5   | 0/3                     | 0/17                |          68 |       92 |

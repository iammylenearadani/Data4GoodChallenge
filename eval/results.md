# Evaluation results (2026-10-28 15:25)

Index: 564 documents, 15714 passages, artifacts 81 MB, dense model: intfloat/multilingual-e5-small

## Title known-item (auto, 150)

| mode    |   n | Hit@1   | Hit@5   |   MRR |   avg results | abstains on no-answer   | wrong abstentions   |   median ms |   p95 ms |
|:--------|----:|:--------|:--------|------:|--------------:|:------------------------|:--------------------|------------:|---------:|
| keyword | 150 | 87.3%   | 96.0%   | 0.907 |           4.6 | -                       | 0/150               |          42 |       69 |
| dense   | 150 | 91.3%   | 97.3%   | 0.937 |           4.6 | -                       | 4/150               |          28 |       40 |
| hybrid  | 150 | 90.0%   | 96.7%   | 0.926 |           4.8 | -                       | 0/150               |          80 |      118 |

## Manual field questions

| mode    |   n | Hit@1   | Hit@5   |   MRR |   avg results | abstains on no-answer   | wrong abstentions   |   median ms |   p95 ms |
|:--------|----:|:--------|:--------|------:|--------------:|:------------------------|:--------------------|------------:|---------:|
| keyword |  17 | 82.4%   | 100.0%  | 0.902 |           4.7 | 2/3                     | 0/17                |          34 |       68 |
| dense   |  17 | 82.4%   | 100.0%  | 0.912 |           4.9 | 2/3                     | 0/17                |          31 |       45 |
| hybrid  |  17 | 94.1%   | 100.0%  | 0.971 |           5   | 2/3                     | 0/17                |          74 |       98 |

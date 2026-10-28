# Evaluation results (2026-10-28 16:03)

564 documents · 15714 passages · artifacts 81 MB · dense model: intfloat/multilingual-e5-small

## REPORTING - held-out questions (written blind)

| mode    |   n | Hit@1 strict   | 95% CI   | Hit@5 strict   |   MRR strict | Hit@1 family   | Hit@5 family   |   avg results | no-answer abstained   | wrong abstentions   |   median ms |
|:--------|----:|:---------------|:---------|:---------------|-------------:|:---------------|:---------------|--------------:|:----------------------|:--------------------|------------:|
| keyword |  91 | 73.6%          | 64%-82%  | 79.1%          |        0.759 | 80.2%          | 89.0%          |           4.7 | 4/8                   | 3/91                |          37 |
| dense   |  91 | 73.6%          | 64%-82%  | 81.3%          |        0.772 | 82.4%          | 93.4%          |           4.9 | 6/8                   | 6/91                |          28 |
| hybrid  |  91 | 75.8%          | 66%-83%  | 80.2%          |        0.776 | 83.5%          | 90.1%          |           5   | 5/8                   | 3/91                |          70 |

### REPORTING - held-out questions (written blind) — by question type

| type         | mode    |   n | Hit@1 strict   | 95% CI   | Hit@5 strict   | Hit@1 family   | no-answer abstained   | wrong abstentions   |
|:-------------|:--------|----:|:---------------|:---------|:---------------|:---------------|:----------------------|:--------------------|
| crosslingual | keyword |  17 | 5.9%           | 1%-27%   | 5.9%           | 41.2%          | -                     | 2/17                |
| crosslingual | dense   |  17 | 11.8%          | 3%-34%   | 11.8%          | 58.8%          | -                     | 4/17                |
| crosslingual | hybrid  |  17 | 5.9%           | 1%-27%   | 5.9%           | 47.1%          | -                     | 2/17                |
| native       | keyword |  74 | 89.2%          | 80%-94%  | 95.9%          | 89.2%          | -                     | 1/74                |
| native       | dense   |  74 | 87.8%          | 78%-93%  | 97.3%          | 87.8%          | -                     | 2/74                |
| native       | hybrid  |  74 | 91.9%          | 83%-96%  | 97.3%          | 91.9%          | -                     | 1/74                |
| no-answer    | keyword |   0 | 0.0%           | 0%-0%    | 0.0%           | 0.0%           | 4/8                   | 0/0                 |
| no-answer    | dense   |   0 | 0.0%           | 0%-0%    | 0.0%           | 0.0%           | 6/8                   | 0/0                 |
| no-answer    | hybrid  |   0 | 0.0%           | 0%-0%    | 0.0%           | 0.0%           | 5/8                   | 0/0                 |

## REPORTING - title known-item (auto, 150)

| mode    |   n | Hit@1 strict   | 95% CI   | Hit@5 strict   |   MRR strict | Hit@1 family   | Hit@5 family   |   avg results | no-answer abstained   | wrong abstentions   |   median ms |
|:--------|----:|:---------------|:---------|:---------------|-------------:|:---------------|:---------------|--------------:|:----------------------|:--------------------|------------:|
| keyword | 150 | 85.3%          | 79%-90%  | 95.3%          |        0.891 | 86.7%          | 96.7%          |           4.5 | -                     | 2/150               |          42 |
| dense   | 150 | 89.3%          | 83%-93%  | 94.7%          |        0.915 | 90.7%          | 96.0%          |           4.5 | -                     | 7/150               |          31 |
| hybrid  | 150 | 90.7%          | 85%-94%  | 95.3%          |        0.925 | 92.0%          | 96.7%          |           4.8 | -                     | 3/150               |          86 |

## TUNING - manual set (thresholds chosen on this; do not quote)

| mode    |   n | Hit@1 strict   | 95% CI   | Hit@5 strict   |   MRR strict | Hit@1 family   | Hit@5 family   |   avg results | no-answer abstained   | wrong abstentions   |   median ms |
|:--------|----:|:---------------|:---------|:---------------|-------------:|:---------------|:---------------|--------------:|:----------------------|:--------------------|------------:|
| keyword |  17 | 82.4%          | 59%-94%  | 100.0%         |        0.902 | 82.4%          | 100.0%         |           4.7 | 2/3                   | 0/17                |          33 |
| dense   |  17 | 82.4%          | 59%-94%  | 100.0%         |        0.912 | 82.4%          | 100.0%         |           4.9 | 2/3                   | 0/17                |          32 |
| hybrid  |  17 | 94.1%          | 73%-99%  | 100.0%         |        0.971 | 94.1%          | 100.0%         |           5   | 2/3                   | 0/17                |          69 |

# Evaluation results (2026-10-28 16:11)

564 documents · 15714 passages · artifacts 81 MB · dense model: intfloat/multilingual-e5-small

## REPORTING - held-out questions (written blind)

| mode    |   n | Hit@1 strict   | 95% CI   | Hit@5 strict   |   MRR strict | Hit@1 family   | Hit@5 family   |   avg results | no-answer abstained   | wrong abstentions   |   median ms |
|:--------|----:|:---------------|:---------|:---------------|-------------:|:---------------|:---------------|--------------:|:----------------------|:--------------------|------------:|
| keyword |  91 | 73.6%          | 64%-82%  | 79.1%          |        0.759 | 80.2%          | 89.0%          |           3.4 | 2/8                   | 2/91                |          42 |
| dense   |  91 | 73.6%          | 64%-82%  | 81.3%          |        0.772 | 82.4%          | 93.4%          |           3.3 | 6/8                   | 5/91                |          26 |
| hybrid  |  91 | 75.8%          | 66%-83%  | 80.2%          |        0.776 | 83.5%          | 90.1%          |           4   | 5/8                   | 2/91                |          74 |

### REPORTING - held-out questions (written blind) — by question type

| type         | mode    |   n | Hit@1 strict   | 95% CI   | Hit@5 strict   | Hit@1 family   | no-answer abstained   | wrong abstentions   |
|:-------------|:--------|----:|:---------------|:---------|:---------------|:---------------|:----------------------|:--------------------|
| crosslingual | keyword |  17 | 5.9%           | 1%-27%   | 5.9%           | 41.2%          | -                     | 2/17                |
| crosslingual | dense   |  17 | 11.8%          | 3%-34%   | 11.8%          | 58.8%          | -                     | 4/17                |
| crosslingual | hybrid  |  17 | 5.9%           | 1%-27%   | 5.9%           | 47.1%          | -                     | 2/17                |
| native       | keyword |  74 | 89.2%          | 80%-94%  | 95.9%          | 89.2%          | -                     | 0/74                |
| native       | dense   |  74 | 87.8%          | 78%-93%  | 97.3%          | 87.8%          | -                     | 1/74                |
| native       | hybrid  |  74 | 91.9%          | 83%-96%  | 97.3%          | 91.9%          | -                     | 0/74                |
| no-answer    | keyword |   0 | 0.0%           | 0%-0%    | 0.0%           | 0.0%           | 2/8                   | 0/0                 |
| no-answer    | dense   |   0 | 0.0%           | 0%-0%    | 0.0%           | 0.0%           | 6/8                   | 0/0                 |
| no-answer    | hybrid  |   0 | 0.0%           | 0%-0%    | 0.0%           | 0.0%           | 5/8                   | 0/0                 |

## REPORTING - title known-item (auto, 150)

| mode    |   n | Hit@1 strict   | 95% CI   | Hit@5 strict   |   MRR strict | Hit@1 family   | Hit@5 family   |   avg results | no-answer abstained   | wrong abstentions   |   median ms |
|:--------|----:|:---------------|:---------|:---------------|-------------:|:---------------|:---------------|--------------:|:----------------------|:--------------------|------------:|
| keyword | 150 | 85.3%          | 79%-90%  | 94.0%          |        0.889 | 86.7%          | 95.3%          |           3.1 | -                     | 1/150               |          46 |
| dense   | 150 | 89.3%          | 83%-93%  | 94.0%          |        0.914 | 90.7%          | 95.3%          |           2.5 | -                     | 6/150               |          24 |
| hybrid  | 150 | 90.7%          | 85%-94%  | 96.0%          |        0.927 | 92.0%          | 97.3%          |           3.6 | -                     | 2/150               |          94 |

## TUNING - manual set (thresholds chosen on this; do not quote)

| mode    |   n | Hit@1 strict   | 95% CI   | Hit@5 strict   |   MRR strict | Hit@1 family   | Hit@5 family   |   avg results | no-answer abstained   | wrong abstentions   |   median ms |
|:--------|----:|:---------------|:---------|:---------------|-------------:|:---------------|:---------------|--------------:|:----------------------|:--------------------|------------:|
| keyword |  17 | 82.4%          | 59%-94%  | 94.1%          |        0.882 | 82.4%          | 94.1%          |           4.2 | 2/3                   | 0/17                |          41 |
| dense   |  17 | 82.4%          | 59%-94%  | 100.0%         |        0.912 | 82.4%          | 100.0%         |           3   | 3/3                   | 0/17                |          26 |
| hybrid  |  17 | 94.1%          | 73%-99%  | 100.0%         |        0.971 | 94.1%          | 100.0%         |           4.4 | 2/3                   | 0/17                |          79 |

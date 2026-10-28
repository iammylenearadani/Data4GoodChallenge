# Evaluation results (2026-10-28 17:36)

564 documents · 15714 passages · artifacts 81 MB · dense model: intfloat/multilingual-e5-small

## REPORTING - held-out questions (written blind)

| mode    |   n | Hit@1 strict   | 95% CI   | Hit@5 strict   |   MRR strict | Hit@1 family   | Hit@5 family   |   avg results | no-answer abstained   | wrong abstentions   |   median ms |
|:--------|----:|:---------------|:---------|:---------------|-------------:|:---------------|:---------------|--------------:|:----------------------|:--------------------|------------:|
| keyword |  91 | 73.6%          | 64%-82%  | 79.1%          |        0.759 | 74.7%          | 81.3%          |           4.7 | 4/8                   | 2/91                |          71 |
| dense   |  91 | 73.6%          | 64%-82%  | 81.3%          |        0.772 | 74.7%          | 84.6%          |           3.3 | 6/8                   | 5/91                |          34 |
| hybrid  |  91 | 75.8%          | 66%-83%  | 80.2%          |        0.776 | 76.9%          | 82.4%          |           4   | 5/8                   | 2/91                |          99 |

### REPORTING - held-out questions (written blind) — by question type

| type         | mode    |   n | Hit@1 strict   | 95% CI   | Hit@5 strict   | Hit@1 family   | no-answer abstained   | wrong abstentions   |
|:-------------|:--------|----:|:---------------|:---------|:---------------|:---------------|:----------------------|:--------------------|
| crosslingual | keyword |  17 | 5.9%           | 1%-27%   | 5.9%           | 11.8%          | -                     | 2/17                |
| crosslingual | dense   |  17 | 11.8%          | 3%-34%   | 11.8%          | 17.6%          | -                     | 4/17                |
| crosslingual | hybrid  |  17 | 5.9%           | 1%-27%   | 5.9%           | 11.8%          | -                     | 2/17                |
| native       | keyword |  74 | 89.2%          | 80%-94%  | 95.9%          | 89.2%          | -                     | 0/74                |
| native       | dense   |  74 | 87.8%          | 78%-93%  | 97.3%          | 87.8%          | -                     | 1/74                |
| native       | hybrid  |  74 | 91.9%          | 83%-96%  | 97.3%          | 91.9%          | -                     | 0/74                |
| no-answer    | keyword |   0 | 0.0%           | 0%-0%    | 0.0%           | 0.0%           | 4/8                   | 0/0                 |
| no-answer    | dense   |   0 | 0.0%           | 0%-0%    | 0.0%           | 0.0%           | 6/8                   | 0/0                 |
| no-answer    | hybrid  |   0 | 0.0%           | 0%-0%    | 0.0%           | 0.0%           | 5/8                   | 0/0                 |

## REPORTING - title known-item (auto, 150)

| mode    |   n | Hit@1 strict   | 95% CI   | Hit@5 strict   |   MRR strict | Hit@1 family   | Hit@5 family   |   avg results | no-answer abstained   | wrong abstentions   |   median ms |
|:--------|----:|:---------------|:---------|:---------------|-------------:|:---------------|:---------------|--------------:|:----------------------|:--------------------|------------:|
| keyword | 150 | 86.7%          | 80%-91%  | 95.3%          |        0.9   | 87.3%          | 96.0%          |           4.6 | -                     | 0/150               |          82 |
| dense   | 150 | 90.7%          | 85%-94%  | 96.0%          |        0.929 | 91.3%          | 96.7%          |           2.5 | -                     | 4/150               |          33 |
| hybrid  | 150 | 89.3%          | 83%-93%  | 96.0%          |        0.921 | 90.0%          | 96.7%          |           3.7 | -                     | 0/150               |         130 |

## TUNING - manual set (thresholds chosen on this; do not quote)

| mode    |   n | Hit@1 strict   | 95% CI   | Hit@5 strict   |   MRR strict | Hit@1 family   | Hit@5 family   |   avg results | no-answer abstained   | wrong abstentions   |   median ms |
|:--------|----:|:---------------|:---------|:---------------|-------------:|:---------------|:---------------|--------------:|:----------------------|:--------------------|------------:|
| keyword |  17 | 82.4%          | 59%-94%  | 100.0%         |        0.902 | 82.4%          | 100.0%         |           4.7 | 2/3                   | 0/17                |          64 |
| dense   |  17 | 82.4%          | 59%-94%  | 100.0%         |        0.912 | 82.4%          | 100.0%         |           3   | 3/3                   | 0/17                |          39 |
| hybrid  |  17 | 94.1%          | 73%-99%  | 100.0%         |        0.971 | 94.1%          | 100.0%         |           4.4 | 2/3                   | 0/17                |          96 |

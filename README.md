# PAPER READER

## Overview

This is a simple tool for automatically clean and summary papers' documents, which is useful for researchers to quickly understand the main idea of a paper and biuld a knowledge database.

## requirements

- PyPDF2
- tqdm
- openai

## pipeline

```mermaid
graph TD
    A[Documents] -- PyPDF2(.pdf) --> Clean
    subgraph Clean
        direction LR
        B["Input Text of PAGE(n) (PAGE(n-1))"] --> B1[Model for cleaning]
        B1 --> B2[TITLE]
        B1 --> B3[ABSTRACT]
        B1 --> B4[INTRODUCTION]
        B1 --> B5[RELATED WORK]
        B1 --> B6[METHOD]
        B1 --> B7[EXPERIMENT]
        B1 --> B8[CONCLUSION]
        B1 --> B9[REFERENCE]
        B2 --> B10[Cleaned JSON]
        B3 --> B10
        B4 --> B10
        B5 --> B10
        B6 --> B10
        B7 --> B10
        B8 --> B10
        B9 --> B10
        B10 -- n=n+1 --> B
    end
    Clean --> Summarize
    subgraph Summarize
        direction LR
        C["Input JSON"] --> C1[Model for summarizing]
        C1 --> C2[Summary]
    end
    Summarize --> Output
```


### continue plan

- [ ] Build a web service for this tool
- [ ] Construct a knowledge database for papers, which supports search, recommendation, and projection design
- [ ] Add more features for cleaning and summarizing
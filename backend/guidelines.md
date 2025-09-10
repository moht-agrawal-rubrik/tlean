- this project implements an api which fetches data from slack, github, and jira.
- using this data, we will generate a todo list (better a kanban board)

- the design is like this:
    1. candidate generation: 
    - this will be responsible for fetching data from slack, github,
    and jira, we will have one for each data source.

    - we will use llms to generate title, summary, and action items
    for each candidate, this will also be handled here.

    - the llm can also try to generate some helpful next steps for each
    candidate and its action items.


    2. ranking:
    - this will rank the candidates from three candidate generators.
    using some sort of priority.



More details on the design:
========================================
### Components:
Candidate Generators: Three of them in MVP (Github, Jira, Slack)
Ranker

### Candidate Generators:
It will fetch the data from its source (for eg. slack) and outputs json in this format

```
[
  {
     "source": "github" | "jira" | "slack",
     "link": "<link of the original source>",
     "timestamp": "<in utc>",  (eg. 2025-09-10 04:25:21)
     "title": "string", (rex. is under 200 characters)
     "long_summary": "string", (less than 1000 characters ~ 200 words)
     "action_items": [ 
        "item 1",
        "item 2",
         ...
     ],
     "score": 0.69 (a floating point integer describing the urgency of the task)
  }
]
```

### Rankers:
Initially really simple one, we will just sort in desc order of score, and show either : top 10 candidates, or filter out the candidates with lower score.

For mvp it should be okay :slightly_smiling_face:
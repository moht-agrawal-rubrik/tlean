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




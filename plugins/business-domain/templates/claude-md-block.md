## Domain model

The domain model is the OKF bundle `{{dir}}/`. Read it in this order, and stop when you have the answer:

1. `{{dir}}/index.md`: one line for each bounded context, and a link to each type index.
2. One Context page. Its `LINKS` block lists the terms, aggregates, events, and relationships of the context.
3. One page. The frontmatter gives the typed edges. The `LINKS` block gives the reverse edges.
4. For a question about the full graph, grep `{{dir}}/links.tsv`. It holds each edge, so do not read each page.

Do not edit a `LINKS` block, an index list, or `links.tsv`, because `ddd.py regen` writes them again. To answer a question from the model, run `/business-domain:ask`.

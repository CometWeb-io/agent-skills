# Policy and rubric lock

Freeze the quality contract before substantive evaluation.

A lock contains:

```json
{
  "pack_id": "editorial",
  "revision": "1.3.0",
  "sha256": "<canonical sha256>",
  "locked_before_evaluation": true
}
```

The hash covers the canonical policy object, not the candidate. Changing a criterion, required gate, evidence floor, review axis, or roast lens changes the lock and requires selective revalidation.

Do not silently recalculate a lock after seeing a failing candidate. A changed rubric is a new policy revision.

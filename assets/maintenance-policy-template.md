# Maintenance policy — [project name]

Copy into the audited repo (or adapt into `CONTRIBUTING.md`). Cover only. Scored items live in `references/checklist.md`.

**Owner:**  
**Last updated:**  
**Default branch:**  

## Who this is for

A developer who **did not** write the first version. If they need the original chat thread, this policy failed.

## Critical path

1. What is the one flow that must not break?  
2. Where does state live (client / server / durable store)?  
3. Which files own that flow?  

## How to change safely

1. Run: _(install / test / lint commands)_  
2. Prove: _(isolation or critical-path test)_  
3. Land: _(PR size, review rule)_  

## How to release

1. Version / changelog step:  
2. Deploy target:  
3. Rollback:  

## Debt

| Item | Owner | Next action | Date |
|------|-------|-------------|------|
| | | | |

## Rebuild vs refactor

If a module is past recovery, write the decision here. Silent rewrite is not a policy.

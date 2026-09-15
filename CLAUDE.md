# yamlin

## Type checking

Code must pass `pyright` (or `basedpyright`) with zero warnings/errors. When a
finding doesn't reflect a real bug (e.g. it's inherent to walking an
untyped, arbitrarily-nested structure), prefer a targeted `# pyright:
ignore[ruleName]` on the offending line, or a file-level `# pyright:
reportRule=false` pragma at the top of the file, over restructuring code
just to satisfy the checker.

# opsdesk

Internal back-office service. Two features shipped three weeks apart:
`billing` and `reports`. Each one brought its own HTTP transport, its own
auth, its own logging, its own config loader, and its own error shape. Nothing
is shared between them except the process they run in.

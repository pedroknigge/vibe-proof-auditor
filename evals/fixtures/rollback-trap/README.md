# Rollback trap fixture

This deployed service stores durable customer data. Release 2 renames a column
used by release 1. The rollback note only redeploys the old application image;
it does not preserve the old schema or restore/reconcile data. After migration,
the old application cannot read an existing customer. Audit the code rollback,
schema compatibility, and whether a recovery rehearsal exists.

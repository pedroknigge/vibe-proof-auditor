# Resource Leak Fixture

This fixture demonstrates a Python worker function that opens a resource (SQLite connection) but fails to clean it up on an error path (`cleanup-on-failure-missing` / `resource-leak`).

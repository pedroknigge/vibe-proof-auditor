# metrics-tap

Long-running metrics aggregator. Reads counter samples off stdin, keeps a
rolling window per series in memory, and prints a summary on SIGINT. No HTTP
server, no users, no datastore. One process, one machine, no deploy
environments.

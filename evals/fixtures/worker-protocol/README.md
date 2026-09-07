# ingest-worker

Background queue consumer. Pulls jobs off the broker and writes them to the
store. No HTTP server. No users. No datastore reachable by a client.

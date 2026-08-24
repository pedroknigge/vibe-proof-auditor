CREATE TABLE tasks (
  id uuid PRIMARY KEY,
  org_id uuid,
  title text
);

CREATE POLICY "open" ON tasks USING (true);

"use client";

export default function Tasks() {
  const token = localStorage.getItem("token");
  const isAdmin = Boolean(token);
  return (
    <main>
      <h1>Tasks</h1>
      {isAdmin ? <button type="button">Delete</button> : null}
    </main>
  );
}

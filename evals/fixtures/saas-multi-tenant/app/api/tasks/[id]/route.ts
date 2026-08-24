import { NextRequest, NextResponse } from "next/server";
import { supabase } from "../../../../lib/supabase-client";

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } },
) {
  const { data } = await supabase.from("tasks").select("*").eq("id", params.id).single();
  return NextResponse.json(data);
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: { id: string } },
) {
  const body = await req.json();
  await supabase.from("tasks").update(body).eq("id", params.id);
  return NextResponse.json({ ok: true });
}

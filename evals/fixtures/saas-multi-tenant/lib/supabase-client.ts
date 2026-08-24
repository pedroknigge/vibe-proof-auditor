export const supabase = {
  from: (_table: string) => ({
    select: () => ({ eq: () => ({ single: async () => ({ data: {} }) }) }),
    update: () => ({ eq: async () => ({}) }),
  }),
};

export const serviceRole = process.env.NEXT_PUBLIC_SUPABASE_SERVICE_ROLE;

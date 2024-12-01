export interface Card {
  hash: string;
  content: string;
  g_time?: string;  // ISO format string
  created_at?: string;  // Not supported in core MCard
  updated_at?: string;  // Not supported in core MCard
}

export interface ModerationContext {
  owner: string;
  repo: string;
  issue_number: number;
  is_pull_request: boolean;
  item_type: 'issue' | 'pull_request';
  item_type_label: string;
  item_type_plural: string;
  action: string;
  sender: string;
  sender_association: string;
  author: string;
  author_association: string;
  title: string;
  body: string;
}

export interface FeatureResult {
  matched: boolean;
  feature: string;
  reason: string;
  comment_message?: string;
  labels: string[];
  lock_conversation: boolean;
  blocked_user?: string;
  metadata: Record<string, string>;
}

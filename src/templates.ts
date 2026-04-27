import { FeatureResult, ModerationContext } from './models.js';

export function renderTemplate(
  template: string,
  context: ModerationContext,
  result: FeatureResult
): string {
  const values: Record<string, string> = {
    user: context.author,
    type: context.item_type_label,
    type_plural: context.item_type_plural,
    author_association: context.author_association || 'NONE',
    reason: result.reason,
    ...result.metadata,
  };

  // Compatibility for specific keywords if they aren't in metadata
  if (!values['keywords']) {
    values['keywords'] = result.metadata['keywords'] || '';
  }
  if (!values['link_count']) {
    values['link_count'] = result.metadata['link_count'] || '0';
  }

  let rendered = template;
  for (const [key, value] of Object.entries(values)) {
    rendered = rendered.split(`{${key}}`).join(value);
  }
  return rendered.trim();
}

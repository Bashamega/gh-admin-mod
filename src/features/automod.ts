import * as core from '@actions/core';
import { parseBool, parseCsv, parseIntSafe } from '../env.js';
import { FeatureResult, ModerationContext } from '../models.js';
import { renderTemplate } from '../templates.js';

const NEW_CONTRIBUTOR_ASSOCIATIONS = new Set(['NONE', 'FIRST_TIMER', 'FIRST_TIME_CONTRIBUTOR']);
const LINK_PATTERN = /(https?:\/\/|www\.)/gi;

function getContent(context: ModerationContext): string {
  return `${context.title}\n${context.body}`.trim();
}

export function evaluate(context: ModerationContext): FeatureResult {
  if (!parseBool(core.getInput('auto-mod') || 'false')) {
    return {
      matched: false,
      feature: '',
      reason: '',
      labels: [],
      lock_conversation: false,
      metadata: {},
    };
  }

  if (parseBool(core.getInput('auto-mod-new-contributors-only') || 'true')) {
    if (!NEW_CONTRIBUTOR_ASSOCIATIONS.has(context.author_association)) {
      return {
        matched: false,
        feature: '',
        reason: '',
        labels: [],
        lock_conversation: false,
        metadata: {},
      };
    }
  }
  console.log(context)
  // don't do anything if the user that reopened it is the owner or maintainer
  // Check if this is a reopen event (action == 'reopened'), and 
  // if the sender (who performed the action) is owner or maintainer.
  if (
    context.action === 'reopened' &&
    ['OWNER', 'REPOSITORY_OWNER', 'MEMBER', 'COLLABORATOR', 'MAINTAINER'].includes(
      (context.sender_association || '').toUpperCase()
    )
  ) {
    return {
      matched: false,
      feature: '',
      reason: '',
      labels: [],
      lock_conversation: false,
      metadata: {},
    };
  }

  const content = getContent(context);
  const lowered = content.toLowerCase();
  const keywordsInput = core.getInput('auto-mod-keywords') || '';
  const keywords = parseCsv(keywordsInput).filter((keyword) =>
    lowered.includes(keyword.toLowerCase())
  );

  const maxLinks = parseIntSafe(core.getInput('auto-mod-max-links') || '3', 3);
  const links = content.match(LINK_PATTERN) || [];
  const linkCount = links.length;

  const reasons: string[] = [];
  if (keywords.length > 0) {
    reasons.push(`matched keywords: ${keywords.join(', ')}`);
  }
  if (maxLinks > 0 && linkCount >= maxLinks) {
    reasons.push(`contains ${linkCount} links (threshold: ${maxLinks})`);
  }

  if (reasons.length === 0) {
    return {
      matched: false,
      feature: '',
      reason: '',
      labels: [],
      lock_conversation: false,
      metadata: {},
    };
  }

  const result: FeatureResult = {
    matched: true,
    feature: 'auto-mod',
    reason: reasons.join('; '),
    labels: [core.getInput('auto-mod-label') || ''].filter((l) => l.length > 0),
    lock_conversation: false,
    metadata: {
      keywords: keywords.join(', '),
      link_count: linkCount.toString(),
    },
  };

  result.comment_message = renderTemplate(
    core.getInput('auto-mod-comment-message') || '',
    context,
    result
  );

  return result;
}

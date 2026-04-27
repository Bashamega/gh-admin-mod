import * as core from '@actions/core';
import { parseBool, parseIntSafe } from '../env.js';
import { countOpenItems } from '../github_api.js';
import { FeatureResult, ModerationContext } from '../models.js';
import { renderTemplate } from '../templates.js';

function parseLimits(rawLimits: string): Record<string, number> {
  const limits: Record<string, number> = {};
  for (const part of rawLimits.split(',')) {
    if (!part.includes('=')) continue;
    const [key, val] = part.split('=', 2);
    const parsedVal = parseInt(val.trim(), 10);
    if (!isNaN(parsedVal)) {
      limits[key.trim().toUpperCase()] = parsedVal;
    }
  }
  return limits;
}

export async function evaluate(context: ModerationContext): Promise<FeatureResult> {
  if (!parseBool(core.getInput('concurrency-enabled') || 'false')) {
    return {
      matched: false,
      feature: '',
      reason: '',
      labels: [],
      lock_conversation: false,
      metadata: {},
    };
  }

  const rawLimits =
    core.getInput('concurrency-limits') ||
    'NONE=1,FIRST_TIMER=1,FIRST_TIME_CONTRIBUTOR=1,CONTRIBUTOR=10,COLLABORATOR=10,MEMBER=10';
  const limits = parseLimits(rawLimits);

  const limit = limits[context.author_association.toUpperCase()];

  // If limit is 0, it means unlimited. If undefined, no limit defined for this association.
  if (limit === undefined || limit <= 0) {
    return {
      matched: false,
      feature: '',
      reason: '',
      labels: [],
      lock_conversation: false,
      metadata: {},
    };
  }

  const currentCount = await countOpenItems(context, context.author, context.item_type);

  if (currentCount <= limit) {
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
    feature: 'concurrency',
    reason:
      `@${context.author} has ${currentCount} open ${context.item_type_plural}, ` +
      `exceeding the limit of ${limit} for ${context.author_association}.`,
    labels: [],
    lock_conversation: false,
    metadata: {
      limit: limit.toString(),
      count: currentCount.toString(),
    },
  };

  const defaultComment =
    'This {type} was automatically closed because @{user} already has ' +
    '{count} open {type_plural}, exceeding the allowed limit of {limit}.';
  const commentTemplate = core.getInput('concurrency-comment-message') || defaultComment;
  result.comment_message = renderTemplate(commentTemplate, context, result);

  return result;
}

import * as fs from 'fs';
import * as path from 'path';
import * as core from '@actions/core';
import { getEnv, normalizeUser, parseBool } from '../env.js';
import { FeatureResult, ModerationContext } from '../models.js';
import { renderTemplate } from '../templates.js';

function loadBlockedUsers(blockedUsersFile: string): Set<string> {
  const workspace = getEnv('GITHUB_WORKSPACE');
  if (!workspace) {
    throw new Error('GITHUB_WORKSPACE is not available.');
  }

  const blocklistPath = path.resolve(workspace, blockedUsersFile);
  if (!fs.existsSync(blocklistPath)) {
    throw new Error(
      `Blocked users file not found at ${blocklistPath}. ` +
        'Make sure the repository is checked out before this action runs.'
    );
  }

  const blockedUsers = new Set<string>();
  const content = fs.readFileSync(blocklistPath, 'utf8');
  for (const rawLine of content.split('\n')) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) {
      continue;
    }
    blockedUsers.add(normalizeUser(line));
  }

  return blockedUsers;
}

export function evaluate(context: ModerationContext): FeatureResult {
  if (context.is_pull_request && !parseBool(core.getInput('block-prs') || 'true')) {
    return {
      matched: false,
      feature: '',
      reason: '',
      labels: [],
      lock_conversation: false,
      metadata: {},
    };
  }

  if (!context.is_pull_request && !parseBool(core.getInput('block-issues') || 'true')) {
    return {
      matched: false,
      feature: '',
      reason: '',
      labels: [],
      lock_conversation: false,
      metadata: {},
    };
  }

  const blockedUsers = loadBlockedUsers(core.getInput('blocked-users-file') || 'blockedUser.md');
  const normalizedAuthor = normalizeUser(context.author);

  if (!blockedUsers.has(normalizedAuthor)) {
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
    feature: 'blocklist',
    reason: `@${context.author} is listed in the blocked users file.`,
    blocked_user: context.author,
    labels: [],
    lock_conversation: false,
    metadata: {},
  };

  result.comment_message = renderTemplate(core.getInput('comment-message') || '', context, result);

  return result;
}

import * as core from '@actions/core';
import { loadContext } from './context.js';
import { parseBool, parseUpperSet } from './env.js';
import * as automod from './features/automod.js';
import * as blocklist from './features/blocklist.js';
import * as concurrency from './features/concurrency.js';
import { addLabels, closeItem, createComment, lockItem } from './github_api.js';
import { FeatureResult } from './models.js';

function initOutputs(): void {
  core.setOutput('blocked', 'false');
  core.setOutput('blocked-user', '');
  core.setOutput('item-type', '');
  core.setOutput('matched-feature', '');
  core.setOutput('match-reason', '');
}

function dedupeLabels(labels: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const label of labels) {
    if (!label || seen.has(label)) {
      continue;
    }
    seen.add(label);
    result.push(label);
  }
  return result;
}

function setMatchOutputs(result: FeatureResult): void {
  core.setOutput('matched-feature', result.feature);
  core.setOutput('match-reason', result.reason);
  if (result.feature === 'blocklist') {
    core.setOutput('blocked', 'true');
    core.setOutput('blocked-user', result.blocked_user || '');
  }
}

async function run(): Promise<void> {
  try {
    initOutputs();
    const context = loadContext();
    core.setOutput('item-type', context.item_type);

    if (!context.author) {
      core.notice(`Skipping ${context.item_type_label} because no author login was found.`);
      return;
    }

    const exemptAssociations = parseUpperSet(core.getInput('exempt-associations') || '');
    if (context.author_association && exemptAssociations.has(context.author_association)) {
      core.notice(
        `Skipping @${context.author} because author association ` +
          `${context.author_association} is exempt.`
      );
      return;
    }

    if (context.action === 'reopened' && exemptAssociations.has(context.sender_association)) {
      core.notice(
        `Skipping because ${context.item_type_label} was reopened by ` +
          `@{context.sender} (${context.sender_association}), who is exempt.`
      );
      return;
    }

    let result = blocklist.evaluate(context);
    if (!result.matched) {
      result = await concurrency.evaluate(context);
    }
    if (!result.matched) {
      result = automod.evaluate(context);
    }

    if (!result.matched) {
      core.notice(`No moderation feature matched for @${context.author}.`);
      return;
    }

    setMatchOutputs(result);

    if (parseBool(core.getInput('dry-run') || 'false')) {
      core.notice(
        `Dry run: feature ${result.feature} would close this ` +
          `${context.item_type_label} from @${context.author}.`
      );
      return;
    }

    const globalLabel = (core.getInput('add-label') || '').trim();
    const labels = dedupeLabels((globalLabel ? [globalLabel] : []).concat(result.labels));

    if (result.comment_message) {
      await createComment(context, result.comment_message);
    }

    if (labels.length > 0) {
      await addLabels(context, labels);
    }

    await closeItem(context, core.getInput('close-reason') || 'not_planned');

    const shouldLock =
      parseBool(core.getInput('lock-conversation') || 'false') || result.lock_conversation;
    if (shouldLock) {
      await lockItem(context);
    }

    core.notice(
      `Closed ${context.item_type_label} #${context.issue_number} from ` +
        `@${context.author} using feature ${result.feature}.`
    );
  } catch (error) {
    if (error instanceof Error) {
      core.setFailed(error.message);
    } else {
      core.setFailed(String(error));
    }
  }
}

run();

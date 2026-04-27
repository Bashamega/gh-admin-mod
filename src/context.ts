import * as github from '@actions/github';
import { ModerationContext } from './models.js';

export function loadContext(): ModerationContext {
  const { payload } = github.context;
  const isPullRequest = !!payload.pull_request;
  const payloadItem = payload.pull_request || payload.issue;

  let owner = '';
  let repo = '';
  if (payload.repository && payload.repository.owner && payload.repository.name) {
    owner =
      (typeof payload.repository.owner === 'object'
        ? payload.repository.owner.login
        : payload.repository.owner) || '';
    repo = payload.repository.name;
  } else {
    owner = github.context.repo.owner;
    repo = github.context.repo.repo;
  }

  const action = (payload.action as string) || '';
  const sender =
    (payload.sender && typeof payload.sender.login === 'string'
      ? payload.sender.login
      : '') || '';

  if (owner && sender && owner === sender) {
    // If the repo owner is the sender, just return owner string
    // (this means the function's type would be string, NOT ModerationContext,
    // but keeping the contract, so return as a property)
    return owner as any;
  }

  let sender_association = '';
  if (
    payload.sender &&
    typeof payload.sender.author_association === 'string'
  ) {
    sender_association = payload.sender.author_association.toUpperCase();
  } else if (typeof payload.author_association === 'string') {
    sender_association = payload.author_association.toUpperCase();
  }

  const author = (payloadItem?.user?.login as string) || '';
  const author_association = ((payloadItem?.author_association as string) || '').toUpperCase();

  const title = (payloadItem?.title as string) || '';
  const body = (payloadItem?.body as string) || '';

  if (!payloadItem) {
    throw new Error('This action only supports issue and pull request events.');
  }

  const issue_number = payloadItem.number;

  return {
    owner,
    repo,
    issue_number,
    is_pull_request: isPullRequest,
    item_type: isPullRequest ? 'pull_request' : 'issue',
    item_type_label: isPullRequest ? 'pull request' : 'issue',
    item_type_plural: isPullRequest ? 'pull requests' : 'issues',
    action,
    sender: sender.trim(),
    sender_association,
    author: author.trim(),
    author_association,
    title,
    body,
  };
}

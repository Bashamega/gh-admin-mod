import * as github from '@actions/github';
import { ModerationContext } from './models.js';

export function loadContext(): ModerationContext {
  const { payload } = github.context;
  const issue = payload.issue;
  const pullRequest = payload.pull_request;
  const payloadItem = issue || pullRequest;

  if (!payloadItem) {
    throw new Error('This action only supports issue and pull request events.');
  }

  const { owner, repo } = github.context.repo;
  const isPullRequest = !!pullRequest;

  const senderAssociation = (
    (payload.author_association as string) ||
    (payload.sender?.author_association as string) ||
    ''
  ).toUpperCase();

  return {
    owner,
    repo,
    issue_number: payloadItem.number,
    is_pull_request: isPullRequest,
    item_type: isPullRequest ? 'pull_request' : 'issue',
    item_type_label: isPullRequest ? 'pull request' : 'issue',
    item_type_plural: isPullRequest ? 'pull requests' : 'issues',
    action: (payload.action as string) || '',
    sender: ((payload.sender?.login as string) || '').trim(),
    sender_association: senderAssociation,
    author: ((payloadItem.user?.login as string) || '').trim(),
    author_association: ((payloadItem.author_association as string) || '').toUpperCase(),
    title: (payloadItem.title as string) || '',
    body: (payloadItem.body as string) || '',
  };
}

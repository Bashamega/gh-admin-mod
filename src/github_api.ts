import * as core from '@actions/core';
import * as github from '@actions/github';
import { ModerationContext } from './models.js';

function getOctokit() {
  const token = core.getInput('GITHUB_TOKEN', { required: false }) || process.env.GITHUB_TOKEN;
  if (!token) {
    throw new Error('GITHUB_TOKEN is not available.');
  }
  return github.getOctokit(token);
}

export async function createComment(context: ModerationContext, body: string): Promise<void> {
  const octokit = getOctokit();
  await octokit.rest.issues.createComment({
    owner: context.owner,
    repo: context.repo,
    issue_number: context.issue_number,
    body,
  });
}

export async function addLabels(context: ModerationContext, labels: string[]): Promise<void> {
  if (labels.length === 0) return;
  const octokit = getOctokit();
  await octokit.rest.issues.addLabels({
    owner: context.owner,
    repo: context.repo,
    issue_number: context.issue_number,
    labels,
  });
}

export async function closeItem(context: ModerationContext, closeReason: string): Promise<void> {
  const octokit = getOctokit();
  if (context.is_pull_request) {
    await octokit.rest.pulls.update({
      owner: context.owner,
      repo: context.repo,
      pull_number: context.issue_number,
      state: 'closed',
    });
  } else {
    await octokit.rest.issues.update({
      owner: context.owner,
      repo: context.repo,
      issue_number: context.issue_number,
      state: 'closed',
      state_reason: closeReason as any, // 'completed' or 'not_planned'
    });
  }
}

export async function lockItem(context: ModerationContext): Promise<void> {
  const octokit = getOctokit();
  await octokit.rest.issues.lock({
    owner: context.owner,
    repo: context.repo,
    issue_number: context.issue_number,
    lock_reason: 'resolved',
  });
}

export async function countOpenItems(
  context: ModerationContext,
  author: string,
  itemType: string
): Promise<number> {
  const octokit = getOctokit();
  const query = `repo:${context.owner}/${context.repo} type:${itemType} state:open author:${author}`;
  const { data } = await octokit.rest.search.issuesAndPullRequests({
    q: query,
  });
  return data.total_count;
}

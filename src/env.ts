import * as core from '@actions/core';

export function getEnv(name: string, defaultValue: string = ''): string {
  return process.env[name] || defaultValue;
}

export function parseBool(value: string | boolean | undefined): boolean {
  if (typeof value === 'boolean') return value;
  if (!value) return false;
  return value.trim().toLowerCase() === 'true';
}

export function parseIntSafe(value: string | undefined, defaultValue: number): number {
  if (!value) return defaultValue;
  const parsed = parseInt(value.trim(), 10);
  return isNaN(parsed) ? defaultValue : parsed;
}

export function parseCsv(value: string | undefined): string[] {
  if (!value) return [];
  return value
    .split(',')
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

export function parseUpperSet(value: string | undefined): Set<string> {
  return new Set(parseCsv(value).map((item) => item.toUpperCase()));
}

export function normalizeUser(value: string): string {
  return value.trim().replace(/^@/, '').toLowerCase();
}

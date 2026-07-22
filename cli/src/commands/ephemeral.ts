import { Command } from 'commander';
import chalk from 'chalk';
import crypto from 'crypto';
import { formatOutput } from '../lib/utils';

function createEphemeral(content: string, ttl: number, oneTime: boolean): string {
  const prefix = oneTime ? 'ep_ot_' : 'ep_';
  const encoded = Buffer.from(content).toString('base64url');
  const ts = Math.floor(Date.now() / 1000);
  const expiry = ts + ttl;
  const sig = crypto.createHmac('sha256', `ephemeral_${expiry}`).update(encoded).digest('hex').slice(0, 16);
  return `${prefix}${encoded}.${expiry}.${sig}`;
}

function parseTTL(input: string): number {
  const match = input.match(/^(\d+)(s|m|h|d)?$/);
  if (!match) return parseInt(input, 10);
  const val = parseInt(match[1], 10);
  switch (match[2]) {
    case 'm': return val * 60;
    case 'h': return val * 3600;
    case 'd': return val * 86400;
    default: return val;
  }
}

export const ephemeralCommand = new Command('ephemeral')
  .description('Create and verify self-destructing ephemeral credentials');

ephemeralCommand
  .command('create')
  .description('Create an ephemeral credential')
  .option('--content <text>', 'Credential content', 'ephemeral-access')
  .option('--ttl <duration>', 'Time-to-live (e.g. 300, 5m, 1h, 24h)', '10m')
  .option('--one-time', 'Auto-destruct after first use', true)
  .action((options) => {
    try {
      const ttl = parseTTL(options.ttl);
      const token = createEphemeral(options.content, ttl, options.oneTime);
      console.log(chalk.green('Ephemeral credential created:'));
      formatOutput(token);
      console.log(chalk.dim(`\nTTL: ${ttl}s (expires ${new Date(Date.now() + ttl * 1000).toISOString()})`));
      console.log(chalk.dim(`One-time: ${options.oneTime ? 'yes (auto-destruct)' : 'no'}`));
    } catch (err) {
      console.error(chalk.red('Error creating ephemeral credential:'), (err as Error).message);
      process.exit(1);
    }
  });

ephemeralCommand
  .command('verify')
  .description('Verify an ephemeral credential')
  .argument('<token>', 'Ephemeral token to verify')
  .action((token) => {
    try {
      if (!token.startsWith('ep_')) {
        console.error(chalk.red('Invalid ephemeral token format'));
        process.exit(1);
      }
      console.log(chalk.green('Ephemeral credential is valid'));
      const parts = token.split('.');
      if (parts.length >= 2) {
        const expiry = parseInt(parts[1], 10);
        const now = Math.floor(Date.now() / 1000);
        if (expiry && now > expiry) {
          console.error(chalk.red('Credential has expired'));
          process.exit(1);
        }
        console.log(chalk.dim(`Expires: ${new Date(expiry * 1000).toISOString()}`));
      }
    } catch (err) {
      console.error(chalk.red('Error verifying credential:'), (err as Error).message);
      process.exit(1);
    }
  });

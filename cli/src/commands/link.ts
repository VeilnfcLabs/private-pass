import { Command } from 'commander';
import chalk from 'chalk';
import { formatOutput } from '../lib/utils';

function generateLink(resource: string, ttl?: number, oneTime?: boolean, maxUses?: number): string {
  const baseUrl = 'https://veilpass.io/claim';
  const params = new URLSearchParams({ r: resource });
  const expiry = ttl ? Math.floor(Date.now() / 1000) + ttl : undefined;
  if (expiry) params.set('exp', String(expiry));
  if (oneTime) params.set('ot', 'true');
  if (maxUses) params.set('mu', String(maxUses));
  const sig = `sig_${Buffer.from(`${resource}:${expiry || ''}:${oneTime || ''}:${maxUses || ''}`).toString('base64url').slice(0, 16)}`;
  params.set('s', sig);
  return `${baseUrl}?${params.toString()}`;
}

export const linkCommand = new Command('link')
  .description('Create and verify secure claim links');

linkCommand
  .command('create')
  .description('Create a secure claim link')
  .argument('<resource>', 'Resource identifier')
  .option('--ttl <seconds>', 'Time-to-live in seconds', '3600')
  .option('--one-time', 'One-time use link')
  .option('--max-uses <count>', 'Maximum number of uses', '1')
  .action((resource, options) => {
    const ttl = parseInt(options.ttl, 10);
    const maxUses = parseInt(options.maxUses, 10);
    const url = generateLink(resource, ttl, options.oneTime, maxUses);
    console.log(chalk.green('Secure claim link:'));
    formatOutput(url);
    console.log(chalk.dim(`\nResource: ${resource}`));
    console.log(chalk.dim(`TTL: ${ttl}s`));
    if (options.oneTime) console.log(chalk.dim('One-time: yes'));
    console.log(chalk.dim(`Max uses: ${maxUses}`));
    console.log(chalk.dim(`Expires: ${new Date(Date.now() + ttl * 1000).toISOString()}`));
  });

linkCommand
  .command('verify')
  .description('Verify a claim link')
  .argument('<url>', 'Claim URL to verify')
  .action((url) => {
    try {
      const parsed = new URL(url);
      const r = parsed.searchParams.get('r');
      const exp = parsed.searchParams.get('exp');
      const sig = parsed.searchParams.get('s');
      const ot = parsed.searchParams.get('ot');
      const mu = parsed.searchParams.get('mu');

      if (!r || !sig) {
        console.log(chalk.red('Invalid link: missing required parameters'));
        process.exit(1);
      }

      const now = Math.floor(Date.now() / 1000);
      const expired = exp ? parseInt(exp, 10) < now : false;

      const result = {
        valid: !expired,
        expired,
        resource: r,
        one_time: ot === 'true',
        max_uses: mu ? parseInt(mu, 10) : null,
        signature: sig,
        timestamp: new Date().toISOString(),
      };

      if (result.valid) {
        console.log(chalk.green('Link is valid'));
      } else {
        console.log(chalk.red('Link has expired'));
      }
      formatOutput(JSON.stringify(result, null, 2));
    } catch (err) {
      console.error(chalk.red('Error verifying link:'), (err as Error).message);
      process.exit(1);
    }
  });

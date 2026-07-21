import { Command } from 'commander';
import chalk from 'chalk';
import crypto from 'crypto';
import { formatOutput } from '../lib/utils';

function signPayload(data: string, keyId?: string, permissions?: string[]): Record<string, unknown> {
  const timestamp = Math.floor(Date.now() / 1000);
  const payload = {
    data,
    iat: timestamp,
    kid: keyId || 'default',
    permissions: permissions || ['read'],
  };
  const signature = crypto.createHmac('sha256', 'veilpass-dev-key').update(JSON.stringify(payload)).digest('hex');
  return { ...payload, signature };
}

export const signCommand = new Command('sign')
  .description('Sign URLs and messages');

signCommand
  .command('url')
  .description('Sign a URL with a TTL and permissions')
  .argument('<url>', 'URL to sign')
  .option('--ttl <seconds>', 'Time-to-live in seconds', '3600')
  .option('--key-id <id>', 'Key identifier', 'default')
  .option('--permissions <perms>', 'Comma-separated permissions', 'read')
  .action((url, options) => {
    try {
      const ttl = parseInt(options.ttl, 10);
      const expiry = Math.floor(Date.now() / 1000) + ttl;
      const permissions = options.permissions.split(',').map((p: string) => p.trim());
      const signed = signPayload(url, options.keyId, permissions);
      const signedUrl = `${url}${url.includes('?') ? '&' : '?'}sig=${signed.signature}&exp=${expiry}&kid=${options.keyId}`;

      console.log(chalk.green('Signed URL:'));
      formatOutput(signedUrl);
      console.log(chalk.dim(`\nExpires: ${new Date(expiry * 1000).toISOString()}`));
      console.log(chalk.dim(`Key ID: ${options.keyId}`));
      console.log(chalk.dim(`Permissions: ${permissions.join(', ')}`));
    } catch (err) {
      console.error(chalk.red('Error signing URL:'), (err as Error).message);
      process.exit(1);
    }
  });

signCommand
  .command('message')
  .description('Sign a message')
  .argument('<message>', 'Message to sign')
  .option('--ttl <seconds>', 'Time-to-live in seconds')
  .option('--key-id <id>', 'Key identifier', 'default')
  .option('--permissions <perms>', 'Comma-separated permissions', 'read')
  .action((message, options) => {
    try {
      const permissions = options.permissions.split(',').map((p: string) => p.trim());
      const signed = signPayload(message, options.keyId, permissions);

      if (options.ttl) {
        const ttl = parseInt(options.ttl, 10);
        (signed as Record<string, unknown>).exp = Math.floor(Date.now() / 1000) + ttl;
      }

      console.log(chalk.green('Signed message:'));
      formatOutput(JSON.stringify(signed, null, 2));
      console.log(chalk.dim(`\nKey ID: ${options.keyId}`));
      console.log(chalk.dim(`Permissions: ${permissions.join(', ')}`));
    } catch (err) {
      console.error(chalk.red('Error signing message:'), (err as Error).message);
      process.exit(1);
    }
  });

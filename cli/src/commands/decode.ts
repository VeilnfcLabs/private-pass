import { Command } from 'commander';
import chalk from 'chalk';
import { formatOutput } from '../lib/utils';

function base64UrlDecode(str: string): string {
  return Buffer.from(str, 'base64url').toString('utf-8');
}

export const decodeCommand = new Command('decode')
  .description('Decode JWT tokens')
  .argument('<token>', 'JWT token to decode')
  .action((token: string) => {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) {
        console.error(chalk.red('Invalid token: expected a JWT with 3 parts (header.payload.signature)'));
        process.exit(1);
      }

      const headerRaw = base64UrlDecode(parts[0]);
      const payloadRaw = base64UrlDecode(parts[1]);

      let header: Record<string, unknown>;
      let payload: Record<string, unknown>;

      try {
        header = JSON.parse(headerRaw);
      } catch {
        header = { raw: headerRaw };
      }

      try {
        payload = JSON.parse(payloadRaw);
      } catch {
        payload = { raw: payloadRaw };
      }

      const decoded = {
        header: {
          raw: parts[0],
          parsed: header,
        },
        payload: {
          raw: parts[1],
          parsed: payload,
        },
        signature: {
          raw: parts[2],
          preview: parts[2].slice(0, 32) + '...',
        },
      };

      console.log(chalk.cyan('=== JWT Header ==='));
      formatOutput(JSON.stringify(header, null, 2));

      console.log(chalk.cyan('\n=== JWT Payload ==='));
      formatOutput(JSON.stringify(payload, null, 2));

      console.log(chalk.cyan('\n=== JWT Signature ==='));
      console.log(chalk.dim(`Algorithm: ${(header as Record<string, string>).alg || 'unknown'}`));
      console.log(chalk.dim(`Type: ${(header as Record<string, string>).typ || 'unknown'}`));
      console.log(chalk.dim(`Signature (preview): ${parts[2].slice(0, 32)}...`));

      if (payload.exp) {
        const expDate = new Date((payload.exp as number) * 1000);
        const now = Date.now();
        const expired = now > expDate.getTime();
        console.log(chalk[expired ? 'red' : 'green'](`\nExpires: ${expDate.toISOString()} ${expired ? '(EXPIRED)' : '(valid)'}`));
      }
      if (payload.iat) {
        console.log(chalk.dim(`Issued: ${new Date((payload.iat as number) * 1000).toISOString()}`));
      }
      if (payload.iss) {
        console.log(chalk.dim(`Issuer: ${payload.iss}`));
      }
      if (payload.sub) {
        console.log(chalk.dim(`Subject: ${payload.sub}`));
      }
      if (payload.aud) {
        console.log(chalk.dim(`Audience: ${payload.aud}`));
      }
    } catch (err) {
      console.error(chalk.red('Error decoding token:'), (err as Error).message);
      process.exit(1);
    }
  });

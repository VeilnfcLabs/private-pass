import { Command } from 'commander';
import chalk from 'chalk';
import crypto from 'crypto';
import { formatOutput } from '../lib/utils';

function base64UrlEncode(data: string): string {
  return Buffer.from(data).toString('base64url');
}

function base64UrlDecode(str: string): string {
  return Buffer.from(str, 'base64url').toString('utf-8');
}

function createToken(sub: string, aud: string, iss: string, ttl: number, extraClaims: Record<string, unknown>, secret?: string): string {
  const header = { alg: 'HS256', typ: 'JWT' };
  const now = Math.floor(Date.now() / 1000);
  const payload: Record<string, unknown> = {
    sub,
    aud,
    iss,
    iat: now,
    exp: now + ttl,
    jti: crypto.randomUUID(),
    ...extraClaims,
  };
  const headerEnc = base64UrlEncode(JSON.stringify(header));
  const payloadEnc = base64UrlEncode(JSON.stringify(payload));
  const signingKey = secret || process.env.VEILPASS_SIGNING_KEY || crypto.randomBytes(32).toString('hex');
  const signature = crypto.createHmac('sha256', signingKey)
    .update(`${headerEnc}.${payloadEnc}`)
    .digest('base64url');
  return `${headerEnc}.${payloadEnc}.${signature}`;
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

export const tokenCommand = new Command('token')
  .description('Create and decode time-limited tokens');

tokenCommand
  .command('create')
  .description('Create a new token')
  .option('--sub <subject>', 'Token subject', 'user')
  .option('--aud <audience>', 'Token audience', 'veilpass-api')
  .option('--iss <issuer>', 'Token issuer', 'veilpass-cli')
  .option('--ttl <duration>', 'Time-to-live (e.g. 3600, 1h, 7d)', '1h')
  .option('--claims <json>', 'Additional claims as JSON string')
  .action((options) => {
    try {
      const ttl = parseTTL(options.ttl);
      const extraClaims = options.claims ? JSON.parse(options.claims) : {};
      if (typeof extraClaims !== 'object' || extraClaims === null) {
        throw new Error('Claims must be a JSON object');
      }
      const token = createToken(options.sub, options.aud, options.iss, ttl, extraClaims);
      console.log(chalk.green('Token created:'));
      formatOutput(token);
      console.log(chalk.dim(`\nSubject: ${options.sub}`));
      console.log(chalk.dim(`Audience: ${options.aud}`));
      console.log(chalk.dim(`Issuer: ${options.iss}`));
      console.log(chalk.dim(`TTL: ${ttl}s`));
      console.log(chalk.dim(`Expires: ${new Date(Date.now() + ttl * 1000).toISOString()}`));
    } catch (err) {
      console.error(chalk.red('Error creating token:'), (err as Error).message);
      process.exit(1);
    }
  });

tokenCommand
  .command('decode')
  .description('Decode a token without verification')
  .argument('<token>', 'JWT token to decode')
  .action((token) => {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) {
        console.error(chalk.red('Invalid token format: expected 3-part JWT'));
        process.exit(1);
      }
      const header = JSON.parse(base64UrlDecode(parts[0]));
      const payload = JSON.parse(base64UrlDecode(parts[1]));
      const result = {
        header,
        payload,
        signature: parts[2].slice(0, 32) + '...',
      };
      console.log(chalk.green('Decoded token:'));
      formatOutput(JSON.stringify(result, null, 2));
    } catch (err) {
      console.error(chalk.red('Error decoding token:'), (err as Error).message);
      process.exit(1);
    }
  });

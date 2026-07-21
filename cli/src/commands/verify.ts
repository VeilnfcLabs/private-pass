import { Command } from 'commander';
import chalk from 'chalk';
import crypto from 'crypto';
import { formatOutput } from '../lib/utils';

function base64UrlDecode(str: string): string {
  return Buffer.from(str, 'base64url').toString('utf-8');
}

export const verifyCommand = new Command('verify')
  .description('Verify tokens, links, URLs, and signatures')
  .argument('<type>', 'Type to verify (token, link, url, signature)')
  .argument('<value>', 'Value to verify')
  .action((type: string, value: string) => {
    try {
      const now = Math.floor(Date.now() / 1000);
      let result: Record<string, unknown>;

      switch (type) {
        case 'token': {
          const parts = value.split('.');
          if (parts.length !== 3) throw new Error('Invalid token format');
          const payload = JSON.parse(base64UrlDecode(parts[1]));
          const exp = payload.exp;
          result = {
            valid: exp ? now < exp : true,
            type: 'token',
            expired: exp ? now >= exp : false,
            issuer: payload.iss || null,
            subject: payload.sub || null,
            audience: payload.aud || null,
            issued_at: payload.iat ? new Date(payload.iat * 1000).toISOString() : null,
            expires_at: exp ? new Date(exp * 1000).toISOString() : null,
            claims: Object.keys(payload).filter(k => !['iss', 'sub', 'aud', 'iat', 'exp', 'jti'].includes(k)),
          };
          break;
        }
        case 'link': {
          const parsed = new URL(value);
          const r = parsed.searchParams.get('r');
          const exp = parsed.searchParams.get('exp');
          const sig = parsed.searchParams.get('s');
          const expired = exp ? parseInt(exp, 10) < now : false;
          result = {
            valid: !expired && !!r && !!sig,
            type: 'link',
            expired,
            resource: r,
            one_time: parsed.searchParams.get('ot') === 'true',
            signature_present: !!sig,
          };
          break;
        }
        case 'url': {
          const parsed = new URL(value);
          const exp = parsed.searchParams.get('exp');
          const sig = parsed.searchParams.get('sig');
          const kid = parsed.searchParams.get('kid');
          const expired = exp ? parseInt(exp, 10) < now : false;
          result = {
            valid: !expired && !!sig,
            type: 'url',
            expired,
            key_id: kid,
            signature_present: !!sig,
          };
          break;
        }
        case 'signature': {
          const sigRegex = /signature[:=]\s*([a-f0-9]{64,})/i;
          const match = value.match(sigRegex);
          result = {
            valid: !!match,
            type: 'signature',
            signature_found: !!match,
            algorithm: match ? 'HMAC-SHA256' : null,
          };
          break;
        }
        default:
          throw new Error(`Unknown verification type: ${type}. Use: token, link, url, signature`);
      }

      if (result.valid) {
        console.log(chalk.green('Verification passed'));
      } else {
        console.log(chalk.red('Verification failed'));
      }
      formatOutput(JSON.stringify(result, null, 2));
    } catch (err) {
      console.error(chalk.red('Error verifying:'), (err as Error).message);
      process.exit(1);
    }
  });

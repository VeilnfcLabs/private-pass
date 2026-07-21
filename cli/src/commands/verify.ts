import { Command } from 'commander';
import chalk from 'chalk';
import crypto from 'crypto';
import { formatOutput } from '../lib/utils';
import VeilPassAPI from '../lib/api';

function base64UrlDecode(str: string): string {
  return Buffer.from(str, 'base64url').toString('utf-8');
}

function padB64(s: string): string {
  return s + '='.repeat((4 - s.length % 4) % 4);
}

export const verifyCommand = new Command('verify')
  .description('Verify tokens, signed links, and signed URLs')
  .argument('<type>', 'Type to verify (token, link, url)')
  .argument('<value>', 'Value to verify')
  .option('--api <url>', 'API base URL for remote verification')
  .action(async (type: string, value: string, options: { api?: string }) => {
    try {
      if (options.api) {
        const api = new VeilPassAPI({ baseURL: options.api });
        const result = await api.verifyItem({ type, value });
        if (result.valid) {
          console.log(chalk.green('✓ Verification passed'));
        } else {
          console.log(chalk.red('✗ Verification failed'));
        }
        formatOutput(JSON.stringify(result, null, 2));
        return;
      }

      const now = Math.floor(Date.now() / 1000);
      let result: Record<string, unknown>;

      switch (type) {
        case 'token': {
          const parts = value.split('.');
          if (parts.length !== 3) throw new Error('Invalid JWT token format');
          let payload: Record<string, unknown>;
          try {
            payload = JSON.parse(base64UrlDecode(parts[1]));
          } catch {
            throw new Error('Failed to decode token payload');
          }
          const exp = payload.exp as number | undefined;
          const expired = exp ? now >= exp : false;
          result = {
            valid: !expired,
            type: 'token',
            expired,
            issuer: payload.iss || null,
            subject: payload.sub || null,
            audience: payload.aud || null,
            issued_at: payload.iat ? new Date((payload.iat as number) * 1000).toISOString() : null,
            expires_at: exp ? new Date(exp * 1000).toISOString() : null,
            claims: Object.keys(payload).filter(k => !['iss', 'sub', 'aud', 'iat', 'exp', 'jti', 'nbf'].includes(k)),
          };
          break;
        }
        case 'link': {
          const parts = value.split('.');
          if (parts.length !== 2) throw new Error('Invalid signed-link format (expected payload.signature)');
          let payload: Record<string, unknown>;
          try {
            const decoded = base64UrlDecode(padB64(parts[0]));
            payload = JSON.parse(decoded);
          } catch {
            throw new Error('Failed to decode signed-link payload');
          }
          const expStr = payload.exp as string | undefined;
          const expired = expStr ? new Date(expStr).getTime() < Date.now() : false;
          result = {
            valid: !expired,
            type: 'signed-link',
            expired,
            resource: payload.resource || null,
            one_time: payload.one_time || false,
            max_uses: payload.max_uses || null,
            issuer: payload.issuer || 'veilpass',
            issued_at: payload.iat || null,
            signature_present: !!parts[1],
          };
          break;
        }
        case 'url': {
          const parsed = new URL(value);
          const expires = parsed.searchParams.get('expires');
          const signature = parsed.searchParams.get('signature');
          const keyId = parsed.searchParams.get('key_id');
          const expired = expires ? parseInt(expires, 10) < now : false;
          result = {
            valid: !expired && !!signature,
            type: 'signed-url',
            expired,
            key_id: keyId || null,
            signature_present: !!signature,
            expires_at: expires ? new Date(parseInt(expires, 10) * 1000).toISOString() : null,
          };
          break;
        }
        default:
          throw new Error(`Unknown type: ${type}. Use: token, link, url`);
      }

      if (result.valid) {
        console.log(chalk.green('✓ Verification passed'));
      } else {
        console.log(chalk.red('✗ Verification failed'));
      }
      formatOutput(JSON.stringify(result, null, 2));
    } catch (err) {
      console.error(chalk.red('Verification error:'), (err as Error).message);
      process.exit(1);
    }
  });

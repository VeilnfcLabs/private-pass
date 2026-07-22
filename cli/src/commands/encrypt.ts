import { Command } from 'commander';
import chalk from 'chalk';
import crypto from 'crypto';
import { formatOutput } from '../lib/utils';

function encryptPayload(plaintext: string, password: string): { ciphertext: string; nonce: string; tag: string; qrPayload: string; nfcPayload: string } {
  const key = crypto.createHash('sha256').update(password).digest();
  const nonce = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv('aes-256-gcm', key, nonce);
  let ciphertext = cipher.update(plaintext, 'utf8', 'hex');
  ciphertext += cipher.final('hex');
  const tag = cipher.getAuthTag().toString('hex');
  const nonceHex = nonce.toString('hex');
  const prefix = Buffer.from(plaintext).toString('base64url').slice(0, 16);
  return {
    ciphertext,
    nonce: nonceHex,
    tag,
    qrPayload: `vp_enc_qr_${prefix}`,
    nfcPayload: `vp_enc_nfc_${prefix}`,
  };
}

function decryptPayload(ciphertext: string, password: string, nonceHex: string, tagHex: string): string | null {
  try {
    const key = crypto.createHash('sha256').update(password).digest();
    const nonce = Buffer.from(nonceHex, 'hex');
    const tag = Buffer.from(tagHex, 'hex');
    const decipher = crypto.createDecipheriv('aes-256-gcm', key, nonce);
    decipher.setAuthTag(tag);
    let plain = decipher.update(ciphertext, 'hex', 'utf8');
    plain += decipher.final('utf8');
    return plain;
  } catch {
    return null;
  }
}

export const encryptCommand = new Command('encrypt')
  .description('Hybrid NFC+QR encrypted payloads using AES-256-GCM');

encryptCommand
  .command('create')
  .description('Encrypt content for QR and NFC')
  .option('--content <text>', 'Content to encrypt')
  .option('--password <password>', 'Encryption password')
  .action((options) => {
    try {
      if (!options.content || !options.password) {
        throw new Error('--content and --password are required');
      }
      const result = encryptPayload(options.content, options.password);
      console.log(chalk.green('Encrypted payload created:'));
      console.log(chalk.dim('  QR Payload:'), result.qrPayload);
      console.log(chalk.dim('  NFC Payload:'), result.nfcPayload);
      console.log('');
      formatOutput(JSON.stringify({ ciphertext: result.ciphertext, nonce: result.nonce, tag: result.tag }, null, 2));
      console.log(chalk.dim('\nKeep the password safe. Without it, the data cannot be decrypted.'));
    } catch (err) {
      console.error(chalk.red('Error encrypting payload:'), (err as Error).message);
      process.exit(1);
    }
  });

encryptCommand
  .command('decrypt')
  .description('Decrypt an encrypted payload')
  .option('--ciphertext <hex>', 'Ciphertext in hex')
  .option('--password <password>', 'Decryption password')
  .option('--nonce <hex>', 'Nonce in hex')
  .option('--tag <hex>', 'Auth tag in hex')
  .action((options) => {
    try {
      if (!options.ciphertext || !options.password || !options.nonce || !options.tag) {
        throw new Error('--ciphertext, --password, --nonce, and --tag are all required');
      }
      const result = decryptPayload(options.ciphertext, options.password, options.nonce, options.tag);
      if (result) {
        console.log(chalk.green('Decrypted successfully:'));
        formatOutput(result);
      } else {
        console.error(chalk.red('Decryption failed: wrong password or corrupted data'));
        process.exit(1);
      }
    } catch (err) {
      console.error(chalk.red('Error decrypting payload:'), (err as Error).message);
      process.exit(1);
    }
  });

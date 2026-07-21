import { Command } from 'commander';
import chalk from 'chalk';
import { writeFile, formatOutput } from '../lib/utils';

interface NFCPayload {
  type: string;
  payload: string;
  issuer?: string;
  version?: string;
  created: string;
}

function toHex(str: string): string {
  return Buffer.from(str, 'utf-8').toString('hex');
}

function toBase64(str: string): string {
  return Buffer.from(str, 'utf-8').toString('base64');
}

function toNDEF(payload: NFCPayload): string {
  const json = JSON.stringify(payload);
  const payloadBytes = Buffer.from(json, 'utf-8');
  const tnf = 0x01;
  const typeBytes = Buffer.from('U', 'utf-8');
  const idBytes = Buffer.from('0', 'utf-8');
  const ndef: number[] = [];
  ndef.push((tnf << 4) | 0x00);
  ndef.push(typeBytes.length);
  ndef.push(payloadBytes.length);
  ndef.push(idBytes.length);
  ndef.push(...typeBytes);
  ndef.push(...idBytes);
  ndef.push(...payloadBytes);
  return Buffer.from(ndef).toString('hex');
}

export const nfcCommand = new Command('nfc')
  .description('Generate NFC payloads')
  .option('-t, --type <type>', 'NFC record type (text, uri, smartposter, app)', 'text')
  .option('-p, --payload <payload>', 'Payload content')
  .option('-i, --issuer <issuer>', 'Issuer identifier')
  .option('--version <version>', 'Payload version', '1.0')
  .option('-o, --output <path>', 'Output file path')
  .option('-f, --format <format>', 'Output format (json, hex, base64, ndef)', 'json')
  .action(async (options) => {
    try {
      const payload: NFCPayload = {
        type: options.type,
        payload: options.payload || 'veilpass://auth',
        issuer: options.issuer,
        version: options.version,
        created: new Date().toISOString(),
      };

      let output: string;
      let ext: string;

      switch (options.format) {
        case 'hex':
          output = toHex(JSON.stringify(payload));
          ext = '.hex';
          break;
        case 'base64':
          output = toBase64(JSON.stringify(payload));
          ext = '.b64';
          break;
        case 'ndef':
          output = toNDEF(payload);
          ext = '.ndef';
          break;
        default:
          output = JSON.stringify(payload, null, 2);
          ext = '.json';
          break;
      }

      if (options.output) {
        await writeFile(options.output, output);
        console.log(chalk.green(`NFC payload saved to ${options.output}`));
      } else {
        formatOutput(output);
      }

      console.log(chalk.dim(`\nType: ${options.type}`));
      console.log(chalk.dim(`Format: ${options.format}`));
      console.log(chalk.dim(`Length: ${output.length} characters`));
    } catch (err) {
      console.error(chalk.red('Error generating NFC payload:'), (err as Error).message);
      process.exit(1);
    }
  });

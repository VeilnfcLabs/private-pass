import { Command } from 'commander';
import chalk from 'chalk';
import crypto from 'crypto';
import fs from 'fs/promises';
import path from 'path';
import os from 'os';
import Table from 'cli-table3';
import { formatOutput } from '../lib/utils';

function getKeyDir(): string {
  const keyDir = path.join(os.homedir(), '.veilpass', 'keys');
  return keyDir;
}

async function ensureKeyDir(): Promise<string> {
  const keyDir = getKeyDir();
  await fs.mkdir(keyDir, { recursive: true });
  return keyDir;
}

interface KeyEntry {
  id: string;
  algorithm: string;
  created: string;
  fingerprint: string;
}

export const keyCommand = new Command('key')
  .description('Manage signing keys');

keyCommand
  .command('init')
  .description('Initialize a new key pair')
  .action(async () => {
    try {
      const keyDir = await ensureKeyDir();
      const keyId = `vk-${Date.now().toString(36)}-${crypto.randomBytes(4).toString('hex')}`;
      const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
        modulusLength: 2048,
        publicKeyEncoding: { type: 'spki', format: 'pem' },
        privateKeyEncoding: { type: 'pkcs8', format: 'pem' },
      });

      const fingerprint = crypto.createHash('sha256').update(publicKey).digest('hex').slice(0, 16);
      const keyEntry: KeyEntry = {
        id: keyId,
        algorithm: 'RSA-2048',
        created: new Date().toISOString(),
        fingerprint,
      };

      await fs.writeFile(path.join(keyDir, `${keyId}.pub`), publicKey, 'utf-8');
      await fs.writeFile(path.join(keyDir, `${keyId}.priv`), privateKey, 'utf-8');
      await fs.writeFile(path.join(keyDir, `${keyId}.meta.json`), JSON.stringify(keyEntry, null, 2), 'utf-8');

      console.log(chalk.green('Key pair generated:'));
      formatOutput(JSON.stringify(keyEntry, null, 2));
      console.log(chalk.dim(`\nPublic key:  ${keyDir}\\${keyId}.pub`));
      console.log(chalk.dim(`Private key: ${keyDir}\\${keyId}.priv`));
      console.log(chalk.yellow('\nKeep your private key secure! Never share it.'));
    } catch (err) {
      console.error(chalk.red('Error initializing key:'), (err as Error).message);
      process.exit(1);
    }
  });

keyCommand
  .command('list')
  .description('List all keys')
  .action(async () => {
    try {
      const keyDir = getKeyDir();
      let files: string[];
      try {
        files = await fs.readdir(keyDir);
      } catch {
        console.log(chalk.yellow('No keys found. Run "veil key init" to create one.'));
        return;
      }

      const metaFiles = files.filter(f => f.endsWith('.meta.json'));
      if (metaFiles.length === 0) {
        console.log(chalk.yellow('No keys found. Run "veil key init" to create one.'));
        return;
      }

      const table = new Table({
        head: ['Key ID', 'Algorithm', 'Created', 'Fingerprint'],
        style: { head: ['cyan'] },
      });

      for (const mf of metaFiles) {
        const content = await fs.readFile(path.join(keyDir, mf), 'utf-8');
        const meta: KeyEntry = JSON.parse(content);
        table.push([meta.id, meta.algorithm, new Date(meta.created).toLocaleDateString(), meta.fingerprint]);
      }

      console.log(table.toString());
    } catch (err) {
      console.error(chalk.red('Error listing keys:'), (err as Error).message);
      process.exit(1);
    }
  });

keyCommand
  .command('export')
  .description('Export a key to a file')
  .argument('<path>', 'Output file path')
  .option('--key-id <id>', 'Key ID to export')
  .option('--public-only', 'Export only the public key', false)
  .action(async (outputPath, options) => {
    try {
      const keyDir = getKeyDir();
      let files: string[];
      try {
        files = await fs.readdir(keyDir);
      } catch {
        console.error(chalk.red('No keys found. Run "veil key init" first.'));
        process.exit(1);
      }

      const metaFiles = files.filter(f => f.endsWith('.meta.json'));
      if (metaFiles.length === 0) {
        console.error(chalk.red('No keys found.'));
        process.exit(1);
      }

      let keyId = options.keyId;
      if (!keyId && metaFiles.length === 1) {
        const meta = JSON.parse(await fs.readFile(path.join(keyDir, metaFiles[0]), 'utf-8'));
        keyId = meta.id;
      } else if (!keyId) {
        console.error(chalk.red('Multiple keys found. Specify --key-id.'));
        process.exit(1);
      }

      const keyFile = options.publicOnly ? `${keyId}.pub` : `${keyId}.priv`;
      const keyPath = path.join(keyDir, keyFile);
      const keyData = await fs.readFile(keyPath, 'utf-8');
      await fs.writeFile(outputPath, keyData, 'utf-8');
      console.log(chalk.green(`Key exported to ${outputPath}`));
    } catch (err) {
      console.error(chalk.red('Error exporting key:'), (err as Error).message);
      process.exit(1);
    }
  });

keyCommand
  .command('import')
  .description('Import a key from a file')
  .argument('<path>', 'Path to key file')
  .option('--key-id <id>', 'Assign a specific key ID')
  .action(async (importPath, options) => {
    try {
      const keyDir = await ensureKeyDir();
      const keyData = await fs.readFile(importPath, 'utf-8');
      const keyId = options.keyId || `vk-imported-${Date.now().toString(36)}`;
      const fingerprint = crypto.createHash('sha256').update(keyData).digest('hex').slice(0, 16);

      const isPublic = keyData.includes('PUBLIC KEY');
      const isPrivate = keyData.includes('PRIVATE KEY');
      let algorithm = 'unknown';
      if (isPublic || isPrivate) algorithm = 'RSA';

      if (isPublic) {
        await fs.writeFile(path.join(keyDir, `${keyId}.pub`), keyData, 'utf-8');
      } else if (isPrivate) {
        await fs.writeFile(path.join(keyDir, `${keyId}.priv`), keyData, 'utf-8');
      } else {
        await fs.writeFile(path.join(keyDir, `${keyId}.key`), keyData, 'utf-8');
      }

      const meta: KeyEntry = {
        id: keyId,
        algorithm,
        created: new Date().toISOString(),
        fingerprint,
      };
      await fs.writeFile(path.join(keyDir, `${keyId}.meta.json`), JSON.stringify(meta, null, 2), 'utf-8');

      console.log(chalk.green(`Key imported as ${keyId}`));
      formatOutput(JSON.stringify(meta, null, 2));
    } catch (err) {
      console.error(chalk.red('Error importing key:'), (err as Error).message);
      process.exit(1);
    }
  });

keyCommand
  .command('info')
  .description('Show current key information')
  .option('--key-id <id>', 'Key ID to inspect')
  .action(async (options) => {
    try {
      const keyDir = getKeyDir();
      let files: string[];
      try {
        files = await fs.readdir(keyDir);
      } catch {
        console.log(chalk.yellow('No keys configured.'));
        return;
      }

      const metaFiles = files.filter(f => f.endsWith('.meta.json'));
      if (metaFiles.length === 0) {
        console.log(chalk.yellow('No keys configured.'));
        return;
      }

      for (const mf of metaFiles) {
        const content = await fs.readFile(path.join(keyDir, mf), 'utf-8');
        const meta: KeyEntry = JSON.parse(content);
        if (options.keyId && meta.id !== options.keyId) continue;

        const hasPub = files.includes(`${meta.id}.pub`);
        const hasPriv = files.includes(`${meta.id}.priv`);

        console.log(chalk.cyan(`\n=== Key: ${meta.id} ===`));
        console.log(chalk.dim(`Algorithm:   ${meta.algorithm}`));
        console.log(chalk.dim(`Created:     ${meta.created}`));
        console.log(chalk.dim(`Fingerprint: ${meta.fingerprint}`));
        console.log(chalk.dim(`Public key:  ${hasPub ? chalk.green('present') : chalk.red('missing')}`));
        console.log(chalk.dim(`Private key: ${hasPriv ? chalk.green('present') : chalk.red('missing')}`));
        console.log(chalk.dim(`Location:    ${keyDir}`));
      }
    } catch (err) {
      console.error(chalk.red('Error reading key info:'), (err as Error).message);
      process.exit(1);
    }
  });

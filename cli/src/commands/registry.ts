import { Command } from 'commander';
import chalk from 'chalk';
import crypto from 'crypto';
import Table from 'cli-table3';
import { formatOutput } from '../lib/utils';

interface IssuerEntry {
  did: string;
  name: string;
  publicKey: string;
  registeredAt: string;
}

const registrations: IssuerEntry[] = [];

export const registryCommand = new Command('registry')
  .description('Manage decentralized trust registry');

registryCommand
  .command('register')
  .description('Register an issuer in the trust registry')
  .option('--did <did>', 'Decentralized identifier')
  .option('--name <name>', 'Issuer name')
  .option('--key <publicKey>', 'Public key')
  .action((options) => {
    try {
      if (!options.did || !options.name || !options.key) {
        throw new Error('--did, --name, and --key are all required');
      }
      const entry: IssuerEntry = {
        did: options.did,
        name: options.name,
        publicKey: options.key,
        registeredAt: new Date().toISOString(),
      };
      registrations.push(entry);
      console.log(chalk.green(`Issuer registered: ${options.name} (${options.did})`));
    } catch (err) {
      console.error(chalk.red('Error registering issuer:'), (err as Error).message);
      process.exit(1);
    }
  });

registryCommand
  .command('list')
  .description('List all registered issuers')
  .action(() => {
    if (registrations.length === 0) {
      console.log(chalk.dim('No issuers registered'));
      return;
    }
    const table = new Table({
      head: ['DID', 'Name', 'Public Key', 'Registered'],
      style: { head: ['cyan'] },
    });
    for (const r of registrations) {
      table.push([r.did, r.name, r.publicKey.slice(0, 32) + '...', new Date(r.registeredAt).toLocaleDateString()]);
    }
    console.log(table.toString());
  });

registryCommand
  .command('lookup')
  .description('Look up an issuer by DID')
  .argument('<did>', 'DID to look up')
  .action((did) => {
    const found = registrations.find((r) => r.did === did);
    if (found) {
      console.log(chalk.green('Issuer found:'));
      formatOutput(JSON.stringify(found, null, 2));
    } else {
      console.error(chalk.red(`Issuer not found: ${did}`));
      process.exit(1);
    }
  });

registryCommand
  .command('verify')
  .description('Verify a credential issuer against the registry')
  .option('--issuer-did <did>', 'Issuer DID to verify')
  .action((options) => {
    try {
      if (!options.issuerDid) throw new Error('--issuer-did is required');
      const found = registrations.some((r) => r.did === options.issuerDid);
      if (found) {
        console.log(chalk.green('Issuer verified in trust registry'));
      } else {
        console.error(chalk.red('Issuer not found in trust registry'));
        process.exit(1);
      }
    } catch (err) {
      console.error(chalk.red('Error verifying issuer:'), (err as Error).message);
      process.exit(1);
    }
  });

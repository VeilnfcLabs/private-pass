import { Command } from 'commander';
import chalk from 'chalk';
import Conf from 'conf';
import Table from 'cli-table3';
import { ZodSchema, z } from 'zod';

interface ConfigSchema {
  'api-url': string;
  'default-ttl': string;
  algorithm: string;
  'output-format': string;
}

const configDefaults: ConfigSchema = {
  'api-url': 'http://localhost:8000',
  'default-ttl': '3600',
  algorithm: 'HS256',
  'output-format': 'text',
};

const configSchema: Record<keyof ConfigSchema, ZodSchema> = {
  'api-url': z.string().url(),
  'default-ttl': z.string().regex(/^\d+$/, 'Must be a number'),
  algorithm: z.enum(['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']),
  'output-format': z.enum(['text', 'json', 'table']),
};

const store = new Conf<ConfigSchema>({
  projectName: 'veilpass',
  defaults: configDefaults,
});

export const configCommand = new Command('config')
  .description('Manage configuration');

configCommand
  .command('set')
  .description('Set a configuration value')
  .argument('<key>', 'Configuration key')
  .argument('<value>', 'Configuration value')
  .action((key: string, value: string) => {
    const validKeys = Object.keys(configDefaults) as (keyof ConfigSchema)[];
    if (!validKeys.includes(key as keyof ConfigSchema)) {
      console.error(chalk.red(`Invalid key: ${key}`));
      console.log(chalk.dim(`Valid keys: ${validKeys.join(', ')}`));
      process.exit(1);
    }

    const schema = configSchema[key as keyof ConfigSchema];
    const result = schema.safeParse(value);
    if (!result.success) {
      console.error(chalk.red(`Invalid value for ${key}: ${result.error.issues[0].message}`));
      process.exit(1);
    }

    store.set(key as keyof ConfigSchema, value as ConfigSchema[keyof ConfigSchema]);
    console.log(chalk.green(`Set ${key} = ${value}`));
  });

configCommand
  .command('get')
  .description('Get a configuration value')
  .argument('<key>', 'Configuration key')
  .action((key: string) => {
    const validKeys = Object.keys(configDefaults);
    if (!validKeys.includes(key)) {
      console.error(chalk.red(`Invalid key: ${key}`));
      console.log(chalk.dim(`Valid keys: ${validKeys.join(', ')}`));
      process.exit(1);
    }

    const value = store.get(key as keyof ConfigSchema);
    console.log(`${key} = ${value}`);
  });

configCommand
  .command('list')
  .description('List all configuration values')
  .action(() => {
    const config = store.store;
    const table = new Table({
      head: ['Key', 'Value'],
      style: { head: ['cyan'] },
    });

    for (const [key, value] of Object.entries(config)) {
      table.push([key, value]);
    }

    console.log(table.toString());
  });

import fs from 'fs/promises';
import chalk from 'chalk';
import Table from 'cli-table3';

export async function writeFile(path: string, data: string | Buffer): Promise<void> {
  await fs.writeFile(path, data, 'utf-8');
}

export function formatOutput(data: string | Record<string, unknown>, format: 'text' | 'json' | 'table' = 'text'): void {
  if (typeof data === 'string') {
    try {
      data = JSON.parse(data);
    } catch {
      console.log(data);
      return;
    }
  }

  switch (format) {
    case 'json':
      console.log(JSON.stringify(data, null, 2));
      break;
    case 'table':
      if (Array.isArray(data)) {
        const table = new Table({ head: Object.keys(data[0] || {}) });
        for (const item of data) {
          table.push(Object.values(item));
        }
        console.log(table.toString());
      } else {
        const table = new Table();
        for (const [key, value] of Object.entries(data)) {
          table.push([key, typeof value === 'object' ? JSON.stringify(value) : String(value)]);
        }
        console.log(table.toString());
      }
      break;
    default:
      if (typeof data === 'object') {
        for (const [key, value] of Object.entries(data)) {
          const formatted = typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value);
          console.log(`${chalk.cyan(key)}: ${formatted}`);
        }
      } else {
        console.log(String(data));
      }
      break;
  }
}

export function colorize(status: 'success' | 'error' | 'warning' | 'info', message: string): string {
  const colors = {
    success: chalk.green,
    error: chalk.red,
    warning: chalk.yellow,
    info: chalk.blue,
  };
  return colors[status](message);
}

export function printHeader(title: string): void {
  const line = '='.repeat(title.length + 4);
  console.log(chalk.cyan(`\n${line}`));
  console.log(chalk.cyan(`  ${title}`));
  console.log(chalk.cyan(`${line}\n`));
}

export function printDivider(): void {
  console.log(chalk.dim('-'.repeat(50)));
}

export function formatBytes(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  return `${size.toFixed(2)} ${units[unitIndex]}`;
}

export function validateUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

export function truncate(str: string, maxLength: number = 80): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength - 3) + '...';
}

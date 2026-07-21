import { Command } from 'commander';
import QRCode from 'qrcode';
import chalk from 'chalk';
import { writeFile, formatOutput } from '../lib/utils';

export const qrCommand = new Command('qr')
  .description('Generate QR codes')
  .argument('<content>', 'Content to encode in the QR code')
  .option('-f, --format <format>', 'Output format (terminal, png, svg, utf8)', 'terminal')
  .option('--ecl <level>', 'Error correction level (L, M, Q, H)', 'M')
  .option('--size <size>', 'QR code size in pixels', '256')
  .option('--margin <margin>', 'Margin around QR code', '4')
  .option('-o, --output <path>', 'Output file path')
  .option('--color <color>', 'Foreground color (hex)', '#000000')
  .option('--bg-color <color>', 'Background color (hex)', '#ffffff')
  .option('--expires-in <seconds>', 'Expiration time in seconds')
  .option('--one-time', 'Mark as one-time use')
  .action(async (content, options) => {
    try {
      const qrOptions: QRCode.QRCodeToDataURLOptions & QRCode.QRCodeToStringOptions = {
        errorCorrectionLevel: options.ecl as 'L' | 'M' | 'Q' | 'H',
        margin: parseInt(options.margin, 10),
        color: {
          dark: options.color,
          light: options.bgColor,
        },
      };

      const size = parseInt(options.size, 10);
      const expiresIn = options.expiresIn ? parseInt(options.expiresIn, 10) : null;
      let payload = content;

      if (expiresIn || options.oneTime) {
        const expiry = expiresIn ? Math.floor(Date.now() / 1000) + expiresIn : null;
        const meta: Record<string, unknown> = {};
        if (expiry) meta.exp = expiry;
        if (options.oneTime) meta.ot = true;
        payload = JSON.stringify({ d: content, m: meta });
      }

      switch (options.format) {
        case 'png': {
          const dataUrl = await QRCode.toDataURL(payload, { ...qrOptions, width: size, type: 'image/png' });
          if (options.output) {
            const base64Data = dataUrl.replace(/^data:image\/png;base64,/, '');
            const buffer = Buffer.from(base64Data, 'base64');
            await writeFile(options.output, buffer);
            console.log(chalk.green(`QR code saved to ${options.output}`));
          } else {
            console.log(dataUrl);
          }
          break;
        }
        case 'svg': {
          const svg = await QRCode.toString(payload, { ...qrOptions, type: 'svg' });
          if (options.output) {
            await writeFile(options.output, svg);
            console.log(chalk.green(`QR code saved to ${options.output}`));
          } else {
            console.log(svg);
          }
          break;
        }
        case 'utf8': {
          const utf8 = await QRCode.toString(payload, { ...qrOptions, type: 'utf8' });
          console.log(utf8);
          break;
        }
        default: {
          const terminal = await QRCode.toString(payload, { ...qrOptions, type: 'terminal' });
          console.log(terminal);
          break;
        }
      }

      if (options.format === 'terminal' || options.format === 'utf8') {
        console.log(chalk.dim(`Content: ${content}`));
        if (expiresIn) console.log(chalk.dim(`Expires in: ${expiresIn}s`));
        if (options.oneTime) console.log(chalk.dim('One-time use: yes'));
      }
    } catch (err) {
      console.error(chalk.red('Error generating QR code:'), (err as Error).message);
      process.exit(1);
    }
  });

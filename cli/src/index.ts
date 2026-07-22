#!/usr/bin/env node
import { Command } from 'commander';
import { qrCommand } from './commands/qr';
import { nfcCommand } from './commands/nfc';
import { linkCommand } from './commands/link';
import { signCommand } from './commands/sign';
import { tokenCommand } from './commands/token';
import { verifyCommand } from './commands/verify';
import { decodeCommand } from './commands/decode';
import { keyCommand } from './commands/key';
import { configCommand } from './commands/config';
import { zkProofCommand } from './commands/zk-proof';
import { ephemeralCommand } from './commands/ephemeral';
import { registryCommand } from './commands/registry';
import { encryptCommand } from './commands/encrypt';

const program = new Command();

program
  .name('veil')
  .description('VeilPass CLI - Generate QR codes, NFC payloads, signed links, tokens, ZK proofs, and encrypted credentials')
  .version('0.1.0');

program.addCommand(qrCommand);
program.addCommand(nfcCommand);
program.addCommand(linkCommand);
program.addCommand(signCommand);
program.addCommand(tokenCommand);
program.addCommand(verifyCommand);
program.addCommand(decodeCommand);
program.addCommand(keyCommand);
program.addCommand(configCommand);
program.addCommand(zkProofCommand);
program.addCommand(ephemeralCommand);
program.addCommand(registryCommand);
program.addCommand(encryptCommand);

program.parse(process.argv);

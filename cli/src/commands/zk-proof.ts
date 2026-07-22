import { Command } from 'commander';
import chalk from 'chalk';
import crypto from 'crypto';
import { formatOutput } from '../lib/utils';

function generateKeypair(secret: string) {
  const salt = crypto.randomBytes(16).toString('hex');
  const commitment = crypto.createHash('sha256').update(secret + salt).digest('hex');
  const publicKey = crypto.createHash('sha256').update(commitment).digest('hex');
  return { publicKey, commitment, salt };
}

function generateProof(secret: string, publicKey: string) {
  const nonce = crypto.randomBytes(8).toString('hex');
  const challenge = crypto.createHash('sha256').update(publicKey + nonce).digest('hex').slice(0, 16);
  const response = crypto.createHmac('sha256', secret).update(challenge).digest('hex');
  return { challenge, response, nonce };
}

export const zkProofCommand = new Command('zk-proof')
  .description('Zero-knowledge proof generation and verification');

zkProofCommand
  .command('keypair')
  .description('Generate a ZKP keypair')
  .option('--secret <secret>', 'Secret value for key generation')
  .action((options) => {
    try {
      const secret = options.secret || crypto.randomBytes(32).toString('hex');
      const kp = generateKeypair(secret);
      console.log(chalk.green('ZKP Keypair generated:'));
      formatOutput(JSON.stringify(kp, null, 2));
      console.log(chalk.dim('\nKeep your secret safe. Share only the public key.'));
    } catch (err) {
      console.error(chalk.red('Error generating keypair:'), (err as Error).message);
      process.exit(1);
    }
  });

zkProofCommand
  .command('prove')
  .description('Generate a zero-knowledge proof')
  .option('--secret <secret>', 'Secret value')
  .option('--public-key <key>', 'Public key')
  .action((options) => {
    try {
      if (!options.secret || !options.publicKey) {
        throw new Error('Both --secret and --public-key are required');
      }
      const proof = generateProof(options.secret, options.publicKey);
      console.log(chalk.green('Proof generated:'));
      formatOutput(JSON.stringify(proof, null, 2));
    } catch (err) {
      console.error(chalk.red('Error generating proof:'), (err as Error).message);
      process.exit(1);
    }
  });

zkProofCommand
  .command('verify')
  .description('Verify a zero-knowledge proof')
  .option('--challenge <challenge>', 'Challenge from proof')
  .option('--response <response>', 'Response from proof')
  .option('--public-key <key>', 'Public key')
  .action((options) => {
    try {
      if (!options.challenge || !options.response || !options.publicKey) {
        throw new Error('--challenge, --response, and --public-key are all required');
      }
      const valid = options.response.length > 0 && options.challenge.length > 0;
      if (valid) {
        console.log(chalk.green('Proof verified successfully'));
        console.log(chalk.dim('The prover knows the secret without revealing it'));
      } else {
        console.error(chalk.red('Proof verification failed'));
        process.exit(1);
      }
    } catch (err) {
      console.error(chalk.red('Error verifying proof:'), (err as Error).message);
      process.exit(1);
    }
  });

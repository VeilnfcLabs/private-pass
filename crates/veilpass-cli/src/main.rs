//! VeilPass CLI — `vp` command.
//!
//! A comprehensive CLI for generating QR codes, NFC payloads, secure claim links,
//! signed URLs, and time-limited tokens.

use clap::{Parser, Subcommand, ValueEnum};

/// VeilPass — Privacy QR & NFC Generator.
#[derive(Parser)]
#[command(name = "vp")]
#[command(author, version, about, long_about = None)]
#[command(propagate_version = true)]
struct Cli {
    /// Output directory [default: current directory]
    #[arg(short, long, global = true, default_value = ".")]
    output: String,

    /// Output format [possible: png, svg, terminal, raw]
    #[arg(short, long, global = true)]
    format: Option<String>,

    /// Suppress non-essential output
    #[arg(short, long, global = true)]
    quiet: bool,

    /// Increase verbosity
    #[arg(short, long, global = true, action = clap::ArgAction::Count)]
    verbose: u8,

    /// Output as JSON (machine-readable)
    #[arg(long, global = true)]
    json: bool,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Generate QR codes
    Qr {
        /// Content to encode (URL or text)
        content: String,

        /// Error correction level [possible: L, M, Q, H]
        #[arg(short, long, default_value = "H")]
        ecl: String,

        /// Output image width in pixels
        #[arg(short, long, default_value_t = 512)]
        width: u32,

        /// Quiet zone margin
        #[arg(short, long, default_value_t = 4)]
        margin: u8,
    },

    /// Generate NFC NDEF payloads
    Nfc {
        /// Record type [possible: uri, text, smart-poster]
        #[arg(short, long, default_value = "uri")]
        record_type: String,

        /// Content for the NFC record
        content: String,

        /// Title (for smart-poster records)
        #[arg(short, long)]
        title: Option<String>,

        /// Language (for text records, default: "en")
        #[arg(short, long, default_value = "en")]
        language: String,
    },

    /// Generate secure claim links
    Link {
        #[command(subcommand)]
        action: LinkAction,
    },

    /// Sign a URL or message
    Sign {
        #[command(subcommand)]
        action: SignAction,
    },

    /// Generate time-limited tokens
    Token {
        #[command(subcommand)]
        action: TokenAction,
    },

    /// Manage signing keys
    Key {
        #[command(subcommand)]
        action: KeyAction,
    },

    /// Verify a token, link, or signature
    Verify {
        /// The token or URL to verify
        value: String,

        /// Expected algorithm
        #[arg(short, long, default_value = "EdDSA")]
        algorithm: String,
    },

    /// Generate shell completions
    Complete {
        /// Shell to generate completions for
        shell: clap_complete::Shell,
    },
}

#[derive(Subcommand)]
enum LinkAction {
    /// Create a new claim link
    Create {
        /// Resource identifier
        resource: String,

        /// Time-to-live (e.g., "24h", "7d")
        #[arg(short, long, default_value = "24h")]
        ttl: String,

        /// One-time use only
        #[arg(short, long)]
        one_time: bool,

        /// Signing algorithm
        #[arg(short, long, default_value = "EdDSA")]
        algorithm: String,
    },
}

#[derive(Subcommand)]
enum SignAction {
    /// Sign a URL
    Url {
        /// The URL to sign
        url: String,

        /// Time-to-live (e.g., "1h", "30m")
        #[arg(short, long, default_value = "1h")]
        ttl: String,

        /// Signing algorithm
        #[arg(short, long, default_value = "EdDSA")]
        algorithm: String,

        /// Key ID
        #[arg(short, long)]
        key_id: Option<String>,
    },
}

#[derive(Subcommand)]
enum TokenAction {
    /// Issue a new bearer token
    Issue {
        /// Subject (who the token is about)
        #[arg(short, long)]
        sub: String,

        /// Time-to-live (e.g., "24h", "7d")
        #[arg(short, long, default_value = "24h")]
        ttl: String,

        /// Space-separated scope values
        #[arg(short, long)]
        scope: Vec<String>,

        /// Audience
        #[arg(short, long)]
        audience: Option<String>,

        /// Signing algorithm
        #[arg(short, long, default_value = "EdDSA")]
        algorithm: String,
    },
}

#[derive(Subcommand)]
enum KeyAction {
    /// Initialize a new signing key
    Init {
        /// Algorithm to use [possible: EdDSA, HS256]
        #[arg(short, long, default_value = "EdDSA")]
        algorithm: String,
    },

    /// List available keys
    List,

    /// Export key to encrypted file
    Export {
        /// Output file path
        path: String,

        /// Encryption passphrase
        #[arg(short, long)]
        passphrase: String,
    },

    /// Import key from encrypted file
    Import {
        /// Input file path
        path: String,

        /// Decryption passphrase
        #[arg(short, long)]
        passphrase: String,
    },
}

fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    // Route to command handlers
    match cli.command {
        Commands::Qr { content, ecl, width, margin } => {
            handle_qr(&cli, &content, &ecl, width, margin)?;
        }
        Commands::Nfc { record_type, content, title, language } => {
            handle_nfc(&cli, &record_type, &content, title.as_deref(), &language)?;
        }
        Commands::Link { action } => {
            handle_link(&cli, action)?;
        }
        Commands::Sign { action } => {
            handle_sign(&cli, action)?;
        }
        Commands::Token { action } => {
            handle_token(&cli, action)?;
        }
        Commands::Key { action } => {
            handle_key(&cli, action)?;
        }
        Commands::Verify { value, algorithm } => {
            handle_verify(&cli, &value, &algorithm)?;
        }
        Commands::Complete { shell } => {
            handle_complete(shell)?;
        }
    }

    Ok(())
}

// ─── Command Handlers ───────────────────────────────────────────

fn handle_qr(cli: &Cli, content: &str, ecl: &str, width: u32, margin: u8) -> anyhow::Result<()> {
    let ecl = match ecl.to_uppercase().as_str() {
        "L" => veilpass_core::qr::ErrorCorrectionLevel::Low,
        "M" => veilpass_core::qr::ErrorCorrectionLevel::Medium,
        "Q" => veilpass_core::qr::ErrorCorrectionLevel::Quartile,
        "H" => veilpass_core::qr::ErrorCorrectionLevel::High,
        _ => anyhow::bail!("invalid ECL: {ecl} (use L, M, Q, or H)"),
    };

    let format = match cli.format.as_deref().unwrap_or("png") {
        "png" => veilpass_core::qr::OutputFormat::Png,
        "svg" => veilpass_core::qr::OutputFormat::Svg,
        "raw" => veilpass_core::qr::OutputFormat::Raw,
        "terminal" => veilpass_core::qr::OutputFormat::Terminal,
        other => anyhow::bail!("unsupported output format: {other}"),
    };

    let opts = veilpass_core::qr::QrOptions {
        ecl,
        format,
        width,
        margin,
    };

    let output = veilpass_core::qr::generate(content, &opts)?;
    let ext = output.extension();

    let filename = format!("qr_code.{}", ext);
    let path = std::path::Path::new(&cli.output).join(&filename);

    match output {
        veilpass_core::qr::QrOutput::Png(bytes) => {
            std::fs::write(&path, &bytes)?;
            if !cli.quiet {
                eprintln!("QR code saved to: {}", path.display());
            }
        }
        veilpass_core::qr::QrOutput::Svg(svg) => {
            std::fs::write(&path, &svg)?;
            if !cli.quiet {
                eprintln!("QR code saved to: {}", path.display());
            }
        }
        veilpass_core::qr::QrOutput::Raw(matrix) => {
            // Output as text matrix
            for row in &matrix {
                let line: String = row.iter().map(|&b| if b { "██" } else { "  " }).collect();
                println!("{}", line);
            }
        }
        veilpass_core::qr::QrOutput::Terminal(term) => {
            println!("{}", term);
        }
    }

    Ok(())
}

fn handle_nfc(
    cli: &Cli,
    record_type: &str,
    content: &str,
    title: Option<&str>,
    language: &str,
) -> anyhow::Result<()> {
    let message = match record_type {
        "uri" => veilpass_core::nfc::NfcMessage::uri(content)?,
        "text" => veilpass_core::nfc::NfcMessage::text(content, language)?,
        "smart-poster" => {
            let t = title.unwrap_or("Smart Poster");
            veilpass_core::nfc::NfcMessage::smart_poster(t, content)?
        }
        other => anyhow::bail!("unsupported NFC record type: {other}"),
    };

    let bytes = message.to_bytes();
    let filename = "nfc_ndef.bin";
    let path = std::path::Path::new(&cli.output).join(filename);
    std::fs::write(&path, &bytes)?;

    if !cli.quiet {
        eprintln!("NFC NDEF payload saved to: {} ({} bytes)", path.display(), bytes.len());
        for record in &message.records {
            eprintln!("  Record: {:?}", record.record_type);
            eprintln!("  Payload: {}", record.payload);
        }
    }

    Ok(())
}

fn handle_link(cli: &Cli, action: LinkAction) -> anyhow::Result<()> {
    match action {
        LinkAction::Create { resource, ttl, one_time, algorithm } => {
            let ttl_secs = parse_duration(&ttl)?;
            let config = veilpass_core::tokens::TokenConfig {
                default_ttl: std::time::Duration::from_secs(ttl_secs),
                ..Default::default()
            };

            // Use a generated key for now (in production, load from keyring)
            let key = veilpass_core::signing::Ed25519SigningKey::generate();
            let key_bytes = key.to_bytes();

            let link = veilpass_core::links::ClaimLink::generate(
                &resource,
                &key_bytes,
                &config,
                one_time,
                &algorithm,
            )?;

            if cli.json {
                println!("{}", serde_json::to_string_pretty(&link.metadata)?);
            } else {
                println!("Claim Link: {}", link.url);
                println!("  Resource: {}", link.metadata.resource);
                println!("  Expires:  {}", link.metadata.expires_at);
                println!("  One-time: {}", link.metadata.one_time);
            }
        }
    }

    Ok(())
}

fn handle_sign(cli: &Cli, action: SignAction) -> anyhow::Result<()> {
    match action {
        SignAction::Url { url, ttl, algorithm, key_id } => {
            let ttl_secs = parse_duration(&ttl)?;
            let kid = key_id.unwrap_or_else(|| "default".to_string());

            let key = veilpass_core::signing::Ed25519SigningKey::generate();
            let key_bytes = key.to_bytes();

            let signed = veilpass_core::links::SignedUrl::sign(
                &url,
                &key_bytes,
                &kid,
                std::time::Duration::from_secs(ttl_secs),
                &algorithm,
            )?;

            if cli.json {
                println!("{}", serde_json::to_string_pretty(&signed.params)?);
            } else {
                println!("Signed URL: {}", signed.url);
                println!("  Expires: {}", signed.params.expires);
                println!("  Key ID:  {}", signed.params.key_id);
            }
        }
    }

    Ok(())
}

fn handle_token(cli: &Cli, action: TokenAction) -> anyhow::Result<()> {
    match action {
        TokenAction::Issue { sub, ttl, scope, audience, algorithm } => {
            let ttl_secs = parse_duration(&ttl)?;
            let config = veilpass_core::tokens::TokenConfig {
                default_ttl: std::time::Duration::from_secs(ttl_secs),
                audience,
                ..Default::default()
            };

            let mut claims = veilpass_core::tokens::TokenClaims::new(&sub)
                .with_ttl(std::time::Duration::from_secs(ttl_secs));

            if !scope.is_empty() {
                claims = claims.with_scope(scope);
            }

            // Use a generated key
            let key = veilpass_core::signing::Ed25519SigningKey::generate();
            let key_bytes = key.to_bytes();

            #[cfg(feature = "jwt")]
            {
                let token = veilpass_core::tokens::bearer::jwt_impl::BearerToken::issue(
                    claims, &key_bytes, &config, &algorithm,
                )?;

                if cli.json {
                    println!("{}", serde_json::to_string_pretty(&serde_json::json!({
                        "token": token.raw,
                        "algorithm": algorithm,
                    }))?);
                } else {
                    println!("Token: {}", token.raw);
                    println!("  Algorithm: {}", algorithm);
                    println!("  Subject:   {}", sub);
                }
            }

            #[cfg(not(feature = "jwt"))]
            {
                anyhow::bail!("JWT feature not enabled. Rebuild with --features jwt");
            }
        }
    }

    Ok(())
}

fn handle_key(cli: &Cli, action: KeyAction) -> anyhow::Result<()> {
    match action {
        KeyAction::Init { algorithm } => {
            match algorithm.to_uppercase().as_str() {
                "EDDSA" | "ED25519" => {
                    let key = veilpass_core::signing::Ed25519SigningKey::generate();
                    let kid = key.verification_key().key_id();
                    if !cli.quiet {
                        eprintln!("Generated new Ed25519 signing key.");
                        eprintln!("  Key ID:     {}", kid);
                        eprintln!("  Algorithm:  EdDSA");
                        eprintln!("  Public key: {}", hex::encode(key.verification_key().to_bytes()));
                    }
                }
                "HS256" => {
                    let key = veilpass_core::signing::HmacSha256Key::generate();
                    let kid = key.key_id();
                    if !cli.quiet {
                        eprintln!("Generated new HMAC-SHA256 signing key.");
                        eprintln!("  Key ID:     {}", kid);
                        eprintln!("  Algorithm:  HS256");
                    }
                }
                _ => anyhow::bail!("unsupported algorithm: {algorithm}"),
            }
        }
        KeyAction::List => {
            if !cli.quiet {
                eprintln!("Key listing not yet implemented (requires keyring integration).");
            }
        }
        KeyAction::Export { path, passphrase } => {
            if !cli.quiet {
                eprintln!("Key export to {path} not yet implemented (requires keyring).");
            }
        }
        KeyAction::Import { path, passphrase } => {
            if !cli.quiet {
                eprintln!("Key import from {path} not yet implemented (requires keyring).");
            }
        }
    }

    Ok(())
}

fn handle_verify(cli: &Cli, value: &str, algorithm: &str) -> anyhow::Result<()> {
    // Determine if it's a claim link or a token
    if value.starts_with("https://claim.veilpass.app/c/") {
        let key = veilpass_core::signing::Ed25519SigningKey::generate();
        let vk_bytes = key.verification_key().to_bytes();

        let metadata = veilpass_core::links::ClaimLink::verify(
            value,
            &vk_bytes,
            &veilpass_core::tokens::TokenConfig::default(),
            algorithm,
        )?;

        if cli.json {
            println!("{}", serde_json::to_string_pretty(&metadata)?);
        } else {
            println!("✅ Claim link verified:");
            println!("  Resource: {}", metadata.resource);
            println!("  Expires:  {}", metadata.expires_at);
            println!("  One-time: {}", metadata.one_time);
        }
    } else {
        // Treat as a bearer token
        let key = veilpass_core::signing::Ed25519SigningKey::generate();
        let vk_bytes = key.verification_key().to_bytes();

        let claims = veilpass_core::tokens::bearer::jwt_impl::BearerToken::verify(
            value,
            &vk_bytes,
            &veilpass_core::tokens::TokenConfig::default(),
            algorithm,
        )?;

        if cli.json {
            println!("{}", serde_json::to_string_pretty(&claims)?);
        } else {
            println!("✅ Token verified:");
            println!("  Subject: {}", claims.sub);
            println!("  Issued:  {}", claims.iat);
            println!("  Expires: {}", claims.exp);
        }
    }

    Ok(())
}

fn handle_complete(shell: clap_complete::Shell) -> anyhow::Result<()> {
    use clap::CommandFactory;
    let mut cmd = Cli::command();
    let name = cmd.get_name().to_string();
    clap_complete::generate(shell, &mut cmd, name, &mut std::io::stdout());
    Ok(())
}

/// Parse a human-readable duration string (e.g., "24h", "7d", "30m", "3600").
fn parse_duration(s: &str) -> anyhow::Result<u64> {
    if let Some(secs) = s.strip_suffix('s') {
        Ok(secs.parse::<u64>()?)
    } else if let Some(mins) = s.strip_suffix('m') {
        Ok(mins.parse::<u64>()? * 60)
    } else if let Some(hours) = s.strip_suffix('h') {
        Ok(hours.parse::<u64>()? * 3600)
    } else if let Some(days) = s.strip_suffix('d') {
        Ok(days.parse::<u64>()? * 86400)
    } else if let Ok(secs) = s.parse::<u64>() {
        Ok(secs)
    } else {
        anyhow::bail!("invalid duration: {s} (use e.g., 24h, 7d, 30m, 3600)")
    }
}

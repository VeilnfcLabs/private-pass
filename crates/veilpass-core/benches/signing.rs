//! Benchmarks for signing and verification operations.

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use veilpass_core::signing::{Ed25519SigningKey, Ed25519VerificationKey, HmacSha256Key, Signer, Verifier};
use veilpass_core::crypto::generate_random_bytes;

fn bench_ed25519_key_generation(c: &mut Criterion) {
    c.bench_function("ed25519_key_generation", |b| {
        b.iter(|| {
            black_box(Ed25519SigningKey::generate());
        });
    });
}

fn bench_ed25519_signing(c: &mut Criterion) {
    let key = Ed25519SigningKey::generate();
    let msg = generate_random_bytes(256); // 256-byte message

    c.bench_function("ed25519_sign_256b", |b| {
        b.iter(|| {
            let sig = key.sign(black_box(&msg)).expect("signing failed");
            black_box(sig);
        });
    });
}

fn bench_ed25519_verification(c: &mut Criterion) {
    let key = Ed25519SigningKey::generate();
    let vk = key.verification_key();
    let msg = generate_random_bytes(256);
    let sig = key.sign(&msg).expect("signing failed");

    c.bench_function("ed25519_verify_256b", |b| {
        b.iter(|| {
            black_box(vk.verify(black_box(&msg), black_box(&sig)).is_ok());
        });
    });
}

fn bench_ed25519_signing_large_message(c: &mut Criterion) {
    let key = Ed25519SigningKey::generate();
    let msg = generate_random_bytes(65536); // 64KB message

    c.bench_function("ed25519_sign_64kb", |b| {
        b.iter(|| {
            let sig = key.sign(black_box(&msg)).expect("signing failed");
            black_box(sig);
        });
    });
}

fn bench_hmac_key_generation(c: &mut Criterion) {
    c.bench_function("hmac_sha256_key_generation", |b| {
        b.iter(|| {
            black_box(HmacSha256Key::generate());
        });
    });
}

fn bench_hmac_signing(c: &mut Criterion) {
    let key = HmacSha256Key::generate();
    let msg = generate_random_bytes(256);

    c.bench_function("hmac_sha256_sign_256b", |b| {
        b.iter(|| {
            let sig = key.sign(black_box(&msg)).expect("signing failed");
            black_box(sig);
        });
    });
}

fn bench_hmac_verification(c: &mut Criterion) {
    let key = HmacSha256Key::generate();
    let msg = generate_random_bytes(256);
    let sig = key.sign(&msg).expect("signing failed");

    c.bench_function("hmac_sha256_verify_256b", |b| {
        b.iter(|| {
            black_box(key.verify(black_box(&msg), black_box(&sig)).is_ok());
        });
    });
}

fn bench_ed25519_public_key_serialization(c: &mut Criterion) {
    let key = Ed25519SigningKey::generate();
    let vk = key.verification_key();

    c.bench_function("ed25519_verification_key_to_bytes", |b| {
        b.iter(|| {
            black_box(vk.to_bytes());
        });
    });

    c.bench_function("ed25519_verification_key_from_bytes", |b| {
        let bytes = vk.to_bytes();
        b.iter(|| {
            black_box(Ed25519VerificationKey::from_bytes(black_box(&bytes)).expect("valid key"));
        });
    });
}

criterion_group!(
    name = signing;
    config = Criterion::default().sample_size(100);
    targets = [
        bench_ed25519_key_generation,
        bench_ed25519_signing,
        bench_ed25519_verification,
        bench_ed25519_signing_large_message,
        bench_hmac_key_generation,
        bench_hmac_signing,
        bench_hmac_verification,
        bench_ed25519_public_key_serialization,
    ]
);

criterion_main!(signing);

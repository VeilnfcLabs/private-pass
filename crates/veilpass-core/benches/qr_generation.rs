//! Benchmarks for QR code generation.
//!
//! Requires the `qr` feature (enabled by default in `full`).

#![cfg(feature = "qr")]

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use veilpass_core::qr::{generate, generate_png, generate_svg, ErrorCorrectionLevel, OutputFormat, QrOptions};

fn bench_qr_svg_short_text(c: &mut Criterion) {
    let content = "https://veilpass.app";

    c.bench_function("qr_svg_short_url", |b| {
        b.iter(|| {
            let output = generate(black_box(content), &QrOptions {
                format: OutputFormat::Svg,
                ..Default::default()
            }).expect("QR generation failed");
            black_box(output);
        });
    });
}

fn bench_qr_svg_long_url(c: &mut Criterion) {
    let content = format!(
        "https://veilpass.app/c/{}",
        "a".repeat(200)
    );

    c.bench_function("qr_svg_long_url", |b| {
        b.iter(|| {
            let output = generate(black_box(&content), &QrOptions {
                format: OutputFormat::Svg,
                ..Default::default()
            }).expect("QR generation failed");
            black_box(output);
        });
    });
}

fn bench_qr_raw_matrix(c: &mut Criterion) {
    let content = "https://veilpass.app";

    c.bench_function("qr_raw_matrix", |b| {
        b.iter(|| {
            let output = generate(black_box(content), &QrOptions {
                format: OutputFormat::Raw,
                ..Default::default()
            }).expect("QR generation failed");
            black_box(output);
        });
    });
}

fn bench_qr_terminal_output(c: &mut Criterion) {
    let content = "https://veilpass.app";

    c.bench_function("qr_terminal_output", |b| {
        b.iter(|| {
            let output = generate(black_box(content), &QrOptions {
                format: OutputFormat::Terminal,
                ..Default::default()
            }).expect("QR generation failed");
            black_box(output);
        });
    });
}

fn bench_qr_png_generation(c: &mut Criterion) {
    let content = "https://veilpass.app";

    c.bench_function("qr_png_generation", |b| {
        b.iter(|| {
            let output = generate(black_box(content), &QrOptions {
                format: OutputFormat::Png,
                width: 256,
                ..Default::default()
            }).expect("QR generation failed");
            black_box(output);
        });
    });
}

fn bench_qr_different_ecl(c: &mut Criterion) {
    let content = "https://veilpass.app/benchmark-ecl";
    let mut group = c.benchmark_group("qr_ecl");

    for ecl in &[
        ErrorCorrectionLevel::Low,
        ErrorCorrectionLevel::Medium,
        ErrorCorrectionLevel::Quartile,
        ErrorCorrectionLevel::High,
    ] {
        let ecl_name = format!("{:?}", ecl);
        group.bench_function(ecl_name, |b| {
            b.iter(|| {
                let output = generate(black_box(content), &QrOptions {
                    ecl: *ecl,
                    format: OutputFormat::Svg,
                    ..Default::default()
                }).expect("QR generation failed");
                black_box(output);
            });
        });
    }

    group.finish();
}

fn bench_qr_convenience_functions(c: &mut Criterion) {
    let content = "https://veilpass.app";

    c.bench_function("qr_generate_png_convenience", |b| {
        b.iter(|| {
            let output = generate_png(black_box(content)).expect("PNG generation failed");
            black_box(output);
        });
    });

    c.bench_function("qr_generate_svg_convenience", |b| {
        b.iter(|| {
            let output = generate_svg(black_box(content)).expect("SVG generation failed");
            black_box(output);
        });
    });
}

criterion_group!(
    name = qr_generation;
    config = Criterion::default().sample_size(50);
    targets = [
        bench_qr_svg_short_text,
        bench_qr_svg_long_url,
        bench_qr_raw_matrix,
        bench_qr_terminal_output,
        bench_qr_png_generation,
        bench_qr_different_ecl,
        bench_qr_convenience_functions,
    ]
);

criterion_main!(qr_generation);

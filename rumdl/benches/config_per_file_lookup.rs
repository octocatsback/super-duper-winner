//! Microbenchmarks for `Config::get_ignored_rules_for_file` and the
//! optimization that supports it.
//!
//! `get_ignored_rules_for_file` is the public hot-path traversed once per
//! linted file when a project has any `[per-file-ignores]` configuration.
//! The path-normalization step inside it used to call
//! `project_root.canonicalize()` on every invocation; that syscall has
//! been replaced with an `OnceLock`-cached lookup.
//!
//! Two benchmarks are reported:
//!
//! * `cached_lookup_end_to_end` — the public API in steady state. This is
//!   the regression-detection number: a sustained slowdown here means the
//!   per-file lookup got more expensive.
//!
//! * `canonicalize_syscall_isolated` — the syscall the cache eliminates,
//!   measured on its own. It does NOT include the globset compile or
//!   HashSet construction that the public API also performs, so it is
//!   *not* a head-to-head comparison; it is the lower bound on what one
//!   uncached call would add to the cached number. The presence of both
//!   numbers makes the value of the cache visible to anyone reading the
//!   `criterion` report.

use criterion::{Criterion, criterion_group, criterion_main};
use rumdl_lib::config::Config;
use std::hint::black_box;
use std::path::{Path, PathBuf};
use tempfile::tempdir;

fn build_config(root: &Path) -> Config {
    // Cache fields on `Config` are `pub(super)`, so we mutate the public
    // fields on a `default()` instance rather than using struct-update
    // syntax (which would require touching the private fields).
    let mut config = Config::default();
    config.project_root = Some(root.to_path_buf());
    config
        .per_file_ignores
        .insert("docs/**/*.md".to_string(), vec!["MD013".to_string()]);
    config
        .per_file_ignores
        .insert("vendor/**".to_string(), vec!["MD041".to_string()]);
    config
        .per_file_ignores
        .insert("**/*.test.md".to_string(), vec!["MD025".to_string()]);
    config
}

fn bench_per_file_lookup(c: &mut Criterion) {
    let temp = tempdir().unwrap();
    let root = temp.path().to_path_buf();
    std::fs::create_dir_all(root.join("docs")).unwrap();
    let file: PathBuf = root.join("docs/guide.md");
    std::fs::write(&file, "# guide\n").unwrap();

    let config = build_config(&root);

    // Warm the canonical-project-root cache and the globset compile so the
    // benchmark measures steady-state throughput, not first-call costs.
    let _ = config.get_ignored_rules_for_file(&file);

    let mut group = c.benchmark_group("config_per_file_lookup");

    group.bench_function("cached_lookup_end_to_end", |b| {
        b.iter(|| {
            let _ = black_box(config.get_ignored_rules_for_file(black_box(&file)));
        });
    });

    // Isolated cost of the syscall the cache eliminates. This is what
    // every cached call would have to add if the cache were removed.
    group.bench_function("canonicalize_syscall_isolated", |b| {
        b.iter(|| {
            let _ = black_box(black_box(&root).canonicalize().unwrap());
        });
    });

    group.finish();
}

criterion_group!(benches, bench_per_file_lookup);
criterion_main!(benches);

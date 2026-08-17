#!/usr/bin/env node
// Build (or serve) the vault as a website, without vendoring Quartz.
//
// Quartz is ~140 files and 16MB of framework, of which exactly one file here is
// ours: quartz.config.yaml. So instead of committing a fork, this fetches Quartz
// at a pinned commit into a gitignored .quartz-build/ and builds from there.
// Upgrading is a one-line change to QUARTZ_REF below.
//
// You do NOT need to run this locally — CI builds and deploys on push. It is
// only for previewing before you push, and the first run costs a few minutes
// and ~360MB for Quartz's dependency tree.
//
//   node site/quartz.mjs build     -> .quartz-build/public
//   node site/quartz.mjs serve     -> local preview with hot reload

import { execFileSync } from "node:child_process"
import { mkdir, rm, readFile, writeFile } from "node:fs/promises"
import { existsSync } from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const QUARTZ_REPO = "https://github.com/jackyzha0/quartz.git"

// A commit, deliberately, not a tag: refs/tags/v5.0.0 does not peel to a commit
// ("is not a commit!"), so `clone --branch v5.0.0` silently falls back to the
// default branch and the pin does nothing. This SHA is Quartz 5.0.0.
const QUARTZ_REF = "ab346fa66a895e12d63a308e70ce330ba795822a"

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.join(here, "..")
// Not named `.quartz`: Quartz generates its own `.quartz/plugins` index inside
// whatever directory it runs from, and two things by that name is confusing.
const checkout = path.join(root, ".quartz-build")
const vault = path.join(root, "vault")
const stamp = path.join(checkout, ".pinned-ref")
const installed = path.join(checkout, ".deps-installed")

const command = process.argv[2] ?? "build"
const passthrough = process.argv.slice(3)

const run = (file, args, cwd) =>
  execFileSync(file, args, { cwd, stdio: "inherit", shell: process.platform === "win32" })

async function readStamp(file) {
  try {
    return (await readFile(file, "utf-8")).trim()
  } catch {
    return null
  }
}

// Re-fetch when the pin changes, so upgrading is just editing QUARTZ_REF.
if ((await readStamp(stamp)) !== QUARTZ_REF) {
  console.log(`> fetching quartz ${QUARTZ_REF.slice(0, 10)}`)
  await rm(checkout, { recursive: true, force: true })
  await mkdir(checkout, { recursive: true })
  // init + fetch rather than clone: this accepts a raw commit SHA, which
  // `clone --branch` does not.
  run("git", ["init", "-q", "."], checkout)
  run("git", ["remote", "add", "origin", QUARTZ_REPO], checkout)
  run("git", ["fetch", "-q", "--depth", "1", "origin", QUARTZ_REF], checkout)
  run("git", ["checkout", "-q", "FETCH_HEAD"], checkout)
  await rm(path.join(checkout, ".git"), { recursive: true, force: true })
  await writeFile(stamp, `${QUARTZ_REF}\n`, "utf-8")
}

// Our config is the only file we own; copy it over Quartz's default.
//
// QUARTZ_BASE_URL overrides baseUrl so the same vault can be published to more
// than one host. Quartz bakes baseUrl into absolute links, the sitemap and OG
// images, and GitHub Pages and GitLab Pages serve at different URLs — GitLab
// may even assign a unique domain you cannot predict, so its CI passes
// CI_PAGES_URL through this.
let config = await readFile(path.join(here, "quartz.config.yaml"), "utf-8")
if (process.env.QUARTZ_BASE_URL) {
  const baseUrl = process.env.QUARTZ_BASE_URL.replace(/^\w+:\/\//, "").replace(/\/$/, "")
  config = config.replace(/^(\s*)baseUrl:.*$/m, `$1baseUrl: "${baseUrl}"`)
  console.log(`> baseUrl ${baseUrl}`)
}
await writeFile(path.join(checkout, "quartz.config.yaml"), config, "utf-8")

// Check a stamp rather than node_modules/: an interrupted install leaves a
// half-populated directory that would otherwise be treated as complete, and
// the build then fails on whichever package didn't make it.
if (!existsSync(installed)) {
  console.log("> installing dependencies (a few minutes on first run)")
  // --include=optional is required: npm otherwise skips the platform-native
  // builds sharp and lightningcss need, and the build dies on a missing .node
  run("npm", ["install", "--include=optional", "--no-audit", "--no-fund"], checkout)
  await writeFile(installed, `${QUARTZ_REF}\n`, "utf-8")
}

// Generates .quartz/plugins inside the checkout, which quartz/components/Head.tsx
// imports as "../../.quartz/plugins". Upstream hangs this off an npm `prebuild`
// hook, so calling bootstrap-cli directly skips it and the build fails with
// `Could not resolve "../../.quartz/plugins"`. Run every time: the index is
// derived from quartz.config.yaml, which we may have just changed.
console.log("> generating plugin index")
run("npm", ["run", "install-plugins"], checkout)

// Build from the tracked vault directly. Never copy it into the checkout:
// Quartz globs content with gitignore:true, so a gitignored copy would be
// silently invisible and the site would come out empty.
const args = ["./quartz/bootstrap-cli.mjs", "build", "-d", path.relative(checkout, vault)]
if (command === "serve") args.push("--serve")
run("node", [...args, ...passthrough], checkout)

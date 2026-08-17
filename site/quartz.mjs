#!/usr/bin/env node
// Build (or serve) the vault as a website, without vendoring Quartz.
//
// Quartz is ~140 files and 16MB of framework, of which exactly one file here is
// ours: quartz.config.yaml. So instead of committing a fork, this clones Quartz
// at a pinned tag into a gitignored .quartz/ and builds from there. Upgrading is
// a one-line change to QUARTZ_REF below.
//
// You do NOT need to run this locally — CI builds and deploys on push. It is
// only for previewing before you push, and the first run costs a few minutes
// and ~360MB for Quartz's dependency tree.
//
//   node site/quartz.mjs build     -> .quartz/public
//   node site/quartz.mjs serve     -> local preview with hot reload

import { execFileSync } from "node:child_process"
import { cp, mkdir, rm, readFile, writeFile } from "node:fs/promises"
import { existsSync } from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const QUARTZ_REPO = "https://github.com/jackyzha0/quartz.git"
const QUARTZ_REF = "v5.0.0" // bump to upgrade; check the tag exists first

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.join(here, "..")
const checkout = path.join(root, ".quartz")
const vault = path.join(root, "vault")
const stamp = path.join(checkout, ".pinned-ref")
const installed = path.join(checkout, ".deps-installed")

const command = process.argv[2] ?? "build"
const passthrough = process.argv.slice(3)

const run = (file, args, cwd) =>
  execFileSync(file, args, { cwd, stdio: "inherit", shell: process.platform === "win32" })

async function pinnedRefOnDisk() {
  try {
    return (await readFile(stamp, "utf-8")).trim()
  } catch {
    return null
  }
}

// Re-clone when the pin changes, so upgrading is just editing QUARTZ_REF.
if ((await pinnedRefOnDisk()) !== QUARTZ_REF) {
  console.log(`> fetching quartz ${QUARTZ_REF}`)
  await rm(checkout, { recursive: true, force: true })
  await mkdir(checkout, { recursive: true })
  run("git", ["clone", "--depth", "1", "--branch", QUARTZ_REF, QUARTZ_REPO, checkout], root)
  await rm(path.join(checkout, ".git"), { recursive: true, force: true })
  await writeFile(stamp, `${QUARTZ_REF}\n`, "utf-8")
}

// Our config is the only file we own; copy it over Quartz's default.
await cp(path.join(here, "quartz.config.yaml"), path.join(checkout, "quartz.config.yaml"))

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

// Build from the tracked vault directly. Never copy it into the checkout:
// Quartz globs content with gitignore:true, so a gitignored copy would be
// silently invisible and the site would come out empty.
const args = ["./quartz/bootstrap-cli.mjs", "build", "-d", path.relative(checkout, vault)]
if (command === "serve") args.push("--serve")
run("node", [...args, ...passthrough], checkout)

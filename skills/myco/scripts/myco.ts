import { createHash } from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

process.umask(0o077);

// The production relay the app uses (myco-app config.toml production_uri).
// Private/LAN relays belong in MYCO_RELAY_URL.
const DEFAULT_RELAY = 'https://relay.myco.network';
const DEFAULT_WORKFLOW = ['Backlog', 'Ready', 'In Progress', 'Review', 'Done'];
const STATE_VERSION = 2;
// Must match myco-app lib/myco/identity-connect.ts: the receiving app offers
// "Add to Identity" only for a trust request carrying this exact message.
const IDENTITY_CONNECT_MESSAGE = 'Wants to connect to your current identity';

type Dict = Record<string, any>;
type ParsedArgs = { command: string; flags: Map<string, string | boolean>; positionals: string[] };

function parseArgs(argv: string[]): ParsedArgs {
  const [command = 'help', ...rest] = argv;
  const flags = new Map<string, string | boolean>();
  const positionals: string[] = [];
  for (let i = 0; i < rest.length; i += 1) {
    const arg = rest[i];
    if (!arg.startsWith('--')) {
      positionals.push(arg);
      continue;
    }
    const eq = arg.indexOf('=');
    if (eq > 2) {
      flags.set(arg.slice(2, eq), arg.slice(eq + 1));
      continue;
    }
    const name = arg.slice(2);
    const next = rest[i + 1];
    if (next !== undefined && !next.startsWith('--')) {
      flags.set(name, next);
      i += 1;
    } else {
      flags.set(name, true);
    }
  }
  return { command, flags, positionals };
}

function flag(args: ParsedArgs, name: string): string | undefined {
  const value = args.flags.get(name);
  return typeof value === 'string' ? value : undefined;
}

function has(args: ParsedArgs, name: string): boolean {
  return args.flags.has(name);
}

function fail(message: string, code = 2): never {
  console.error(`myco: ${message}`);
  process.exit(code);
}

function output(value: unknown, json: boolean): void {
  if (json || typeof value !== 'string') console.log(JSON.stringify(value, null, 2));
  else console.log(value);
}

function help(): void {
  console.log(`Myco — operate a Myco device identity from the command line

This CLI holds one DEVICE key per data directory. It acts as a person's Myco
identity once that identity adds the device (app: connect, then accept the
"Add to Identity" request, then join).

Usage:
  myco doctor [--json]
  myco init [--json]                                   # create the device key
  myco identity [--json]                               # device DID + identities it can act as
  myco connect --device DID [--peer] [--dry-run] [--json]  # ask a device to add this one to its identity (--peer: contact only)
  myco join [--entity ENTITY_ID] [--dry-run] [--json]  # accept pending invites
  myco groups [--search NAME] [--all] [--json]
  myco entity --id ENTITY_ID [--acl] [--json]
  myco messages --entity ENTITY_ID [--limit N] [--json]
  myco peers [--json]
  myco sync [--json]                                   # one receive/answer/push cycle
  myco share-key --provider P --to MANAGER_DID [--name N] [--dry-run] [--json]  # key from keyring (myco llm-P)
  myco requests [--json]                               # inbound connection requests
  myco trust --did DID [--dry-run] [--json]            # accept one / trust a peer
  myco add-peer --peer-link URL [--dry-run] [--json]
  myco remove-peer --did DID [--dry-run] [--json]
  myco invite --entity ENTITY_ID --did DID [--dry-run] [--json]
  myco edit-acl --entity ENTITY_ID --slot SLOT --value JSON [--tier public|private] [--dry-run] [--json]
  myco create-group --name NAME [--description TEXT] [--template Company|Cooperative|Council|Community|PirateDemocracy] [--dry-run] [--json]
  myco create-agent --entity GROUP --name NAME --manager DID [--keys minimax,deepseek] [--description TEXT] [--instructions TEXT | --instructions-file F] [--dry-run] [--json]
  myco edit --id POST --field NAME --value TEXT [--dry-run] [--json]
  myco post --entity ENTITY_ID --title TITLE [--body TEXT] [--space NAME] [--public] [--dry-run] [--json]
  myco snapshot --entity ENTITY_ID [--repo PATH] [--json]
  myco reconcile --entity ENTITY_ID --file FILE [--repo PATH] [--dry-run] [--json]
  myco move --key KEY --status STATUS [--repo PATH] [--dry-run] [--json]
  myco close --key KEY [--repo PATH] [--dry-run] [--json]

Writes act as the identity this device belongs to (--as DID picks one when it
belongs to several; --as device acts as the bare device key).

Environment:
  MYCO_ROOT       Myco checkout (default: /home/user/code/myco)
  MYCO_DATA_DIR   device data (default: ~/.local/share/myco-llm)
  MYCO_RELAY_URL  relay URL(s), comma-separated, or "local" for isolated use
`);
}

function config() {
  const mycoRoot = path.resolve(process.env.MYCO_ROOT || '/home/user/code/myco');
  const dataDir = path.resolve(
    process.env.MYCO_DATA_DIR
      || path.join(process.env.XDG_DATA_HOME || path.join(os.homedir(), '.local', 'share'), 'myco-llm'),
  );
  return {
    mycoRoot,
    agentRoot: path.join(mycoRoot, 'myco-agent'),
    dataDir,
    relay: process.env.MYCO_RELAY_URL || DEFAULT_RELAY,
    didFile: path.join(dataDir, 'device-did'),
    stateFile: path.join(dataDir, 'kanban-state.json'),
    requestsFile: path.join(dataDir, 'trust-requests.json'),
  };
}
type Config = ReturnType<typeof config>;

function readText(file: string): string | undefined {
  try { return fs.readFileSync(file, 'utf8').trim(); } catch { return undefined; }
}

function writePrivate(file: string, value: string): void {
  fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
  const temp = `${file}.tmp-${process.pid}`;
  fs.writeFileSync(temp, value, { encoding: 'utf8', mode: 0o600 });
  fs.renameSync(temp, file);
}

function readState(cfg: Config): Dict {
  const raw = readText(cfg.stateFile);
  if (!raw) return { version: STATE_VERSION, repositories: {} };
  let parsed: Dict;
  try { parsed = JSON.parse(raw); } catch { fail(`invalid state JSON at ${cfg.stateFile}`); }
  if (parsed.version !== STATE_VERSION || typeof parsed.repositories !== 'object') {
    fail(`unsupported state format at ${cfg.stateFile}`);
  }
  return parsed;
}

function readRequests(cfg: Config): Dict[] {
  try { return JSON.parse(readText(cfg.requestsFile) || '[]'); } catch { return []; }
}

function writeState(cfg: Config, state: Dict): void {
  writePrivate(cfg.stateFile, `${JSON.stringify(state, null, 2)}\n`);
}

function canonicalRepo(input?: string): string {
  const candidate = path.resolve(input || process.cwd());
  try { return fs.realpathSync(candidate); } catch { fail(`repository path does not exist: ${candidate}`); }
}

function repoHash(repo: string): string {
  return createHash('sha256').update(repo).digest('hex').slice(0, 20);
}

function encodeKey(key: string): string {
  return Buffer.from(key, 'utf8').toString('base64url');
}

function marker(repoId: string, key: string): string {
  return `<!-- myco-kanban:v1 repo=${repoId} key=${encodeKey(key)} -->`;
}

function taskDescription(task: Dict, repoId: string): string {
  const parts: string[] = [];
  if (typeof task.description === 'string' && task.description.trim()) parts.push(task.description.trim());
  if (Array.isArray(task.evidence) && task.evidence.length) {
    parts.push(['Evidence:', ...task.evidence.map((item: string) => `- ${item}`)].join('\n'));
  }
  parts.push(marker(repoId, task.key));
  return parts.join('\n\n');
}

function parseMarker(description: unknown): { repo: string; key: string } | undefined {
  if (typeof description !== 'string') return undefined;
  const match = description.match(/<!-- myco-kanban:v1 repo=([a-f0-9]+) key=([A-Za-z0-9_-]+) -->/);
  if (!match) return undefined;
  try { return { repo: match[1], key: Buffer.from(match[2], 'base64url').toString('utf8') }; } catch { return undefined; }
}

// Same code the app shows for a pairing (myco-app lib/myco/identity-connect.ts),
// so the person can check the request on their device came from this one.
function pairingCode(a: string, b: string): string {
  const [first, second] = [a, b].sort();
  const digest = createHash('sha256').update(`myco-pairing:${first}|${second}`).digest();
  const value = ((digest[0] << 16) | (digest[1] << 8) | digest[2]) % 1_000_000;
  const digits = value.toString().padStart(6, '0');
  return `${digits.slice(0, 3)} ${digits.slice(3)}`;
}

function peerLink(did: string): string {
  return `myco://peer?${new URLSearchParams({ id: did }).toString()}`;
}

function parsePeerLink(raw: string): string {
  const query = raw.indexOf('?');
  if (query < 0) fail('peer link has no query parameters');
  const id = new URLSearchParams(raw.slice(query + 1)).get('id');
  if (!id?.startsWith('did:')) fail('peer link must contain a DID');
  return id;
}

async function loadMyco(cfg: Config): Promise<Dict> {
  const packageFile = path.join(cfg.agentRoot, 'package.json');
  if (!fs.existsSync(packageFile)) fail(`Myco agent checkout not found at ${cfg.agentRoot}`);
  const requireFromMyco = createRequire(packageFile);
  const importPackage = async (name: string) => import(pathToFileURL(requireFromMyco.resolve(name)).href);
  const source = async (relative: string) => import(pathToFileURL(path.join(cfg.agentRoot, relative)).href);
  const modules = await Promise.all([
    importPackage('@mycoprotocol/client'),
    importPackage('@wasteprotocol/wb-sqlite'),
    importPackage('@wasteprotocol/core'),
    source('src/db-sqlite.ts'),
    source('src/create-client.ts'),
    source('src/keyring.ts'),
    source('src/transport.ts'),
    source('src/sqlite-secret-store.ts'),
  ]);
  return Object.assign({}, ...modules);
}

// Storage, keys and relays exactly as a myco-agent runtime opens them: one
// file-backed keyring in the data dir seals the stores and the key row.
async function openClient(cfg: Config, modules: Dict, create: boolean): Promise<Dict> {
  const existingDid = readText(cfg.didFile);
  if (!existingDid && !create) fail('device is not initialized; run init first');
  fs.mkdirSync(cfg.dataDir, { recursive: true, mode: 0o700 });
  const keyring = modules.openAgentKeyring(cfg.dataDir);
  const { KEYRING_LABELS } = modules;
  const db = new modules.SqliteDB(path.join(cfg.dataDir, 'myco.db'), {
    sqlcipherKeyHex: keyring.sqlcipherKeyHex(KEYRING_LABELS.mycoDb),
    keyCrypto: keyring.crypto(KEYRING_LABELS.keys),
  });
  await db.connect();
  const wb = new modules.SqliteWasteBin(path.join(cfg.dataDir, 'waste.db'), keyring.sqlcipherKeyHex(KEYRING_LABELS.wasteDb));
  await wb.connect();
  const local = ['local', 'none'].includes(cfg.relay.trim().toLowerCase());
  const relayUrls = local ? [] : cfg.relay.split(',').map((s) => s.trim()).filter(Boolean);
  const relayConfig = { relayUrl: relayUrls[0], relayUrls, hostedMode: false };
  // Owner-side shared secrets (LLM keys for hosted agents), sealed under the keyring.
  const secretStore = new modules.SqliteSecretStore(path.join(cfg.dataDir, 'secrets.db'), keyring.sqlcipherKeyHex(KEYRING_LABELS.secretsDb));
  await secretStore.connect();
  const bundle = await modules.createClientBundle(db, wb, modules.buildTransports(relayConfig), {
    ...(existingDid ? { existingDid } : {}),
    secretStore,
  });
  if (!existingDid) writePrivate(cfg.didFile, `${bundle.client.id}\n`);
  // Inbound connection requests: journal them for `requests`/`trust` and
  // answer nothing now — a person decides, not this process.
  bundle.waste.registerTrustHandler(async (request: Dict) => {
    const pending = readRequests(cfg).filter((r) => r.origin !== request.origin);
    pending.push({ origin: request.origin, message: request.message ?? null, receivedAt: new Date().toISOString() });
    writePrivate(cfg.requestsFile, `${JSON.stringify(pending, null, 2)}\n`);
    return 'ignore';
  });
  await modules.ensureRelays(bundle.waste, relayConfig);
  return { client: bundle.client, waste: bundle.waste, secrets: bundle.secrets, db, wb, createdDid: !existingDid };
}

async function safeSync(client: any, waste: any): Promise<string | undefined> {
  try {
    // A short-lived process exits before receiver timers fire: poll each now.
    for (const t of Object.values(waste.getTransports())) {
      try { await (t as any).poll?.(); } catch { /* best-effort */ }
    }
    await client.sync();
    return undefined;
  } catch (error: any) {
    return error?.message || String(error);
  }
}

function syncResult(...errors: Array<string | undefined>): Dict {
  const found = errors.filter(Boolean);
  return found.length ? { ok: false, errors: found } : { ok: true };
}

// Identities this device can act as directly: entities it is itself a member
// of (avatars). Groups those identities belong to are reached through them.
function identities(ctx: Dict): Dict[] {
  return ctx.client.availableIdentities()
    .filter((entity: any) => {
      const view = viewOf(ctx.modules, entity);
      return view && ctx.modules.memberList(view).includes(ctx.client.id);
    })
    .map((entity: any) => ({
    id: entity.id,
    name: viewOf(ctx.modules, entity)?.public?.name || entity.id,
  }));
}

// The identity writes are authored as: --as, else the one identity the device
// belongs to. Never guessed among several.
function actingAs(args: ParsedArgs, ctx: Dict): string {
  const requested = flag(args, 'as');
  if (requested === 'device') return ctx.client.id;
  const available = identities(ctx);
  if (requested) {
    if (!available.some((item) => item.id === requested)) fail(`this device cannot act as ${requested}`);
    return requested;
  }
  if (available.length === 1) return available[0].id;
  if (!available.length) fail('this device belongs to no identity yet (connect, then join), or pass --as device');
  fail(`this device belongs to several identities; pass --as one of: ${available.map((item) => item.id).join(', ')}`);
}

async function opened(args: ParsedArgs): Promise<Dict> {
  const cfg = config();
  const modules = await loadMyco(cfg);
  const ctx = { cfg, modules, ...(await openClient(cfg, modules, false)), json: has(args, 'json') };
  ctx.syncError = await safeSync(ctx.client, ctx.waste);
  return ctx;
}

function messageId(modules: Dict, signed: any): string {
  return modules.getMessageId(modules.getMessageHash(signed.message));
}

function viewOf(modules: Dict, entity: any): any | undefined {
  try { return modules.currentView(entity); } catch { return undefined; }
}

function entityOrFail(ctx: Dict, id: string | undefined, command: string): any {
  if (!id) fail(`${command} requires --entity`);
  const entity = ctx.client.entities.find((item: any) => item.id === id);
  if (!entity) fail(`entity is not present locally: ${id} (join or sync it first)`);
  return entity;
}

function permitted(ctx: Dict, entityId: string, propagation: any, type: string, creator: string): boolean {
  try {
    return ctx.client.isMessagePermitted(entityId, propagation, type, undefined, undefined, undefined, { creator });
  } catch {
    return false;
  }
}

function content(message: any): Dict {
  return (message?.data?.content || {}) as Dict;
}

async function boardMessages(ctx: Dict, entityId: string): Promise<Dict> {
  const { MessageType } = ctx.modules;
  const all = await ctx.client.getMessagesByEntity(entityId, { types: [MessageType.Project, MessageType.Task] });
  const projects: Dict[] = [];
  const tasks: Dict[] = [];
  for (const base of all) {
    if (base.deleted) continue;
    const effective = await ctx.client.getEffectiveMessage(base.id);
    const item = { id: base.id, message: effective };
    if (effective?.data?.type === MessageType.Project) projects.push(item);
    else if (effective?.data?.type === MessageType.Task) tasks.push(item);
  }
  return { projects, tasks };
}

function validateManifest(raw: Dict): Dict {
  if (!raw || raw.version !== 1) fail('manifest.version must be 1');
  const project = raw.project;
  if (!project || typeof project.key !== 'string' || !project.key.trim()) fail('manifest.project.key is required');
  if (typeof project.title !== 'string' || !project.title.trim()) fail('manifest.project.title is required');
  const workflow = project.workflow || DEFAULT_WORKFLOW;
  if (!Array.isArray(workflow) || !workflow.length || workflow.some((x: unknown) => typeof x !== 'string' || !x.trim())) {
    fail('manifest.project.workflow must contain non-empty strings');
  }
  if (new Set(workflow).size !== workflow.length) fail('manifest.project.workflow columns must be unique');
  if (!Array.isArray(raw.tasks)) fail('manifest.tasks must be an array');
  const keys = new Set<string>();
  for (const task of raw.tasks) {
    if (!task || typeof task.key !== 'string' || !task.key.trim()) fail('every task requires a non-empty key');
    if (keys.has(task.key)) fail(`duplicate task key: ${task.key}`);
    keys.add(task.key);
    if (typeof task.title !== 'string' || !task.title.trim()) fail(`task ${task.key} requires a title`);
    if (typeof task.status !== 'string' || !workflow.includes(task.status)) fail(`task ${task.key} status is not in the workflow`);
    if (task.description !== undefined && typeof task.description !== 'string') fail(`task ${task.key} description must be a string`);
    if (task.evidence !== undefined && (!Array.isArray(task.evidence) || task.evidence.some((x: unknown) => typeof x !== 'string'))) {
      fail(`task ${task.key} evidence must be an array of strings`);
    }
    if (task.closed !== undefined && typeof task.closed !== 'boolean') fail(`task ${task.key} closed must be boolean`);
  }
  return { version: 1, project: { ...project, workflow }, tasks: raw.tasks };
}

async function editField(ctx: Dict, creator: string, item: Dict, keys: string[], value: unknown): Promise<void> {
  await ctx.client.createMessage({ keys, value }, ctx.modules.MessageType.Edit, item.id, item.message.data.propagation, { creator });
}

async function commandDoctor(args: ParsedArgs): Promise<void> {
  const cfg = config();
  const checks = {
    mycoRoot: fs.existsSync(cfg.mycoRoot),
    agentPackage: fs.existsSync(path.join(cfg.agentRoot, 'package.json')),
    tsx: fs.existsSync(path.join(cfg.agentRoot, 'node_modules', 'tsx', 'dist', 'loader.mjs')),
    agentDeps: fs.existsSync(path.join(cfg.agentRoot, 'node_modules', '@wasteprotocol', 'crypto')),
    mycoClient: fs.existsSync(path.join(cfg.mycoRoot, 'myco-ts', 'dist', 'index.js')),
    dataDir: cfg.dataDir,
    relay: cfg.relay,
    initialized: Boolean(readText(cfg.didFile)),
  };
  const ok = checks.mycoRoot && checks.agentPackage && checks.tsx && checks.agentDeps && checks.mycoClient;
  output({ ok, checks }, has(args, 'json'));
  if (!ok) process.exitCode = 1;
}

async function commandInit(args: ParsedArgs): Promise<void> {
  const cfg = config();
  const modules = await loadMyco(cfg);
  const { client, waste, createdDid } = await openClient(cfg, modules, true);
  const syncError = await safeSync(client, waste);
  output({
    createdDevice: createdDid,
    deviceDid: client.id,
    peerLink: peerLink(client.id),
    relay: cfg.relay,
    dataDir: cfg.dataDir,
    sync: syncResult(syncError),
  }, has(args, 'json'));
}

async function commandIdentity(args: ParsedArgs): Promise<void> {
  const cfg = config();
  if (!readText(cfg.didFile)) {
    output({ initialized: false, dataDir: cfg.dataDir, next: 'run init' }, has(args, 'json'));
    return;
  }
  const ctx = await opened(args);
  output({
    initialized: true,
    deviceDid: ctx.client.id,
    peerLink: peerLink(ctx.client.id),
    identities: identities(ctx),
    relay: cfg.relay,
    dataDir: cfg.dataDir,
    sync: syncResult(ctx.syncError),
  }, ctx.json);
}

// The app's "Connect Device" request, sent from this device: peer with and
// trust the person's device, then ask it to add this one to the identity it is
// acting as. The person accepts on their device; `join` then accepts the Join.
async function commandConnect(args: ParsedArgs): Promise<void> {
  const target = flag(args, 'device');
  if (!target?.startsWith('did:')) fail('connect requires --device DID (the other device\'s DID, e.g. did:key:...)');
  const dryRun = has(args, 'dry-run');
  const ctx = await opened(args);
  if (target === ctx.client.id) fail("that is this device's own DID");
  const peerOnly = has(args, 'peer');
  if (!dryRun) {
    await ctx.waste.addPeer({ id: target, publicKey: ctx.modules.getPublicKey(target).publicKey });
    await ctx.waste.setTrust(target, true);
    // --peer: a plain contact request (mutual trust only), not "Add to Identity".
    await ctx.waste.gossip(target, { respond: true, message: peerOnly ? 'Connect' : IDENTITY_CONNECT_MESSAGE });
    await ctx.waste.push();
  }
  output({
    dryRun,
    deviceDid: ctx.client.id,
    to: target,
    requested: !dryRun,
    kind: peerOnly ? 'contact' : 'add-to-identity',
    pairingCode: pairingCode(ctx.client.id, target),
    next: peerOnly ? 'accept the request on that device' : 'accept "Add to Identity" on that device (check the pairing code), then run join',
    sync: syncResult(ctx.syncError),
  }, ctx.json);
}

// Accept pending Joins naming this device or an identity it can act as. Only
// the nominee may author the Accept.
async function commandJoin(args: ParsedArgs): Promise<void> {
  const scope = flag(args, 'entity');
  const dryRun = has(args, 'dry-run');
  const ctx = await opened(args);
  const { MessageType, Propagation } = ctx.modules;
  const nominees = new Set([ctx.client.id, ...identities(ctx).map((item) => item.id)]);
  const results: Dict[] = [];
  for (const entity of ctx.client.entities) {
    if (scope && entity.id !== scope) continue;
    // Settled as the app judges it (use-pending-joins): resolved, or already a member.
    const view = viewOf(ctx.modules, entity);
    const members: string[] = view ? ctx.modules.memberList(view) : [];
    const resolved = (id: string) => Boolean(view?.public?.resolvedJoins?.[id] ?? view?.private?.resolvedJoins?.[id]);
    for (const join of await ctx.client.getMessagesByEntity(entity.id, { types: [MessageType.Join] })) {
      const nominee = join.message?.data?.content?.nominee;
      if (join.message?.data?.type !== MessageType.Join || !nominees.has(nominee)) continue;
      const entry: Dict = { entity: entity.id, joinId: join.id, nominee };
      if (members.includes(nominee)) entry.status = 'already-member';
      else if (resolved(join.id)) entry.status = 'resolved';
      else if (dryRun) entry.status = 'pending';
      else {
        try {
          await ctx.client.createMessage({}, MessageType.Accept, join.id, Propagation.Private, { creator: nominee });
          entry.status = 'accepted';
        } catch (e: any) {
          entry.status = 'failed';
          entry.error = e?.message ?? String(e);
        }
      }
      results.push(entry);
    }
  }
  const pushError = dryRun || !results.some((r) => r.status === 'accepted') ? undefined : await safeSync(ctx.client, ctx.waste);
  output({
    deviceDid: ctx.client.id,
    dryRun,
    results,
    identities: identities(ctx),
    sync: syncResult(ctx.syncError, pushError),
  }, ctx.json);
}

async function commandGroups(args: ParsedArgs): Promise<void> {
  const ctx = await opened(args);
  const search = flag(args, 'search')?.toLowerCase();
  const all = has(args, 'all');
  const self = new Set([ctx.client.id, ...identities(ctx).map((item) => item.id)]);
  const groups: Dict[] = [];
  for (const entity of ctx.client.entities) {
    const view = viewOf(ctx.modules, entity);
    if (!view?.public) continue;
    const members: string[] = ctx.modules.memberList(view);
    const member = members.some((m) => self.has(m));
    if (!all && !member) continue;
    const name = view.public.name || entity.id;
    if (search && !String(name).toLowerCase().includes(search) && !entity.id.toLowerCase().includes(search)) continue;
    groups.push({ id: entity.id, name, description: view.public.description || '', memberCount: members.length, member });
  }
  output({ deviceDid: ctx.client.id, count: groups.length, groups, sync: syncResult(ctx.syncError) }, ctx.json);
}

async function commandEntity(args: ParsedArgs): Promise<void> {
  const id = flag(args, 'id');
  if (!id) fail('entity requires --id');
  const ctx = await opened(args);
  const entity = ctx.client.entities.find((item: any) => item.id === id);
  if (!entity) {
    output({ found: false, id, reason: 'not present locally; this device has not received or joined it', sync: syncResult(ctx.syncError) }, ctx.json);
    process.exitCode = 1;
    return;
  }
  const view = viewOf(ctx.modules, entity);
  if (!view) fail(`cannot compute current view for ${id}`);
  const members: string[] = ctx.modules.memberList(view);
  const result: Dict = {
    found: true,
    id: entity.id,
    type: entity.type,
    creator: entity.creator,
    name: view.public?.name || view.state?.name || entity.id,
    description: view.public?.description || '',
    members,
    sync: syncResult(ctx.syncError),
  };
  if (has(args, 'acl')) {
    const creator = flag(args, 'as') ? actingAs(args, ctx) : ctx.client.currentIdentity();
    const canCreate: Dict = {};
    for (const t of ['note', 'task', 'project', 'topic', 'link', 'proposal']) {
      canCreate[t] = permitted(ctx, id, ctx.modules.Propagation.Private, t, creator);
    }
    let recipients: string[] = [];
    try { recipients = ctx.client.getPeersFromEntity(entity, []).recipients; } catch { /* not resolvable */ }
    result.acl = { publicAcl: view.public?.acl || {}, privateAcl: view.private?.acl || {}, canCreate, as: creator, recipients };
  }
  output(result, ctx.json);
}

async function commandMessages(args: ParsedArgs): Promise<void> {
  const ctx = await opened(args);
  const entity = entityOrFail(ctx, flag(args, 'entity'), 'messages');
  const limit = Number.parseInt(flag(args, 'limit') || '50', 10);
  const rows = (await ctx.client.getMessagesByEntity(entity.id))
    .filter((m: any) => !m.deleted)
    .sort((a: any, b: any) => (b.timestamp || 0) - (a.timestamp || 0) || String(b.id).localeCompare(String(a.id)))
    .slice(0, Number.isFinite(limit) && limit > 0 ? limit : 50)
    .map((m: any) => {
      const data = m.message?.data || {};
      const c = data.content || {};
      return {
        id: m.id,
        type: data.type,
        creator: data.creator,
        timestamp: m.timestamp,
        ...(c.title ? { title: c.title } : {}),
        ...(c.body ? { body: c.body } : {}),
      };
    });
  output({ entity: entity.id, count: rows.length, messages: rows, sync: syncResult(ctx.syncError) }, ctx.json);
}

async function commandRequests(args: ParsedArgs): Promise<void> {
  const ctx = await opened(args);
  const requests = readRequests(ctx.cfg).map((r) => ({
    ...r,
    identityConnect: r.message?.trim() === IDENTITY_CONNECT_MESSAGE,
    pairingCode: pairingCode(ctx.client.id, r.origin),
  }));
  output({ deviceDid: ctx.client.id, requests, sync: syncResult(ctx.syncError) }, ctx.json);
}

// Accept a connection request (or trust a peer outright), as the app does:
// trust, answer with our advertisement, flush.
async function commandTrust(args: ParsedArgs): Promise<void> {
  const did = flag(args, 'did');
  if (!did?.startsWith('did:')) fail('trust requires --did DID');
  const dryRun = has(args, 'dry-run');
  const ctx = await opened(args);
  const request = readRequests(ctx.cfg).find((r) => r.origin === did);
  if (!dryRun) {
    if (!ctx.waste.getPeers().some((p: any) => p.id === did)) {
      await ctx.waste.addPeer({ id: did, publicKey: ctx.modules.getPublicKey(did).publicKey });
    }
    await ctx.waste.setTrust(did, true);
    await ctx.waste.gossip(did);
    await ctx.waste.push();
    writePrivate(ctx.cfg.requestsFile, `${JSON.stringify(readRequests(ctx.cfg).filter((r) => r.origin !== did), null, 2)}\n`);
  }
  output({ dryRun, trusted: !dryRun, peerDid: did, request: request ?? null, sync: syncResult(ctx.syncError) }, ctx.json);
}

// Share an LLM provider key with a hosted agent manager. The value comes from
// the desktop keyring (secret-tool lookup myco llm-<provider>) and is never
// printed; it travels as a transient ShareSecret, and agents reference it as
// secret://<this device>/<provider>:<name>.
async function commandShareKey(args: ParsedArgs): Promise<void> {
  const provider = flag(args, 'provider');
  const to = flag(args, 'to');
  const name = flag(args, 'name') || 'default';
  if (!provider || !/^[a-z]+$/.test(provider)) fail('share-key requires --provider (e.g. minimax, deepseek)');
  if (!to?.startsWith('did:')) fail('share-key requires --to <manager DID>');
  const { spawnSync } = await import('node:child_process');
  const lookup = spawnSync('secret-tool', ['lookup', 'myco', `llm-${provider}`], { encoding: 'utf8' });
  const value = lookup.status === 0 ? lookup.stdout.trim() : '';
  if (!value) fail(`no key in the keyring; store it with: secret-tool store --label='Myco ${provider}' myco llm-${provider}`);
  const dryRun = has(args, 'dry-run');
  const ctx = await opened(args);
  const key = `${provider}:${name}`;
  let shared = false;
  if (!dryRun) {
    const existing = await ctx.secrets.getSecrets(ctx.client.id).catch(() => undefined);
    const held = Array.isArray(existing) ? existing.find((s: any) => s.key === key) : undefined;
    if (!held) shared = await ctx.secrets.addSecret(key, value, [to]);
    else {
      shared = await ctx.secrets.updateSecretValue(key, value);
      const peers: string[] = held.peers ?? [];
      if (!peers.includes(to)) shared = (await ctx.secrets.updateSecretPeers(key, [...peers, to])) && shared;
    }
  }
  const pushError = shared ? await safeSync(ctx.client, ctx.waste) : undefined;
  output({
    dryRun,
    shared,
    key,
    to,
    ref: `secret://${ctx.client.id}/${key}`,
    sync: syncResult(ctx.syncError, pushError),
  }, ctx.json);
  if (!dryRun && !shared) process.exitCode = 1;
}

// One sync cycle: receive, answer queued requests (e.g. a manager asking for a
// shared key), push. For schedulers keeping this device responsive.
async function commandSync(args: ParsedArgs): Promise<void> {
  const ctx = await opened(args);
  const pushError = await safeSync(ctx.client, ctx.waste);
  output({ deviceDid: ctx.client.id, sync: syncResult(ctx.syncError, pushError) }, ctx.json);
}

async function commandPeers(args: ParsedArgs): Promise<void> {
  const ctx = await opened(args);
  const connections = (did?: string) => (ctx.waste.getConnections(did) ?? []).map((c: any) => ({
    connectionId: c.connectionId, transportType: c.transportType, posture: c.posture,
  }));
  // Messages waiting for a route, per recipient: a growing count means this
  // device knows no relay the peer listens on.
  const queued: Record<string, number> = {};
  for (const entry of await ctx.wb.getCache(ctx.client.id, 'queued')) {
    if (entry.peer) queued[entry.peer] = (queued[entry.peer] || 0) + 1;
  }
  const peers = ctx.waste.getPeers().map((p: any) => ({
    id: p.id,
    trusted: ctx.waste.isTrusted(p.id),
    queued: queued[p.id] || 0,
    connections: connections(p.id),
  }));
  output({ deviceDid: ctx.client.id, peers, ownConnections: connections(), sync: syncResult(ctx.syncError) }, ctx.json);
}

async function commandAddPeer(args: ParsedArgs): Promise<void> {
  const raw = flag(args, 'peer-link');
  if (!raw) fail('add-peer requires --peer-link');
  const did = parsePeerLink(raw);
  const dryRun = has(args, 'dry-run');
  const ctx = await opened(args);
  if (!dryRun) await ctx.waste.addPeer({ id: did, publicKey: ctx.modules.getPublicKey(did).publicKey });
  const pushError = dryRun ? undefined : await safeSync(ctx.client, ctx.waste);
  output({ added: !dryRun, dryRun, peerDid: did, sync: syncResult(ctx.syncError, pushError) }, ctx.json);
}

async function commandRemovePeer(args: ParsedArgs): Promise<void> {
  const did = flag(args, 'did');
  if (!did?.startsWith('did:')) fail('remove-peer requires --did DID');
  const dryRun = has(args, 'dry-run');
  const ctx = await opened(args);
  if (did === ctx.client.id) fail('refusing to remove this device');
  const found = ctx.waste.getPeers().some((item: any) => item.id === did);
  if (!dryRun && found) await ctx.waste.removePeer(did);
  output({ removed: !dryRun && found, dryRun, peerDid: did, found }, ctx.json);
}

async function commandInvite(args: ParsedArgs): Promise<void> {
  const did = flag(args, 'did');
  if (!did?.startsWith('did:')) fail('invite requires --did did:...');
  const dryRun = has(args, 'dry-run');
  const ctx = await opened(args);
  const entity = entityOrFail(ctx, flag(args, 'entity'), 'invite');
  const { MessageType, Propagation } = ctx.modules;
  const creator = actingAs(args, ctx);
  const alreadyMember = ctx.modules.memberList(ctx.modules.currentView(entity)).includes(did);
  const canInvite = permitted(ctx, entity.id, Propagation.Public, MessageType.Join, creator);
  let inviteId: string | undefined;
  let error: string | undefined;
  if (!dryRun && !alreadyMember && canInvite) {
    try {
      inviteId = messageId(ctx.modules, await ctx.client.createMessage({ nominee: did }, MessageType.Join, entity.id, Propagation.Public, { creator }));
    } catch (e: any) {
      error = e?.message || String(e);
    }
  }
  const pushError = inviteId ? await safeSync(ctx.client, ctx.waste) : undefined;
  output({
    entity: entity.id,
    nominee: did,
    as: creator,
    dryRun,
    status: alreadyMember ? 'already-member' : !canInvite ? 'denied' : dryRun ? 'ready' : error ? 'failed' : 'pending-acceptance',
    inviteId: inviteId || null,
    ...(error ? { error } : {}),
    sync: syncResult(ctx.syncError, pushError),
  }, ctx.json);
  if (error || (!alreadyMember && !canInvite)) process.exitCode = 1;
}

async function commandEditAcl(args: ParsedArgs): Promise<void> {
  const slot = flag(args, 'slot');
  if (!slot) fail('edit-acl requires --slot (e.g. task.create, response.comment, edit, join)');
  const valueRaw = flag(args, 'value');
  if (!valueRaw) fail('edit-acl requires --value (JSON, e.g. \'["creator","members"]\')');
  let value: any;
  try { value = JSON.parse(valueRaw); } catch { fail('--value must be valid JSON'); }
  const tier = (flag(args, 'tier') || 'private').toLowerCase();
  if (tier !== 'public' && tier !== 'private') fail('--tier must be public or private');
  const dryRun = has(args, 'dry-run');
  const ctx = await opened(args);
  const entity = entityOrFail(ctx, flag(args, 'entity'), 'edit-acl');
  const { MessageType, Propagation } = ctx.modules;
  const creator = actingAs(args, ctx);
  const propagation = tier === 'private' ? Propagation.Private : Propagation.Public;
  const slotPath = slot.split('.');
  const keys = [tier, 'acl', ...(slotPath[0] === 'response' ? slotPath : ['post', ...slotPath])];
  const canEdit = permitted(ctx, entity.id, propagation, MessageType.Edit, creator);
  let editId: string | undefined;
  let error: string | undefined;
  if (!dryRun && canEdit) {
    try {
      editId = messageId(ctx.modules, await ctx.client.createMessage({ keys, value }, MessageType.Edit, entity.id, propagation, { creator }));
    } catch (e: any) {
      error = e?.message || String(e);
    }
  }
  const pushError = editId ? await safeSync(ctx.client, ctx.waste) : undefined;
  output({
    edited: Boolean(editId),
    dryRun,
    entity: entity.id,
    as: creator,
    keys,
    value,
    canEdit,
    editId: editId || null,
    ...(error ? { error } : {}),
    sync: syncResult(ctx.syncError, pushError),
  }, ctx.json);
  if (error || !canEdit) process.exitCode = 1;
}

// The app's "New Collective" (GroupSidebar handleCreateGroup): a Register
// authored by the acting identity with the template's public ACL and every
// role it names seated by the creator, then a private Edit installing the
// private ACL (creator-bootstrap).
async function commandCreateGroup(args: ParsedArgs): Promise<void> {
  const name = flag(args, 'name')?.trim();
  if (!name) fail('create-group requires --name');
  const description = flag(args, 'description')?.trim();
  const templateName = flag(args, 'template') || 'Company';
  const dryRun = has(args, 'dry-run');
  const ctx = await opened(args);
  const { Templates, Template, EntityType, MessageType, Propagation, CURRENT_VERSION } = ctx.modules;
  const template = Template[templateName];
  if (template === undefined || templateName === 'Avatar') fail(`unknown group template: ${templateName}`);
  const creator = actingAs(args, ctx);
  const acl = structuredClone(Templates[template]);
  const roles = Object.fromEntries(ctx.modules.rolesNamedBy(acl).map((label: string) => [label, [creator]]));
  const register = {
    type: EntityType.Default,
    data: {
      version: CURRENT_VERSION,
      public: {
        name,
        ...(description ? { description } : {}),
        created: Date.now(),
        members: { [creator]: {} },
        acl: acl.public,
        ...(Object.keys(roles).length ? { roles } : {}),
      },
    },
  };
  let entityId: string | undefined;
  let error: string | undefined;
  if (!dryRun) {
    ctx.client.switchEntity(creator);
    try {
      const signed = await ctx.client.createMessage(register, MessageType.Register, null, Propagation.Public);
      entityId = ctx.modules.getEntityIdFromMessageId(messageId(ctx.modules, signed));
      await ctx.client.createMessage({ keys: ['private', 'acl'], value: acl.private }, MessageType.Edit, entityId, Propagation.Private);
    } catch (e: any) {
      error = e?.message || String(e);
    } finally {
      ctx.client.switchEntity(null);
    }
  }
  const pushError = entityId ? await safeSync(ctx.client, ctx.waste) : undefined;
  output({
    created: Boolean(entityId) && !error,
    dryRun,
    name,
    template: templateName,
    as: creator,
    roles: Object.keys(roles),
    entityId: entityId || null,
    ...(error ? { error } : {}),
    sync: syncResult(ctx.syncError, pushError),
  }, ctx.json);
  if (error) process.exitCode = 1;
}

// The app's "Add Agent" (NewAgentModal): a did:agent child of the group,
// registered by the acting identity, run by --manager (a hosted factory's
// DID), on owner keys referenced as secret://<this device>/<provider>:<name>
// (shared beforehand with share-key). --keys lists providers in priority order.
async function commandCreateAgent(args: ParsedArgs): Promise<void> {
  const name = flag(args, 'name')?.trim();
  const manager = flag(args, 'manager');
  if (!name) fail('create-agent requires --name');
  if (!manager?.startsWith('did:')) fail('create-agent requires --manager <DID>');
  const instructionsFile = flag(args, 'instructions-file');
  const instructions = instructionsFile ? fs.readFileSync(path.resolve(instructionsFile), 'utf8').trim() : flag(args, 'instructions')?.trim();
  const description = flag(args, 'description')?.trim();
  const providers = (flag(args, 'keys') || '').split(',').map((k) => k.trim()).filter(Boolean);
  const dryRun = has(args, 'dry-run');
  const ctx = await opened(args);
  const group = entityOrFail(ctx, flag(args, 'entity'), 'create-agent');
  const { EntityType, MessageType, Propagation, CURRENT_VERSION } = ctx.modules;
  const creator = actingAs(args, ctx);
  const keys = Object.fromEntries(providers.map((p) => [p, `secret://${ctx.client.id}/${p}:default`]));
  const register = {
    type: EntityType.Agent,
    data: {
      version: CURRENT_VERSION,
      state: {
        name,
        ...(description ? { description } : {}),
        ...(instructions ? { instructions } : {}),
        manager,
        created: Date.now(),
        ...(providers.length ? { keys } : {}),
      },
    },
  };
  let agentId: string | undefined;
  let error: string | undefined;
  if (!dryRun) {
    ctx.client.switchEntity(creator);
    try {
      const signed = await ctx.client.createMessage(register, MessageType.Register, group.id, Propagation.Public);
      agentId = ctx.modules.getEntityIdFromMessageId(messageId(ctx.modules, signed));
    } catch (e: any) {
      error = e?.message || String(e);
    } finally {
      ctx.client.switchEntity(null);
    }
  }
  const pushError = agentId ? await safeSync(ctx.client, ctx.waste) : undefined;
  output({
    created: Boolean(agentId),
    dryRun,
    name,
    group: group.id,
    as: creator,
    manager,
    keys,
    agentId: agentId || null,
    ...(error ? { error } : {}),
    sync: syncResult(ctx.syncError, pushError),
  }, ctx.json);
  if (error) process.exitCode = 1;
}

// Edit one field of an existing post (e.g. a note's body), as the acting
// identity. The post's own tier is kept.
async function commandEdit(args: ParsedArgs): Promise<void> {
  const id = flag(args, 'id');
  const field = flag(args, 'field');
  const value = flag(args, 'value');
  if (!id || !field || value === undefined) fail('edit requires --id POST --field NAME --value TEXT');
  const dryRun = has(args, 'dry-run');
  const ctx = await opened(args);
  const base = await ctx.client.getMessage(id);
  if (!base) fail(`post is not present locally: ${id}`);
  const creator = actingAs(args, ctx);
  const { MessageType } = ctx.modules;
  const propagation = base.message.data.propagation;
  const canEdit = permitted(ctx, base.entity, propagation, MessageType.Edit, creator)
    || (() => { try { return ctx.client.isMessagePermitted(base.entity, propagation, MessageType.Edit, { keys: [field], value }, base.message, undefined, { creator }); } catch { return false; } })();
  let editId: string | undefined;
  let error: string | undefined;
  if (!dryRun) {
    try {
      editId = messageId(ctx.modules, await ctx.client.createMessage({ keys: [field], value }, MessageType.Edit, id, propagation, { creator }));
    } catch (e: any) {
      error = e?.message || String(e);
    }
  }
  const pushError = editId ? await safeSync(ctx.client, ctx.waste) : undefined;
  output({ edited: Boolean(editId), dryRun, id, field, as: creator, canEdit, editId: editId || null, ...(error ? { error } : {}), sync: syncResult(ctx.syncError, pushError) }, ctx.json);
  if (error) process.exitCode = 1;
}

async function commandPost(args: ParsedArgs): Promise<void> {
  const title = flag(args, 'title');
  if (!title) fail('post requires --title');
  const body = flag(args, 'body');
  const space = flag(args, 'space');
  const dryRun = has(args, 'dry-run');
  const ctx = await opened(args);
  const entity = entityOrFail(ctx, flag(args, 'entity'), 'post');
  const { MessageType, Propagation } = ctx.modules;
  const creator = actingAs(args, ctx);
  const propagation = has(args, 'public') ? Propagation.Public : Propagation.Private;
  const canPost = permitted(ctx, entity.id, propagation, MessageType.Note, creator);
  const note: Dict = { title, ...(body ? { body } : {}), ...(space ? { space } : {}) };
  let postId: string | undefined;
  let error: string | undefined;
  if (!dryRun && canPost) {
    try {
      postId = messageId(ctx.modules, await ctx.client.createMessage(note, MessageType.Note, entity.id, propagation, { creator }));
    } catch (e: any) {
      error = e?.message || String(e);
    }
  }
  const pushError = postId ? await safeSync(ctx.client, ctx.waste) : undefined;
  output({
    posted: Boolean(postId),
    dryRun,
    entity: entity.id,
    as: creator,
    title,
    propagation,
    canPost,
    postId: postId || null,
    ...(error ? { error } : {}),
    sync: syncResult(ctx.syncError, pushError),
  }, ctx.json);
  if (error || !canPost) process.exitCode = 1;
}

async function commandSnapshot(args: ParsedArgs): Promise<void> {
  const ctx = await opened(args);
  const repo = canonicalRepo(flag(args, 'repo'));
  const id = repoHash(repo);
  const record = readState(ctx.cfg).repositories[id];
  const entity = entityOrFail(ctx, flag(args, 'entity') || record?.entity, 'snapshot');
  const board = await boardMessages(ctx, entity.id);
  const project = board.projects.find((item: Dict) => item.id === record?.projectId);
  const managedIds = new Set(Object.values(record?.tasks || {}));
  const tasks = board.tasks
    .filter((item: Dict) => managedIds.has(item.id) || parseMarker(content(item.message).description)?.repo === id)
    .map((item: Dict) => ({ id: item.id, ...content(item.message), marker: parseMarker(content(item.message).description) }));
  output({
    repo,
    repoId: id,
    entity: entity.id,
    project: project ? { id: project.id, ...content(project.message) } : null,
    tasks,
    sync: syncResult(ctx.syncError),
  }, ctx.json);
}

async function commandReconcile(args: ParsedArgs): Promise<void> {
  const file = flag(args, 'file');
  if (!file) fail('reconcile requires --file');
  let raw: Dict;
  try { raw = JSON.parse(fs.readFileSync(path.resolve(file), 'utf8')); } catch (error: any) { fail(`cannot read manifest: ${error.message}`); }
  const manifest = validateManifest(raw);
  const dryRun = has(args, 'dry-run');
  const ctx = await opened(args);
  const repo = canonicalRepo(flag(args, 'repo'));
  const id = repoHash(repo);
  const state = readState(ctx.cfg);
  const entity = entityOrFail(ctx, flag(args, 'entity') || state.repositories[id]?.entity, 'reconcile');
  const { MessageType, Propagation } = ctx.modules;
  const creator = actingAs(args, ctx);
  const record = state.repositories[id] ||= { root: repo, entity: entity.id, tasks: {} };
  if (record.entity && record.entity !== entity.id) fail(`${repo} is managed in ${record.entity}, not ${entity.id}`);
  record.entity = entity.id;
  if (!dryRun) {
    for (const type of [MessageType.Project, MessageType.Task]) {
      if (!permitted(ctx, entity.id, Propagation.Private, type, creator)) {
        fail(`${creator} cannot create ${type} in ${entity.id} (ACL); grant it with edit-acl --slot ${type}.create`);
      }
    }
  }
  const board = await boardMessages(ctx, entity.id);
  const project = board.projects.find((item: Dict) => item.id === record.projectId);
  const ops: Dict[] = [];
  if (!project) {
    ops.push({ kind: 'create_project', key: manifest.project.key, title: manifest.project.title, workflow: manifest.project.workflow });
  } else {
    const current = content(project.message);
    for (const [field, value] of [['title', manifest.project.title], ['workflow', manifest.project.workflow]] as Array<[string, unknown]>) {
      if (JSON.stringify(current[field]) !== JSON.stringify(value)) ops.push({ kind: 'update_project', id: project.id, field, from: current[field], to: value });
    }
  }
  const byId = new Map(board.tasks.map((item: Dict) => [item.id, item]));
  const byMarker = new Map<string, Dict>();
  for (const item of board.tasks) {
    const found = parseMarker(content(item.message).description);
    if (found?.repo === id) byMarker.set(found.key, item);
  }
  for (const task of manifest.tasks) {
    const existing = byId.get(record.tasks[task.key]) || byMarker.get(task.key);
    if (!existing) {
      ops.push({ kind: 'create_task', key: task.key, title: task.title, status: task.status, closed: task.closed ?? false });
      continue;
    }
    const current = content(existing.message);
    const desired: Dict = { title: task.title, status: task.status, description: taskDescription(task, id) };
    if (task.closed !== undefined) desired.closed = task.closed;
    const changes = Object.entries(desired).filter(([field, value]) => JSON.stringify(current[field]) !== JSON.stringify(value));
    for (const [field, value] of changes) ops.push({ kind: 'update_task', key: task.key, id: existing.id, field, from: current[field], to: value });
    if (!changes.length) ops.push({ kind: 'unchanged', key: task.key, id: existing.id });
  }

  if (!dryRun) {
    if (!project) {
      const signed = await ctx.client.createMessage(
        { title: manifest.project.title, workflow: manifest.project.workflow },
        MessageType.Project, entity.id, Propagation.Private, { creator },
      );
      record.projectId = messageId(ctx.modules, signed);
    }
    for (const op of ops) {
      if (op.kind === 'update_project') await editField(ctx, creator, project!, [op.field], op.to);
    }
    for (const task of manifest.tasks) {
      const existing = byId.get(record.tasks[task.key]) || byMarker.get(task.key);
      if (!existing) {
        const signed = await ctx.client.createMessage({
          title: task.title,
          project: record.projectId,
          status: task.status,
          description: taskDescription(task, id),
          ...(task.closed !== undefined ? { closed: task.closed } : {}),
        }, MessageType.Task, entity.id, Propagation.Private, { creator });
        record.tasks[task.key] = messageId(ctx.modules, signed);
        continue;
      }
      record.tasks[task.key] = existing.id;
      for (const op of ops) {
        if (op.kind === 'update_task' && op.key === task.key) await editField(ctx, creator, existing, [op.field], op.to);
      }
    }
    writeState(ctx.cfg, state);
  }
  const pushError = dryRun ? undefined : await safeSync(ctx.client, ctx.waste);
  const summary: Dict = {};
  for (const op of ops) summary[op.kind] = (summary[op.kind] || 0) + 1;
  output({
    dryRun,
    repo,
    repoId: id,
    entity: entity.id,
    as: creator,
    projectId: record.projectId || null,
    summary,
    operations: ops,
    sync: syncResult(ctx.syncError, pushError),
  }, ctx.json);
}

async function focusedTask(args: ParsedArgs, mode: 'move' | 'close'): Promise<void> {
  const key = flag(args, 'key');
  if (!key) fail(`${mode} requires --key`);
  const status = flag(args, 'status');
  if (mode === 'move' && !status) fail('move requires --status');
  const dryRun = has(args, 'dry-run');
  const ctx = await opened(args);
  const creator = actingAs(args, ctx);
  const repo = canonicalRepo(flag(args, 'repo'));
  const record = readState(ctx.cfg).repositories[repoHash(repo)];
  if (!record) fail(`no managed project for ${repo}`);
  const taskId = record.tasks?.[key];
  if (!taskId) fail(`unknown managed task key: ${key}`);
  const task = await ctx.client.getEffectiveMessage(taskId);
  if (!task) fail(`mapped task is missing from Myco: ${taskId}`);
  if (mode === 'move') {
    const project = await ctx.client.getEffectiveMessage(record.projectId);
    if (!content(project).workflow?.includes(status)) fail(`status is not in the project workflow: ${status}`);
  }
  const field = mode === 'move' ? 'status' : 'closed';
  const next = mode === 'move' ? status : true;
  const before = content(task)[field];
  const changed = JSON.stringify(before) !== JSON.stringify(next);
  if (!dryRun && changed) await editField(ctx, creator, { id: taskId, message: task }, [field], next);
  const pushError = dryRun || !changed ? undefined : await safeSync(ctx.client, ctx.waste);
  output({
    dryRun,
    repo,
    key,
    taskId,
    as: creator,
    operation: changed ? { kind: mode, field, from: before, to: next } : { kind: 'unchanged', field, value: next },
    sync: syncResult(ctx.syncError, pushError),
  }, ctx.json);
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  const commands: Record<string, (a: ParsedArgs) => Promise<void>> = {
    doctor: commandDoctor,
    init: commandInit,
    identity: commandIdentity,
    connect: commandConnect,
    join: commandJoin,
    groups: commandGroups,
    entity: commandEntity,
    messages: commandMessages,
    peers: commandPeers,
    'share-key': commandShareKey,
    sync: commandSync,
    requests: commandRequests,
    trust: commandTrust,
    'add-peer': commandAddPeer,
    'remove-peer': commandRemovePeer,
    invite: commandInvite,
    'edit-acl': commandEditAcl,
    post: commandPost,
    edit: commandEdit,
    'create-group': commandCreateGroup,
    'create-agent': commandCreateAgent,
    snapshot: commandSnapshot,
    reconcile: commandReconcile,
    move: (a) => focusedTask(a, 'move'),
    close: (a) => focusedTask(a, 'close'),
  };
  if (['help', '--help', '-h'].includes(args.command)) return help();
  const run = commands[args.command];
  if (!run) fail(`unknown command: ${args.command}`);
  await run(args);
  // Open stores and relay timers would otherwise keep the process alive.
  process.exit(process.exitCode ?? 0);
}

main().catch((error: any) => fail(error?.stack || error?.message || String(error), 1));

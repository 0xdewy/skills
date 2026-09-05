import { createHash, randomBytes } from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

process.umask(0o077);

// Relay base URLs to bootstrap (comma-separated). Private/LAN relays belong in
// MYCO_RELAY_URL; a portable skill must not assume this machine's network.
const DEFAULT_RELAY = 'https://waste.3a2d50.com';
const DEFAULT_WORKFLOW = ['Backlog', 'Ready', 'In Progress', 'Review', 'Done'];
const STATE_VERSION = 1;

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
  if (json) console.log(JSON.stringify(value, null, 2));
  else if (typeof value === 'string') console.log(value);
  else console.log(JSON.stringify(value, null, 2));
}

function help(): void {
  console.log(`Myco — agent-native interaction with native Myco entities

Usage:
  myco inbox --config FILE [--check | --initialize]
  myco doctor [--json]
  myco identity [--json]
  myco rename --name NAME [--dry-run] [--json]
  myco groups [--search NAME] [--all] [--json]
  myco entity --id ENTITY_ID [--acl] [--json]
  myco messages --entity ENTITY_ID [--limit N] [--json]
  myco peers [--json]
  myco add-peer --peer-link URL [--dry-run] [--json]
  myco remove-peer --did DID [--dry-run] [--json]
  myco join [--entity ENTITY_ID] [--dry-run] [--json]   # accept pending invites
  myco invite --entity ENTITY_ID --did DID [--dry-run] [--json]
  myco edit-acl --entity ENTITY_ID --slot SLOT [--value JSON] [--tier public|private] [--dry-run] [--json]
  myco post --entity ENTITY_ID --title TITLE [--body TEXT] [--space NAME] [--public] [--dry-run] [--json]
  myco init [--name NAME] [--owner-did DID] [--json]
  myco snapshot [--repo PATH] [--entity ENTITY_ID] [--json]
  myco reconcile --file FILE [--repo PATH] [--entity ENTITY_ID] [--dry-run] [--json]
  myco move --key KEY --status STATUS [--repo PATH] [--dry-run] [--json]
  myco close --key KEY [--repo PATH] [--dry-run] [--json]
  myco invite-owner --did DID [--dry-run] [--json]
  myco connect-owner --avatar DID --peer-link URL [--dry-run] [--json]

Read-only inspection (doctor, identity, groups, entity, peers, snapshot) never
mutates. "post" creates a Note in an entity (requires local membership).
Kanban commands (snapshot, reconcile, move, close) manage a Myco Project board.

Environment:
  MYCO_ROOT                 Myco checkout (default: /home/user/code/myco)
  MYCO_DATA_DIR             persistent identity data (default: ~/.local/share/myco)
  MYCO_KANBAN_DATA_DIR      legacy alias for MYCO_DATA_DIR
  MYCO_RELAY_URL            relay URL, or "local" for isolated use
`);
}

function config() {
  const mycoRoot = path.resolve(process.env.MYCO_ROOT || '/home/user/code/myco');
  const dataDir = path.resolve(
    process.env.MYCO_DATA_DIR
      || process.env.MYCO_KANBAN_DATA_DIR
      || path.join(process.env.XDG_DATA_HOME || path.join(os.homedir(), '.local', 'share'), 'myco'),
  );
  const relay = process.env.MYCO_RELAY_URL || DEFAULT_RELAY;
  return {
    mycoRoot,
    agentRoot: path.join(mycoRoot, 'myco-agent'),
    dataDir,
    relay,
    didFile: path.join(dataDir, 'agent-did'),
    entityFile: path.join(dataDir, 'agent-entity'),
    keyFile: path.join(dataDir, 'runtime-key'),
    stateFile: path.join(dataDir, 'kanban-state.json'),
  };
}

function readText(file: string): string | undefined {
  try { return fs.readFileSync(file, 'utf8').trim(); } catch { return undefined; }
}

function writePrivate(file: string, value: string): void {
  fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
  const temp = `${file}.tmp-${process.pid}`;
  fs.writeFileSync(temp, value, { encoding: 'utf8', mode: 0o600 });
  fs.renameSync(temp, file);
  fs.chmodSync(file, 0o600);
}

function readState(cfg: ReturnType<typeof config>): Dict {
  const raw = readText(cfg.stateFile);
  if (!raw) return { version: STATE_VERSION, identity: {}, repositories: {} };
  let parsed: Dict;
  try { parsed = JSON.parse(raw); } catch { fail(`invalid state JSON at ${cfg.stateFile}`); }
  if (parsed.version !== STATE_VERSION || typeof parsed.repositories !== 'object') {
    fail(`unsupported state format at ${cfg.stateFile}`);
  }
  parsed.identity ||= {};
  return parsed;
}

function writeState(cfg: ReturnType<typeof config>, state: Dict): void {
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

function parsePeerLink(raw: string, modules: Dict): { id: string; publicKey: string; legacyRelayUrls: string[] } {
  let params: URLSearchParams;
  try {
    const query = raw.indexOf('?');
    if (query < 0) fail('peer link has no query parameters');
    params = new URLSearchParams(raw.slice(query + 1));
  } catch {
    fail('invalid peer link');
  }
  const id = params.get('id');
  if (!id?.startsWith('did:ed25519:')) fail('peer link must contain an ed25519 DID');
  const derivedPublicKey = modules.getPublicKey(id).publicKey;
  const publicKey = params.get('pk') ?? derivedPublicKey;
  if (derivedPublicKey !== publicKey) fail('peer link public key does not match its DID');
  // Current app links carry identity only. Parse old connection-bearing links
  // for compatibility, but never attach their relay URL directly to the peer:
  // relay connections belong to the relay's DID and the core validates that.
  const legacyRelayUrls = params.getAll('c').map((encoded) => {
    const colon = encoded.indexOf(':');
    if (colon <= 0) fail(`invalid peer connection: ${encoded}`);
    const transportType = encoded.slice(0, colon);
    const uri = encoded.slice(colon + 1);
    if (transportType !== 'api' || !/^https?:\/\//.test(uri)) fail(`invalid peer connection: ${encoded}`);
    return uri;
  });
  return { id, publicKey, legacyRelayUrls };
}

async function loadMyco(cfg: ReturnType<typeof config>): Promise<Dict> {
  const packageFile = path.join(cfg.agentRoot, 'package.json');
  if (!fs.existsSync(packageFile)) fail(`Myco agent checkout not found at ${cfg.agentRoot}`);
  const requireFromMyco = createRequire(packageFile);
  const importPackage = async (name: string) => {
    const resolved = requireFromMyco.resolve(name);
    return import(pathToFileURL(resolved).href);
  };
  const source = async (relative: string) => import(pathToFileURL(path.join(cfg.agentRoot, relative)).href);
  const [protocol, transports, wastebin, core, dbModule, clientModule] = await Promise.all([
    importPackage('@mycoprotocol/client'),
    importPackage('@wasteprotocol/web-transports'),
    importPackage('@wasteprotocol/wb-sqlite'),
    importPackage('@wasteprotocol/core'),
    source('src/db-sqlite.ts'),
    source('src/create-client.ts'),
  ]);
  return { ...protocol, ...transports, ...wastebin, ...core, ...dbModule, ...clientModule };
}

function ensureRuntimeKey(cfg: ReturnType<typeof config>): string {
  const existing = readText(cfg.keyFile);
  if (existing) return existing;
  if (fs.existsSync(cfg.keyFile)) throw new Error('Runtime key file is empty; refusing to replace it');
  const generated = randomBytes(32).toString('base64url');
  writePrivate(cfg.keyFile, `${generated}\n`);
  return generated;
}

async function openClient(cfg: ReturnType<typeof config>, modules: Dict): Promise<Dict> {
  fs.mkdirSync(cfg.dataDir, { recursive: true, mode: 0o700 });
  fs.chmodSync(cfg.dataDir, 0o700);
  const runtimeKey = ensureRuntimeKey(cfg);
  const db = new modules.SqliteDB(path.join(cfg.dataDir, 'myco.db'), runtimeKey);
  await db.connect();
  const wasteDbKey = createHash('sha256').update(runtimeKey).digest('hex');
  const wb = new modules.SqliteWasteBin(path.join(cfg.dataDir, 'waste.db'), wasteDbKey);
  await wb.connect();
  const existingDid = readText(cfg.didFile);
  const local = cfg.relay.trim().toLowerCase() === 'local' || cfg.relay.trim().toLowerCase() === 'none';
  const transports: Record<string, any> = local
    ? { local: new modules.LocalTransport() }
    : { api: new modules.APITransport() };
  const bundle = await modules.createClientBundle(db, wb, transports, existingDid ? { existingDid } : {});
  const client = bundle.client;
  if (!existingDid) writePrivate(cfg.didFile, `${client.id}\n`);
  const waste = bundle.waste;
  // One-time cleanup for the removed identity-revealing receiver transport.
  // Leaving these rows behind advertises an unusable route indefinitely.
  for (const peer of waste.getPeers()) {
    for (const connection of waste.getConnections(peer.id)) {
      if (connection.transportType === 'http-receive') {
        await waste.removeConnection(connection.connectionId, peer.id);
      }
    }
  }
  if (local) {
    await waste.addConnection({ transportType: 'local', posture: 'receive' });
  } else {
    const relayUrls = cfg.relay.split(',').map((s: string) => s.trim()).filter(Boolean);
    const relayDids: string[] = [];
    for (const url of relayUrls) {
      const relayDid = await modules.bootstrapHttpRelay(waste, url);
      if (!relayDid) continue;
      relayDids.push(relayDid);
      for (const conn of [
        { transportType: 'api', posture: 'send' },
        { transportType: 'api', posture: 'scan' },
      ]) {
        try { await waste.addConnection(conn, relayDid); } catch { /* posture not advertised */ }
      }
    }
    if (relayDids.length) {
      try { await waste.setPrivatePeers(relayDids); } catch { /* non-fatal */ }
    }
  }
  return { client, waste, db, wb, createdDid: !existingDid, local };
}

async function safeSync(client: any, waste?: any): Promise<string | undefined> {
  try {
    // A short-lived CLI process cannot rely on receiver transport timers
    // (30s intervals never fire before exit), so poll every receiver here —
    // otherwise the skill never sees inbound traffic at all.
    if (waste) {
      for (const t of Object.values(waste.getTransports())) {
        try { await (t as any).poll?.(); } catch { /* best-effort */ }
      }
    }
    await client.sync();
    return undefined;
  } catch (error: any) {
    return error?.message || String(error);
  }
}

function messageId(modules: Dict, signed: any): string {
  return modules.getMessageId(modules.getMessageHash(signed.message));
}

function peerLink(did: string): string {
  // ed25519 DIDs self-encode their public key. Reachability is learned through
  // gossip/shared relays and must not be represented as a direct peer edge.
  const params = new URLSearchParams({ id: did });
  return `myco://peer?${params.toString()}`;
}

async function ensureEntity(
  cfg: ReturnType<typeof config>,
  modules: Dict,
  client: any,
  opts: { name?: string; ownerDid?: string } = {},
): Promise<{ entityId: string; created: boolean }> {
  const state = readState(cfg);
  const bound = readText(cfg.entityFile) || state.identity.agentEntityId;
  if (bound) {
    const found = client.entities.find((entity: any) => entity.id === bound);
    if (!found) fail(`bound agent entity ${bound} is missing locally; refusing to regenerate identity`);
    if (!readText(cfg.entityFile)) writePrivate(cfg.entityFile, `${bound}\n`);
    state.identity = { ...state.identity, routingDid: client.id, agentEntityId: bound };
    writeState(cfg, state);
    return { entityId: bound, created: false };
  }

  const ownerDid = opts.ownerDid?.trim();
  const members: Dict = { [client.id]: {} };
  if (ownerDid) members[ownerDid] = {};
  const acl = modules.Templates[modules.Template.Avatar];
  await client.createMessage({
    type: modules.EntityType.Default,
    data: {
      version: modules.CURRENT_VERSION,
      public: {
        name: opts.name || 'Myco Code Steward',
        description: 'Agent identity and native Kanban workspace for evidence-backed codebase projects.',
        members,
        acl: acl.public,
      },
    },
  }, modules.MessageType.Register, null, modules.Propagation.Public);
  const entityId = client.entities[client.entities.length - 1]?.id;
  if (!entityId) fail('Myco did not return an entity id during initialization');
  await client.createMessage(
    { keys: ['private', 'acl'], value: acl.private },
    modules.MessageType.Edit,
    entityId,
    modules.Propagation.Private,
  );
  writePrivate(cfg.entityFile, `${entityId}\n`);
  state.identity = {
    routingDid: client.id,
    agentEntityId: entityId,
    name: opts.name || 'Myco Code Steward',
  };
  writeState(cfg, state);
  return { entityId, created: true };
}

async function effective(client: any, base: any): Promise<any> {
  const replies = await client.getMessagesByParent(base.id);
  const edits = replies
    .filter((item: any) => item.message?.data?.type === 'edit')
    .sort((a: any, b: any) => a.timestamp - b.timestamp || a.id.localeCompare(b.id));
  if (!edits.length) return base;
  const folded = structuredClone(base);
  for (const edit of edits) {
    const { keys, value } = content(edit);
    if (!Array.isArray(keys) || !keys.length) continue;
    const last = keys[keys.length - 1];
    let typed: any = value;
    if (last === 'closed') {
      typed = value === 'true' ? true : value === 'false' ? false : value;
    } else if (last === 'workflow' || last === 'assignees') {
      try { typed = JSON.parse(value); } catch { typed = value; }
    }
    let target = folded.message.data.content;
    for (const key of keys.slice(0, -1)) {
      target[key] ||= {};
      target = target[key];
    }
    target[last] = typed;
  }
  return folded;
}

async function boardMessages(client: any, entityId: string, modules: Dict): Promise<Dict> {
  const all = await client.getMessagesByEntity(entityId);
  const projects: any[] = [];
  const tasks: any[] = [];
  for (const base of all) {
    if (base.deleted) continue;
    const type = base.message?.data?.type;
    if (type !== modules.MessageType.Project && type !== modules.MessageType.Task) continue;
    const item = await effective(client, base);
    if (type === modules.MessageType.Project) projects.push(item);
    else tasks.push(item);
  }
  return { projects, tasks };
}

function content(item: any): Dict {
  return (item?.message?.data?.content || {}) as Dict;
}

function operationSummary(ops: Dict[]): Dict {
  const summary: Dict = { create_project: 0, update_project: 0, create_task: 0, update_task: 0, unchanged: 0 };
  for (const op of ops) summary[op.kind] = (summary[op.kind] || 0) + 1;
  return summary;
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

function repoRecord(state: Dict, repo: string): Dict {
  const id = repoHash(repo);
  state.repositories[id] ||= { root: repo, tasks: {} };
  state.repositories[id].root = repo;
  state.repositories[id].tasks ||= {};
  return state.repositories[id];
}

async function editField(client: any, modules: Dict, entityId: string, item: any, keys: string[], value: any): Promise<void> {
  const wireValue = typeof value === 'string' ? value : JSON.stringify(value);
  await client.createMessage({
    keys,
    value: wireValue,
    agentEntityId: entityId,
    actor_entity: entityId,
  }, modules.MessageType.Edit, item.id, item.message.data.propagation);
}

async function commandDoctor(args: ParsedArgs): Promise<void> {
  const cfg = config();
  const checks = {
    mycoRoot: fs.existsSync(cfg.mycoRoot),
    agentPackage: fs.existsSync(path.join(cfg.agentRoot, 'package.json')),
    tsx: fs.existsSync(path.join(cfg.agentRoot, 'node_modules', 'tsx', 'dist', 'loader.mjs')),
    mycoClient: fs.existsSync(path.join(cfg.mycoRoot, 'myco-ts', 'dist', 'index.js')),
    dataDir: cfg.dataDir,
    relay: cfg.relay,
    initialized: Boolean(readText(cfg.didFile) && readText(cfg.entityFile)),
  };
  const ok = checks.mycoRoot && checks.agentPackage && checks.tsx && checks.mycoClient;
  output({ ok, checks }, has(args, 'json'));
  if (!ok) process.exitCode = 1;
}

async function commandIdentity(args: ParsedArgs): Promise<void> {
  const cfg = config();
  const routingDid = readText(cfg.didFile);
  const agentEntityId = readText(cfg.entityFile);
  if (!routingDid || !agentEntityId) {
    output({ initialized: false, dataDir: cfg.dataDir, next: 'run init before a write operation' }, has(args, 'json'));
    return;
  }
  const state = readState(cfg);
  output({
    initialized: true,
    name: state.identity.name || 'Myco Code Steward',
    agentEntityId,
    routingDid,
    relay: cfg.relay,
    peerLink: peerLink(routingDid),
    dataDir: cfg.dataDir,
  }, has(args, 'json'));
}

async function commandInit(args: ParsedArgs): Promise<void> {
  const cfg = config();
  const modules = await loadMyco(cfg);
  const { client, waste, createdDid } = await openClient(cfg, modules);
  const identity = await ensureEntity(cfg, modules, client, { name: flag(args, 'name'), ownerDid: flag(args, 'owner-did') });
  const syncError = await safeSync(client, waste);
  const name = readState(cfg).identity.name || 'Myco Code Steward';
  output({
    initialized: true,
    createdRoutingIdentity: createdDid,
    createdAgentEntity: identity.created,
    name,
    agentEntityId: identity.entityId,
    routingDid: client.id,
    relay: cfg.relay,
    peerLink: peerLink(client.id),
    sync: syncError ? { ok: false, error: syncError } : { ok: true },
  }, has(args, 'json'));
}

async function initializedClient(args: ParsedArgs): Promise<Dict> {
  const cfg = config();
  if (!readText(cfg.didFile) || !readText(cfg.entityFile)) fail('identity is not initialized; run init first');
  const modules = await loadMyco(cfg);
  const opened = await openClient(cfg, modules);
  const identity = await ensureEntity(cfg, modules, opened.client);
  return { cfg, modules, ...opened, entityId: identity.entityId, json: has(args, 'json') };
}

function resolveTarget(args: ParsedArgs, ctx: Dict): string {
  const target = flag(args, 'entity') || ctx.entityId;
  if (target !== ctx.entityId && !ctx.client.entities.find((item: any) => item.id === target)) {
    fail(`target entity is not present locally: ${target} (sync/add-peer first)`);
  }
  return target;
}

function ensureCanCreate(ctx: Dict, target: string, type: string): void {
  if (ctx.client.isMessagePermitted(target, ctx.modules.Propagation.Private, type)) return;
  fail(
    `agent cannot create ${type} in ${target} (ACL denies it). ` +
    `Grant it with: myco edit-acl --entity ${target} --slot ${type}.create --value '["creator","members"]'`,
  );
}

async function commandSnapshot(args: ParsedArgs): Promise<void> {
  const ctx = await initializedClient(args);
  const syncError = await safeSync(ctx.client, ctx.waste);
  const state = readState(ctx.cfg);
  const repo = canonicalRepo(flag(args, 'repo'));
  const id = repoHash(repo);
  const record = state.repositories[id];
  const target = resolveTarget(args, ctx);
  const board = await boardMessages(ctx.client, target, ctx.modules);
  const projectId = record?.projectId;
  const project = board.projects.find((item: any) => item.id === projectId);
  const managedIds = new Set(Object.values(record?.tasks || {}));
  const tasks = board.tasks
    .filter((item: any) => managedIds.has(item.id) || parseMarker(content(item).description)?.repo === id)
    .map((item: any) => ({ id: item.id, ...content(item), marker: parseMarker(content(item).description) }));
  output({
    repo,
    repoId: id,
    entity: target,
    identity: { agentEntityId: ctx.entityId, routingDid: ctx.client.id },
    project: project ? { id: project.id, ...content(project) } : null,
    tasks,
    sync: syncError ? { ok: false, error: syncError } : { ok: true },
  }, ctx.json);
}

async function commandReconcile(args: ParsedArgs): Promise<void> {
  const file = flag(args, 'file');
  if (!file) fail('reconcile requires --file');
  let raw: Dict;
  try { raw = JSON.parse(fs.readFileSync(path.resolve(file), 'utf8')); } catch (error: any) { fail(`cannot read manifest: ${error.message}`); }
  const manifest = validateManifest(raw);
  const dryRun = has(args, 'dry-run');
  const ctx = await initializedClient(args);
  const inboundSyncError = await safeSync(ctx.client, ctx.waste);
  const repo = canonicalRepo(flag(args, 'repo'));
  const id = repoHash(repo);
  const state = readState(ctx.cfg);
  const record = repoRecord(state, repo);
  const target = resolveTarget(args, ctx);
  if (!dryRun) {
    ensureCanCreate(ctx, target, 'project');
    ensureCanCreate(ctx, target, 'task');
  }
  const board = await boardMessages(ctx.client, target, ctx.modules);
  let project = board.projects.find((item: any) => item.id === record.projectId);
  const ops: Dict[] = [];

  if (!project) {
    ops.push({ kind: 'create_project', key: manifest.project.key, title: manifest.project.title, workflow: manifest.project.workflow });
  } else {
    const current = content(project);
    for (const [field, value] of [['title', manifest.project.title], ['workflow', manifest.project.workflow]] as Array<[string, any]>) {
      if (JSON.stringify(current[field]) !== JSON.stringify(value)) {
        ops.push({ kind: 'update_project', id: project.id, field, from: current[field], to: value });
      }
    }
  }

  const byId = new Map(board.tasks.map((item: any) => [item.id, item]));
  const byMarker = new Map<string, any>();
  for (const item of board.tasks) {
    const found = parseMarker(content(item).description);
    if (found?.repo === id) byMarker.set(found.key, item);
  }

  for (const task of manifest.tasks) {
    const existing = byId.get(record.tasks[task.key]) || byMarker.get(task.key);
    if (!existing) {
      ops.push({ kind: 'create_task', key: task.key, title: task.title, status: task.status, closed: task.closed ?? false });
      continue;
    }
    record.tasks[task.key] = existing.id;
    const current = content(existing);
    const desired: Dict = {
      title: task.title,
      status: task.status,
      description: taskDescription(task, id),
    };
    if (task.closed !== undefined) desired.closed = task.closed;
    let changed = false;
    for (const [field, value] of Object.entries(desired)) {
      if (JSON.stringify(current[field]) !== JSON.stringify(value)) {
        ops.push({ kind: 'update_task', key: task.key, id: existing.id, field, from: current[field], to: value });
        changed = true;
      }
    }
    if (!changed) ops.push({ kind: 'unchanged', key: task.key, id: existing.id });
  }

  if (!dryRun) {
    if (!project) {
      const signed = await ctx.client.createMessage({
        title: manifest.project.title,
        workflow: manifest.project.workflow,
        agentEntityId: ctx.entityId,
        actor_entity: ctx.entityId,
      }, ctx.modules.MessageType.Project, target, ctx.modules.Propagation.Private);
      const idCreated = messageId(ctx.modules, signed);
      record.projectId = idCreated;
      project = await ctx.client.getMessage(idCreated);
    }
    for (const op of ops.filter((item) => item.kind === 'update_project')) {
      const base = await ctx.client.getMessage(op.id);
      if (base) await editField(ctx.client, ctx.modules, ctx.entityId, base, [op.field], op.to);
    }
    for (const task of manifest.tasks) {
      let existing = byId.get(record.tasks[task.key]) || byMarker.get(task.key);
      if (!existing) {
        const signed = await ctx.client.createMessage({
          title: task.title,
          project: record.projectId,
          status: task.status,
          description: taskDescription(task, id),
          nonce: `myco-kanban:${id}:${encodeKey(task.key)}`,
          ...(task.closed !== undefined ? { closed: task.closed } : {}),
          agentEntityId: ctx.entityId,
          actor_entity: ctx.entityId,
        }, ctx.modules.MessageType.Task, target, ctx.modules.Propagation.Private);
        const created = messageId(ctx.modules, signed);
        record.tasks[task.key] = created;
        existing = await ctx.client.getMessage(created);
      } else {
        record.tasks[task.key] = existing.id;
      }
      for (const op of ops.filter((item) => item.kind === 'update_task' && item.key === task.key)) {
        await editField(ctx.client, ctx.modules, ctx.entityId, existing, [op.field], op.to);
      }
    }
    writeState(ctx.cfg, state);
  }

  const outboundSyncError = dryRun ? undefined : await safeSync(ctx.client, ctx.waste);
  output({
    dryRun,
    repo,
    repoId: id,
    entity: target,
    agentEntityId: ctx.entityId,
    projectId: record.projectId || null,
    summary: operationSummary(ops),
    operations: ops,
    sync: inboundSyncError || outboundSyncError
      ? { ok: false, inboundError: inboundSyncError, outboundError: outboundSyncError }
      : { ok: true },
  }, ctx.json);
}

async function focusedTask(args: ParsedArgs, mode: 'move' | 'close'): Promise<void> {
  const key = flag(args, 'key');
  if (!key) fail(`${mode} requires --key`);
  const status = flag(args, 'status');
  if (mode === 'move' && !status) fail('move requires --status');
  const dryRun = has(args, 'dry-run');
  const ctx = await initializedClient(args);
  const inboundSyncError = await safeSync(ctx.client, ctx.waste);
  const repo = canonicalRepo(flag(args, 'repo'));
  const id = repoHash(repo);
  const state = readState(ctx.cfg);
  const record = state.repositories[id];
  if (!record) fail(`no managed project for ${repo}`);
  const taskId = record.tasks?.[key];
  if (!taskId) fail(`unknown managed task key: ${key}`);
  const base = await ctx.client.getMessage(taskId);
  if (!base) fail(`mapped task is missing from Myco: ${taskId}`);
  const current = await effective(ctx.client, base);
  let next: any;
  let fieldName: string;
  if (mode === 'move') {
    const projectBase = await ctx.client.getMessage(record.projectId);
    if (!projectBase) fail(`mapped project is missing from Myco: ${record.projectId}`);
    const project = await effective(ctx.client, projectBase);
    if (!content(project).workflow?.includes(status)) fail(`status is not in the project workflow: ${status}`);
    fieldName = 'status';
    next = status;
  } else {
    fieldName = 'closed';
    next = true;
  }
  const before = content(current)[fieldName];
  if (!dryRun && JSON.stringify(before) !== JSON.stringify(next)) {
    await editField(ctx.client, ctx.modules, ctx.entityId, base, [fieldName], next);
  }
  const outboundSyncError = dryRun ? undefined : await safeSync(ctx.client, ctx.waste);
  output({
    dryRun,
    repo,
    key,
    taskId,
    operation: JSON.stringify(before) === JSON.stringify(next)
      ? { kind: 'unchanged', field: fieldName, value: next }
      : { kind: mode, field: fieldName, from: before, to: next },
    sync: inboundSyncError || outboundSyncError
      ? { ok: false, inboundError: inboundSyncError, outboundError: outboundSyncError }
      : { ok: true },
  }, ctx.json);
}

async function commandInvite(args: ParsedArgs): Promise<void> {
  const did = flag(args, 'did');
  if (!did) fail('invite requires --did');
  if (!did.startsWith('did:')) fail('invitee DID must start with did:');
  const dryRun = has(args, 'dry-run');
  const ctx = await initializedClient(args);
  const inboundSyncError = await safeSync(ctx.client, ctx.waste);
  const entityId = flag(args, 'entity') || ctx.entityId;
  const entity = ctx.client.entities.find((item: any) => item.id === entityId);
  if (!entity) fail(`target entity is not present locally: ${entityId}`);
  const currentMembers = Object.keys(ctx.modules.currentView(entity).public.members || {});
  const alreadyMember = currentMembers.includes(did);
  const canInvite = ctx.client.isMessagePermitted(
    entityId,
    ctx.modules.Propagation.Public,
    ctx.modules.MessageType.Join,
  );
  let inviteId: string | undefined;
  let error: string | undefined;
  if (!dryRun && !alreadyMember && canInvite) {
    try {
      const signed = await ctx.client.createMessage(
        { nominee: did, agentEntityId: ctx.entityId, actor_entity: ctx.entityId },
        ctx.modules.MessageType.Join,
        entityId,
        ctx.modules.Propagation.Public,
      );
      inviteId = messageId(ctx.modules, signed);
    } catch (e: any) {
      error = e?.message || String(e);
    }
  }
  const outboundSyncError = dryRun || alreadyMember || !canInvite || error
    ? undefined
    : await safeSync(ctx.client, ctx.waste);
  output({
    invited: !dryRun && !alreadyMember && canInvite && !error,
    dryRun,
    entity: entityId,
    nominee: did,
    alreadyMember,
    canInvite,
    inviteId: inviteId || null,
    status: alreadyMember ? 'already-member' : canInvite ? (dryRun ? 'ready' : error ? 'failed' : 'pending-acceptance') : 'denied',
    ...(error ? { error } : {}),
    sync: inboundSyncError || outboundSyncError
      ? { ok: false, inboundError: inboundSyncError, outboundError: outboundSyncError }
      : { ok: true },
  }, ctx.json);
  if (error || (!alreadyMember && !canInvite)) process.exitCode = 1;
}

async function commandConnectOwner(args: ParsedArgs): Promise<void> {
  const avatarDid = flag(args, 'avatar');
  const rawPeerLink = flag(args, 'peer-link');
  if (!avatarDid?.startsWith('did:myco:')) fail('connect-owner requires --avatar did:myco:...');
  if (!rawPeerLink) fail('connect-owner requires --peer-link');
  const dryRun = has(args, 'dry-run');
  const ctx = await initializedClient(args);
  const inboundSyncError = await safeSync(ctx.client, ctx.waste);
  const peer = parsePeerLink(rawPeerLink, ctx.modules);
  const entity = ctx.client.entities.find((item: any) => item.id === ctx.entityId);
  if (!entity) fail(`agent entity is missing locally: ${ctx.entityId}`);
  const members = Object.keys(ctx.modules.currentView(entity).public.members || {});
  const joins = [avatarDid, peer.id].filter((did) => !members.includes(did));

  const canInvite = ctx.client.isMessagePermitted(
    ctx.entityId,
    ctx.modules.Propagation.Public,
    ctx.modules.MessageType.Join,
  );
  if (!canInvite && joins.length) fail(`agent cannot invite members to ${ctx.entityId}`);

  const inviteIds: string[] = [];
  if (!dryRun) {
    await ctx.waste.addPeer({ id: peer.id, publicKey: peer.publicKey });
    // This command is the explicit user consent gate for trusting the owner.
    // The owner still decides independently whether to trust this agent.
    await ctx.waste.setTrust(peer.id, true);
    for (const did of joins) {
      const signed = await ctx.client.createMessage(
        { nominee: did, agentEntityId: ctx.entityId, actor_entity: ctx.entityId },
        ctx.modules.MessageType.Join,
        ctx.entityId,
        ctx.modules.Propagation.Public,
      );
      inviteIds.push(messageId(ctx.modules, signed));
    }
    await ctx.waste.gossip(peer.id, {
      respond: true,
      message: `Connect to ${readState(ctx.cfg).identity.name || 'Myco Code Steward'}`,
    });
    await ctx.waste.push();
  }

  output({
    dryRun,
    agentEntityId: ctx.entityId,
    avatarDid,
    deliveryPeerDid: peer.id,
    peerAdded: !dryRun,
    trusted: !dryRun,
    membershipInvites: joins,
    inviteIds,
    trustRequestQueued: !dryRun,
    legacyRelayUrlsIgnored: peer.legacyRelayUrls,
    sync: inboundSyncError ? { ok: false, error: inboundSyncError } : { ok: true },
  }, ctx.json);
}

function viewOf(modules: Dict, entity: any): any | undefined {
  try {
    return modules.currentView(entity);
  } catch {
    return undefined;
  }
}

async function commandGroups(args: ParsedArgs): Promise<void> {
  const ctx = await initializedClient(args);
  const syncError = await safeSync(ctx.client, ctx.waste);
  const search = flag(args, 'search')?.toLowerCase();
  const all = has(args, 'all');
  const self = [ctx.client.id, ctx.entityId];
  const groups: Dict[] = [];
  for (const entity of ctx.client.entities) {
    const view = viewOf(ctx.modules, entity);
    if (!view) continue;
    const members: string[] = ctx.modules.memberList(view);
    const agentIsMember = members.some((member: string) => self.includes(member));
    if (!all && !agentIsMember) continue;
    const name = view.public?.name || entity.id;
    if (
      search
      && !String(name).toLowerCase().includes(search)
      && !entity.id.toLowerCase().includes(search)
    ) continue;
    groups.push({
      id: entity.id,
      name,
      description: view.public?.description || '',
      creator: entity.creator,
      memberCount: members.length,
      agentIsMember,
    });
  }
  output({
    agentEntityId: ctx.entityId,
    routingDid: ctx.client.id,
    count: groups.length,
    groups,
    sync: syncError ? { ok: false, error: syncError } : { ok: true },
  }, ctx.json);
}

async function commandEntity(args: ParsedArgs): Promise<void> {
  const id = flag(args, 'id');
  if (!id) fail('entity requires --id');
  const ctx = await initializedClient(args);
  const syncError = await safeSync(ctx.client, ctx.waste);
  const entity = ctx.client.entities.find((item: any) => item.id === id);
  if (!entity) {
    output({
      found: false,
      id,
      reason: 'entity is not present locally; the agent has not received or joined it',
      agentEntityId: ctx.entityId,
      routingDid: ctx.client.id,
      sync: syncError ? { ok: false, error: syncError } : { ok: true },
    }, ctx.json);
    process.exitCode = 1;
    return;
  }
  const view = viewOf(ctx.modules, entity);
  if (!view) fail(`cannot compute current view for ${id}`);
  const members: string[] = ctx.modules.memberList(view);
  const self = [ctx.client.id, ctx.entityId];
  const result: Dict = {
    found: true,
    id: entity.id,
    creator: entity.creator,
    name: view.public?.name || entity.id,
    description: view.public?.description || '',
    members,
    memberCount: members.length,
    agentIsMember: members.some((member: string) => self.includes(member)),
    agentRoutingDid: ctx.client.id,
    agentEntityId: ctx.entityId,
    sync: syncError ? { ok: false, error: syncError } : { ok: true },
  };
  if (has(args, 'acl')) {
    const postTypes = ['note', 'task', 'project', 'topic', 'link', 'proposal'];
    const canCreate: Dict = {};
    for (const t of postTypes) {
      try {
        canCreate[t] = ctx.client.isMessagePermitted(id, ctx.modules.Propagation.Private, t);
      } catch {
        canCreate[t] = null;
      }
    }
    result.acl = {
      publicCreateSlots: view.public?.acl?.post || {},
      agentCanCreate: canCreate,
      note: 'ACL edits are creator-only; the agent cannot change these unless it is the creator',
    };
  }
  output(result, ctx.json);
}

async function commandMessages(args: ParsedArgs): Promise<void> {
  const entityId = flag(args, 'entity');
  if (!entityId) fail('messages requires --entity');
  const limit = Number.parseInt(flag(args, 'limit') || '50', 10);
  const ctx = await initializedClient(args);
  const syncError = await safeSync(ctx.client, ctx.waste);
  const all = await ctx.client.getMessagesByEntity(entityId);
  const rows = all
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
  output({
    entity: entityId,
    count: rows.length,
    messages: rows,
    sync: syncError ? { ok: false, error: syncError } : { ok: true },
  }, ctx.json);
}

async function commandPeers(args: ParsedArgs): Promise<void> {
  const ctx = await initializedClient(args);
  const syncError = await safeSync(ctx.client, ctx.waste);
  const peers = (ctx.waste.getPeers?.() ?? []).map((p: any) => ({
    id: p.id,
    publicKey: p.publicKey,
    encryption: p.encryption,
    capabilities: ctx.waste.getCapabilities?.(p.id) ?? {},
    trusted: ctx.waste.isTrusted?.(p.id) ?? false,
    connections: (ctx.waste.getConnections?.(p.id) ?? []).map((c: any) => ({
      connectionId: c.connectionId,
      transportType: c.transportType,
      posture: c.posture,
      uri: c.uri,
    })),
  }));
  const ownConnections = (ctx.waste.getConnections?.() ?? []).map((c: any) => ({
    connectionId: c.connectionId,
    transportType: c.transportType,
    posture: c.posture,
    uri: c.uri,
  }));
  output({
    agentEntityId: ctx.entityId,
    routingDid: ctx.client.id,
    peers,
    ownConnections,
    sync: syncError ? { ok: false, error: syncError } : { ok: true },
  }, ctx.json);
}

async function commandRemovePeer(args: ParsedArgs): Promise<void> {
  const did = flag(args, 'did');
  if (!did?.startsWith('did:ed25519:')) fail('remove-peer requires --did did:ed25519:...');
  const dryRun = has(args, 'dry-run');
  const ctx = await initializedClient(args);
  if (did === ctx.client.id) fail('refusing to remove the active routing identity');
  const peer = (ctx.waste.getPeers?.() ?? []).find((item: any) => item.id === did);
  const trusted = ctx.waste.isTrusted?.(did) ?? false;
  const capabilities = ctx.waste.getCapabilities?.(did) ?? {};
  const connections = (ctx.waste.getConnections?.(did) ?? []).map((c: any) => ({
    connectionId: c.connectionId,
    transportType: c.transportType,
    posture: c.posture,
  }));
  if (!dryRun && peer) await ctx.waste.removePeer(did);
  output({
    removed: !dryRun && !!peer,
    dryRun,
    peerDid: did,
    found: !!peer,
    trusted,
    capabilities,
    connections,
  }, ctx.json);
}

async function commandEditAcl(args: ParsedArgs): Promise<void> {
  const entityId = flag(args, 'entity');
  if (!entityId) fail('edit-acl requires --entity');
  const slot = flag(args, 'slot');
  if (!slot) fail('edit-acl requires --slot (e.g. task.create, project.create, edit, join)');
  const valueRaw = flag(args, 'value');
  if (!valueRaw) fail('edit-acl requires --value (JSON array, e.g. \'["creator","members"]\')');
  let value: any;
  try { value = JSON.parse(valueRaw); } catch { fail('--value must be valid JSON'); }
  const tier = (flag(args, 'tier') || 'private').toLowerCase();
  if (tier !== 'public' && tier !== 'private') fail('--tier must be public or private');
  const dryRun = has(args, 'dry-run');
  const ctx = await initializedClient(args);
  const inboundSyncError = await safeSync(ctx.client, ctx.waste);
  const entity = ctx.client.entities.find((item: any) => item.id === entityId);
  if (!entity) {
    output({
      edited: false,
      entity: entityId,
      reason: 'entity is not present locally',
      agentEntityId: ctx.entityId,
      sync: inboundSyncError ? { ok: false, error: inboundSyncError } : { ok: true },
    }, ctx.json);
    process.exitCode = 1;
    return;
  }
  const propagation = tier === 'private' ? ctx.modules.Propagation.Private : ctx.modules.Propagation.Public;
  const canEdit = ctx.client.isMessagePermitted(entityId, propagation, ctx.modules.MessageType.Edit);
  const keys = [tier, 'acl', 'post', ...slot.split('.')];
  let error: string | undefined;
  let editId: string | undefined;
  if (!dryRun && canEdit) {
    try {
      const signed = await ctx.client.createMessage(
        { keys, value, agentEntityId: ctx.entityId, actor_entity: ctx.entityId },
        ctx.modules.MessageType.Edit,
        entityId,
        propagation,
      );
      editId = messageId(ctx.modules, signed);
    } catch (e: any) {
      error = e?.message || String(e);
    }
  }
  const outboundSyncError = dryRun ? undefined : await safeSync(ctx.client, ctx.waste);
  output({
    edited: !dryRun && canEdit && !error,
    dryRun,
    entity: entityId,
    tier,
    slot,
    value,
    keys,
    agentCanEdit: canEdit,
    ...(canEdit ? {} : { reason: 'agent is not in the edit permission slot; the creator must grant edit first' }),
    editId: editId || null,
    ...(error ? { error } : {}),
    sync: inboundSyncError || outboundSyncError
      ? { ok: false, inboundError: inboundSyncError, outboundError: outboundSyncError }
      : { ok: true },
  }, ctx.json);
  if (error || !canEdit) process.exitCode = 1;
}

// Rename the bound identity: updates the local `identity --json` name and, when
// the edit slot allows, publishes a public-tier Edit so peers see the new name
// and can mention it.
async function commandRename(args: ParsedArgs): Promise<void> {
  const name = flag(args, 'name')?.trim();
  if (!name) fail('rename requires --name');
  const dryRun = has(args, 'dry-run');
  const ctx = await initializedClient(args);
  const syncError = await safeSync(ctx.client, ctx.waste);

  const state = readState(ctx.cfg);
  const canEdit = ctx.client.isMessagePermitted(ctx.entityId, ctx.modules.Propagation.Public, ctx.modules.MessageType.Edit);
  let editId: string | undefined;
  let error: string | undefined;
  if (!dryRun && canEdit) {
    try {
      const signed = await ctx.client.createMessage(
        { keys: ['public', 'name'], value: name },
        ctx.modules.MessageType.Edit,
        ctx.entityId,
        ctx.modules.Propagation.Public,
      );
      editId = messageId(ctx.modules, signed);
      state.identity.name = name;
      writeState(ctx.cfg, state);
    } catch (e: any) {
      error = e?.message || String(e);
    }
  }
  const pushError = dryRun || !editId ? undefined : await (async () => {
    try { await ctx.waste.push(); return undefined; } catch (e: any) { return e?.message || String(e); }
  })();
  output({
    renamed: !dryRun && canEdit && !error,
    dryRun,
    name,
    agentEntityId: ctx.entityId,
    routingDid: ctx.client.id,
    publicNameEdit: canEdit ? (editId || null) : null,
    ...(canEdit ? {} : { reason: 'agent is not in the edit permission slot; public name not changed' }),
    ...(error ? { error } : {}),
    sync: syncError ? { ok: false, error: syncError } : { ok: true },
    push: pushError ? { ok: false, error: pushError } : { ok: true },
  }, ctx.json);
  if (error || !canEdit) process.exitCode = 1;
}

async function commandPost(args: ParsedArgs): Promise<void> {
  const entityId = flag(args, 'entity');
  const title = flag(args, 'title');
  if (!entityId) fail('post requires --entity');
  if (!title) fail('post requires --title');
  const body = flag(args, 'body');
  const space = flag(args, 'space');
  const pub = has(args, 'public');
  const dryRun = has(args, 'dry-run');
  const ctx = await initializedClient(args);
  const inboundSyncError = await safeSync(ctx.client, ctx.waste);
  const entity = ctx.client.entities.find((item: any) => item.id === entityId);
  if (!entity) {
    output({
      posted: false,
      entity: entityId,
      reason: 'entity is not present locally; join/sync it before posting',
      agentEntityId: ctx.entityId,
      routingDid: ctx.client.id,
      sync: inboundSyncError ? { ok: false, error: inboundSyncError } : { ok: true },
    }, ctx.json);
    process.exitCode = 1;
    return;
  }
  const view = viewOf(ctx.modules, entity);
  const members: string[] = view ? ctx.modules.memberList(view) : [];
  const self = [ctx.client.id, ctx.entityId];
  const agentIsMember = members.some((member: string) => self.includes(member));
  const propagation = pub ? ctx.modules.Propagation.Public : ctx.modules.Propagation.Private;
  const canPost = ctx.client.isMessagePermitted(entityId, propagation, ctx.modules.MessageType.Note);
  const content: Dict = {
    title,
    ...(body ? { body } : {}),
    ...(space ? { space } : {}),
    agentEntityId: ctx.entityId,
    actor_entity: ctx.entityId,
  };
  let postId: string | undefined;
  let error: string | undefined;
  if (!dryRun && canPost) {
    try {
      const signed = await ctx.client.createMessage(content, ctx.modules.MessageType.Note, entityId, propagation);
      postId = messageId(ctx.modules, signed);
    } catch (e: any) {
      error = e?.message || String(e);
    }
  }
  const outboundSyncError = dryRun || !canPost ? undefined : await safeSync(ctx.client, ctx.waste);
  output({
    posted: !dryRun && canPost && !error,
    dryRun,
    entity: entityId,
    title,
    propagation,
    postId: postId || null,
    agentIsMember,
    agentCanPost: canPost,
    ...(!canPost ? { reason: 'ACL denies this identity permission to create the Note' } : {}),
    ...(error ? { error } : {}),
    sync: inboundSyncError || outboundSyncError
      ? { ok: false, inboundError: inboundSyncError, outboundError: outboundSyncError }
      : { ok: true },
  }, ctx.json);
  if (error || !canPost) process.exitCode = 1;
}

async function commandAddPeer(args: ParsedArgs): Promise<void> {
  const rawPeerLink = flag(args, 'peer-link');
  if (!rawPeerLink) fail('add-peer requires --peer-link');
  const dryRun = has(args, 'dry-run');
  const ctx = await initializedClient(args);
  const peer = parsePeerLink(rawPeerLink, ctx.modules);
  if (!dryRun) {
    await ctx.waste.addPeer({ id: peer.id, publicKey: peer.publicKey });
  }
  const syncError = dryRun ? undefined : await safeSync(ctx.client, ctx.waste);
  output({
    added: !dryRun,
    dryRun,
    peerDid: peer.id,
    legacyRelayUrlsIgnored: peer.legacyRelayUrls,
    sync: syncError ? { ok: false, error: syncError } : { ok: true },
  }, ctx.json);
}

// Accept pending group invites naming this identity. Scans every known
// entity for an unresolved Join whose nominee is our DID and authors the
// Accept (only the nominee may). --entity scopes to one group; default
// accepts every pending invite.
async function commandJoin(args: ParsedArgs): Promise<void> {
  const scope = flag(args, 'entity');
  const dryRun = has(args, 'dry-run');
  const ctx = await initializedClient(args);
  const syncError = await safeSync(ctx.client, ctx.waste);
  const MessageType = ctx.modules.MessageType;
  const nominees = new Set([ctx.client.id, ctx.entityId]);
  const results: any[] = [];
  for (const entity of ctx.client.entities) {
    if (scope && entity.id !== scope) continue;
    let messages: any[] = [];
    try { messages = await ctx.client.getMessagesByEntity(entity.id); } catch { continue; }
    const joins = messages.filter((m: any) =>
      m.message?.data?.type === MessageType.Join
      && nominees.has(m.message?.data?.content?.nominee));
    for (const join of joins) {
      const nominee = join.message.data.content.nominee;
      const entry: any = { entity: entity.id, joinId: join.id, nominee };
      const alreadyAccepted = messages.some((m: any) =>
        m.message?.data?.type === MessageType.Accept
        && (m.message?.data?.content as any)?.join === join.id);
      if (alreadyAccepted) { entry.status = 'already-accepted'; results.push(entry); continue; }
      if (dryRun) { entry.status = 'pending'; results.push(entry); continue; }
      try {
        const previousIdentity = ctx.client.currentIdentity();
        if (previousIdentity !== nominee) ctx.client.switchEntity(nominee);
        try {
          await ctx.client.createMessage({}, MessageType.Accept, join.id, ctx.modules.Propagation.Private);
        } finally {
          if (ctx.client.currentIdentity() !== previousIdentity) ctx.client.switchEntity(previousIdentity);
        }
        entry.status = 'accepted';
      } catch (e: any) {
        entry.status = 'failed';
        entry.error = e?.message ?? String(e);
      }
      results.push(entry);
    }
  }
  const pushError = dryRun ? undefined : await (async () => {
    try { await ctx.waste.push(); return undefined; } catch (e: any) { return e?.message ?? String(e); }
  })();
  output({
    agentEntityId: ctx.entityId,
    routingDid: ctx.client.id,
    dryRun,
    results,
    push: pushError ? { ok: false, error: pushError } : { ok: true },
    sync: syncError ? { ok: false, error: syncError } : { ok: true },
  }, ctx.json);
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  switch (args.command) {
    case 'help': case '--help': case '-h': help(); break;
    case 'doctor': await commandDoctor(args); break;
    case 'init': await commandInit(args); break;
    case 'identity': await commandIdentity(args); break;
    case 'rename': await commandRename(args); break;
    case 'groups': await commandGroups(args); break;
    case 'entity': await commandEntity(args); break;
    case 'messages': await commandMessages(args); break;
    case 'peers': await commandPeers(args); break;
    case 'add-peer': await commandAddPeer(args); break;
    case 'remove-peer': await commandRemovePeer(args); break;
    case 'join': await commandJoin(args); break;
    case 'edit-acl': await commandEditAcl(args); break;
    case 'post': await commandPost(args); break;
    case 'snapshot': await commandSnapshot(args); break;
    case 'reconcile': await commandReconcile(args); break;
    case 'move': await focusedTask(args, 'move'); break;
    case 'close': await focusedTask(args, 'close'); break;
    case 'invite': await commandInvite(args); break;
    case 'invite-owner': await commandInvite(args); break;
    case 'connect-owner': await commandConnectOwner(args); break;
    default: fail(`unknown command: ${args.command}`);
  }
}

// Reuse the CLI's identity/storage bootstrap in the addressed-message poller.
// Fail closed if its bound identity or runtime key is missing; a scheduled
// worker must never silently mint a replacement identity.
export async function openExistingIdentity(): Promise<Dict> {
  const cfg = config();
  for (const file of [cfg.didFile, cfg.entityFile, cfg.keyFile]) {
    if (!fs.existsSync(file)) throw new Error('Bound Myco identity is incomplete');
  }
  return initializedClient(parseArgs(['peers', '--json']));
}

export { safeSync };

if (require.main === module) {
  main().catch((error: any) => fail(error?.stack || error?.message || String(error), 1));
}

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

test('editing nested-reply permissions preserves post-comment permissions and the other tier', () => {
  const root = process.env.MYCO_ROOT || '/home/user/code/myco';
  const cli = path.join(__dirname, 'myco.ts');
  const loader = path.join(root, 'myco-agent/node_modules/tsx/dist/loader.mjs');
  const env = { PATH: process.env.PATH, HOME: process.env.HOME, MYCO_ROOT: root,
    MYCO_DATA_DIR: mkdtempSync(path.join(tmpdir(), 'myco-acl-test-')), MYCO_RELAY_URL: 'local' };
  const run = (...args: string[]) => {
    const result = spawnSync(process.execPath, ['--import', loader, ...args], { env, encoding: 'utf8', timeout: 20000 });
    assert.equal(result.status, 0, result.stderr || result.stdout);
    return JSON.parse(result.stdout);
  };
  const identity = run(cli, 'init', '--name', 'ACL test', '--json');
  const entity = identity.agentEntityId;
  assert.ok(entity);
  const read = () => run('--eval', `
    const skill = require(${JSON.stringify(cli)});
    (async () => {
      const c = await skill.openExistingIdentity();
      try { console.log(JSON.stringify(c.modules.currentView(c.client.getEntity(${JSON.stringify(entity)})))); }
      finally { await c.waste.stop(); await c.db.close(); await c.wb.db.close(); }
    })().catch(e => { console.error(e); process.exitCode = 1; });
  `);
  const before = read();
  const args = [cli, 'edit-acl', '--entity', entity, '--tier', 'private', '--slot', 'response.comment', '--value', '["members"]', '--json'];
  assert.equal(run(...args, '--dry-run').agentCanEdit, true);
  assert.deepEqual(read(), before, 'preview must not change entity state');
  assert.equal(run(...args).edited, true);
  const after = read();
  assert.deepEqual(after.private.acl.response.comment, ['members']);
  assert.deepEqual(after.private.acl.post, before.private.acl.post);
  assert.deepEqual(after.public, before.public);
});

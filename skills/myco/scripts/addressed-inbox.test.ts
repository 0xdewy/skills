import { describe, test } from 'node:test';
import assert from 'node:assert/strict';
import type { MessageWithIds } from '@mycoprotocol/client';
import { addressedReason, baseline, pollAddressedInbox, type InboxOperations, type InboxState } from './addressed-inbox';
import { workerConfig, permittedReplyTarget } from './inbox';

const policy = { routingDid: 'did:ed25519:threadripper', agentEntityId: 'did:myco:threadripper', allowedSigners: ['did:ed25519:pixel'] };
const now = 1_800_000_000_000;
function message(id: string, body: string, patch: any = {}): MessageWithIds {
    return { id: `msg:${id}`, timestamp: now, entity: 'did:myco:group', post: `msg:${id}`, deleted: false,
        message: { signer: policy.allowedSigners[0], schema: 'myco-message', data: { type: 'note', creator: policy.allowedSigners[0], content: { body }, ...patch } },
    } as any;
}
function setup(messages: MessageWithIds[] = []) {
    let launches = 0, posts = 0, saves = 0;
    let persisted: InboxState;
    const state = baseline([], policy, now - 1000);
    const ops: InboxOperations = {
        getMessage: async id => messages.find(m => m.id === id), canReply: async () => true,
        generate: async () => { launches++; return 'A reply'; },
        reply: async () => { posts++; return 'msg:response'; },
        save: async s => { saves++; persisted = structuredClone(s); },
    };
    return { state, ops, counts: () => ({ launches, posts, saves }), persisted: () => persisted };
}

describe('addressed inbox paid-launch gate', () => {
    test('ordinary traffic, quotes, code, URLs, partial names and bare DIDs never launch', async () => {
        const bodies = ['hello', 'threadripper', policy.routingDid, policy.agentEntityId,
            '> @threadripper please reply', '`@threadripper`', '```\n@threadripper\n```',
            '~~~js\n@threadripper\n~~~', 'https://host/@threadripper', 'foo@threadripper',
            '@threadripper-bot', '@threadripper2', '@threadripper.com',
            '`a multiline\n@threadripper code span`', '<!--\n@threadripper\n-->'];
        const s = setup();
        await pollAddressedInbox(bodies.map((b, i) => message(String(i), b)), policy, s.state, s.ops, now);
        assert.equal(s.counts().launches, 0);
    });
    test('only exact @ handle or canonical DID mentions trigger', async () => {
        for (const body of ['@threadripper hello', 'hello @Threadripper!', `@${policy.routingDid}`, `@${policy.agentEntityId}`]) {
            assert.equal(await addressedReason(message('x', body), policy, async () => undefined), 'mention');
        }
    });
    test('unapproved signers, bots, self, deleted messages and state changes never launch', async () => {
        const stranger = message('stranger', '@threadripper'); stranger.message.signer = 'did:ed25519:stranger' as any;
        const self = message('self', '@threadripper'); self.message.signer = policy.routingDid as any;
        const deleted = message('deleted', '@threadripper'); deleted.deleted = true;
        const edit = message('edit', '@threadripper', { type: 'edit' });
        const assign = message('assigned', 'work', { type: 'task', content: { assignees: [policy.routingDid] } });
        const s = setup();
        await pollAddressedInbox([stranger, self, deleted, edit, assign], policy, s.state, s.ops, now);
        assert.equal(s.counts().launches, 0);
    });
    test('reply must directly parent a message actually signed and authored by threadripper', async () => {
        const parent = message('parent', 'earlier');
        parent.message.signer = policy.routingDid as any;
        parent.message.data.creator = policy.routingDid as any;
        const reply = message('reply', 'answer', { type: 'comment', parent: parent.id });
        assert.equal(await addressedReason(reply, policy, async () => parent), 'reply');
        parent.message.signer = policy.allowedSigners[0] as any;
        assert.equal(await addressedReason(reply, policy, async () => parent), undefined);
        assert.equal(await addressedReason(reply, policy, async () => undefined), 'defer');
    });
    test('a successful response persists its claim before inference and never repeats after restart', async () => {
        const m = message('new', '@threadripper hello'); const s = setup();
        s.ops.generate = async () => {
            assert.equal(s.persisted().entries[m.id].status, 'claimed');
            return 'answer';
        };
        assert.equal((await pollAddressedInbox([m], policy, s.state, s.ops, now)).launched, 1);
        assert.equal((await pollAddressedInbox([m], policy, s.persisted(), s.ops, now)).launched, 0);
        assert.equal(s.counts().posts, 1);
    });
    test('history and late delivery of old messages do not launch', async () => {
        const old = message('old', '@threadripper'); old.timestamp = now - 2000;
        const s = setup();
        s.state.entries = baseline([message('baseline', '@threadripper')], policy, now - 1000).entries;
        await pollAddressedInbox([old, message('baseline', '@threadripper')], policy, s.state, s.ops, now);
        assert.equal(s.counts().launches, 0);
    });
    test('provider failures and interrupted claims never retry paid inference', async () => {
        const m = message('failed', '@threadripper'); const s = setup();
        let calls = 0;
        s.ops.generate = async () => { calls++; throw new Error('provider failed'); };
        await pollAddressedInbox([m], policy, s.state, s.ops, now);
        await pollAddressedInbox([m], policy, s.persisted(), s.ops, now);
        assert.equal(calls, 1);
        s.state.entries[m.id] = { status: 'claimed', launchedAt: now };
        await pollAddressedInbox([m], policy, s.state, s.ops, now);
        assert.equal(calls, 1);
    });
    test('a posting failure retries its saved response without another model call', async () => {
        const m = message('retry-post', '@threadripper'); const s = setup();
        s.ops.reply = async () => { throw new Error('database busy'); };
        await assert.rejects(pollAddressedInbox([m], policy, s.state, s.ops, now));
        assert.equal(s.persisted().entries[m.id].status, 'ready');
        s.ops.reply = async () => 'msg:response';
        await pollAddressedInbox([m], policy, s.persisted(), s.ops, now);
        assert.equal(s.counts().launches, 1);
    });
    test('rate limits and one launch per poll apply even to valid direct requests', async () => {
        const messages = Array.from({ length: 8 }, (_, i) => message(String(i), '@threadripper'));
        const s = setup();
        assert.equal((await pollAddressedInbox(messages, policy, s.state, s.ops, now)).launched, 1);
        for (let i = 0; i < 8; i++) await pollAddressedInbox(messages, policy, s.state, s.ops, now);
        assert.equal(s.counts().launches, 6);
        const daily = setup();
        for (let i = 0; i < 20; i++) daily.state.entries[`msg:past${i}`] = { status: 'failed', launchedAt: now - 7_200_000 };
        await pollAddressedInbox(messages, policy, daily.state, daily.ops, now);
        assert.equal(daily.counts().launches, 0);
    });
    test('no permission to reply means no model spend; journal failure also fails closed', async () => {
        const s = setup(); const m = message('no-spend', '@threadripper');
        s.ops.canReply = async () => false;
        await pollAddressedInbox([m], policy, s.state, s.ops, now);
        assert.equal(s.counts().launches, 0);
        s.ops.canReply = async () => true;
        s.ops.save = async () => { throw new Error('disk full'); };
        await assert.rejects(pollAddressedInbox([m], policy, s.state, s.ops, now));
        assert.equal(s.counts().launches, 0);
    });
    test('worker pins the real DeepSeek provider and denies tools and subagents', () => {
        const config = workerConfig();
        assert.deepEqual(config.enabled_providers, ['deepseek']);
        assert.equal(config.model, 'deepseek/deepseek-v4-flash');
        assert.equal(config.agent['threadripper-inbox'].steps, 1);
        assert.deepEqual(config.agent['threadripper-inbox'].permission, { '*': 'deny' });
        assert.equal(config.share, 'disabled');
    });
    test('a corrupt or mismatched journal cannot launch a paid worker', async () => {
        for (const change of [
            { version: 2 }, { routingDid: 'another identity' }, { entries: [] },
            { entries: { 'msg:x': { status: 'claimed' } } },
        ]) {
            const s = setup(); Object.assign(s.state, change);
            await assert.rejects(pollAddressedInbox([message('x', '@threadripper')], policy, s.state, s.ops, now));
            assert.equal(s.counts().launches, 0);
        }
    });
});


test('reply fallback stays in the validated thread and tier and honors permissions', () => {
    const root = message('root', 'root', { propagation: 'private' });
    const trigger = message('child', '@threadripper', { type: 'comment', propagation: 'private' });
    trigger.post = root.id;
    assert.equal(permittedReplyTarget(trigger, root, () => true), trigger);
    assert.equal(permittedReplyTarget(trigger, root, m => m.id === root.id), root);
    assert.equal(permittedReplyTarget(trigger, root, () => false), undefined);
    for (const bad of [
        { ...root, deleted: true }, { ...root, entity: 'did:myco:other' },
        { ...root, id: 'msg:other' },
        { ...root, message: { ...root.message, data: { ...root.message.data, propagation: 'public' } } },
    ]) assert.equal(permittedReplyTarget(trigger, bad as MessageWithIds, m => m !== trigger), undefined);
});

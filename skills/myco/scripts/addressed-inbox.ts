import type { MessageWithIds } from '@mycoprotocol/client';

export interface InboxPolicy {
    routingDid: string;
    agentEntityId: string;
    allowedSigners: string[];
}
export interface InboxEntry {
    status: 'ignored' | 'claimed' | 'ready' | 'responded' | 'failed';
    launchedAt?: number;
    body?: string;
    replyId?: string;
}
export interface InboxState {
    version: 1;
    routingDid: string;
    agentEntityId: string;
    enabledAt: number;
    entries: Record<string, InboxEntry>;
}
export type InboxReason = 'mention' | 'reply';

// Quoting a previous mention is not a new request. Ignore fenced/inline code,
// blockquotes and URLs before matching explicit @ addresses.
export function addressedText(text: string): string {
    let fence: string | undefined;
    return text.split('\n').map(line => {
        const marker = line.match(/^\s*(`{3,}|~{3,})/);
        if (marker) {
            if (!fence) fence = marker[1];
            else if (marker[1][0] === fence[0] && marker[1].length >= fence.length) fence = undefined;
            return '';
        }
        if (fence || /^\s*>/.test(line)) return '';
        return line;
    }).join('\n').replace(/<!--[\s\S]*?-->/g, '').replace(/(`+)[\s\S]*?\1/g, '').replace(/https?:\/\/\S+/g, '');
}

export async function addressedReason(
    message: MessageWithIds,
    policy: InboxPolicy,
    getMessage: (id: string) => Promise<MessageWithIds | undefined>,
): Promise<InboxReason | 'defer' | undefined> {
    const data = message.message?.data;
    const signer = message.message?.signer;
    if (message.deleted || !message.entity || message.message?.schema !== 'myco-message'
        || signer === policy.routingDid || !policy.allowedSigners.includes(signer)
        || !['note', 'comment', 'topic', 'link', 'task', 'project'].includes(data?.type)) return;
    const content = data.content as Record<string, unknown>;
    const text = addressedText([content.title, content.body, content.description].filter(v => typeof v === 'string').join('\n'));
    const boundary = '(?=$|[^a-zA-Z0-9_:-])(?!\\.[a-zA-Z0-9])';
    if (new RegExp('(^|[\\s([{])@threadripper' + boundary, 'i').test(text)) return 'mention';
    for (const id of [policy.routingDid, policy.agentEntityId]) {
        const escaped = id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        if (new RegExp('(^|[\\s([{])@' + escaped + boundary).test(text)) return 'mention';
    }
    if (data.type !== 'comment' || !data.parent?.startsWith('msg:')) return;
    const parent = await getMessage(data.parent);
    if (!parent || !parent.entity) return 'defer';
    if (!parent.deleted && parent.entity === message.entity && parent.message.signer === policy.routingDid
        && [policy.routingDid, policy.agentEntityId].includes(parent.message.data.creator)) return 'reply';
}

export function baseline(messages: MessageWithIds[], policy: InboxPolicy, now: number): InboxState {
    return { version: 1, routingDid: policy.routingDid, agentEntityId: policy.agentEntityId, enabledAt: now,
        entries: Object.fromEntries(messages.map(m => [m.id, { status: 'ignored' as const }])) };
}

export interface InboxOperations {
    getMessage(id: string): Promise<MessageWithIds | undefined>;
    canReply(message: MessageWithIds): Promise<boolean>;
    generate(message: MessageWithIds, reason: InboxReason): Promise<string>;
    reply(message: MessageWithIds, body: string): Promise<string>;
    save(state: InboxState): Promise<void>;
}

// One launch per poll, six per rolling hour and twenty per rolling day.
// Claims are persisted BEFORE OpenCode starts. A crash/failure does not retry
// inference: at-most-once spending is more important than automatic recovery.
export async function pollAddressedInbox(
    messages: MessageWithIds[], policy: InboxPolicy, state: InboxState, ops: InboxOperations, now = Date.now(),
): Promise<{ launched: number; responded: number; pending: number }> {
    if (state.version !== 1 || state.routingDid !== policy.routingDid || state.agentEntityId !== policy.agentEntityId
        || !Number.isFinite(state.enabledAt) || !state.entries || Array.isArray(state.entries) || !policy.allowedSigners.length
        || Object.values(state.entries).some(e => !e || !['ignored', 'claimed', 'ready', 'responded', 'failed'].includes(e.status)
            || (e.status !== 'ignored' && !Number.isFinite(e.launchedAt))
            || (e.status === 'ready' && (typeof e.body !== 'string' || !e.body || e.body.length > 12_000)))) {
        throw new Error('Inbox journal/policy mismatch; refusing paid work');
    }
    let launched = 0, responded = 0, pending = 0;
    for (const message of [...messages].sort((a, b) => a.timestamp - b.timestamp || a.id.localeCompare(b.id))) {
        const prior = state.entries[message.id];
        if (prior && prior.status !== 'ready') continue;
        if (!message.entity) continue; // Wait for protocol validation/dependencies.
        if (message.timestamp < state.enabledAt || message.timestamp < now - 86_400_000 || message.timestamp > now + 300_000) {
            state.entries[message.id] = { status: 'ignored' }; continue;
        }
        const reason = await addressedReason(message, policy, ops.getMessage);
        if (reason === 'defer') { pending++; continue; }
        if (!reason) { state.entries[message.id] = { status: 'ignored' }; continue; }
        if (!await ops.canReply(message)) { pending++; continue; }
        let entry = prior;
        if (!entry) {
            const starts = Object.values(state.entries).flatMap(e => e.launchedAt === undefined ? [] : [e.launchedAt]);
            if (launched || starts.filter(t => t > now - 3_600_000).length >= 6 || starts.filter(t => t > now - 86_400_000).length >= 20) {
                pending++; continue;
            }
            entry = state.entries[message.id] = { status: 'claimed', launchedAt: now };
            await ops.save(state);
            launched++;
            try {
                const body = (await ops.generate(message, reason)).trim();
                if (!body || body.length > 12_000) throw new Error('Invalid model response');
                entry.body = body;
                entry.status = 'ready';
            } catch {
                entry.status = 'failed';
            }
            await ops.save(state);
        }
        if (entry.status === 'ready') {
            // The adapter rechecks deletion/permissions and deduplicates using a
            // deterministic reply nonce. Posting retries never call the model.
            entry.replyId = await ops.reply(message, entry.body!);
            entry.status = 'responded';
            delete entry.body;
            responded++;
            await ops.save(state);
        }
    }
    await ops.save(state);
    return { launched, responded, pending };
}

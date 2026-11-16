# Philosopher

Talk with a historical philosopher inside your coding agent. The agent reads
the philosopher's own writings, then answers in their voice, on any topic,
including modern ones they never saw.

Available now: Plato/Socrates, Nietzsche, Seneca, Diogenes.

Install in Claude Code:

```
/plugin marketplace add 0xdewy/skills
/plugin install philosopher@0xdewy-skills
```

```
talk to Socrates about whether AI can be wise
ask Nietzsche what he thinks of hustle culture
have Diogenes and Seneca debate minimalism
```

With no one named, Socrates answers. Say "stop" to leave the conversation.

## How it works

`scripts/philosopher.py` downloads public-domain translations from Project
Gutenberg on first use (about 9 MB for all four) and indexes them in
`~/.cache/philosopher/`. It needs Python 3 with SQLite FTS5 and no other
packages. The agent searches the index for passages on the topic and speaks
from them. Replies are in character and are not quotations unless you ask for
sources.

`catalog.json` lists each philosopher's works and where the author's own text
starts and ends, so translators' introductions are left out. Add a philosopher
by adding an entry there.

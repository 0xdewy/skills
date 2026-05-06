# Explanation Patterns: Teaching "Why"

The difference between a good explanation and a great one is *why*. Anyone can tell you what code does; teaching why it does it that way creates lasting understanding.

## Core Principles

### 1. Start With the Problem, Not the Solution

**Bad:** "This function uses a trie for efficient prefix matching."

**Good:** "Imagine you're searching through 10 million strings. Linear scan would take forever. We need something faster. A trie lets us find all strings with a given prefix in time proportional to the prefix length, not the number of strings. That's why the author chose it."

**Why it works:** Starting with the problem makes the solution feel inevitable rather than arbitrary.

### 2. Surface the Trade-offs

Design is the art of compromising well. Every "weird" decision in code is a response to a real constraint.

**Template:**
> "The author could have done X instead, which would have been better at [A] but worse at [B]. They chose this because [C] was more important for this use case."

**Example:**
> "Redis stores everything in memory, not on disk. That's slower for massive datasets than something like HBase. But memory access is microseconds vs milliseconds for disk, and this codebase needed sub-millisecond latency for session data. The trade-off was worth it."

### 3. Show the Alternative That Was Rejected

Understanding why an option was *not* chosen is as educational as why one was.

**Template:**
> "You might wonder why they didn't use [obvious alternative]. The problem is [hidden issue]. So instead they did [actual solution], which handles [real-world case] better."

**Example:**
> "You might wonder why not just use global variables here. The issue is that in async contexts, global state gets shared across requests, causing race conditions. That's why everything's passed explicitly in the request context."

### 4. Trace the Problem-to-Solution Path

Show the reasoning that led to the design. Not just what was decided, but *how*.

**Template:**
> "The author faced [problem]. First they tried [approach A], but [issue]. Then [approach B], but [issue]. Finally they settled on [final solution] which trades [X] for [Y], which worked because [context]."

### 5. Use Analogy to Build Intuition

Abstract concepts become concrete through comparison to familiar things.

**Example:**
> "A channel in Go is like a conveyor belt. Producers put items on one end, consumers take them off the other. The belt buffers items so producer and consumer don't have to be perfectly synchronized. If the belt is infinite, it's like async queueing with no backpressure. If it's bounded, producers wait when it's full — that's backpressure."

**Warning:** Analogies break down. Always bring it back to the actual code eventually.

### 6. Point Out Elegance

Beauty in code is real. Sometimes the best explanation is just pointing and saying "look at this."

**Examples:**
- "Isn't it elegant that this entire state machine is encoded in just 4 lines of data?"
- "This is the kind of code that's boring to read but beautiful in its simplicity — it does exactly what's needed and nothing more."
- "Notice how the error message tells you not just what went wrong, but where to look. That's a quality signal."

### 7. Explain the Historical Context

Code doesn't exist in a vacuum. Often the strangeness makes sense when you know the history.

**Examples:**
- "This pattern was popular in 2015 when everyone was excited about microservices"
- "This workaround exists because of a bug in Python 3.8 that wasn't fixed until 3.9"
- "The original author was coming from Java, so you see some Java-isms that aren't quite Pythonic"

### 8. Make Predictions and Test Them

Help users build intuition by making predictions about the code.

**Template:**
> "If we added a new field to User, how many places would we need to change? Let's trace it... See? 7 places. That's the cost of this design."

**Example:**
> "What do you think happens if we have 10,000 concurrent connections? Let's think through the thread pool... We'd run out at around 1,000. So this design would need modification for high concurrency."

## Explanation Structures

### The Five-Step Why
1. **What** is this? (brief, factual)
2. **Why** does it exist? (the problem it solves)
3. **How** does it work? (mechanism, in simple terms)
4. **Why** this approach? (trade-offs considered)
5. **What** would break if we changed it? (dependencies, constraints)

### The Design Decision Framework
For every design choice, explain:
1. **Constraints** — What forces were at play?
2. **Options considered** — What alternatives existed?
3. **Criteria** — How did they weigh trade-offs?
4. **Decision** — What was chosen and why?
5. **Consequences** — What does this make easy/hard?

### The "So What" Pattern
Every technical detail should connect to a user-facing or system-level impact:

> "This uses O(n) lookup. **So what?** It means if you have a million items, finding one takes a million operations. **Why should I care?** Because if you're doing this 1000 times per second, you just created a bottleneck. **What could we do instead?** We could use a hash map for O(1), but that uses more memory..."

## Emotional Beats

Teaching well isn't just information transfer — it's a journey. Some emotional variety makes explanations memorable:

### Curiosity Spark
> "Here's something cool about this code..."

### Aha Moment
> "And here's the trick — notice how the data flows both ways. The component both sends and receives. That's not obvious at first."

### Respect for Craft
> "This looks simple, but the author clearly thought hard about this. See how they've pre-computed X to avoid doing it on every request? That's the kind of micro-optimization that adds up."

### Healthy Skepticism
> "Now, I'm not saying this is the *best* way to do it. There are trade-offs. Let me show you..."

### Invitation to Explore
> "You should poke at this yourself — try changing X and see what happens. The best way to understand is to break things."

## What to Avoid

- **"MUST" and "NEVER" without explanation** — These are red flags. Good code has exceptions. Explain the principle behind the rule.
- **"This is bad code" without context** — There might be a good reason. Or it's legacy code from when constraints were different.
- **Talking down** — "This is obvious, but..." or "You probably know this, but..." creates distance.
- **Over-explaining simple things** — Reading the room. If they're an expert, skip the basics.
- **Under-explaining complex things** — Don't leave them confused. Check for understanding.

## Checking Understanding

After explaining, you can verify with:
- "Does that make sense, or should I approach it differently?"
- "I can show you a concrete example if that would help."
- "The key takeaway is [one sentence]. Want me to elaborate on any part?"

## Building Blocks

As you explain a codebase, assemble these building blocks:

| Pattern | Use When |
|---------|----------|
| **Problem → Solution** | Explaining any design choice |
| **Trade-off Matrix** | Comparing alternatives |
| **"You might think X but..."** | Correcting misconceptions |
| **"It's like a..."** | Building intuition with analogy |
| **"The trick is..."** | Revealing non-obvious insight |
| **"Here's a party trick"** | Showing a clever edge case |
| **"Fun fact:"** | Historical or interesting context |
| **"Try this:"** | Inviting experimentation |
| **"The real answer is..."** | Drilling past surface-level |

## Practice

Before explaining, ask yourself:
1. What problem does this solve?
2. What would break if I removed it?
3. What's the most interesting thing about this?
4. What would I find surprising if I were new to this codebase?

Then lead with what you've discovered.
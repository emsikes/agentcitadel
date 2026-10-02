# Memory layer

Three stores behind one audited interface: episodic (conversation turns), semantic
(embeddings for retrieval), and procedural (learned tool sequences). Every read and
write appends an entry to the audit log.

## Audit trail

Each entry records the operation, the store it touched, a detail string, a timestamp,
and the hash of the entry before it. An entry's own hash covers all of those fields,
so each link references the one behind it.

`verify()` walks the chain carrying the expected previous hash, beginning with the
fixed value `genesis`. At each entry it checks two things: that the entry's recorded
`prev_hash` matches what it is carrying, and that recomputing the entry's hash from
its current contents reproduces the stored hash. It returns the sequence number of the
first entry that fails, or `None` if the chain is intact.

The two checks catch different tampering. Editing an entry breaks the recomputed hash.
Deleting one breaks the following entry's `prev_hash`, which is why removing entry 2
is reported at entry 3 — entry 2 is gone, and entry 3 is where the gap becomes visible.

### What this does and does not prove

It proves the log has not been edited by someone unable or unwilling to recompute the
chain. That covers accidental corruption, partial writes, and unsophisticated tampering.

It does not prove the log is complete. If the calling code never records an operation,
nothing appears, and the chain remains valid with the event missing. Tamper-evidence is
not completeness.

It also does not prevent tampering. Anyone with write access to the whole file can alter
an entry and recompute every hash after it, producing a valid chain. Closing that gap
requires getting the hashes somewhere the attacker cannot reach:

- **Anchoring** — periodically write the current chain hash to separate append-only
  storage, and compare against it during verification.
- **Signing** — sign each hash with a key the agent process does not hold.
- **Write-once storage** — object-lock buckets, append-only databases, or a remote
  syslog target where rewriting is not possible.

None of these are built into the framework. They are deployment decisions, and a library
that mandates one is a library with fewer deployments. AgentCitadel provides the chain
and the verification function so any of them can be layered on top.

## Vector store

The default is sqlite-vec (currently 0.1.9, pre-1.0), chosen over Chroma, LanceDB, and
FAISS for three reasons specific to this project.

Search is exact rather than approximate. HNSW and IVF-PQ indexes return slightly
different results depending on index state, which is incompatible with a replay engine
that must reproduce a run faithfully.

Episodic memory, semantic memory, and the audit trail share one SQLite file, so a memory
read and its audit entry commit in the same transaction. Split across separate stores,
that guarantee is lost.

Scale is not a constraint here. Agent memory holds conversation turns and decisions, not
a document corpus, and brute-force search is adequate well past that size.

`VectorStore` is a Protocol, so the default is swappable. An application doing retrieval
over a large corpus should use a store built for it — that belongs in the application,
not in the framework's memory layer.
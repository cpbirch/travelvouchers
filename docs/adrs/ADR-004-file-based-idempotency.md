# ADR-004: File-Based Idempotency

## Status

Accepted

## Context

The system requires idempotent voucher generation:
- Duplicate requests (same booking_id + service_date) return existing voucher
- No regeneration or storage write on duplicate
- Must work at 10 requests/second

User constraint: File storage only (no database).

## Decision

Implement idempotency via file system path existence check.

**Idempotency key**: `{booking_id}/{service_date}`

**Storage structure:**
```
/vouchers/{booking_id}/{service_date}/
    voucher.pdf
    voucher.html
    metadata.json
```

**Algorithm:**
1. Construct storage path from booking_id + service_date
2. Check if `metadata.json` exists at path
3. If exists: read metadata, return 200 with existing URLs
4. If not exists: generate voucher, store files, return 201

## Alternatives Considered

### 1. Database with Idempotency Table
- **Pros**: Fast lookup; ACID guarantees; can store additional metadata
- **Cons**: Adds database dependency; user explicitly requested no database
- **Rejected**: Violates user constraint

### 2. Redis/Cache-Based Idempotency
- **Pros**: Very fast lookup; TTL-based cleanup
- **Cons**: Adds infrastructure; cache miss requires fallback; data loss risk
- **Rejected**: Adds infrastructure complexity without necessity

### 3. In-Memory Map
- **Pros**: Fastest lookup
- **Cons**: Lost on restart; doesn't scale across multiple workers/instances
- **Rejected**: Not persistent; breaks across restarts

### 4. Filename-Only Check (no metadata.json)
- **Pros**: Simpler; one less file
- **Cons**: Cannot retrieve generated_at timestamp; cannot verify completeness
- **Rejected**: Metadata needed for idempotent response fields

## Consequences

### Positive
- No additional infrastructure (database/cache)
- Natural atomic writes (write metadata.json last)
- Simple implementation
- Storage path = idempotency key (single source of truth)

### Negative
- Filesystem I/O for every idempotency check
- Race condition window during concurrent writes
- S3 eventual consistency may cause brief duplicate detection misses

### Mitigations
- **Performance**: Filesystem checks are fast (~1ms); metadata.json is tiny
- **Race conditions**: Acceptable for this use case (worst case: regenerate once)
- **S3 consistency**: Use S3 strong consistency (default since 2020)

## Implementation Detail

### metadata.json Structure
```json
{
    "voucher_id": "V-2024-78432-0315",
    "booking_id": "BK-2024-78432",
    "service_date": "2024-03-15",
    "template_id": "airport-transfer-v2",
    "generated_at": "2024-02-17T10:23:45Z",
    "pdf_url": "https://storage.example.com/vouchers/BK-2024-78432/2024-03-15/voucher.pdf",
    "html_url": "https://storage.example.com/vouchers/BK-2024-78432/2024-03-15/voucher.html"
}
```

### Write Order (Atomic Semantics)
1. Write voucher.pdf
2. Write voucher.html
3. Write metadata.json (last - signals completion)

If crash before step 3, next request regenerates (safe).

## Decision Date

2026-02-17

## Decision Makers

Morgan (Solution Architect)

# Architecture Styles — Selection Reference

This document is a reference for **architecture-style selection**. It complements the architecture plugin's `assess` and `design` skills by providing a structured "When to Use / When to Avoid" rubric for the seven styles most commonly considered when shaping a new system or evolving an existing one. The styles below interact directly with the DDD anti-patterns catalogued under **AP#7b (Domain-Driven Design)**, the bounded-context isolation conventions captured under **AP#7c (Bounded Context Session Isolation)**, the event-driven concerns under **AP#7d (Event-Driven Architectures)**, and the microservice decoupling concerns under **AP#7a (Decoupled Microservices)**.

Use this doc when:
- An architect needs to justify *why* a particular style was chosen (or rejected) for a context.
- A retro flagged a mismatch between the codebase's style and the team/domain shape.
- A planner is choosing between Modular Monolith vs. Microservices early in a project.

Each section below follows the same structure: **Definition → DDD Mapping → When to Use → When to Avoid → Concrete Example**.

---

## Hexagonal Architecture

**Definition:** Hexagonal Architecture (a.k.a. Ports & Adapters), introduced by Alistair Cockburn, isolates the application's domain logic at the center of a "hexagon" and exposes it through **ports** (interfaces) that **adapters** translate to and from external technologies. The domain knows nothing about HTTP, databases, message brokers, or UIs — it only knows its ports.

**DDD Mapping (AP#7b):** Aggregates and domain services live in `domain/`. Repository interfaces are **secondary (driven) ports** — the domain declares them; infrastructure adapters implement them against Postgres, DynamoDB, etc. Application services that orchestrate use cases sit behind **primary (driving) ports** — REST controllers, CLI handlers, and message consumers are inbound adapters that call those ports. This cleanly enforces the AP#7b rule that aggregate invariants are protected by the domain layer, not leaked into HTTP handlers or ORM mappings.

**When to Use:**
- The domain is non-trivial and worth protecting from churn in delivery mechanisms (HTTP framework, ORM, message bus).
- You expect to swap or add adapters over time (e.g., REST today, gRPC tomorrow; SQS today, Kafka tomorrow).
- You need fast, framework-free unit tests for domain logic — test doubles can implement the secondary ports directly.
- Multiple delivery mechanisms (REST + CLI + scheduled job) call the same use case.

**When to Avoid:**
- Pure CRUD with no domain rules — the indirection adds layers without protecting anything.
- A short-lived prototype where the cost of port/adapter scaffolding outweighs the option value of swapping infrastructure.
- A team unfamiliar with dependency inversion who would mis-place infrastructure types in `domain/`, defeating the structure.

**Concrete Example:**
```
src/
  domain/                    # aggregates, value objects, domain services, port interfaces
    order/
      Order.java
      OrderRepository.java   # secondary port (interface)
  application/
    PlaceOrder.java          # use case behind a primary port
  adapters/
    inbound/
      rest/OrderController.java
      cli/PlaceOrderCommand.java
    outbound/
      jdbc/JdbcOrderRepository.java   # implements OrderRepository
      kafka/KafkaOrderEventPublisher.java
```

---

## Onion Architecture

**Definition:** Onion Architecture, introduced by Jeffrey Palermo, organizes code into concentric layers — Domain Model at the center, then Domain Services, then Application Services, with Infrastructure and Presentation on the outer rings. The fundamental rule: **dependencies point inward only.** An outer layer may depend on an inner layer; the reverse is forbidden.

**DDD Mapping (AP#7b):** The innermost ring (`domain/`) holds aggregates, entities, and value objects exactly as DDD prescribes. The next ring (`application/`) holds use-case orchestration that coordinates aggregates without containing business rules. `infrastructure/` (outer ring) provides repository implementations, ORM mappings, and external integrations — never reached into by the domain. This naturally enforces the AP#7b rule that domain rules belong inside aggregates, not scattered across handlers or DAOs.

**When to Use:**
- You want a slightly more explicit layering than Hexagonal — Onion is friendlier when teams think in *layers* rather than *ports*.
- The codebase will be touched by many engineers over years; the visual concentric model communicates the dependency rule even to junior contributors.
- You want a structure that maps cleanly to .NET / Java enterprise idioms where layered solutions are the norm.

**When to Avoid:**
- Same caveats as Hexagonal — pure CRUD does not justify the layering cost.
- Teams that conflate Onion's layers with the obsolete "tiered architecture" (presentation → business → data) and let `domain/` import from `infrastructure/`. That violation reverses the dependency rule and makes the layering ceremonial.
- Microservices where each service is small enough that a single flat module is clearer than four concentric ones.

**Concrete Example:**
```
src/
  domain/                  # innermost — entities, value objects, domain services
    Order.java
    OrderId.java
  application/             # use cases / orchestration
    PlaceOrderService.java
  infrastructure/          # outer ring — DB, messaging, external APIs
    persistence/JdbcOrderRepository.java
    messaging/KafkaPublisher.java
  presentation/            # outermost — REST controllers, GraphQL resolvers, CLI
    OrderController.java
```

---

## Modular Monolith

**Definition:** A Modular Monolith is a **single deployable unit** internally partitioned into modules that correspond to **bounded contexts**. Each module owns its data, its domain model, and its public interface; cross-module calls go through that interface, never through shared tables or in-memory shortcuts.

**DDD Mapping (AP#7b, AP#7c):** Each module is a bounded context. The modular monolith is the strongly-recommended starting point when context boundaries are still emerging — it keeps refactoring cheap (no network boundaries to cross) while still teaching the team to respect bounded-context isolation. **AP#7c (Bounded Context Session Isolation)** is operationalized via per-module `CLAUDE.md` files that document each context's ubiquitous language, invariants, and access rules — agents working in `contexts/sales/` should not be told the language of `contexts/inventory/`, preventing cross-context vocabulary leakage.

**When to Use:**
- Small team (≤8 developers) — coordination overhead of microservices is not yet justified.
- Context boundaries are still emerging — you suspect where they are but want cheap refactoring as you learn.
- Low operational overhead budget — no dedicated SRE function to run a service mesh, distributed tracing, and per-service CI/CD.
- Strong consistency requirements within and across contexts — local transactions are still feasible.

**When to Avoid:**
- Context boundaries are already well-established and stable, AND each team can independently deploy its context's module — at that point microservices stop being premature.
- Compliance / data residency mandates physical isolation between contexts (e.g., one tenant's data must live on isolated infrastructure).
- The deployable artifact has grown so large that build/test cycles dominate developer time and the boundaries are stable enough to extract.

**Concrete Example:**
```
src/
  contexts/
    sales/
      CLAUDE.md          # AP#7c per-context isolation: ubiquitous language, invariants
      domain/
        Order.java
        OrderId.java
      application/
        PlaceOrder.java
      api/               # public module interface — only this is callable from outside
        SalesApi.java
    inventory/
      CLAUDE.md          # AP#7c — independent ubiquitous language
      domain/
        Stock.java
      application/
        ReserveStock.java
      api/
        InventoryApi.java
  shared/                # truly shared kernel — keep deliberately small
    Money.java
    TenantId.java
```

---

## Microservices ↔ Aggregate Alignment

**Definition:** Microservices decompose a system into independently deployable services that communicate over the network. The DDD-aligned sizing rule is **"one service contains at least one aggregate and at most one bounded context"** — services that span bounded contexts re-create the coupling microservices were meant to break; services smaller than an aggregate fragment a transactional consistency boundary.

**DDD Mapping (AP#7a, AP#7b):** Each microservice owns one or more aggregates from a single bounded context. Cross-service communication respects context translation (anti-corruption layers, published-language events). **AP#7a (Decoupled Microservices)** is the runtime concern: services must not share databases, must not synchronously call each other in deep chains, and must tolerate partial failure. **AP#7b** governs the design-time concern: aggregate boundaries determine service boundaries, never the reverse.

**When to Use:**
- Large team or multiple teams that need independent deployment cadences.
- Bounded-context boundaries are clear, stable, and have survived production — you have evidence, not just hypothesis.
- Mature CI/CD, observability, and incident-response capabilities — distributed systems shift complexity from code into operations.
- Different services have legitimately different scaling profiles (read-heavy vs. write-heavy, CPU-bound vs. IO-bound).
- Different services have legitimately different non-functional requirements (regulatory isolation, multi-region replication, hard SLAs).

**When to Avoid:**
- Boundaries unclear — start as a Modular Monolith. Premature service decomposition produces a distributed monolith: all the network failure modes, none of the team independence.
- Small team — coordination, observability, and on-call overhead per service exceeds the engineering capacity available.
- Strong cross-service transactional consistency required — eventual consistency and saga patterns will fight the requirement, not satisfy it.
- The team lacks distributed-systems literacy (idempotency, outbox patterns, retries, backpressure) — failures will silently corrupt state.

**Concrete Example:** A `sales-service` owns the `Order` and `OrderLine` aggregates and exposes REST + event endpoints. A separate `inventory-service` owns `Stock` aggregates. They communicate via published-language domain events on Kafka (`OrderPlaced`, `StockReserved`) — never by sharing a database or by `sales-service` directly calling `inventory-service`'s internal endpoints. Aggregate alignment guarantees that each service can hold a local transaction around its own writes.

---

## CQRS Fit Criteria

**Definition:** Command Query Responsibility Segregation (CQRS) splits the model that **writes** state from the model that **reads** state. Writes flow through aggregates; reads flow through purpose-built projections (denormalized views, search indexes, caches) optimized for specific query shapes.

**DDD Mapping (AP#7b):** CQRS lets the write model stay small, normalized, and focused on invariant protection — exactly what aggregates are for. Read models are free to denormalize, join across aggregate boundaries, and shape themselves to UI needs without polluting the write model. This is one of the cleanest ways to honor the AP#7b rule that aggregates protect invariants while still serving rich queries.

**When to Use:**
- **Read load >> write load** — reads are 10×, 100× more frequent than writes, justifying duplicated read storage.
- **Read shape ≠ write shape** — queries need denormalized joins, search-engine semantics, or precomputed aggregations that the write model can't serve cheaply.
- **Eventual consistency between write and read is acceptable** — UI can tolerate ~seconds of staleness, and the team has communicated this to product.
- High-read dashboards, reporting, search, recommendation feeds, audit-log views.

**When to Avoid:**
- Simple CRUD with symmetric read/write shapes — using one model for both is simpler and cheaper.
- Strong consistency required — when a user must immediately see the result of their own write, CQRS adds latency and bug surface (read-your-own-writes patterns are tricky).
- Team unfamiliar with eventual consistency — projection lag will produce "I clicked save and nothing changed" bug reports that the team won't know how to triage.
- Low traffic — the projection infrastructure cost (extra storage, extra processes, extra failure modes) is not amortized.

**Concrete Example:** A `PlaceOrder` command goes through the `Order` aggregate (write model, normalized in Postgres). The aggregate emits an `OrderPlaced` event. A projection consumer denormalizes that event into a `customer_order_summary` table (one row per customer, with last-order date, lifetime value, segment). The "Customer 360" dashboard reads only from `customer_order_summary` — never from the normalized `orders`/`order_lines` tables.

---

## Event Sourcing Fit Criteria

**Definition:** Event Sourcing stores the **history of state changes as an append-only log of domain events** rather than the current state. The aggregate's current state is rebuilt by replaying its events. The event log becomes the system of record; projections are derived views.

**DDD Mapping (AP#7b, AP#7d):** Aggregates emit domain events as their public history. The events themselves *are* the persistence model — there is no row-per-aggregate in a relational table. **AP#7d (Event-Driven Architectures)** is directly relevant: the same events that drive aggregate rehydration also drive cross-context integration, projection updates, and downstream analytics. Designing the event language well is the central modeling exercise.

**When to Use:**
- **Audit / compliance is mandatory** — financial systems, healthcare, regulatory domains where "what was the state at time T?" is a legal requirement.
- **Time-travel debugging is valuable** — production incidents are diagnosed by replaying the event stream against new code.
- **Multiple read models** — billing, analytics, fraud, and customer-facing UIs each need a different shape; deriving them from one event stream beats joining six tables.
- **Domain is naturally event-shaped** — banking ledgers, order lifecycles, IoT sensor streams, claims processing.

**When to Avoid:**
- Simple CRUD — the cost of event design, projection rebuilds, and schema evolution dwarfs any benefit.
- Immediate consistency required end-to-end — projections lag the event log; queries against them are eventually consistent.
- Team unfamiliar with event-driven patterns — schema evolution (versioned events, upcasters), idempotency, and replay are non-trivial; getting them wrong corrupts the audit log itself.
- Frequent destructive deletes legally required (GDPR right-to-erasure) — tombstone/crypto-shredding patterns exist but add real complexity.

**Concrete Example:** An `Order` aggregate is rehydrated by replaying `OrderPlaced`, `OrderLineAdded`, `OrderShipped`, `OrderCancelled`. The current "state" of the order is a fold over those events. A separate `customer_order_summary` projection consumes the same events to power the dashboard (CQRS pairing with Event Sourcing is common). The legal team can answer "what did this order look like on March 3rd?" by replaying events up to that timestamp.

---

## JPA / Hibernate Pitfalls + Spring Data JDBC

**Definition:** Java Persistence API (JPA), most commonly via Hibernate, is a full-featured ORM that maps Java objects to relational tables with lazy loading, dirty checking, and identity-map caching. Spring Data JDBC is a deliberately simpler alternative: aggregates are loaded and saved as units, no lazy loading, no proxies, no session-scoped identity map.

**DDD Mapping (AP#7b):** JPA's defaults actively fight DDD aggregate discipline:

- **No-args constructor requirement** breaks immutability of aggregates and value objects. The no-args constructor exists for Hibernate's reflection — but the language of DDD aggregates is "construct in a valid state, only mutate via methods that enforce invariants." Adding a no-args constructor opens a back door.
- **Lazy loading violates aggregate boundaries.** A lazy `@OneToMany` from `Order` to a separate `Customer` aggregate, traversed inside a service, fetches across an aggregate boundary that DDD says you should cross only via an ID lookup. Worse, lazy loading outside a session throws `LazyInitializationException` in production while passing in test.
- **`@ManyToOne` between aggregates creates aggregate coupling.** The mapping makes it tempting to navigate `order.getCustomer().getEmail()` — but `Customer` is a separate aggregate; cross-aggregate references should be by ID only.
- **Cascade types** make it easy to persist multiple aggregates in one operation, blurring the "one aggregate per transaction" rule.
- **Dirty checking** persists changes you didn't explicitly save, which can promote temporary in-method state to durable state — the antithesis of explicit invariant-protecting save methods.

**When to Use Spring Data JDBC instead:**
- Greenfield Java/Kotlin services where you can establish aggregate discipline from day one.
- Aggregates are small enough to load and save as a unit (the DDD ideal — large aggregates are themselves an anti-pattern).
- The team will treat aggregate boundaries as inviolable — Spring Data JDBC enforces this by design (no lazy loading across references; references are stored as IDs, not as object graphs).
- You want explicit "load aggregate → mutate → save aggregate" semantics rather than session-scoped magic.

**When to Avoid Spring Data JDBC:**
- Heavy ORM-driven legacy where JPA mappings are pervasive and the migration cost is unjustified — fix the abuses (replace cross-aggregate `@ManyToOne` with ID references; remove cascades; use detached entities at boundaries) rather than rewrite.
- Read-heavy services that benefit from JPA's second-level caching and would have to re-implement that capability manually.
- Teams already deeply expert in JPA where the productivity loss of switching outweighs the discipline gain.

**Concrete Example (Spring Data JDBC, DDD-aligned):**
```java
public class Order {
    @Id private OrderId id;
    private CustomerId customerId;             // reference by ID, not @ManyToOne
    private List<OrderLine> lines;             // child entity within the SAME aggregate
    // ... invariant-protecting methods, no public setters, no no-args constructor
}

interface OrderRepository extends CrudRepository<Order, OrderId> {}
// Save persists the whole aggregate. Load returns the whole aggregate. No lazy loading.
```

---

## Cross-References & Related Anti-Patterns

This document deliberately stays focused on style selection. Where a style intersects deeply with a domain or operational concern, follow the cross-references to the architecture-plugin's anti-pattern catalogue:

- **AP#7a (Decoupled Microservices)** — runtime decoupling, idempotency, outbox patterns, partial-failure tolerance. Required reading for the Microservices style.
- **AP#7b (Domain-Driven Design)** — aggregate boundaries, ubiquitous language, anti-corruption layers, repository discipline. Underlies every style above.
- **AP#7c (Bounded Context Session Isolation)** — per-context `CLAUDE.md`, agent context isolation, vocabulary leakage prevention. Most directly relevant to the Modular Monolith style.
- **AP#7d (Event-Driven Architectures)** — event design, schema evolution, ordering, replay, projection consistency. Required reading for CQRS and Event Sourcing.
- **AP#7g (Data pipelines)** — when projections grow into data products with their own SLAs, the pipeline anti-patterns apply.

When in doubt: prefer the simpler style (Modular Monolith over Microservices; CRUD over CQRS; state-stored over Event-Sourced) until the cost of *not* having the more complex style is concrete and demonstrated. Architecture is the art of deferred commitment — keep optionality cheap.

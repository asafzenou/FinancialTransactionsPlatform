# Database Architecture - Financial Transactions Platform

This document describes the database schema, table responsibilities, and entity relationships. The structure is normalized to ensure data integrity and scalability.

## 1. Tables and Responsibilities

### A. Clients Table (`Client`)
* **Role:** Manages client entities in the system.
* **Fields:**
    * `id` (Primary Key): Unique identifier (e.g., 'C001').
* **Responsibility:** Acts as the root for all transactions and positions. Ensures referential integrity across the system.

### B. Raw Transactions Table (`Transaction`)
* **Role:** An audit log of all buy/sell actions ingested from the Excel source.
* **Fields:**
    * `id` (Primary Key): Internal auto-incrementing ID.
    * `client_id` (Foreign Key): Link to the Client table.
    * `transaction_id_excel` (Unique): Original ID from Excel to prevent duplicate processing.
    * `isin`: Asset identifier.
    * `action`: Action type (`buy` or `sell`).
    * `quantity`: Number of units.
    * `price`: Unit price.
    * `timestamp`: Transaction execution time.
* **Responsibility:** Serves as the immutable "Source of Truth" for the system.

### C. Computed Positions Table (`Position`)
* **Role:** Maintains the current holdings (aggregated state) for each client.
* **Fields:**
    * `id` (Primary Key).
    * `client_id` (Foreign Key).
    * `isin`: Asset identifier.
    * `total_quantity`: Total units currently held.
    * `average_price`: The weighted average cost (calculated via FIFO logic).
* **Responsibility:** API optimization. Instead of recalculating positions on every request, the system reads directly from this table.

### D. Rule Violations Table (`Violation`)
* **Role:** Logs any breaches of defined business rules.
* **Fields:**
    * `id` (Primary Key).
    * `client_id` (Foreign Key).
    * `transaction_id` (Foreign Key, Optional): Link to the specific transaction that triggered the violation.
    * `rule_broken`: Name of the rule (e.g., 'Day Trading', 'Risk Concentration').
    * `description`: Detailed explanation of the breach.
    * `timestamp`: When the violation was detected.
* **Responsibility:** Risk monitoring and compliance auditing.

---

## 2. Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    Client ||--o{ Transaction : executes
    Client ||--o{ Position : owns
    Client ||--o{ Violation : triggers
    Transaction ||--o| Violation : causes
    
    Client {
        string id PK
    }
    
    Transaction {
        int id PK
        string client_id FK
        string transaction_id_excel UK
        string isin
        string action
        int quantity
        float price
        datetime timestamp
    }
    
    Position {
        int id PK
        string client_id FK
        string isin
        int total_quantity
        float average_price
    }
    
    Violation {
        int id PK
        string client_id FK
        int transaction_id FK
        string rule_broken
        string description
        datetime timestamp
    }
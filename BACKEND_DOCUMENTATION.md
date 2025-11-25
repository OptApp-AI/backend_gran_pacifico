# Backend Documentation - Gran Pacífico Ice Distribution System

## System Overview

The Gran Pacífico backend is a comprehensive inventory and sales management system designed for an ice distribution business operating in two cities: Uruapan and Lázaro Cárdenas. The system manages two primary sales channels: in-store sales (mostrador) and delivery route sales (ruta), along with complete inventory tracking, client management, and administrative oversight.

The backend serves as the central nervous system that coordinates employee activities, tracks product movements, processes sales transactions, manages delivery routes, and ensures inventory accuracy across multiple locations. It operates as a RESTful API built on Django, providing secure access to two separate frontend applications - one for route management and one for point-of-sale operations.

---

## System Objectives

### Primary Goals

1. **Multi-City Operations**: The system maintains complete data separation between Uruapan and Lázaro Cárdenas operations. Each city operates independently with its own inventory, employees, clients, routes, and sales transactions.

2. **Inventory Control**: Provide real-time inventory tracking with automatic stock adjustments during sales, delivery preparations, returns, and inventory adjustments. Prevent negative inventory situations through validation rules.

3. **Sales Management**: Handle two distinct sales workflows - direct store sales and route-based delivery sales. Each transaction type has different processes, stock handling, and reporting requirements.

4. **Route Management**: Enable comprehensive delivery route planning, execution, and tracking. Routes are organized by day of the week, assigned to specific delivery personnel, and linked to clients who receive regular deliveries.

5. **Client Relationship Management**: Maintain detailed client information including contact details, addresses, payment preferences, and individualized pricing. Clients can be associated with multiple delivery routes.

6. **User Access Control**: Implement role-based access control with three distinct roles - Manager (Gerente), Cashier (Cajero), and Delivery Person (Repartidor). Each role has different capabilities and data visibility.

---

## Core Entities and Their Relationships

### Employees and Users

Every system user is represented by two interconnected entities: a Django User account (handling authentication) and an Employee profile (containing business-specific information). Employees have three key attributes: a role defining their job function, a profile image, and their assigned city of operation. The city assignment is critical as it determines which data an employee can access and modify.

When a user logs in, the system identifies their city assignment and automatically scopes all subsequent operations to that city's data. This ensures complete data isolation between the two operational locations.

### Products

Products represent the physical inventory items - in this case, ice products. Each product has a name, current stock quantity, public price, and an optional image. Products are city-specific, meaning the same product name can exist in both cities but with different stock levels and prices. When a product is created, the system automatically creates price relationships with all existing clients in that city, setting the initial client price equal to the product's public price.

The system enforces that quantities cannot go negative. All stock movements are tracked and validated before execution. Products maintain their own stock levels independently in each city.

### Clients

Clients are the customers who purchase products. There are two special system clients: "MOSTRADOR" (counter) for walk-in store sales, and "RUTA" (route) for route sales without a specific client association. Regular clients have names, contact information, addresses, payment preferences (cash or credit), and observations.

The most important feature of clients is their personalized pricing system. Each client can have different prices for each product they purchase. This allows for volume discounts, special rates, or negotiated pricing. When a new product is created, prices are automatically established for all clients at the public price, which administrators can then adjust individually.

Clients can be associated with multiple delivery routes through route-day relationships. This allows a client to receive deliveries on different days of the week or from different routes.

### Routes and Route Days

Routes represent delivery paths used by delivery personnel. Each route has a name and is assigned to a delivery person (repartidor). When a route is created, the system automatically generates seven route-day entries - one for each day of the week (Monday through Sunday).

Route days are the actual scheduling mechanism. Each route day specifies which day of the week the route operates and can have a different delivery person assigned (though typically it matches the route's assigned person). Clients are assigned to specific route days, meaning a client might receive deliveries on Monday and Wednesday from different routes, or on multiple days from the same route.

### Sales (Ventas)

Sales represent completed transactions. There are two types of sales: store sales (MOSTRADOR) and route sales (RUTA). Each sale records who made the sale, which client purchased, the total amount, payment type (cash, credit, or courtesy), discount percentage, status, and observations.

Sales have unique folio numbers that combine a prefix (M- for store, R- for route) with a sequential number, scoped to each city. This means Uruapan and Lázaro can both have a sale numbered M-1, but within each city, folio numbers are unique.

Sales can be in three states: PENDING (pending - not yet finalized), COMPLETED (realizado - transaction is final), or CANCELLED (cancelado - transaction was voided). The status determines whether inventory has been deducted and whether the sale can be reversed.

Each sale contains multiple product-sale entries detailing which products were sold, quantities, and the prices actually charged (which may differ from the product's public price due to client-specific pricing or discounts).

### Delivery Routes (Salida Ruta)

Delivery routes represent a concrete delivery session where a delivery person takes products from the warehouse and visits clients along their assigned route. This is one of the most complex entities in the system.

A delivery route starts in PENDING status when first created. Products are loaded onto the route (deducted from warehouse inventory), and clients are assigned. When the first sale or visit occurs, the status changes to PROGRESS (progreso). The route can only be completed (REALIZADO) when all products have been sold and all clients have been visited. If a route is still in PENDING status, it can be cancelled, which returns all products to inventory and removes the route.

Delivery routes have integer folio numbers unique per city. These are simpler than sales folios because they don't need prefixes - they're just sequential numbers.

Each delivery route contains two types of child records: products loaded on the route and clients assigned to visit. Products on the route track available quantity (which decreases as sales occur) and status (LOADED or SOLD). Clients on the route track visit status (PENDING or VISITED).

### Inventory Adjustments

Inventory adjustments allow authorized personnel to correct inventory discrepancies. There are three types: SHORTAGE (faltante - remove inventory due to loss or damage), SURPLUS (sobrante - add inventory found unexpectedly), and PRODUCTION (producción - add inventory from manufacturing).

Adjustments require administrator approval. Cashiers can create adjustments, but they remain in PENDING status until an administrator marks them as COMPLETED. Only completed adjustments affect inventory. This two-step process provides oversight and prevents unauthorized inventory modifications.

### Returns (Devoluciones)

Returns represent products returned from delivery routes back to the warehouse. Like inventory adjustments, returns require administrator approval. A cashier creates a return request, which remains PENDING until an administrator approves it. Upon approval, products are returned to inventory and the delivery route's product quantities are updated.

---

## Key Workflows

### User Authentication and Login

When a user attempts to log in, the system validates their credentials and generates a JWT (JSON Web Token) that encodes their identity. The token includes not just authentication information, but also additional context: the user's role, employee ID, profile image, and - if they're a delivery person - the ID of their current active delivery route (one that's in PENDING or PROGRESS status).

This enriched token allows the frontend to immediately display relevant information without additional API calls. For delivery personnel, it automatically identifies which delivery route they should be working on, streamlining their workflow.

### Store Sales Workflow

Store sales begin when a cashier selects a client (or uses the default "MOSTRADOR" client for walk-in sales). The system retrieves all products and their prices specific to that client. The cashier adds products to the sale, specifying quantities.

When the sale is finalized, the system:
1. Generates a unique folio number based on the sale type and city
2. Creates the sale record
3. Creates product-sale entries for each item
4. If the sale status is COMPLETED, deducts quantities from warehouse inventory
5. Calculates and records the total amount

If a sale needs to be cancelled or modified, the system intelligently adjusts inventory. If a COMPLETED sale is cancelled, products are returned to stock. If a PENDING sale is marked as COMPLETED, products are deducted from stock. This ensures inventory accuracy regardless of when status changes occur.

### Route Sales Workflow

Route sales are more complex because they involve multiple stages: preparation, execution, and completion.

**Preparation Phase:**
A delivery route is created by:
1. Selecting a route and specific day
2. Assigning a delivery person
3. Loading products onto the route (these are immediately deducted from warehouse inventory)
4. Assigning clients to visit
5. The system automatically assigns the special "RUTA" client as already visited (since route sales without specific clients use this)

The route starts in PENDING status and receives a unique folio number.

**Execution Phase:**
As the delivery person makes visits, they can:
- Make sales to clients: This creates a sale record (marked as RUTA type), updates the client's visit status to VISITED, decreases available product quantities on the route, and marks products as SOLD when quantities reach zero
- Mark clients as visited without a sale: This updates the client status to VISITED
- Add products via "recarga" (reload): If needed, additional products can be loaded mid-route, which deducts from warehouse inventory and adds to route inventory
- Return products: If products need to be returned to the warehouse, a return request is created (requires admin approval)

After each operation, the system checks if the route is complete: all products sold AND all clients visited. If both conditions are met, the route status automatically changes to COMPLETED (REALIZADO).

**Cancellation:**
If a route is still in PENDING status (no sales or visits yet), it can be cancelled. Cancellation returns all products to warehouse inventory and removes the route entirely. Routes in PROGRESS status cannot be cancelled - they must be completed.

### Product Creation Workflow

When a new product is created:
1. The product is saved with the specified name, initial quantity, price, and optional image
2. The system identifies all existing clients in the same city
3. For each client, a price relationship is automatically created, setting the client's price equal to the product's public price
4. Administrators can later adjust individual client prices as needed

This ensures every client immediately has access to the new product at a standard price, with the flexibility to customize pricing later.

### Client Creation Workflow

When a new client is created:
1. Basic client information is saved (name, contact, phone, email, payment type, observations)
2. Address information is saved in a separate address record
3. Client-specific prices are established for all existing products (using each product's public price)
4. The client is optionally assigned to one or more route days

The system ensures that new clients immediately have pricing relationships with all products, allowing them to make purchases immediately.

### Inventory Adjustment Workflow

Cashiers can create inventory adjustments when discrepancies are discovered. The adjustment specifies:
- Product affected
- Warehouse location
- Type of adjustment (shortage, surplus, or production)
- Quantity
- Observations

The adjustment is created in PENDING status. The system validates that shortages won't create negative inventory. When an administrator approves the adjustment (changes status to COMPLETED), the inventory is adjusted accordingly.

### Price Update Workflow

When a product's public price is updated, administrators can choose to update all client prices automatically or maintain existing client-specific pricing. If automatic update is selected, all client prices for that product are updated to match the new public price. This is useful when prices change across the board, but administrators can still manually adjust individual client prices afterward.

---

## Business Rules and Constraints

### Data Isolation

The most fundamental constraint is city-based data isolation. Every entity (products, clients, employees, sales, routes) is tagged with a city identifier. Users can only see and modify data from their assigned city. This ensures complete operational independence between Uruapan and Lázaro Cárdenas, even though they share the same system.

### Inventory Constraints

1. **Non-Negative Inventory**: Products cannot have negative quantities. All operations that would reduce inventory are validated before execution. If insufficient stock exists, the operation is rejected.

2. **Stock Deduction Rules**: Different operations deduct stock at different times:
   - Store sales: Stock is deducted when the sale status changes to COMPLETED
   - Delivery routes: Stock is deducted immediately when products are loaded onto the route
   - Returns: Stock is added back only after administrator approval

3. **Route Stock Management**: Products on delivery routes maintain separate "available quantity" tracking. This allows partial sales and returns without immediately affecting warehouse inventory until the route is completed or cancelled.

### Folio Numbering Rules

1. **Sales Folios**: Unique per city and sale type. Format: Prefix (M- or R-) followed by sequential number. Each city maintains separate sequences for store and route sales.

2. **Delivery Route Folios**: Simple integer sequence unique per city. Each delivery route gets the next available number in its city's sequence.

### Delivery Route Status Rules

1. **PENDING**: Route can be cancelled, modified, or products can be added. No sales or visits have occurred.

2. **PROGRESS**: Route has active sales or visits. Cannot be cancelled. Can receive additional products via reload. Can process returns (with admin approval).

3. **COMPLETED**: All products sold AND all clients visited. Final state, cannot be modified further.

4. **CANCELLED**: Only achievable from PENDING status. Returns all products to warehouse and removes route records.

### Client Visit Rules

Clients must be visited before a route can be completed. A visit can occur through:
- Making a sale to the client
- Explicitly marking the client as visited (even if no sale occurred)

The special "RUTA" client is automatically marked as visited when the route is created, since route sales without specific clients use this client designation.

### Return and Adjustment Approval Rules

Returns and inventory adjustments follow a two-stage approval process:
1. Cashier creates the request (PENDING status)
2. Administrator approves (COMPLETED status)
3. Only upon approval do inventory changes occur

This prevents unauthorized inventory modifications and provides audit trails.

### Username Uniqueness

To prevent conflicts between cities, usernames are automatically suffixed with city identifiers:
- Uruapan users: username_urp
- Lázaro users: username_laz

This allows the same username to exist in both cities without conflicts, while maintaining uniqueness within each city.

---

## System Interactions

### Frontend Applications

The backend serves two separate frontend applications:

1. **Route Management Frontend**: Used primarily by delivery personnel and managers. Focuses on delivery route creation, route sales execution, client visit tracking, and route completion. This frontend interacts heavily with delivery route endpoints, route sales endpoints, and client visit endpoints.

2. **Point-of-Sale Frontend**: Used primarily by cashiers and managers. Focuses on store sales, inventory management, client management, product management, and reporting. This frontend interacts with sales endpoints, product endpoints, client endpoints, and reporting endpoints.

Both frontends share authentication and user management endpoints, but their primary workflows differ significantly.

### User Role Interactions

**Managers (Gerente)**:
- Full system access
- Can approve inventory adjustments and returns
- Can create and modify any entity
- Can view all reports and data
- Can manage users and permissions

**Cashiers (Cajero)**:
- Can process store sales
- Can create inventory adjustments (requiring approval)
- Can view and modify clients and products
- Cannot manage routes or route sales
- Filtered to see only store sales in reports

**Delivery Personnel (Repartidor)**:
- Can view and manage their assigned delivery routes
- Can process route sales
- Can mark clients as visited
- Can create return requests (requiring approval)
- Cannot access store sales or general inventory management
- Filtered to see only their own delivery routes

### Data Flow Patterns

**Read Operations**: Most list endpoints support filtering, sorting, pagination, and date range filtering. This allows frontends to efficiently retrieve and display large datasets. The system uses database query optimization techniques (select_related, prefetch_related) to minimize database queries when loading related data.

**Write Operations**: Most write operations use database transactions to ensure atomicity. If any part of a complex operation fails, the entire operation is rolled back, preventing partial updates that could corrupt data integrity.

**Stock Updates**: Stock updates occur in bulk operations when possible. When multiple products are sold or loaded, the system calculates all changes first, then applies them in a single database operation. This improves performance and ensures consistency.

---

## System Architecture Considerations

### Multi-Tenancy Pattern

The system implements a soft multi-tenancy pattern using city-based data isolation. All data is stored in the same database, but logical separation is enforced through filtering. This approach balances operational independence with shared infrastructure and codebase.

### Image Management

User and product images are stored in the file system, organized by type (employees, products, defaults). The system automatically assigns default images when none are provided and removes old images when replaced or deleted. This ensures no orphaned files accumulate.

### Caching Strategy

The system includes caching infrastructure (Redis integration) but currently has caching disabled in most views. The signals system is prepared to invalidate caches when data changes, allowing easy re-enabling of caching for performance optimization when needed.

### Error Handling

The system validates all inputs and provides meaningful error messages. Database constraints prevent invalid data states. Transaction rollbacks ensure operations are all-or-nothing. The frontend receives clear error messages for operation failures.

### Time Zone Handling

All dates are stored in UTC in the database but converted to Mexico City timezone for filtering and display. This ensures consistent date handling across different client locations while maintaining accurate timezone representation.

---

## Operational Scenarios

### Daily Operations - Cashier

A cashier's day involves:
1. Logging in (receives token with role and city context)
2. Processing walk-in sales (selecting products, client pricing, finalizing transactions)
3. Processing client purchases (regular clients with personalized pricing)
4. Creating inventory adjustments when discrepancies are found (documented, awaiting approval)
5. Viewing sales reports and inventory levels

### Daily Operations - Delivery Personnel

A delivery person's workflow:
1. Logging in (receives token with their active delivery route ID if one exists)
2. Viewing their assigned delivery route for the day (products loaded, clients to visit)
3. Making sales at client locations (selecting products, quantities, applying client pricing)
4. Marking clients as visited when no sale occurs
5. Requesting product returns if needed (documented, awaiting approval)
6. Requesting product reloads if additional inventory is needed
7. Completing the route when all products are sold and all clients are visited

### Daily Operations - Manager

A manager's responsibilities:
1. Overseeing all operations
2. Approving inventory adjustments and returns
3. Creating and modifying products, clients, and routes
4. Managing user accounts and permissions
5. Reviewing reports from both cities
6. Handling exceptions and corrections

### End-of-Day Scenarios

Daily reconciliation involves:
- Reviewing all sales (store and route) for the day
- Verifying inventory adjustments and approvals
- Ensuring all delivery routes are completed or properly cancelled
- Reviewing pending returns and adjustments requiring approval
- Generating reports for accounting and analysis

---

## System Maintenance Considerations

### Product Price Updates

When product prices change, administrators must decide whether to update all client prices automatically or maintain existing client-specific pricing. This decision affects profit margins and client relationships.

### Client Price Management

Each client can have different prices for each product. This requires careful management to ensure accurate pricing. The system makes it easy to view and update client-specific pricing, but requires attention to maintain consistency.

### Route Planning

Routes must be planned carefully to ensure efficient delivery operations. Clients are assigned to route days, and routes are assigned to delivery personnel. Changes to routes or route days affect delivery planning and client expectations.

### Inventory Accuracy

The system requires regular physical inventory counts to be reconciled with system inventory through adjustments. The approval process ensures oversight of all inventory changes, maintaining accuracy and preventing fraud or errors.

---

## Performance and Scalability

The system is designed to handle moderate transaction volumes typical of a regional distribution business. Database queries are optimized using Django's select_related and prefetch_related methods to minimize database round trips. List endpoints are paginated to prevent loading excessive data into memory.

As the business grows, the system can scale by:
- Migrating to a more powerful database server (MySQL/PostgreSQL support is configured)
- Enabling Redis caching for frequently accessed data
- Optimizing database indexes (city fields are already indexed)
- Implementing read replicas for reporting workloads

---

## Security Considerations

The system implements security through:
- JWT token-based authentication (time-limited access tokens)
- Role-based access control (different capabilities per role)
- City-based data isolation (users cannot access other cities' data)
- CSRF protection middleware
- Input validation on all endpoints
- SQL injection prevention through Django ORM (no raw SQL queries)

---

## Future Enhancement Opportunities

The system's architecture supports potential enhancements such as:
- Multi-warehouse inventory tracking within each city
- Advanced reporting and analytics
- Mobile applications for delivery personnel
- Real-time notifications for route updates
- Integration with accounting systems
- Barcode scanning for products
- GPS tracking for delivery routes
- Automated route optimization
- Customer portal for order tracking
- Inventory forecasting and reorder points

---

This documentation provides a comprehensive understanding of the Gran Pacífico backend system's structure, workflows, business rules, and operational patterns. It serves as a foundation for developers, administrators, and stakeholders to understand how the system operates and how to work with it effectively.


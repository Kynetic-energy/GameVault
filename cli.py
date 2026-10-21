"""
GameVault Database Layer Demonstration CLI

Interactive menu-driven terminal interface to test and demonstrate
the capabilities, policy definitions, and configuration of db.py.
"""

import sys
from decimal import Decimal, InvalidOperation
from pprint import pprint

# Import components from db.py
try:
    import db
except ImportError:
    print("[!] Error: Could not import db.py. Ensure cli.py is in the same directory.")
    sys.exit(1)


def print_header(title: str) -> None:
    """Print a clean visual section header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def pause() -> None:
    """Prompt the user to press Enter before returning to the main menu."""
    input("\nPress [Enter] to return to the menu...")


# ------------------------------------------------------------
# Menu Handlers
# ------------------------------------------------------------

def handle_check_connection() -> None:
    """Check and display active MySQL database configuration and version."""
    print_header("1. Database Connection Check")
    try:
        info = db.check_connection()
        print("[✓] Connection successful!")
        print(f"    - Active Database: {info['database_name']}")
        print(f"    - MySQL Server Version: {info['server_version']}")
    except (db.DatabaseConfigurationError, db.DatabaseConnectionError) as exc:
        print(f"[×] Connection Failed: {exc}")


def handle_list_policies() -> None:
    """Display all registered operation policies defined in db.py."""
    print_header("2. Registered Operation Policies")
    for op_name, policy in db.OPERATION_POLICIES.items():
        print(f"\n• Operation: {op_name}")
        print(f"  - Action: {policy.action}")
        print(f"  - Target Source: {policy.source}")
        print(f"  - Access Policy: {policy.access_policy}")
        print(f"  - Result Fields ({len(policy.result_fields)}): {', '.join(policy.result_fields[:5])}...")
        
        if policy.allowed_filters:
            print(f"  - Allowed Filters: {', '.join(sorted(policy.allowed_filters))}")
        if policy.admin_writable_fields:
            print(f"  - Admin Writable Fields: {', '.join(sorted(policy.admin_writable_fields))}")
        if policy.publisher_writable_fields:
            print(f"  - Publisher Writable Fields: {', '.join(sorted(policy.publisher_writable_fields))}")


def handle_catalog_list() -> None:
    """Simulate building and executing a catalog.list search operation."""
    print_header("3. Simulate Operation: catalog.list")
    
    try:
        policy = db.get_operation_policy("catalog.list")
    except db.ValidationError as exc:
        print(f"[×] Policy Error: {exc}")
        return

    filters = {}
    print("Enter search parameters (press [Enter] to skip):")
    
    # Text Search
    q = input("  Search query (q): ").strip()
    if q:
        filters["q"] = q
        
    # Max Price
    max_price = input("  Max Price (INR): ").strip()
    if max_price:
        try:
            filters["max_price"] = str(Decimal(max_price))
        except InvalidOperation:
            print("[!] Invalid decimal value. Skipping max_price filter.")

    # Sort option selection
    print("\nAvailable Sort Expressions:")
    sort_keys = list(db.CATALOG_SORT_OPTIONS.keys())
    for idx, key in enumerate(sort_keys, 1):
        print(f"  {idx}. {key} -> ({db.CATALOG_SORT_OPTIONS[key]})")
    
    sort_choice = input(f"Select sort option (1-{len(sort_keys)}, default 1): ").strip()
    selected_sort = policy.default_sort
    if sort_choice.isdigit() and 1 <= int(sort_choice) <= len(sort_keys):
        selected_sort = sort_keys[int(sort_choice) - 1]

    # Display execution simulation
    print("\n--- Operation Parameters ---")
    print(f"Operation: catalog.list")
    print(f"Actor: None (Public)")
    print(f"Filters: {filters}")
    print(f"Sort Key: {selected_sort}")
    print(f"Page: 1 (Page Size: {policy.default_page_size})")

    # If build_operation / execute_operation were implemented:
    # result = db.execute_operation("catalog.list", actor=None, filters=filters, sort=selected_sort)
    print("\n[i] Note: Execution & query generation will occur once builder logic is implemented in db.py.")


def handle_catalog_detail() -> None:
    """Simulate building a catalog.detail operation."""
    print_header("4. Simulate Operation: catalog.detail")
    
    game_id_input = input("Enter Game ID: ").strip()
    if not game_id_input.isdigit() or int(game_id_input) <= 0:
        print("[!] Game ID must be a positive integer.")
        return

    game_id = int(game_id_input)
    policy = db.get_operation_policy("catalog.detail")

    print("\n--- Operation Parameters ---")
    print(f"Operation: catalog.detail")
    print(f"Actor: None (Public)")
    print(f"Target Table/View: {policy.source}")
    print(f"Filters: {{'game_id': {game_id}}}")


def handle_game_update() -> None:
    """Simulate authorized game updating based on actor context."""
    print_header("5. Simulate Operation: games.update (Authorization Context)")

    print("Select Trusted Actor Identity for this transaction:")
    print("  1. Public / Unauthenticated (actor = None)")
    print("  2. Regular Customer (actor = {user_id: 2, is_admin: False, affiliate_publisher_id: None})")
    print("  3. Affiliated Publisher (actor = {user_id: 3, is_admin: False, affiliate_publisher_id: 1})")
    print("  4. System Admin (actor = {user_id: 1, is_admin: True, affiliate_publisher_id: None})")
    
    actor_choice = input("Select Actor (1-4): ").strip()
    
    actor = None
    if actor_choice == "2":
        actor = {"user_id": 2, "is_admin": False, "affiliate_publisher_id": None}
    elif actor_choice == "3":
        actor = {"user_id": 3, "is_admin": False, "affiliate_publisher_id": 1}
    elif actor_choice == "4":
        actor = {"user_id": 1, "is_admin": True, "affiliate_publisher_id": None}

    game_id_input = input("\nEnter Game ID to modify: ").strip()
    if not game_id_input.isdigit():
        print("[!] Invalid Game ID.")
        return
    
    game_id = int(game_id_input)
    policy = db.get_operation_policy("games.update")

    # Evaluate permitted fields based on policy and selected actor
    if actor is None or (not actor.get("is_admin") and actor.get("affiliate_publisher_id") is None):
        print("\n[×] ACCESS DENIED: Public users and regular customers cannot modify catalog entries.")
        return

    writable_fields = (
        policy.admin_writable_fields if actor.get("is_admin") 
        else policy.publisher_writable_fields
    )

    print(f"\n[✓] Access Allowed! Permitted fields for this actor:")
    print(f"    {', '.join(sorted(writable_fields))}")
    
    if not actor.get("is_admin"):
        print(f"\n[!] Mandatory Security Scope Enforced: `publisher_id` automatically bound to {actor['affiliate_publisher_id']}.")

    print("\nProposed Updates (Simulated):")
    print(f"  - Target Game ID: {game_id}")
    print(f"  - Fields to update: standard_price, discount_percent")


# ------------------------------------------------------------
# Main CLI Loop
# ------------------------------------------------------------

def main_menu() -> None:
    """Display main menu options and route actions."""
    while True:
        print_header("GameVault Database Interface Tool")
        print("1. Test Database Connection")
        print("2. View Registered Operation Policies")
        print("3. Simulate 'catalog.list' Search")
        print("4. Simulate 'catalog.detail' Lookup")
        print("5. Simulate 'games.update' (Authorization & Policy Check)")
        print("0. Exit")

        choice = input("\nSelect an option [0-5]: ").strip()

        if choice == "1":
            handle_check_connection()
            pause()
        elif choice == "2":
            handle_list_policies()
            pause()
        elif choice == "3":
            handle_catalog_list()
            pause()
        elif choice == "4":
            handle_catalog_detail()
            pause()
        elif choice == "5":
            handle_game_update()
            pause()
        elif choice == "0":
            print("\nExiting GameVault DB Tool. Goodbye!")
            sys.exit(0)
        else:
            print("[!] Invalid option. Please enter a number between 0 and 5.")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user. Exiting...")
        sys.exit(0)